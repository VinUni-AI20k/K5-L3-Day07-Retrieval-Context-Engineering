"""Behavior checks for the runnable Day 7 baseline and Day 6 JSON adapter."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter'))
from baseline import TfidfIndex, evaluate, hit, join_gold, pack_context, validate
from convert_day6 import convert_chunk, convert_question


def chunk(id, text, page=1):
    return {'id': id, 'source_id': 'doc', 'source': 'doc.pdf', 'page': page,
            'text': text, 'metadata': {'year': 2025}}


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [chunk('a', 'Hoàn tiền mất bảy ngày.'), chunk('b', 'Giao hàng mất ba ngày.', 2)]
        self.q = {'id': 'q', 'split': 'dev', 'question': 'Hoàn tiền bao lâu?',
                  'gold': [{'source_id': 'doc', 'page': 1, 'evidence': 'bảy ngày'}], 'expected_answer': 'bảy ngày'}

    def test_rank_and_evidence(self):
        validate(self.chunks, [self.q])
        trace = evaluate(TfidfIndex(self.chunks), [self.q])[0]
        self.assertEqual(trace['results'][0]['id'], 'a')
        self.assertTrue(trace['hit1'] and trace['hit3'] and trace['context_hit'])
        self.assertFalse(hit(self.chunks[1], self.q['gold']))

    def test_gold_alternative_and_wrong_page(self):
        valid = {'source_id': 'doc', 'page': 1, 'evidence': 'bảy ngày'}
        wrong = {'source_id': 'doc', 'page': 2, 'evidence': 'bảy ngày'}
        self.assertFalse(hit(self.chunks[0], [wrong]))
        self.assertTrue(hit(self.chunks[0], [wrong, valid]))
        with self.assertRaises(ValueError):
            validate(self.chunks, [{**self.q, 'gold': [wrong]}])

    def test_budget_dedup_and_empty_query(self):
        context, ids = pack_context([self.chunks[0], self.chunks[0]], 800)
        self.assertEqual(ids, ['a'])
        self.assertLessEqual(len(context), 800)
        self.assertEqual(pack_context(self.chunks, 1), ('', []))
        self.assertEqual(TfidfIndex(self.chunks).search('khôngkhớp'), [])
        trace = evaluate(TfidfIndex(self.chunks), [self.q], budget=1)[0]
        self.assertTrue(trace['hit3'])
        self.assertFalse(trace['context_hit'])

    def test_convert_day6_and_preserve_filter(self):
        raw_chunk = {'chunk_id': 'c1', 'document_id': 'doc', 'source': 'doc.pdf', 'page': 1,
                     'text': 'bảy ngày', 'metadata': {'year': 2025, 'section': 'POLICY'},
                     'embedding': [0.1, 0.2]}
        raw_q = {'id': 'q', 'split': 'dev', 'question': 'bao lâu', 'gold_source_id': 'doc',
                 'gold_page': 1, 'evidence_quote': 'bảy ngày', 'expected_answer': 'bảy ngày', 'filter': {'year': 2025}}
        c, q = convert_chunk(raw_chunk), convert_question(raw_q)
        validate([c], [q])
        self.assertEqual(q['filter'], {'year': 2025})
        self.assertEqual(c['id'], 'c1')
        self.assertEqual(c['metadata']['section'], 'POLICY')
        self.assertEqual(c['embedding'], [0.1, 0.2])

    def test_unanswerable_questions_convert_and_are_excluded_from_retrieval_metrics(self):
        raw = {'id': 'u1', 'split': 'dev', 'question': 'Hỏi ngoài nội dung?',
               'answerable': False, 'expected_behavior': 'search_and_abstain',
               'absence_reason': 'Không có nội dung này trong corpus.'}
        q = convert_question(raw)
        validate(self.chunks, [self.q, q])
        traces = evaluate(TfidfIndex(self.chunks), [self.q, q])
        self.assertTrue(traces[0]['answerable'])
        self.assertFalse(traces[1]['answerable'])
        self.assertEqual(traces[1]['gold'], [])
        self.assertFalse(traces[1]['hit1'] or traces[1]['hit3'] or traces[1]['context_hit'])
        with self.assertRaises(ValueError):
            validate(self.chunks, [{**q, 'gold': self.q['gold']}])

    def test_agent_questions_join_to_separate_gold_without_leaking_labels(self):
        question = {'id': 'q', 'split': 'dev', 'question': 'Hoàn tiền bao lâu?',
                    'filter': None}
        label = {'id': 'q', 'split': 'dev', 'answerable': True,
                 'expected_answer': 'bảy ngày',
                 'gold': [{'source_id': 'doc', 'page': 1, 'evidence': 'bảy ngày'}]}
        self.assertEqual(join_gold([question], [label]), [{**question, **label}])
        with self.assertRaises(ValueError):
            join_gold([{**question, 'expected_answer': 'bảy ngày'}], [label])
        with self.assertRaises(ValueError):
            join_gold([question], [{**label, 'split': 'test'}])

    def test_converter_appends_supplemental_questions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw_chunk = {'chunk_id': 'a', 'document_id': 'doc', 'source': 'doc.pdf', 'page': 1,
                         'text': 'Hoàn tiền mất bảy ngày.', 'metadata': {}}
            raw_question = {'id': 'q', 'split': 'dev', 'question': 'Hoàn tiền bao lâu?',
                            'gold_source_id': 'doc', 'gold_page': 1, 'evidence_quote': 'bảy ngày',
                            'expected_answer': 'bảy ngày'}
            missing = {'id': 'u', 'split': 'test', 'question': 'Câu ngoài nội dung?',
                       'answerable': False, 'expected_behavior': 'search_and_abstain',
                       'absence_reason': 'Không có nội dung này trong corpus.'}
            for name, value in (('chunks', [raw_chunk]), ('questions', {'questions': [raw_question]}),
                                ('supplement', [missing])):
                (root / f'{name}.json').write_text(json.dumps(value), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(ROOT / 'starter/convert_day6.py'),
                 '--chunks', str(root / 'chunks.json'),
                 '--questions', str(root / 'questions.json'),
                 '--supplemental', str(root / 'supplement.json'),
                 '--output', str(root / 'converted')],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            converted = json.loads((root / 'converted/questions.json').read_text(encoding='utf-8'))
            self.assertEqual([q['id'] for q in converted], ['q', 'u'])
            validate(json.loads((root / 'converted/chunks.json').read_text(encoding='utf-8')), converted)

    def test_cli_uses_requested_split_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'chunks.json').write_text(json.dumps(self.chunks), encoding='utf-8')
            unanswerable = {'id': 'u', 'split': 'dev', 'question': 'Hỏi ngoài nội dung?',
                            'answerable': False, 'expected_behavior': 'search_and_abstain',
                            'absence_reason': 'Không có nội dung này trong corpus.'}
            # A test gold which fails validation must not be inspected by a dev run.
            test = {**self.q, 'id': 't', 'split': 'test', 'gold': [{'source_id': 'x', 'page': 9, 'evidence': 'missing'}]}
            (root/'q.json').write_text(json.dumps([self.q, unanswerable, test]), encoding='utf-8')
            subprocess.run([sys.executable, str(ROOT/'starter/baseline.py'), '--chunks', str(root/'chunks.json'),
                            '--questions', str(root/'q.json'), '--split', 'dev', '--output', str(root/'out')],
                           check=True, capture_output=True, text=True)
            summary = json.loads((root/'out/summary.json').read_text())
            self.assertEqual((summary['split'], summary['n'], summary['hit1']), ('dev', 1, 1))
            self.assertEqual((summary['questions_total'], summary['unanswerable_n']), (2, 1))
            traces = json.loads((root/'out/traces.json').read_text(encoding='utf-8'))
            self.assertEqual(len(traces), 2)


if __name__ == '__main__': unittest.main()
