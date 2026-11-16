"""Dense Day 6 and hybrid retrieval runners for the Day 7 benchmark."""
import argparse
import importlib
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Protocol

from baseline import TfidfIndex, evaluate, join_gold, validate


class Embedder(Protocol):
    def embed_query(self, question: str) -> list[float]:
        ...


class VectorStore(Protocol):
    dimensions: int

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        ...


class DenseRetriever:
    """Adapt the Day 6 embedder and pgvector store to the Day 7 chunk contract."""

    strategy = 'dense_day6'

    def __init__(self, embedder: Embedder, store: VectorStore, strategy: str = 'C') -> None:
        self.embedder = embedder
        self.store = store
        self.day6_strategy = strategy

    def search(
        self,
        question: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError('top_k must be positive.')
        if filters and (set(filters) != {'section'} or not isinstance(filters['section'], str)):
            raise ValueError('Day 6 supports only exact-match filtering on section.')
        query_vector = self.embedder.embed_query(question)
        if len(query_vector) != self.store.dimensions:
            raise ValueError('Query embedding dimension does not match the Day 6 vector store.')
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in query_vector):
            raise ValueError('Query embedding contains a non-finite value.')
        rows = self.store.search(
            self.day6_strategy,
            query_vector,
            top_k=top_k,
            filters=filters,
        )
        results = []
        for row in rows:
            required = ('chunk_id', 'document_id', 'source', 'page', 'text', 'metadata', 'score')
            if any(key not in row for key in required):
                raise ValueError('Day 6 vector store returned a chunk with missing fields.')
            if not isinstance(row['metadata'], dict):
                raise ValueError('Day 6 vector store returned non-object chunk metadata.')
            results.append({
                **row,
                'id': row['chunk_id'],
                'source_id': row['document_id'],
                'strategy': self.strategy,
            })
        if len(results) > top_k or len({chunk['id'] for chunk in results}) != len(results):
            raise ValueError('Day 6 vector store must return at most top_k unique chunk IDs.')
        return results


class RrfHybridRetriever:
    """Fuse dense and TF-IDF rankings with Reciprocal Rank Fusion."""

    strategy = 'hybrid_rrf'

    def __init__(self, dense: DenseRetriever, lexical: TfidfIndex, candidate_k: int = 10,
                 rrf_constant: int = 60) -> None:
        if candidate_k < 1 or rrf_constant < 1:
            raise ValueError('candidate_k and rrf_constant must be positive.')
        self.dense = dense
        self.lexical = lexical
        self.candidate_k = candidate_k
        self.rrf_constant = rrf_constant

    def search(
        self,
        question: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError('top_k must be positive.')
        dense_rows = self.dense.search(question, top_k=self.candidate_k, filters=filters)
        lexical_rows = self.lexical.search(question, top_k=self.candidate_k, filters=filters)
        fused: dict[str, dict[str, Any]] = {}
        for name, rows in (('dense', dense_rows), ('lexical', lexical_rows)):
            for rank, row in enumerate(rows, start=1):
                item = fused.setdefault(row['id'], {
                    **row,
                    'score': 0.0,
                    'dense_rank': None,
                    'lexical_rank': None,
                })
                item[f'{name}_rank'] = rank
                item['score'] += 1 / (self.rrf_constant + rank)
        results = sorted(
            fused.values(),
            key=lambda row: (
                -row['score'],
                min(rank for rank in (row['dense_rank'], row['lexical_rank']) if rank is not None),
                row['id'],
            ),
        )[:top_k]
        for row in results:
            row['strategy'] = self.strategy
        return results


def _load_day6_retriever(day6_root: Path, dotenv_path: Path | None, strategy: str) -> DenseRetriever:
    if not day6_root.is_dir():
        raise ValueError(f'Day 6 starter directory does not exist: {day6_root}')
    if dotenv_path:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path)
    sys.path.insert(0, str(day6_root))
    try:
        embeddings_module = importlib.import_module('src.embeddings')
        store_module = importlib.import_module('src.store')
    except ImportError as error:
        raise RuntimeError(
            'Could not import the Day 6 starter. Use its Python environment and pass --day6-starter.'
        ) from error

    embedder = embeddings_module.OpenRouterEmbedder()
    store = store_module.PgVectorStore(os.getenv('DATABASE_URL', ''), dimensions=embedder.dimensions)
    return DenseRetriever(embedder, store, strategy=strategy)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run Day 7 dense, TF-IDF, or hybrid retrieval.')
    parser.add_argument('--chunks', required=True, type=Path)
    parser.add_argument('--questions', required=True, type=Path)
    parser.add_argument('--gold', type=Path, help='Evaluator labels; never passed to a retriever.')
    parser.add_argument('--split', required=True, choices=('dev', 'test'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--method', required=True, choices=('dense', 'tfidf', 'hybrid'))
    parser.add_argument('--day6-starter', type=Path, help='Required by dense and hybrid methods.')
    parser.add_argument('--dotenv', type=Path, help='Day 6 .env path containing DATABASE_URL.')
    parser.add_argument('--day6-strategy', default='C')
    parser.add_argument('--candidate-k', type=int, default=10,
                        help='Candidate count per retriever before hybrid rank fusion.')
    parser.add_argument('--budget', type=int, default=800,
                        help='Maximum context size in characters.')
    args = parser.parse_args()
    if args.budget < 1:
        parser.error('--budget must be positive.')

    chunks = json.loads(args.chunks.read_text(encoding='utf-8'))
    questions = json.loads(args.questions.read_text(encoding='utf-8'))
    if args.gold:
        questions = join_gold(questions, json.loads(args.gold.read_text(encoding='utf-8')))
    selected = [question for question in questions if question.get('split') == args.split]
    validate(chunks, selected)

    lexical = TfidfIndex(chunks)
    started = time.perf_counter()
    dense = None
    if args.method in ('dense', 'hybrid'):
        if args.day6_starter is None:
            parser.error('--day6-starter is required for dense and hybrid methods.')
        dense = _load_day6_retriever(args.day6_starter, args.dotenv, args.day6_strategy)
    if args.method == 'dense':
        index = dense
    elif args.method == 'hybrid':
        index = RrfHybridRetriever(dense, lexical, candidate_k=args.candidate_k)
    else:
        index = lexical
    index_seconds = time.perf_counter() - started

    traces = evaluate(index, selected, budget=args.budget)
    answerable_traces = [trace for trace in traces if trace['answerable']]
    embedding_requests = getattr(getattr(dense, 'embedder', None), 'total_requests', 0)
    embedding_tokens = getattr(getattr(dense, 'embedder', None), 'total_tokens', 0)
    summary = {
        'strategy': index.strategy,
        'split': args.split,
        'n': len(answerable_traces),
        'questions_total': len(traces),
        'unanswerable_n': len(traces) - len(answerable_traces),
        'hit1': sum(trace['hit1'] for trace in answerable_traces),
        'hit3': sum(trace['hit3'] for trace in answerable_traces),
        'context_hit': sum(trace['context_hit'] for trace in answerable_traces),
        'avg_context_chars': statistics.mean(trace['context_chars'] for trace in traces),
        'budget_chars': args.budget,
        'median_ms': statistics.median(trace['elapsed_ms'] for trace in traces),
        'index_seconds': index_seconds,
        'embedding_requests': embedding_requests,
        'embedding_tokens': embedding_tokens,
        'service_cost_usd': None if embedding_requests else 0,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (('traces.json', traces), ('summary.json', summary)):
        (args.output / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
