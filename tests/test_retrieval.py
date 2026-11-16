"""Focused tests for Day 6 dense and RRF hybrid retrieval."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter'))
from baseline import TfidfIndex, evaluate
from retrieval import DenseRetriever, RrfHybridRetriever


def chunk(chunk_id, text, page=1):
    return {
        'id': chunk_id,
        'text': text,
        'source_id': 'doc',
        'source': 'doc.pdf',
        'page': page,
        'metadata': {'section': 'POLICY'},
    }


class Embedder:
    def __init__(self, vector):
        self.vector = vector
        self.questions = []

    def embed_query(self, question):
        self.questions.append(question)
        return self.vector


class VectorStore:
    dimensions = 2

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def search(self, strategy, query_vector, top_k=3, filters=None):
        self.calls.append((strategy, query_vector, top_k, filters))
        return self.rows[:top_k]


class LexicalIndex:
    strategy = 'tfidf'

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def search(self, question, top_k=3, filters=None):
        self.calls.append((question, top_k, filters))
        return self.rows[:top_k]


class RetrievalTests(unittest.TestCase):
    def test_dense_adapter_embeds_query_and_preserves_day6_filter_and_order(self):
        rows = [
            {'chunk_id': 'dense-first', 'document_id': 'doc', 'source': 'doc.pdf',
             'page': 'unit-1', 'text': 'First evidence.', 'metadata': {'section': 'POLICY'}, 'score': 0.9},
            {'chunk_id': 'dense-second', 'document_id': 'doc', 'source': 'doc.pdf',
             'page': 'unit-2', 'text': 'Second evidence.', 'metadata': {'section': 'POLICY'}, 'score': 0.8},
        ]
        embedder = Embedder([0.25, 0.75])
        store = VectorStore(rows)
        dense = DenseRetriever(embedder, store, strategy='C')

        results = dense.search('refund period', top_k=2, filters={'section': 'POLICY'})

        self.assertEqual(embedder.questions, ['refund period'])
        self.assertEqual(store.calls, [('C', [0.25, 0.75], 2, {'section': 'POLICY'})])
        self.assertEqual([row['id'] for row in results], ['dense-first', 'dense-second'])
        self.assertEqual(results[0]['source_id'], 'doc')
        self.assertEqual(results[0]['strategy'], 'dense_day6')

    def test_dense_adapter_rejects_mismatched_embedding_dimensions(self):
        dense = DenseRetriever(Embedder([0.1]), VectorStore([]))
        with self.assertRaises(ValueError):
            dense.search('query')

    def test_dense_adapter_rejects_unsupported_filter_before_embedding(self):
        embedder = Embedder([0.1, 0.2])
        dense = DenseRetriever(embedder, VectorStore([]))
        with self.assertRaises(ValueError):
            dense.search('query', filters={'year': 2025})
        self.assertEqual(embedder.questions, [])

    def test_evaluate_converts_benchmark_filter_for_day6_vector_store(self):
        row = {'chunk_id': 'filtered', 'document_id': 'doc', 'source': 'doc.pdf',
               'page': 1, 'text': 'Evidence.', 'metadata': {'section': 'POLICY'}, 'score': 0.9}
        store = VectorStore([row])
        dense = DenseRetriever(Embedder([0.25, 0.75]), store)
        question = {'id': 'q', 'split': 'dev', 'question': 'query',
                    'filter': {'field': 'section', 'value': 'POLICY', 'provided_by': 'question'},
                    'gold': [{'source_id': 'doc', 'page': 1, 'evidence': 'Evidence.'}]}

        trace = evaluate(dense, [question])[0]

        self.assertEqual(store.calls[0][3], {'section': 'POLICY'})
        self.assertTrue(trace['hit1'])

    def test_rrf_hybrid_fuses_distinct_rankings_and_keeps_component_ranks(self):
        dense_rows = [chunk('a', 'Algebra rules.'), chunk('b', 'Linear equations.')]
        lexical_chunks = [chunk('b', 'Linear equations.'), chunk('c', 'Polynomial terms.')]
        dense = DenseRetriever(Embedder([0.2, 0.8]), VectorStore([
            {'chunk_id': row['id'], 'document_id': row['source_id'], 'source': row['source'],
             'page': row['page'], 'text': row['text'], 'metadata': row['metadata'], 'score': 0.8}
            for row in dense_rows
        ]))
        lexical = LexicalIndex([
            {**lexical_chunks[0], 'score': 0.7, 'strategy': 'tfidf'},
            {**lexical_chunks[1], 'score': 0.6, 'strategy': 'tfidf'},
        ])
        hybrid = RrfHybridRetriever(dense, lexical, candidate_k=3)

        results = hybrid.search('query', top_k=3)

        self.assertEqual([row['id'] for row in results], ['b', 'a', 'c'])
        self.assertEqual((results[0]['dense_rank'], results[0]['lexical_rank']), (2, 1))
        self.assertEqual((results[1]['dense_rank'], results[1]['lexical_rank']), (1, None))
        self.assertTrue(all(row['strategy'] == 'hybrid_rrf' for row in results))

    def test_evaluate_applies_question_filter_and_records_strategy(self):
        chunks = [chunk('wanted', 'Refunds last seven days.'),
                  {**chunk('other', 'Refunds last seven days.'), 'metadata': {'section': 'OTHER'}}]
        question = {'id': 'q', 'split': 'dev', 'question': 'Refunds last how many days?',
                    'filter': {'field': 'section', 'value': 'POLICY', 'provided_by': 'question'},
                    'gold': [{'source_id': 'doc', 'page': 1, 'evidence': 'seven days'}]}
        trace = evaluate(TfidfIndex(chunks), [question])[0]

        self.assertEqual([row['id'] for row in trace['results']], ['wanted'])
        self.assertEqual(trace['retrieval_filter'], {'section': 'POLICY'})
        self.assertEqual(trace['strategy'], 'tfidf')
        self.assertTrue(trace['hit1'])


if __name__ == '__main__':
    unittest.main()
