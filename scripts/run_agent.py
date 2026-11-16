"""Run the agent on a benchmark split and write results/agent/<split>/<config>/traces.json.

Usage (Day 7 .venv): python scripts/run_agent.py --split dev --config base [--resume] [--ids d01,d02]
The config is configs/<name>.json (overrides src/agent.py DEFAULT_CONFIG). Reads ONLY benchmark/questions.json
(id/split/question); never reads gold. The test split is refused unless --allow-test.
Traces are saved after every query; --resume keeps non-error traces and re-runs errored/missing ones.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import agent as A  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("dev", "test"), required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--allow-test", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--ids", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.split == "test" and not a.allow_test:
        sys.exit("refusing to run the test split without --allow-test (config must be frozen first)")
    cfg = json.loads((ROOT / "configs" / f"{a.config}.json").read_text(encoding="utf-8"))
    cfg = cfg.get("config", cfg)  # configs/final.json nests the runnable config under "config"
    cfg["name"] = a.config
    qs = [q for q in json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8")) if q["split"] == a.split]
    if a.ids:
        want = set(a.ids.split(","))
        qs = [q for q in qs if q["id"] in want]
    out = Path(a.out) if a.out else ROOT / "results" / "agent" / a.split / a.config
    out.mkdir(parents=True, exist_ok=True)
    path = out / "traces.json"
    done = {}
    if a.resume and path.exists():
        done = {t["query_id"]: t for t in json.loads(path.read_text(encoding="utf-8")) if t["status"] != "error"}
    (out / "config.json").write_text(json.dumps({**A.DEFAULT_CONFIG, **cfg}, indent=2) + "\n", encoding="utf-8")
    client = A.GeminiClient({**A.DEFAULT_CONFIG, **cfg})
    traces = dict(done)
    for q in qs:
        if q["id"] in done:
            continue
        t = A.run_query(q["id"], q["question"], cfg, client)
        traces[q["id"]] = t
        ordered = [traces[x["id"]] for x in qs if x["id"] in traces]
        path.write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f'{q["id"]} {t["status"]:8s} tools={t["tool_calls"]} llm={t["llm_calls"]} tok={t["tokens"]["total"]} '
              f'{t["latency_s"]:.1f}s cites={t["citations"]} {t["errors"][:1]}', flush=True)
        if t["reason"] == "quota_exhausted":
            print("quota exhausted; stopping (resume later with --resume)")
            break


if __name__ == "__main__":
    main()
