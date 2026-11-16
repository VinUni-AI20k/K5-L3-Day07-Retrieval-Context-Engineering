"""TF-IDF retrieval baseline for Day 7. Python 3.11+, standard library only."""
import argparse
import json
import math
import re
import statistics
import time
import unicodedata
from collections import Counter
from pathlib import Path


def tokenize(text):
    return re.findall(r'\w+', unicodedata.normalize('NFC', text).casefold())


def validate(chunks, questions):
    if not isinstance(chunks, list) or not chunks:
        raise ValueError('chunks phải là JSON array không rỗng')
    if not isinstance(questions, list) or not questions:
        raise ValueError('questions phải là JSON array không rỗng')
    ids = set()
    for c in chunks:
        for key in ('id', 'text', 'source_id', 'source', 'page', 'metadata'):
            if key not in c or c[key] is None:
                raise ValueError(f'chunk thiếu {key}')
        if not all(isinstance(c[k], str) and c[k].strip() for k in ('id', 'text', 'source_id', 'source')):
            raise ValueError('chunk id/text/source_id/source phải là chuỗi không rỗng')
        if not isinstance(c['metadata'], dict) or c['id'] in ids:
            raise ValueError('metadata phải là object và ID chunk phải duy nhất')
        ids.add(c['id'])
    ids.clear()
    for q in questions:
        if not isinstance(q.get('id'), str) or not q['id'].strip() or q['id'] in ids:
            raise ValueError('question id phải là chuỗi không rỗng và duy nhất')
        ids.add(q['id'])
        if q.get('split') not in ('dev', 'test') or not isinstance(q.get('question'), str) or not q['question'].strip():
            raise ValueError(f"question {q['id']}: split hoặc question không hợp lệ")
        if q.get('answerable', True) is False:
            if q.get('expected_behavior') != 'search_and_abstain' or not isinstance(q.get('absence_reason'), str) or not q['absence_reason'].strip():
                raise ValueError(f"question {q['id']}: câu thiếu evidence cần expected_behavior và absence_reason")
            if q.get('gold') not in (None, []):
                raise ValueError(f"question {q['id']}: câu thiếu evidence không được có gold")
            continue
        if not isinstance(q.get('expected_answer'), str) or not q['expected_answer'].strip():
            raise ValueError(f"question {q['id']}: expected_answer phải là chuỗi không rỗng")
        if not isinstance(q.get('gold'), list) or not q['gold']:
            raise ValueError(f"question {q['id']}: gold phải là danh sách không rỗng")
        for g in q['gold']:
            if not all(key in g and g[key] is not None for key in ('source_id', 'page', 'evidence')) or not isinstance(g['evidence'], str) or not g['evidence']:
                raise ValueError(f"question {q['id']}: gold không hợp lệ")
            if not any(hit(c, [g]) for c in chunks):
                raise ValueError(f"question {q['id']}: gold không nằm trọn trong chunk đúng nguồn/trang")


def join_gold(questions, labels):
    if not isinstance(questions, list) or not isinstance(labels, list):
        raise ValueError('questions và gold phải là JSON array')
    if any(not isinstance(q, dict) for q in questions) or any(not isinstance(label, dict) for label in labels):
        raise ValueError('mọi question và gold label phải là JSON object')
    private_fields = {'answerable', 'expected_answer', 'expected_behavior', 'absence_reason', 'gold'}
    label_fields = {'id', 'split', 'answerable', 'expected_answer', 'expected_behavior', 'absence_reason', 'gold'}
    question_ids = [q.get('id') for q in questions]
    label_ids = [label.get('id') for label in labels]
    if any(not isinstance(qid, str) or not qid for qid in question_ids):
        raise ValueError('mọi question phải có id không rỗng')
    if any(not isinstance(label_id, str) or not label_id for label_id in label_ids):
        raise ValueError('mọi gold label phải có id không rỗng')
    if len(set(question_ids)) != len(question_ids) or len(set(label_ids)) != len(label_ids):
        raise ValueError('question ID phải duy nhất trong questions và gold')
    if set(question_ids) != set(label_ids):
        raise ValueError('ID trong questions và gold phải khớp chính xác')
    if any(private_fields.intersection(q) for q in questions):
        raise ValueError('questions dành cho agent không được chứa nhãn gold')
    if any(set(label) - label_fields for label in labels):
        raise ValueError('gold chỉ được chứa ID, split và nhãn evaluator')
    labels_by_id = {label['id']: label for label in labels}
    joined = []
    for question in questions:
        label = labels_by_id[question['id']]
        if label.get('split') != question.get('split'):
            raise ValueError(f"{question['id']}: split trong questions và gold không khớp")
        joined.append({**question, **label})
    return joined


def hit(chunk, gold):
    return any(chunk['source_id'] == g['source_id'] and chunk['page'] == g['page'] and g['evidence'] in chunk['text'] for g in gold)


