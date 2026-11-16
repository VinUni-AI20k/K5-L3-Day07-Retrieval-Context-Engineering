"""Smoke check fixture contract; add tests for your implementation."""
import json
import unittest
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter'))
from baseline import join_gold, validate


class FixtureTest(unittest.TestCase):
    def test_fixture_gold_resolves(self):
        chunks=json.loads((ROOT/'data/example_chunks.json').read_text(encoding='utf-8'))
        questions=json.loads((ROOT/'data/example_questions.json').read_text(encoding='utf-8'))
        for q in questions:
            for g in q['gold']:
                self.assertTrue(any(c['source_id']==g['source_id'] and c['page']==g['page'] and g['evidence'] in c['text'] for c in chunks))

    def test_day07_benchmark_is_independent_and_gold_is_separate(self):
        chunks = json.loads((ROOT / 'data/day06_strategy_c_chunks.json').read_text(encoding='utf-8'))
        questions = json.loads((ROOT / 'data/day07_questions.json').read_text(encoding='utf-8'))
        labels = json.loads((ROOT / 'data/day07_gold.json').read_text(encoding='utf-8'))
        private_fields = {'answerable', 'expected_answer', 'expected_behavior', 'absence_reason', 'gold'}
        self.assertTrue(all(not private_fields.intersection(q) for q in questions))
        labels_by_id = {label['id']: label for label in labels}

        counts = {
            split: (
                sum(q['split'] == split and labels_by_id[q['id']]['answerable'] for q in questions),
                sum(q['split'] == split and not labels_by_id[q['id']]['answerable'] for q in questions),
            )
            for split in ('dev', 'test')
        }
        self.assertEqual(counts, {'dev': (18, 2), 'test': (5, 2)})

        historical = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))
        historical_test = {q['question'] for q in historical if q['split'] == 'test'}
        new_test = [q for q in questions if q['split'] == 'test']
        self.assertTrue(all(q['question'] not in historical_test for q in new_test))
        validate(chunks, join_gold(questions, labels))


if __name__ == '__main__': unittest.main()
