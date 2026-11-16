"""Agent loop connecting a model controller to the Day 6 retriever."""
import json
import math
from pathlib import Path
from typing import Any, Protocol

from baseline import pack_context


class Controller(Protocol):
    def decide(self, question: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Use a model to choose search or answer from the supplied context."""
        ...

    def verify(
        self, question: str, answer: str, citations: list[str], context: str,
    ) -> dict[str, Any]:
        """Use a model to confirm that the cited source content supports the answer."""
        ...


class Retriever(Protocol):
    def search(
        self, query: str, *, filters: dict[str, Any] | None, top_k: int,
    ) -> list[dict[str, Any]]:
        """Return chunks with id, text, source_id, source, page, metadata and score/rank."""
        ...


def _result(
    status: str, answer: str, citations: list[str], events: list[dict[str, Any]],
    context: str, context_ids: list[str], errors: list[dict[str, str]],
    trace_path: str | Path | None,
) -> dict[str, Any]:
    result = {
        'status': status,
        'answer': answer,
        'citations': citations,
        'context': context,
        'context_ids': context_ids,
        'events': events,
        'errors': errors,
    }
    if trace_path is not None:
        path = Path(trace_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def run_agent(
    question: str,
    controller: Controller,
    retriever: Retriever,
    *,
    filters: dict[str, Any] | None = None,
    max_searches: int = 4,
    top_k: int = 3,
    budget: int = 800,
    trace_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run model-directed retrieval and return a complete, optionally persisted trace.

    A final answer is accepted only when every citation is in the final context and
    the controller's semantic verifier confirms that the sources support the answer.
    Adapter failures are returned explicitly with their trace and error details.
    """
    if not isinstance(question, str) or not question.strip() or max_searches < 1 or top_k < 1 or budget < 1:
        raise ValueError('question, max_searches, top_k hoặc budget không hợp lệ')

    history: list[dict[str, Any]] = []
    chunks: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    context, context_ids = '', []
    search_count = 0
    search_history: list[dict[str, Any]] = []

    for _ in range(max_searches + 1):
        decision_input = {'question': question, 'history': history}
        try:
            action = controller.decide(question, history)
        except Exception as error:
            errors.append({'stage': 'decide', 'type': type(error).__name__, 'message': str(error)})
            events.append({'event': 'model_call', 'tool': 'decide', 'input': decision_input,
                           'error': errors[-1]})
            return _result('error', '', [], events, context, context_ids, errors, trace_path)
        events.append({'event': 'model_call', 'tool': 'decide', 'input': decision_input,
                       'result': action})
        if not isinstance(action, dict):
            errors.append({'stage': 'decide', 'type': 'ValueError', 'message': 'model action phải là object'})
            events.append({'event': 'error', 'error': errors[-1]})
            return _result('error', '', [], events, context, context_ids, errors, trace_path)

        if action.get('action') == 'search':
            query = action.get('query')
            if not isinstance(query, str) or not query.strip():
                errors.append({'stage': 'decide', 'type': 'ValueError',
                               'message': 'search query phải là chuỗi không rỗng'})
                events.append({'event': 'error', 'error': errors[-1]})
                return _result('error', '', [], events, context, context_ids, errors, trace_path)
            if search_count >= max_searches:
                events.append({'event': 'search_limit', 'limit': max_searches})
                return _result('abstain', 'Không đủ bằng chứng để trả lời.', [],
                               events, context, context_ids, errors, trace_path)

            call = {'query': query, 'filters': filters, 'top_k': top_k}
            try:
                results = retriever.search(query, filters=filters, top_k=top_k)
                if not isinstance(results, list) or len(results) > top_k:
                    raise ValueError('retriever phải trả list có tối đa top_k chunk')
                normalized_results = []
                seen_ids = set()
                for rank, row in enumerate(results, start=1):
                    required = ('id', 'text', 'source_id', 'source', 'page', 'metadata')
                    if not isinstance(row, dict) or any(key not in row for key in required):
                        raise ValueError('retriever chunk thiếu trường id/text/source_id/source/page/metadata')
                    if (not isinstance(row['id'], str) or not row['id']
                            or not isinstance(row['text'], str) or not row['text']
                            or not isinstance(row['source_id'], str) or not row['source_id']
                            or not isinstance(row['source'], str) or not row['source']
                            or row['page'] is None or not isinstance(row['metadata'], dict)):
                        raise ValueError('retriever chunk có id/text/source/page/metadata không hợp lệ')
                    if row['id'] in seen_ids:
                        raise ValueError('retriever phải trả chunk ID duy nhất')
                    seen_ids.add(row['id'])
                    has_score = (isinstance(row.get('score'), (int, float))
                                 and not isinstance(row.get('score'), bool)
                                 and math.isfinite(row['score']))
                    has_rank = isinstance(row.get('rank'), int) and row['rank'] > 0
                    if not has_score and not has_rank:
                        raise ValueError('retriever chunk cần score hoặc rank')
                    normalized_results.append({**row, 'rank': row.get('rank', rank)})
                results = normalized_results
            except Exception as error:
                errors.append({'stage': 'search', 'type': type(error).__name__, 'message': str(error)})
                events.append({'event': 'tool_call', 'tool': 'search', 'input': call,
                               'error': errors[-1]})
                return _result('error', '', [], events, context, context_ids, errors, trace_path)

            search_count += 1
            candidates.extend(results)
            context, context_ids = pack_context(candidates, budget=budget)
            chunks = {chunk['id']: chunk for chunk in candidates if chunk['id'] in context_ids}
            events.append({'event': 'tool_call', 'tool': 'search', 'input': call,
                           'result': results, 'context': context, 'context_ids': context_ids})
            search_history.append({
                'query': query,
                'filters': filters,
                'results': [{
                    'id': chunk['id'],
                    'source': chunk['source'],
                    'page': chunk['page'],
                    'rank': chunk['rank'],
                    'score': chunk.get('score'),
                } for chunk in results],
            })
            history = [{
                'tool': 'search',
                'calls': search_history,
                'context': context,
                'context_ids': context_ids,
            }]
        elif action.get('action') == 'answer':
            answer, citations = action.get('answer'), action.get('citations')
            if (not isinstance(answer, str) or not isinstance(citations, list)
                    or any(not isinstance(item, str) for item in citations)):
                errors.append({'stage': 'decide', 'type': 'ValueError',
                               'message': 'answer/citations không hợp lệ'})
                events.append({'event': 'error', 'error': errors[-1]})
                return _result('error', '', [], events, context, context_ids, errors, trace_path)
            citations = list(dict.fromkeys(citations))
            valid_citations = bool(
                answer.strip() and citations and context
                and all(item in chunks and f'[{item}]' in answer for item in citations)
            )
            if not valid_citations:
                events.append({'event': 'answer_rejected', 'reason': 'invalid_or_missing_citations',
                               'answer': answer, 'citations': citations})
                return _result('abstain', 'Không đủ bằng chứng để trả lời.', [],
                               events, context, context_ids, errors, trace_path)

            verification_input = {
                'question': question,
                'answer': answer,
                'citations': citations,
                'context': context,
            }
            try:
                verification = controller.verify(question, answer, citations, context)
            except Exception as error:
                errors.append({'stage': 'verify', 'type': type(error).__name__, 'message': str(error)})
                events.append({'event': 'model_call', 'tool': 'verify', 'input': verification_input,
                               'error': errors[-1]})
                return _result('error', '', [], events, context, context_ids, errors, trace_path)
            events.append({'event': 'model_call', 'tool': 'verify', 'input': verification_input,
                           'result': verification})
            if not isinstance(verification, dict) or not isinstance(verification.get('supported'), bool):
                errors.append({'stage': 'verify', 'type': 'ValueError',
                               'message': 'verifier cần trả supported dạng boolean'})
                events.append({'event': 'error', 'error': errors[-1]})
                return _result('error', '', [], events, context, context_ids, errors, trace_path)
            supported_citations = verification.get('supported_citations')
            if (verification['supported']
                    and (not isinstance(supported_citations, list)
                         or any(not isinstance(item, str) for item in supported_citations)
                         or set(supported_citations) != set(citations))):
                verification = {**verification, 'supported': False,
                                'rejection_reason': 'not_all_citations_confirmed'}
                events.append({'event': 'verification_rejected', 'result': verification})
            if not verification['supported']:
                events.append({'event': 'answer_rejected', 'reason': 'evidence_not_supported',
                               'answer': answer, 'citations': citations})
                return _result('abstain', 'Không đủ bằng chứng để trả lời.', [],
                               events, context, context_ids, errors, trace_path)
            events.append({'event': 'answer', 'answer': answer, 'citations': citations})
            return _result('answered', answer, citations, events, context, context_ids, errors, trace_path)
        else:
            errors.append({'stage': 'decide', 'type': 'ValueError',
                           'message': 'action phải là search hoặc answer'})
            events.append({'event': 'error', 'error': errors[-1]})
            return _result('error', '', [], events, context, context_ids, errors, trace_path)

    return _result('abstain', 'Không đủ bằng chứng để trả lời.', [],
                   events, context, context_ids, errors, trace_path)
