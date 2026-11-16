"""Offline checks for user PDFs (scripts/ingest_pdf.py, src/local_docs.py) and that the frozen textbook path is unchanged.
No model, no network, no gold."""
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import agent as A  # noqa: E402
from src import retrievers as R  # noqa: E402

spec = importlib.util.spec_from_file_location("ingest_pdf", ROOT / "scripts" / "ingest_pdf.py")
ING = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ING)

FAKE = {"name": "fake_doc", "title": "Đại số tuyến tính", "description": "bài giảng", "language": "vi", "math": True,
        "embed_model": "x", "query_prefix": "query: ", "dim": 384, "example_id": "FAKE-p0006-000",
        "chapters": {"1": "Tập hợp", "2": "Ma trận"}}


def final_cfg():
    f = json.loads((ROOT / "configs" / "final.json").read_text(encoding="utf-8"))
    return f, {**A.DEFAULT_CONFIG, **f["config"]}


class TextbookUnchangedTests(unittest.TestCase):
    def test_frozen_system_prompt_hash(self):
        f, cfg = final_cfg()
        self.assertEqual(hashlib.sha256(A.system_prompt(cfg).encode("utf-8")).hexdigest(), f["system_prompt_sha256"])

    def test_textbook_chapters_and_tool_text(self):
        _, cfg = final_cfg()
        self.assertEqual(A.allowed_chapters(cfg), [5, 6, 7])
        search = A.tool_declarations(cfg)[0]
        self.assertIn("textbook chunks", search.description)
        self.assertIn("one of 5, 6, 7", search.parameters.properties["chapter"].description)

    def test_english_tokenizer_unchanged(self):
        self.assertEqual(R.tokenize("The socialization of children"), ["socialize", "children"])
        self.assertEqual(R.collection_lang("soc3e_B"), "en")


class VietnameseTests(unittest.TestCase):
    def test_tokenize_vi_syllables_and_pairs(self):
        toks = R.tokenize("Ma trận nghịch đảo của A", "vi")
        for t in ("ma", "trận", "nghịch", "đảo", "ma_trận", "nghịch_đảo"):
            self.assertIn(t, toks)
        self.assertNotIn("của", toks)
        self.assertIn("không_gian", R.tokenize("không gian véctơ", "vi"))

    def test_tokenize_vi_normalizes_unicode(self):
        decomposed = "ma trận"  # "trận" typed with combining marks
        self.assertIn("trận", R.tokenize(decomposed, "vi"))


