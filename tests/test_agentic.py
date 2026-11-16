"""Offline behavioral checks only; fake adapters do not measure model quality."""
import sys
import unittest
import json
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from agentic import run_agent

CHUNK = {'id': 'c1', 'text': 'Hoàn tiền trong 7 ngày.', 'source_id': 'doc',
         'source': 'doc.pdf', 'page': 1, 'score': 0.8, 'metadata': {}}

class Controller:
    def __init__(self, actions): self.actions = iter(actions)
    def decide(self, question, history): return next(self.actions)
    def verify(self, question, answer, citations, context):
        return {'supported': True, 'supported_citations': citations}

class Retriever:
    def __init__(self, results): self.results = results; self.calls = []
    def search(self, query, *, filters, top_k):
        self.calls.append((query, filters, top_k)); return self.results

class AgentTests(unittest.TestCase):
    def test_agent_searches_and_cites_actual_context(self):
        c = Controller([{'action': 'search', 'query': 'hoàn tiền'},
                        {'action': 'answer', 'answer': '7 ngày [c1]', 'citations': ['c1']}])
        r = Retriever([CHUNK]); result = run_agent('Hoàn tiền?', c, r, filters={'year': 2025})
        self.assertEqual(result['status'], 'answered')
        self.assertEqual(result['citations'], ['c1'])
        self.assertEqual(r.calls, [('hoàn tiền', {'year': 2025}, 3)])
        self.assertEqual(result['context_ids'], ['c1'])
        self.assertEqual(result['events'][1]['result'][0]['rank'], 1)
        self.assertEqual(result['events'][-2]['tool'], 'verify')

    def test_invalid_citation_and_empty_context_abstain(self):
        for rows, cid in (([CHUNK], 'not-present'), ([], 'c1')):
            c = Controller([{'action':'search','query':'q'}, {'action':'answer','answer':f'7 ngày [{cid}]','citations':[cid]}])
            self.assertEqual(run_agent('q', c, Retriever(rows))['status'], 'abstain')

    def test_search_limit_is_enforced(self):
        c = Controller([{'action':'search','query':'one'}, {'action':'search','query':'two'}, {'action':'search','query':'three'}])
        r = Retriever([CHUNK]); result = run_agent('q', c, r, max_searches=2)
        self.assertEqual(result['status'], 'abstain'); self.assertEqual(len(r.calls), 2)

    def test_context_budget_across_multiple_searches(self):
        other = {**CHUNK, 'id': 'c2', 'text': 'Một đoạn bằng chứng khác.'}
        class SequentialRetriever:
            def __init__(self): self.i = 0
            def search(self, query, *, filters, top_k):
                self.i += 1
                return [CHUNK] if self.i == 1 else [other]
        class InspectController:
            def __init__(self): self.i = 0
            def decide(self, question, history):
                self.i += 1
                if history:
                    assert len(history) == 1 and len(history[0]['context']) <= 90
                    assert len(history[0]['calls']) == self.i - 1
                if self.i <= 2: return {'action': 'search', 'query': str(self.i)}
                return {'action': 'answer', 'answer': '7 ngày [c1]', 'citations': ['c1']}
            def verify(self, question, answer, citations, context):
                return {'supported': True, 'supported_citations': citations}
        result = run_agent('q', InspectController(), SequentialRetriever(), budget=90)
        self.assertEqual(result['status'], 'answered')
        self.assertTrue(all(len(e['context']) <= 90 for e in result['events'] if e['event'] == 'tool_call'))

    def test_decision_history_does_not_duplicate_full_search_results(self):
        long_chunk = {**CHUNK, 'text': 'evidence ' * 10}

        class HistoryController(Controller):
            def __init__(self):
                super().__init__([
                    {'action': 'search', 'query': 'first'},
                    {'action': 'search', 'query': 'second'},
                    {'action': 'answer', 'answer': '7 days [c1]', 'citations': ['c1']},
                ])
                self.history_at_second_search = None

            def decide(self, question, history):
                if history and len(history[0]['calls']) == 1:
                    self.history_at_second_search = history[0]
                return super().decide(question, history)

        class RepeatedRetriever:
            def search(self, query, *, filters, top_k):
                return [long_chunk]

        controller = HistoryController()
        result = run_agent('question', controller, RepeatedRetriever())
        self.assertEqual(result['status'], 'answered')
        previous_result = controller.history_at_second_search['calls'][0]['results'][0]
        self.assertNotIn('text', previous_result)
        self.assertIn('context', controller.history_at_second_search)

    def test_configurable_retrieval_allows_more_than_two_calls(self):
        c = Controller([{'action': 'search', 'query': str(i)} for i in range(3)] +
                       [{'action': 'answer', 'answer': '7 ngày [c1]', 'citations': ['c1']}])
        r = Retriever([CHUNK])
        result = run_agent('q', c, r, max_searches=3, top_k=7, budget=1200)
        self.assertEqual(result['status'], 'answered')
        self.assertEqual(len(r.calls), 3)
        self.assertTrue(all(call[2] == 7 for call in r.calls))

    def test_tool_errors_are_not_hidden(self):
        class Broken:
            def search(self, query, *, filters, top_k): raise ConnectionError('database unavailable')
        result = run_agent('q', Controller([{'action':'search','query':'q'}]), Broken())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['errors'][0]['message'], 'database unavailable')
        self.assertEqual(result['events'][-1]['event'], 'tool_call')

    def test_unsupported_answer_abstains_even_with_valid_chunk_id(self):
        class UnsupportedController(Controller):
            def verify(self, question, answer, citations, context):
                return {'supported': False, 'supported_citations': [],
                        'reason': 'The cited passage does not support this claim.'}
        c = UnsupportedController([
            {'action': 'search', 'query': 'hoàn tiền'},
            {'action': 'answer', 'answer': 'Hoàn tiền trong 30 ngày [c1]', 'citations': ['c1']},
        ])
        result = run_agent('Hoàn tiền?', c, Retriever([CHUNK]))
        self.assertEqual(result['status'], 'abstain')
        self.assertEqual(result['citations'], [])
        self.assertTrue(any(event['event'] == 'verification_rejected' or
                            event['event'] == 'answer_rejected' for event in result['events']))

    def test_verifier_must_confirm_every_citation(self):
        class PartialVerifier(Controller):
            def verify(self, question, answer, citations, context):
                return {'supported': True, 'supported_citations': []}
        c = PartialVerifier([
            {'action': 'search', 'query': 'hoàn tiền'},
            {'action': 'answer', 'answer': '7 ngày [c1]', 'citations': ['c1']},
        ])
        result = run_agent('Hoàn tiền?', c, Retriever([CHUNK]))
        self.assertEqual(result['status'], 'abstain')
        self.assertIn('verification_rejected', [event['event'] for event in result['events']])

    def test_trace_is_persisted_with_final_context_and_model_calls(self):
        c = Controller([{'action': 'search', 'query': 'hoàn tiền'},
                        {'action': 'answer', 'answer': '7 ngày [c1]', 'citations': ['c1']}])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.json'
            result = run_agent('Hoàn tiền?', c, Retriever([CHUNK]), trace_path=path)
            saved = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(saved, result)
        self.assertIn('Hoàn tiền trong 7 ngày.', saved['context'])
        self.assertEqual([event['tool'] for event in saved['events']
                          if event['event'] == 'model_call'], ['decide', 'decide', 'verify'])

if __name__ == '__main__': unittest.main()