def retrieval_filters(question_filter):
    if question_filter is None:
        return None
    if not isinstance(question_filter, dict):
        raise ValueError('question filter phải là object')
    if 'field' in question_filter or 'value' in question_filter:
        if not {'field', 'value'} <= set(question_filter) or set(question_filter) - {'field', 'value', 'provided_by'}:
            raise ValueError('question filter cần field/value và không được có trường lạ')
        field = question_filter['field']
        if not isinstance(field, str) or not field.strip():
            raise ValueError('question filter field phải là chuỗi không rỗng')
        if question_filter.get('provided_by', 'question') != 'question':
            raise ValueError('retrieval filter chỉ được lấy từ câu hỏi đã cung cấp')
        return {field: question_filter['value']}
    return question_filter


class TfidfIndex:
    strategy = 'tfidf'

    def __init__(self, chunks):
        self.chunks = chunks
        counts = [Counter(tokenize(c['text'])) for c in chunks]
        df = Counter(term for row in counts for term in row)
        self.idf = {term: math.log((1 + len(chunks)) / (1 + count)) + 1 for term, count in df.items()}
        self.vectors = [self._vector(row) for row in counts]

    def _vector(self, counts):
        vector = {term: count * self.idf[term] for term, count in counts.items() if term in self.idf}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1
        return {term: value / norm for term, value in vector.items()}

    def search(self, question, top_k=3, filters=None):
        query = self._vector(Counter(tokenize(question)))
        results = []
        for chunk, vector in zip(self.chunks, self.vectors):
            if filters and any(chunk['metadata'].get(key) != value for key, value in filters.items()):
                continue
            score = sum(value * vector.get(term, 0) for term, value in query.items())
            if score > 0:
                results.append({**chunk, 'score': score, 'strategy': 'tfidf'})
        return sorted(results, key=lambda c: (-c['score'], c['id']))[:top_k]


def pack_context(results, budget=800):
    blocks, ids, seen = [], [], set()
    for c in results:
        if c['id'] in seen:
            continue
        seen.add(c['id'])
        block = f"[{c['id']} | {c['source']} | page {c['page']}]\n{c['text']}"
        if len('\n\n'.join(blocks + [block])) <= budget:
            blocks.append(block)
            ids.append(c['id'])
    return '\n\n'.join(blocks), ids


def evaluate(index, questions, budget=800):
    traces = []
    for q in questions:
        start = time.perf_counter()
        filters = retrieval_filters(q.get('filter'))
        results = index.search(q['question'], top_k=3, filters=filters)
        context, ids = pack_context(results, budget)
        elapsed_ms = (time.perf_counter() - start) * 1000
        answerable = q.get('answerable', True) is not False
        gold = q.get('gold', []) if answerable else []
        marked = [{**c, 'hit': hit(c, gold)} for c in results]
        traces.append({'query_id': q['id'], 'split': q['split'], 'question': q['question'],
                       'answerable': answerable,
                       'strategy': getattr(index, 'strategy', 'tfidf'), 'top_k': 3, 'budget_chars': budget,
                       'filter': q.get('filter'), 'retrieval_filter': filters,
                       'gold': gold, 'results': marked, 'context': context, 'context_ids': ids,
                       'context_chars': len(context), 'elapsed_ms': elapsed_ms,
                       'hit1': bool(marked and marked[0]['hit']),
                       'hit3': any(c['hit'] for c in marked),
                       'context_hit': any(c['hit'] and c['id'] in ids for c in marked)})
    return traces


def main():
    parser = argparse.ArgumentParser(description='Chạy baseline TF-IDF trên một split rõ ràng')
    parser.add_argument('--chunks', required=True, type=Path)
    parser.add_argument('--questions', required=True, type=Path)
    parser.add_argument('--gold', type=Path, help='Nhãn evaluator riêng; không đưa file này cho agent')
    parser.add_argument('--split', required=True, choices=('dev', 'test'))
    parser.add_argument('--output', required=True, type=Path, help='Thư mục output; file cùng tên sẽ bị ghi đè')
    args = parser.parse_args()
    chunks = json.loads(args.chunks.read_text(encoding='utf-8'))
    questions = json.loads(args.questions.read_text(encoding='utf-8'))
    if args.gold:
        labels = json.loads(args.gold.read_text(encoding='utf-8'))
        questions = join_gold(questions, labels)
    # Do not inspect held-out test evidence during dev work.
    selected = [q for q in questions if q.get('split') == args.split]
    validate(chunks, selected)
    started = time.perf_counter()
    index = TfidfIndex(chunks)
    index_seconds = time.perf_counter() - started
    traces = evaluate(index, selected)
    answerable_traces = [t for t in traces if t['answerable']]
    summary = {'strategy': getattr(index, 'strategy', 'tfidf'), 'split': args.split, 'n': len(answerable_traces),
               'questions_total': len(traces),
               'unanswerable_n': len(traces) - len(answerable_traces),
               'hit1': sum(t['hit1'] for t in answerable_traces),
               'hit3': sum(t['hit3'] for t in answerable_traces),
               'context_hit': sum(t['context_hit'] for t in answerable_traces),
               'avg_context_chars': statistics.mean(t['context_chars'] for t in traces),
               'median_ms': statistics.median(t['elapsed_ms'] for t in traces),
               'index_seconds': index_seconds, 'service_cost_usd': 0}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, obj in (('traces.json', traces), ('summary.json', summary)):
        (args.output / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