class DocPromptTests(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(A.d6.LD, "manifest", side_effect=lambda n: FAKE if n == "fake_doc" else None)
        p.start()
        self.addCleanup(p.stop)
        self.cfg = {**A.DEFAULT_CONFIG, "collection": "fake_doc", "neighbors": True}

    def test_doc_prompt(self):
        sp = A.system_prompt(self.cfg)
        self.assertIn('"Đại số tuyến tính" (bài giảng)', sp)
        self.assertIn("written in Vietnamese", sp)
        self.assertIn("1 Tập hợp; 2 Ma trận", sp)
        self.assertIn("MATH:", sp)
        self.assertIn("[FAKE-p0006-000]", sp)
        self.assertIn("get_neighbors", sp)
        self.assertNotIn("Sociology", sp)

    def test_doc_tools_and_chapters(self):
        self.assertEqual(A.allowed_chapters(self.cfg), [1, 2])
        search = A.tool_declarations(self.cfg)[0]
        self.assertIn("document chunks", search.description)
        self.assertIn("one of 1, 2", search.parameters.properties["chapter"].description)


class IngestTests(unittest.TestCase):
    def test_normalize_math_glyphs(self):
        self.assertEqual(ING.normalize("det A ⁄= 0 ⏐⏐⏐ a b ⏐⏐⏐"), "det A ≠ 0 | a b |")
        self.assertEqual(ING.normalize(" 1 2  "), "[ 1 2 ]")

    def test_clean_page_strips_header_footer(self):
        lines, info = ING.clean_page("6 Chương 1. Tập hợp - Logic\nNội dung\n6")
        self.assertEqual(lines, ["Nội dung"])
        self.assertEqual((info["printed_page"], info["chapter"], info["chapter_title"]), (6, 1, "Tập hợp - Logic"))
        lines, _ = ING.clean_page("1. Logic 7\nNội dung khác\n7")
        self.assertEqual(lines, ["Nội dung khác"])

    def test_parse_pages(self):
        self.assertEqual(ING.parse_pages("1-3, 7"), {1, 2, 3, 7})
        self.assertEqual(ING.parse_pages(""), set())

    def test_build_chunks(self):
        body = "\n".join(f"Dòng nội dung số {i} về ma trận và định thức." for i in range(40))
        pages = ["Bìa sách", "CHƯƠNG 1\nTẬP HỢP - LOGIC\n§1. LOGIC\n1.1 Các phép toán logic\n" + body + "\n1",
                 "2 Chương 1. Tập hợp - Logic\n§2. TẬP HỢP\n" + body + "\n2"]
        chunks, titles = ING.build_chunks(pages, "d", "d.pdf", "D", chunk_chars=600, overlap=100, skip={1})
        self.assertEqual(titles, {1: "Tập hợp - Logic"})
        self.assertTrue(all(c["page"] in (2, 3) for c in chunks))
        self.assertEqual(len({c["id"] for c in chunks}), len(chunks))
        self.assertTrue(chunks[0]["text"].startswith("[Chương 1. Tập hợp - Logic › §1. Logic › 1.1 Các phép toán logic]"))
        self.assertTrue(all(len(c["text"]) < 900 for c in chunks))
        sec2 = [c for c in chunks if c["metadata"]["section"].startswith("§2")]
        self.assertTrue(sec2 and sec2[0]["page"] == 3 and sec2[0]["metadata"]["chapter"] == 1)
        # neighbouring chunks inside a section overlap; a new § section starts fresh
        self.assertIn(chunks[0]["text"].split("\n")[-1], chunks[1]["text"])


FAKE_LIB = {"name": "library", "kind": "library", "title": "All documents", "language": "multi", "math": True,
            "embed_model": "x", "query_prefix": "query: ", "dim": 384, "chapters": {}, "example_id": "B-soc3e-p0131-000",
            "documents": [{"collection": "secret_doc", "title": "Secret Title Nobody Should See", "chunks": 3}]}

spec_lib = importlib.util.spec_from_file_location("build_library", ROOT / "scripts" / "build_library.py")
LIB = importlib.util.module_from_spec(spec_lib)
spec_lib.loader.exec_module(LIB)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(A.d6.LD, "manifest", side_effect=lambda n: FAKE_LIB if n == "library" else None)
        p.start()
        self.addCleanup(p.stop)
        self.cfg = {**A.DEFAULT_CONFIG, "collection": "library", "neighbors": True, "allow_chapter_filter": False}

    def test_library_prompt_reveals_no_documents(self):
        sp = A.system_prompt(self.cfg)
        self.assertIn("library of documents", sp)
        self.assertIn("do not know in advance", sp)
        for leak in ("Secret Title", "secret_doc", "Sociology", "soc3e", "Đại số", "chapter"):
            self.assertNotIn(leak, sp)
        self.assertIn("MATH:", sp)

    def test_library_search_tool_has_no_filter(self):
        self.assertEqual(A.allowed_chapters(self.cfg), [])
        search = A.tool_declarations(self.cfg)[0]
        self.assertEqual(set(search.parameters.properties), {"query", "top_k"})
        self.assertIn("every document in the library", search.description)

    def test_tokenize_multi(self):
        toks = R.tokenize("Socialization and ma trận nghịch đảo", "multi")
        for t in ("socialize", "ma", "trận", "ma_trận", "nghịch_đảo"):
            self.assertIn(t, toks)
        self.assertNotIn("and", toks)

    def test_document_shown_only_for_library_chunks(self):
        ctx = A.Context(1000)
        meta = {"section": "S", "chapter": 1}
        added, _, _ = ctx.admit([{"id": "a", "text": "x", "page": 1, "metadata": meta},
                                 {"id": "b", "text": "y", "page": 2, "metadata": {**meta, "doc_title": "Book B"}}], "search")
        self.assertNotIn("document", added[0])          # textbook chunks: unchanged shape and rendering
        self.assertEqual(A.render_chunks([added[0]]), '<chunk id="a" page="1" section="S">\nx\n</chunk>')
        self.assertIn('<chunk id="b" document="Book B" page="2"', A.render_chunks([added[1]]))

    def test_collect_tags_documents_and_rejects_duplicate_ids(self):
        tb = [{"id": "T-1", "text": "t", "page": 1, "metadata": {"chapter": 5, "nested": {"x": 1}}}]
        doc = [{"id": "D-1", "text": "d", "page": 2, "metadata": {"chapter": 1}}]
        with mock.patch.object(LIB.d6, "load_chunks", return_value=tb), \
                mock.patch.object(LIB.LD, "document_names", return_value=["my_doc"]), \
                mock.patch.object(LIB.LD, "manifest", return_value={"title": "My Doc", "language": "vi"}), \
                mock.patch.object(LIB.LD, "load_chunks", return_value=doc):
            chunks, docs = LIB.collect()
            self.assertEqual([(c["id"], c["metadata"]["document"], c["metadata"]["doc_title"]) for c in chunks],
                             [("T-1", "soc3e_B", LIB.TEXTBOOK[1]), ("D-1", "my_doc", "My Doc")])
            self.assertNotIn("nested", chunks[0]["metadata"])  # Chroma metadata must be flat
            self.assertEqual([d["chunks"] for d in docs], [1, 1])
        with mock.patch.object(LIB.d6, "load_chunks", return_value=tb), \
                mock.patch.object(LIB.LD, "document_names", return_value=["my_doc"]), \
                mock.patch.object(LIB.LD, "manifest", return_value={"title": "My Doc"}), \
                mock.patch.object(LIB.LD, "load_chunks", return_value=tb):
            with self.assertRaises(SystemExit):
                LIB.collect()


if __name__ == "__main__":
    unittest.main()
