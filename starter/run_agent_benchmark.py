"""Run the real OpenRouter-backed agent without loading evaluator labels."""
import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from agentic import run_agent
from baseline import TfidfIndex, retrieval_filters
from openrouter_controller import OpenRouterController
from retrieval import RrfHybridRetriever, _load_day6_retriever


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def _validate_questions(questions: Any, split: str) -> list[dict[str, Any]]:
    if not isinstance(questions, list):
        raise ValueError('questions must be a JSON array')
    ids: set[str] = set()
    selected = []
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError('each question must be a JSON object')
        query_id = question.get('id')
        if not isinstance(query_id, str) or not query_id or query_id in ids:
            raise ValueError('question IDs must be non-empty and unique')
        ids.add(query_id)
        if question.get('split') not in ('dev', 'test'):
            raise ValueError(f'{query_id}: invalid split')
        if not isinstance(question.get('question'), str) or not question['question'].strip():
            raise ValueError(f'{query_id}: question must be non-empty')
        if any(key in question for key in ('answerable', 'expected_answer', 'gold', 'absence_reason')):
            raise ValueError(f'{query_id}: evaluator-only labels are forbidden in questions')
        retrieval_filters(question.get('filter'))
        if question['split'] == split:
            selected.append(question)
    if not selected:
        raise ValueError(f'no questions found for split {split}')
    return selected


def _sum_usage(calls: list[dict[str, Any]], field: str) -> int | float | None:
    values = [call[field] for call in calls if isinstance(call.get(field), (int, float))]
    return sum(values) if values else None


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the OpenRouter-backed Day 7 agent.')
    parser.add_argument('--chunks', required=True, type=Path)
    parser.add_argument('--questions', required=True, type=Path)
    parser.add_argument('--split', required=True, choices=('dev', 'test'))
    parser.add_argument('--method', required=True, choices=('tfidf', 'hybrid'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--day6-starter', type=Path)
    parser.add_argument('--dotenv', type=Path)
    parser.add_argument('--day6-strategy', default='C')
    parser.add_argument('--candidate-k', type=int, default=10)
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--budget', type=int, default=800)
    parser.add_argument('--max-searches', type=int, default=4)
    args = parser.parse_args()
    if min(args.candidate_k, args.top_k, args.budget, args.max_searches) < 1:
        parser.error('candidate-k, top-k, budget, and max-searches must be positive')

    if args.dotenv:
        try:
            from dotenv import load_dotenv
        except ImportError as error:
            raise RuntimeError('python-dotenv is required when --dotenv is used') from error
        load_dotenv(args.dotenv)

    chunks = _read_json(args.chunks)
    questions = _validate_questions(_read_json(args.questions), args.split)
    if not isinstance(chunks, list) or not chunks:
        raise ValueError('chunks must be a non-empty JSON array')
    lexical = TfidfIndex(chunks)
    if args.method == 'hybrid':
        if args.day6_starter is None:
            parser.error('--day6-starter is required for hybrid retrieval')
        dense = _load_day6_retriever(args.day6_starter, args.dotenv, args.day6_strategy)
        retriever = RrfHybridRetriever(dense, lexical, candidate_k=args.candidate_k)
    else:
        dense = None
        retriever = lexical

    traces = []
    total_elapsed_ms = []
    for question in questions:
        controller = OpenRouterController()
        query_started = time.perf_counter()
        result = run_agent(
            question['question'],
            controller,
            retriever,
            filters=retrieval_filters(question.get('filter')),
            max_searches=args.max_searches,
            top_k=args.top_k,
            budget=args.budget,
        )
        elapsed_ms = (time.perf_counter() - query_started) * 1000
        usage = controller.calls
        trace = {
            'query_id': question['id'],
            'split': question['split'],
            'question': question['question'],
            'method': retriever.strategy,
            'model': controller.model,
            'parameters': {
                'day6_strategy': args.day6_strategy if args.method == 'hybrid' else None,
                'candidate_k': args.candidate_k if args.method == 'hybrid' else None,
                'top_k': args.top_k,
                'budget_chars': args.budget,
                'max_searches': args.max_searches,
                'filter': question.get('filter'),
            },
            **result,
            'model_usage': usage,
            'elapsed_ms': elapsed_ms,
        }
        traces.append(trace)
        total_elapsed_ms.append(elapsed_ms)
        print(json.dumps({
            'query_id': question['id'],
            'status': result['status'],
            'model_calls': len(usage),
            'elapsed_ms': round(elapsed_ms, 2),
        }, ensure_ascii=False))

    all_calls = [call for trace in traces for call in trace['model_usage']]
    statuses = {status: sum(trace['status'] == status for trace in traces)
                for status in ('answered', 'abstain', 'error')}
    embedding = getattr(getattr(dense, 'embedder', None), 'total_requests', 0)
    embedding_tokens = getattr(getattr(dense, 'embedder', None), 'total_tokens', 0)
    known_costs = [call['cost_usd'] for call in all_calls
                   if isinstance(call.get('cost_usd'), (int, float))]
    summary = {
        'split': args.split,
        'method': retriever.strategy,
        'model': traces[0]['model'],
        'questions': len(traces),
        'statuses': statuses,
        'median_ms_per_question': statistics.median(total_elapsed_ms),
        'model_calls': len(all_calls),
        'model_prompt_tokens': _sum_usage(all_calls, 'prompt_tokens'),
        'model_completion_tokens': _sum_usage(all_calls, 'completion_tokens'),
        'model_total_tokens': _sum_usage(all_calls, 'total_tokens'),
        'model_cost_usd': sum(known_costs) if len(known_costs) == len(all_calls) else None,
        'model_cost_usd_known': sum(known_costs) if known_costs else None,
        'model_calls_missing_cost': len(all_calls) - len(known_costs),
        'embedding_requests': embedding,
        'embedding_tokens': embedding_tokens,
        'embedding_cost_usd': None if embedding else 0,
        'parameters': traces[0]['parameters'],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'traces.json').write_text(
        json.dumps(traces, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    (args.output / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
