import json
import io
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from openrouter_controller import OpenRouterController


class Response:
    def __init__(self, value):
        self.value = json.dumps(value).encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.value


class OpenRouterControllerTests(unittest.TestCase):
    def test_decide_parses_json_and_records_usage_without_exposing_key(self):
        response = Response({
            'choices': [{'message': {'content': '{"action":"search","query":"evidence"}'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 4, 'total_tokens': 14, 'cost': 0.0001},
        })
        controller = OpenRouterController(api_key='test-secret', model='test-model')
        with patch('openrouter_controller.urllib.request.urlopen', return_value=response) as urlopen:
            result = controller.decide('question', [])

        request = urlopen.call_args.args[0]
        self.assertEqual(result, {'action': 'search', 'query': 'evidence'})
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-secret')
        self.assertEqual(json.loads(request.data)['model'], 'test-model')
        self.assertEqual(controller.calls[0]['total_tokens'], 14)
        self.assertNotIn('test-secret', json.dumps(controller.calls))

    def test_rejects_non_object_model_response(self):
        response = Response({
            'choices': [{'message': {'content': '[]'}}],
            'usage': {},
        })
        controller = OpenRouterController(api_key='test-secret', model='test-model')
        with patch('openrouter_controller.urllib.request.urlopen', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'invalid chat response'):
                controller.decide('question', [])
        self.assertIn('invalid response', controller.calls[0]['error'])

    def test_http_error_trace_omits_provider_user_identifiers(self):
        body = json.dumps({
            'error': {
                'message': 'Provider returned error',
                'metadata': {
                    'provider_name': 'OpenAI',
                    'provider_error_code': 'context_length_exceeded',
                    'raw': json.dumps({'error': {
                        'message': 'Reduce prompt length.',
                        'code': 'context_length_exceeded',
                    }}),
                },
            },
            'user_id': 'private-provider-id',
        }).encode('utf-8')
        error = HTTPError('https://example.invalid', 400, 'Bad Request', None, io.BytesIO(body))
        controller = OpenRouterController(api_key='test-secret', model='test-model')
        with patch('openrouter_controller.urllib.request.urlopen', side_effect=error):
            with self.assertRaisesRegex(RuntimeError, 'HTTP 400'):
                controller.decide('question', [])
        error_detail = json.dumps(controller.calls)
        self.assertIn('context_length_exceeded', error_detail)
        self.assertNotIn('private-provider-id', error_detail)


if __name__ == '__main__':
    unittest.main()
