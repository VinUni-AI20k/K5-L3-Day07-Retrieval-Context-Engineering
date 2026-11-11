"""Smoke check fixture contract; add tests for your implementation."""
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class FixtureTest(unittest.TestCase):
    def test_fixture_gold_resolves(self):
        chunks=json.loads((ROOT/'data/example_chunks.json').read_text(encoding='utf-8'))
        questions=json.loads((ROOT/'data/example_questions.json').read_text(encoding='utf-8'))
        for q in questions:
            for g in q['gold']:
                self.assertTrue(any(c['source_id']==g['source_id'] and c['page']==g['page'] and g['evidence'] in c['text'] for c in chunks))
if __name__ == '__main__': unittest.main()
