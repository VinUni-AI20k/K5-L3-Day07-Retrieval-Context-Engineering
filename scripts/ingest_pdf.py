"""Ingest text PDFs into a new collection the agent and UI can answer from (no OCR: the PDF must contain real text).

Usage (Day 7 .venv):
  python scripts/ingest_pdf.py PATH.pdf [PATH2.pdf ...] --name dai_so --title "Đại số tuyến tính" \
      [--description "..."] [--lang vi] [--math] [--skip-pages 1-5] [--model intfloat/multilingual-e5-small]
Afterwards the document is part of the "library" (rebuilt automatically, see scripts/build_library.py), which the UI
searches by default: no config needs to name the document.

Steps: extract text per page with pypdf -> clean (running headers/page numbers, PDF math glyph pieces, NFC) ->
chunk (~--chunk-chars characters, split at line boundaries, new chunk at each chapter/§ section, --overlap between
neighbouring chunks, breadcrumb "chapter > section" as the first line) -> embed with --model -> (re)create the Chroma
collection <name> in the active vector store -> write data/local_docs/<name>/{collection.json, chunks.json}.
Re-running replaces the collection. The textbook collections (soc3e_A/B) are never touched.

VnTeX PDFs (Vietnamese LaTeX, fonts named Vn*) often carry a broken ToUnicode table: the page renders fine but copied
text has wrong accents ("Phỗp" for "Phép"). By default those fonts are decoded from their glyph names instead, which
are correct; --keep-tounicode disables this.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import day6_store as d6  # noqa: E402
from src import local_docs as LD  # noqa: E402

# Adobe private-use glyph pieces used for tall brackets/braces in TeX math: keep one bracket char, drop extensions.
PUA = {0xF8EB: "(", 0xF8EE: "[", 0xF8F1: "{", 0xF8F6: ")", 0xF8F9: "]", 0xF8FC: "}"}
PUA.update({c: "" for c in range(0xF8E5, 0xF900) if c not in PUA})
NEGATED = {"⁄=": "≠", "⁄∈": "∉", "⁄⊂": "⊄", "⁄≡": "≢"}
CHAPTER_START = re.compile(r"^CHƯƠNG\s+(\d+)\s*$", re.I)
SECTION = re.compile(r"^§\s*(\d+)\.\s*(\S.*)$")
SUBSECTION = re.compile(r"^(\d+\.\d+)\s+([^\W\d_].{1,90})$")
RUNNING_HEADER_CHAPTER = re.compile(r"^\d+\s+Chương\s+(\d+)\.\s*(.+?)\.?$")


# --- extraction --------------------------------------------------------------------------------------
def extract_pages(pdf: Path, keep_tounicode: bool = False) -> list[str]:
    import pypdf
    from pypdf.generic import NameObject
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = pypdf.PdfReader(str(pdf))
    if not keep_tounicode:
        for page in reader.pages:
            res = page.get("/Resources")
            fonts = (res.get_object().get("/Font") if res is not None else None) or {}
            for ref in fonts.values():
                f = ref.get_object()
                if "+Vn" in str(f.get("/BaseFont")) and "/ToUnicode" in f and "/Encoding" in f:
                    del f[NameObject("/ToUnicode")]  # in memory only; the PDF file is never written
    return [p.extract_text() or "" for p in reader.pages]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(PUA)
    for k, v in NEGATED.items():
        text = text.replace(k, v)
    text = re.sub(r"⏐+", "|", text)
    text = re.sub(r"‖{2,}", "‖", text)
    return re.sub(r"[ \t]{2,}", " ", text)


def clean_page(raw: str) -> tuple[list[str], dict]:
    """Lines of one page without the running header and page-number footer, plus what the header told us."""
    lines = [ln.strip() for ln in normalize(raw).split("\n")]
    lines = [ln for ln in lines if ln]
    info: dict = {}
    if lines and lines[-1].isdigit():
        info["printed_page"] = int(lines[-1])
        lines = lines[:-1]
    if lines and "printed_page" in info:
        n = str(info["printed_page"])
        head = lines[0]
        m = RUNNING_HEADER_CHAPTER.match(head)
        if m and head.startswith(n + " "):
            info["chapter"], info["chapter_title"] = int(m.group(1)), m.group(2).strip()
            lines = lines[1:]
        elif head.endswith(" " + n) and len(head) < 120 and not (CHAPTER_START.match(head) or SECTION.match(head)):
            lines = lines[1:]  # "1. Logic 7": section title + page number (but never "CHƯƠNG 7" on page 7)
    return lines, info


# --- chunking ----------------------------------------------------------------------------------------
def pretty(title: str) -> str:
    t = title.strip().rstrip(".")
    return t[:1].upper() + t[1:].lower() if t.isupper() else t


def parse_pages(spec: str) -> set[int]:
    out: set[int] = set()
    for part in filter(None, (s.strip() for s in (spec or "").split(","))):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def build_chunks(pages: list[str], doc_id: str, source: str, id_prefix: str, chunk_chars: int = 1000,
                 overlap: int = 150, skip: set[int] | None = None) -> tuple[list[dict], dict[int, str]]:
    """pages[i] is the raw text of PDF page i+1. Returns (chunks, {chapter: title})."""
    skip = skip or set()
    chunks: list[dict] = []
    titles: dict[int, str] = {}
    per_page: dict[int, int] = {}
    st = {"chapter": None, "section": "", "sub": ""}
    buf: list[tuple[int, str]] = []          # (pdf page, line)
    head: dict = dict(st)                    # breadcrumb state when the buffer started
    pending_title: list[str] | None = None   # uppercase chapter-title lines right after "CHƯƠNG N"
    section_open = False                     # the previous line was a "§N. TITLE" heading (it may wrap)
    cleaned = {pno: clean_page(raw) for pno, raw in enumerate(pages, start=1) if pno not in skip}
    for _, info in cleaned.values():         # running headers ("6 Chương 1. Tập hợp - ...") give well-cased titles
        if info.get("chapter") is not None:
            titles.setdefault(info["chapter"], info["chapter_title"])

    def crumb(s):
        parts = []
        if s["chapter"] is not None:
            parts.append(f"Chương {s['chapter']}" + (f". {titles[s['chapter']]}" if s["chapter"] in titles else ""))
        parts += [p for p in (s["section"], s["sub"]) if p]
        return " › ".join(parts)

    def flush(carry: bool):
        nonlocal buf, head
        body = [ln for _, ln in buf]
        if sum(len(x) for x in body) >= 40:
            page = buf[0][0]
            idx = per_page.get(page, 0)
            per_page[page] = idx + 1
            bc = crumb(head)
            text = (f"[{bc}]\n" if bc else "") + "\n".join(body)
            chunks.append({"id": f"{id_prefix}-p{page:04d}-{idx:03d}", "text": text, "source_id": doc_id, "source": source,
                           "page": page, "metadata": {
                               "document_id": doc_id, "source": source, "page": page, "page_end": buf[-1][0],
                               "chapter": head["chapter"] if head["chapter"] is not None else 0,
                               "section": " › ".join(p for p in (head["section"], head["sub"]) if p),
                               "document_type": "body"}})
        kept: list[tuple[int, str]] = []
        if carry:
            size = 0
            for item in reversed(buf[1:]):   # never carry the whole chunk
                size += len(item[1])
                if size > overlap:
                    break
                kept.insert(0, item)
        buf = kept
        head = dict(st)

    for pno, (lines, _info) in cleaned.items():
        for ln in lines:
            if (m := CHAPTER_START.match(ln)):
                flush(carry=False)
                st.update(chapter=int(m.group(1)), section="", sub="")
                head = dict(st)
                pending_title = []
                buf.append((pno, ln))
                continue
            if pending_title is not None:
                if ln.isupper() and not SECTION.match(ln):
                    pending_title.append(ln)        # e.g. "TẬP HỢP - LOGIC - ÁNH XẠ - SỐ PHỨC"
                else:                               # fallback title when the PDF has no running headers
                    if pending_title:
                        titles.setdefault(st["chapter"], pretty(" ".join(pending_title)))
                    pending_title = None
            if section_open and ln.isupper() and not SECTION.match(ln):  # wrapped "§4. ..." heading, second line
                st["section"] += " " + pretty(ln).lower()
                head = dict(st)
                buf.append((pno, ln))
                continue
            section_open = False
            if (m := SECTION.match(ln)):
                if sum(len(x) for _, x in buf) >= 200:  # keep a bare chapter heading together with its first section
                    flush(carry=False)
                st.update(section=f"§{m.group(1)}. {pretty(m.group(2))}", sub="")
                head = dict(st)
                section_open = True
            elif (m := SUBSECTION.match(ln)) and not re.search(r"[=<>≤≥]", ln):
                if sum(len(x) for _, x in buf) >= chunk_chars // 3:
                    flush(carry=False)
                st["sub"] = f"{m.group(1)} {m.group(2).strip()}"
                if sum(len(x) for _, x in buf) < 200:  # buffer holds only headings so far: label it with this subsection
                    head = dict(st)
            buf.append((pno, ln))
            if sum(len(x) for _, x in buf) >= chunk_chars:
                flush(carry=True)
    flush(carry=False)
    return chunks, titles


# --- embedding + store ---------------------------------------------------------------------------------
def default_prefixes(model: str) -> tuple[str, str]:
    return ("query: ", "passage: ") if "e5" in model.lower() else ("", "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdfs", nargs="+", type=Path)
    ap.add_argument("--name", required=True, help="collection name: lowercase letters, digits, _ (e.g. dai_so)")
    ap.add_argument("--title", help="document title shown to the model and in the UI (kept from a previous run if omitted)")
    ap.add_argument("--description", help="one line on what the document is about")
    ap.add_argument("--lang", default="vi", help="document language code, e.g. vi or en (keyword search tokenizer)")
    ap.add_argument("--math", action="store_true", help="tell the model formulas were flattened by PDF extraction")
    ap.add_argument("--skip-pages", default="", help="PDF pages to leave out, e.g. 1-5 (cover, table of contents)")
    ap.add_argument("--model", default="intfloat/multilingual-e5-small", help="sentence-transformers embedding model")
    ap.add_argument("--query-prefix")
    ap.add_argument("--passage-prefix")
    ap.add_argument("--chunk-chars", type=int, default=1000)
    ap.add_argument("--overlap", type=int, default=150)
    ap.add_argument("--id-prefix", help="chunk id prefix (default: NAME in upper case)")
    ap.add_argument("--keep-tounicode", action="store_true", help="do not apply the VnTeX accent fix")
    ap.add_argument("--dry-run", type=Path, metavar="OUT.json",
                    help="only extract and chunk; write the chunks to OUT.json (no model, no vector store)")
    ap.add_argument("--no-library", action="store_true",
                    help="do not rebuild the all-documents library afterwards (scripts/build_library.py)")
    a = ap.parse_args(argv)

    if not LD.valid_name(a.name) or a.name == LD.LIBRARY:
        ap.error("--name must be 2-41 chars of a-z, 0-9, _ and not a textbook collection name or 'library'")
    for p in a.pdfs:
        if not p.is_file():
            ap.error(f"not a file: {p}")
    out_dir = LD.DOCS_DIR / a.name
    old = json.loads((out_dir / "collection.json").read_text(encoding="utf-8")) if (out_dir / "collection.json").is_file() else {}
    title = a.title or old.get("title") or a.pdfs[0].stem
    qp, pp = default_prefixes(a.model)
    qp = a.query_prefix if a.query_prefix is not None else qp
    pp = a.passage_prefix if a.passage_prefix is not None else pp
    prefix = a.id_prefix or a.name.upper().replace("_", "")

    t0 = time.perf_counter()
    chunks: list[dict] = []
    chapters: dict[int, str] = {}
    for i, pdf in enumerate(a.pdfs):
        pages = extract_pages(pdf, a.keep_tounicode)
        skip = parse_pages(a.skip_pages) if i == 0 or len(a.pdfs) == 1 else set()
        pid = prefix if len(a.pdfs) == 1 else f"{prefix}{i + 1}"
        cs, titles = build_chunks(pages, a.name, pdf.name, pid, a.chunk_chars, a.overlap, skip)
        chunks += cs
        for k, v in titles.items():
            chapters.setdefault(k, v)
        print(f"{pdf.name}: {len(pages)} pages -> {len(cs)} chunks")
    if not chunks:
        print("No text extracted. Scanned PDFs need OCR, which this script does not do.", file=sys.stderr)
        return 1
    if len(a.pdfs) > 1:
        chapters = {}  # chapter numbers would collide across files; filtering by chapter is disabled
    if a.dry_run:
        a.dry_run.write_text(json.dumps({"chapters": chapters, "chunks": chunks}, ensure_ascii=False, indent=1), encoding="utf-8")
        sizes = [len(c["text"]) for c in chunks]
        print(f"dry run: {len(chunks)} chunks (avg {sum(sizes) // len(sizes)} chars), chapters={chapters} -> {a.dry_run}")
        return 0

    from sentence_transformers import SentenceTransformer
    import chromadb
    model = SentenceTransformer(a.model, device="cpu")
    vecs = model.encode([pp + c["text"] for c in chunks], batch_size=16, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=False)
    try:
        store = d6.store_path()
    except FileNotFoundError:
        store = d6.LOCAL_STORE
    client = chromadb.PersistentClient(path=str(store))
    try:
        client.delete_collection(a.name)
    except Exception:
        pass
    col = client.create_collection(a.name, metadata={"hnsw:space": "cosine", "embed_model": a.model, "kind": "local_doc"})
    for i in range(0, len(chunks), 256):
        b = chunks[i:i + 256]
        col.upsert(ids=[c["id"] for c in b], documents=[c["text"] for c in b],
                   metadatas=[c["metadata"] for c in b], embeddings=vecs[i:i + 256].tolist())

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    manifest = {
        "name": a.name, "title": title, "description": a.description if a.description is not None else old.get("description", ""),
        "language": a.lang, "math": bool(a.math or old.get("math")), "sources": [p.name for p in a.pdfs],
        "embed_model": a.model, "query_prefix": qp, "passage_prefix": pp, "dim": int(vecs.shape[1]),
        "chunks": len(chunks), "chunk_chars": a.chunk_chars, "overlap": a.overlap, "skip_pages": a.skip_pages,
        "chapters": {str(k): v for k, v in sorted(chapters.items())}, "example_id": chunks[0]["id"],
        "built": date.today().isoformat(), "examples": old.get("examples", []),
    }
    (out_dir / "collection.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sizes = [len(c["text"]) for c in chunks]
    print(f"collection={a.name} count={col.count()} store={store} model={a.model} dim={vecs.shape[1]}")
    print(f"chunk chars: avg {sum(sizes) // len(sizes)}, min {min(sizes)}, max {max(sizes)}; chapters={manifest['chapters']}")
    print(f"wrote {out_dir / 'collection.json'} ({time.perf_counter() - t0:.1f}s)")
    if col.count() != len(chunks):
        return 1
    if not a.no_library:
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_library import build_library
        build_library()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
