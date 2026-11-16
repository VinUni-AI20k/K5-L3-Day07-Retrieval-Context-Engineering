"""Offline checks of the Day 7 agent's own helpers (no model, no network, no gold)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agent import Context, ids_in_brackets, render_chunks, system_prompt, DEFAULT_CONFIG


def hit(i, n, rank=1):
    return {"id": i, "text": "x" * n, "page": 1, "source_id": "s", "metadata": {"section": "S", "chapter": 5}, "score": 1.0, "rank": rank}


class AgentHelperTests(unittest.TestCase):
    def test_grouped_bracket_ids(self):
        self.assertEqual(ids_in_brackets("a [B-1, B-2]; b [B-3]"), {"B-1", "B-2", "B-3"})

    def test_context_dedup_and_budget(self):
        c = Context(100)
        added, dups, dropped = c.admit([hit("a", 60), hit("b", 60), hit("c", 30)], "search")
        self.assertEqual([x["id"] for x in added], ["a", "c"])
        self.assertEqual(dropped, ["b"])
        added, dups, dropped = c.admit([hit("a", 60)], "search")
        self.assertEqual(dups, ["a"])
        self.assertLessEqual(c.used, 100)

    def test_chunks_are_delimited_and_prompt_says_data(self):
        c = Context(1000); added, _, _ = c.admit([hit("a", 5)], "search")
        self.assertIn('<chunk id="a"', render_chunks(added))
        self.assertIn("untrusted DATA", system_prompt({**DEFAULT_CONFIG}))


if __name__ == "__main__":
    unittest.main()
