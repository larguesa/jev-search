"""Offline v0.2 contracts; synthetic credentials and mocked HTTP only."""
import contextlib
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import jev_search as j

DEFAULT_RESPONSE = object()

class EvolutionTests(unittest.TestCase):
    def invoke(self, flags=(), env=None, response=DEFAULT_RESPONSE, raw_response=None):
        data = response if response is not DEFAULT_RESPONSE else {'model': j.MODEL, 'id': 'gen-test',
                            'usage': {'cost': 0, 'input_tokens': 1, 'output_tokens': 0},
                            'answers': {f'l{i}': {'type': 'noul', 'noul': .7} for i in range(20)}}
        http = MagicMock()
        http.__enter__.return_value.read.return_value = json.dumps(data).encode() if raw_response is None else raw_response
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, env or {}, clear=True), patch('sys.argv', [
                'jev-search', '--query', 'greeting',
                str(Path(__file__).parent / 'fixtures/synthetic.txt'), *flags]), \
                patch('urllib.request.OpenerDirector.open', return_value=http) as transport, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = j.main()
        return status, out.getvalue(), err.getvalue(), transport

    def test_typesafe_contract_and_model_selection(self):
        for flags, env, requested, returned in [
            (['--provider', 'typesafe'], {}, 'jev-1.13.0', 'jev-1.13.0'),
            ([], {'JEV_SEARCH_PROVIDER': 'typesafe', 'JEV_SEARCH_MODEL': 'jev-latest'}, 'jev-latest', 'jev-1.13.0'),
            (['--provider', 'typesafe', '--model', 'jev-2.0'], {'JEV_SEARCH_PROVIDER': 'openrouter', 'JEV_SEARCH_MODEL': 'ignored'}, 'jev-2.0', 'jev-2.0'),
        ]:
            data = {'model': returned, 'answers': {f'l{i}': {'type': 'noul', 'noul': .6} for i in range(20)},
                    'usage': {'input_tokens': 10, 'output_tokens': 0}}
            status, out, err, transport = self.invoke(flags, dict(env, JEV_SEARCH_API_KEY='synthetic-key'), data)
            self.assertEqual(status, 0, err)
            request = transport.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.typesafe.ai/v1/systemone')
            payload = json.loads(request.data)
            self.assertEqual(payload['model'], requested)
            self.assertEqual(set(payload), {'state', 'questions', 'model'})
            self.assertEqual(payload['questions']['l0']['type'], 'noul')
            self.assertNotIn('cost', json.loads(out)['raw_response']['usage'])

    def test_typesafe_aliases_accept_both_documented_response_forms(self):
        for alias in ['jev-latest', 'jev-preview']:
            for returned in [alias, 'jev-1.13.0']:
                with self.subTest(alias=alias, returned=returned):
                    data = {'model': returned, 'answers': {
                        f'l{i}': {'type': 'noul', 'noul': .6} for i in range(20)}}
                    status, out, err, transport = self.invoke(
                        ['--provider', 'typesafe', '--model', alias],
                        {'JEV_SEARCH_API_KEY': 'synthetic-key'}, data)
                    self.assertEqual(status, 0, err)
                    self.assertEqual(json.loads(out)['raw_response']['model'], returned)
                    self.assertEqual(transport.call_count, 1)

    def test_malformed_raw_json_is_controlled(self):
        for raw in [b'', b'{"sensitive":', b'sensitive-not-json']:
            with self.subTest(raw=raw):
                status, out, err, transport = self.invoke(
                    env={'JEV_SEARCH_API_KEY': 'synthetic-key'}, raw_response=raw)
                self.assertEqual(status, 1)
                self.assertFalse(out)
                self.assertNotIn('sensitive', err)
                self.assertIn('error', json.loads(err))
                self.assertEqual(transport.call_count, 1)

    def test_openrouter_custom_model_has_no_pilot_price_cap(self):
        status, out, err, transport = self.invoke(['--dry-run', '--model', 'typesafe/jev-future'])
        self.assertEqual(status, 0, err)
        payload = json.loads(out)['request']
        self.assertEqual(payload['model'], 'typesafe/jev-future')
        self.assertEqual(payload['provider'], {'only': ['typesafe'], 'allow_fallbacks': False, 'data_collection': 'deny'})

    def test_typesafe_optional_metadata_is_strict(self):
        rows = [{'original': 'hello', 'file': 'f', 'line': 1}]
        base = {'model': 'jev-1.13.0', 'answers': {'l0': {'type': 'noul', 'noul': .5}}}
        self.assertTrue(j.validate_response(base, rows, 'typesafe')[0]['match'])
        import copy
        for field, value in [('usage', None), ('usage', []), ('usage', {'cost': True}), ('usage', {'cost': 10**400}),
                             ('usage', {'input_tokens': -1}), ('usage', {'output_tokens': .5}),
                             ('id', 42), ('id', ''), ('model', None), ('answers', []),
                             ('answers', {'l0': None}), ('answers', {'l0': {'type': 'noul', 'noul': True}})]:
            bad = copy.deepcopy(base); bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                j.validate_response(bad, rows, 'typesafe')
        bad = copy.deepcopy(base); bad['answers']['l0']['confidence'] = float('nan')
        with self.assertRaises(ValueError): j.validate_response(bad, rows, 'typesafe')
        for provider, model in [('typesafe', 'jev-1.13.0'), ('openrouter', j.MODEL)]:
            good = dict(base, model=model, id='gen-test', usage={'cost': 100, 'input_tokens': 1, 'output_tokens': 0})
            self.assertTrue(j.validate_response(good, rows, provider)[0]['match'])

    def test_credentials_and_legacy_send(self):
        for provider in ['openrouter', 'typesafe']:
            for key in ['', 'synthetic\nkey', 'synthetic key', 'não-ascii']:
                status, out, err, transport = self.invoke(['--provider', provider], {
                    'JEV_SEARCH_API_KEY': key, 'OPENROUTER_API_KEY': 'not-a-fallback',
                    'TYPESAFE_API_KEY': 'not-a-fallback'})
                self.assertEqual(status, 1)
                self.assertFalse(out)
                self.assertNotIn('synthetic', err)
                transport.assert_not_called()
        status, out, err, transport = self.invoke(['--send'], {'JEV_SEARCH_API_KEY': 'synthetic-key'})
        self.assertEqual(status, 0, err)
        self.assertEqual(json.loads(out)['mode'], 'sent')
        self.assertEqual(transport.call_count, 1)

    def test_transport_errors_are_safe_and_not_retried(self):
        import urllib.error
        import http.client
        for provider in ['typesafe', 'openrouter']:
            for failure in [urllib.error.URLError('sensitive'), TimeoutError('sensitive'),
                            http.client.IncompleteRead(b'sensitive'),
                            urllib.error.HTTPError('https://example.invalid', 429, 'sensitive', {}, None)]:
                with patch('urllib.request.OpenerDirector.open', side_effect=failure) as transport:
                    with self.assertRaises(ValueError) as caught:
                        j.send_request({}, 'synthetic-key', provider)
                    self.assertNotIn('sensitive', str(caught.exception))
                    self.assertIn('not retried', str(caught.exception))
                    self.assertEqual(transport.call_count, 1)

    def test_invalid_configuration_and_responses(self):
        for env in [{'JEV_SEARCH_PROVIDER': 'unknown'}, {'JEV_SEARCH_MODEL': ''}, {'JEV_SEARCH_MODEL': 'bad\nmodel'}]:
            status, out, err, transport = self.invoke(['--dry-run'], env)
            self.assertEqual(status, 1)
            transport.assert_not_called()
        for data in [None, [], True, 42, 'sensitive', {'model': j.MODEL}, {'error': 'sensitive'}]:
            status, out, err, transport = self.invoke(env={'JEV_SEARCH_API_KEY': 'synthetic-key'}, response=data)
            self.assertEqual(status, 1)
            self.assertFalse(out)
            self.assertNotIn('sensitive', err)

    def test_real_search_is_default(self):
        status, out, err, transport = self.invoke(env={'JEV_SEARCH_API_KEY': 'synthetic-key'})
        self.assertEqual(status, 0, err)
        self.assertEqual(json.loads(out)['mode'], 'sent')
        self.assertEqual(transport.call_count, 1)
        request = transport.call_args.args[0]
        self.assertEqual(request.full_url, j.URL)
        self.assertEqual(request.get_header('Authorization'), 'Bearer synthetic-key')

    def test_dry_run_never_reads_key_or_network(self):
        original = os.environ.get
        def guarded(name, default=None):
            if name == 'JEV_SEARCH_API_KEY':
                self.fail('dry-run read credentials')
            return original(name, default)
        with patch.object(os.environ, 'get', side_effect=guarded):
            status, out, err, transport = self.invoke(['--dry-run'])
        self.assertEqual(status, 0, err)
        self.assertEqual(json.loads(out)['mode'], 'dry-run')
        transport.assert_not_called()

    def test_argument_errors_never_echo_rejected_values(self):
        import subprocess
        import sys
        marker = 'SYNTHETIC-PRIVATE-VALUE'
        for flags in [['--provider', marker], ['--max-requests', marker],
                      ['--max-requests', '987654321'], ['--' + marker]]:
            with self.subTest(flags=flags):
                run = subprocess.run([sys.executable, '-m', 'jev_search', '--dry-run',
                                      '--query', 'greeting', 'unused.txt', *flags],
                                     capture_output=True, text=True, env={})
                self.assertEqual(run.returncode, 2)
                self.assertFalse(run.stdout)
                self.assertNotIn(flags[-1], run.stderr)
                self.assertIn('invalid arguments', run.stderr)
                self.assertIn('--help', run.stderr)

    def test_help_remains_useful(self):
        import subprocess
        import sys
        run = subprocess.run([sys.executable, '-m', 'jev_search', '--help'],
                             capture_output=True, text=True, env={})
        self.assertEqual(run.returncode, 0, run.stderr)
        for option in ['--dry-run', '--provider', '--model', '--max-requests', '--query']:
            self.assertIn(option, run.stdout)
        self.assertFalse(run.stderr)

    def test_send_and_dry_run_are_exclusive(self):
        with self.assertRaises(SystemExit) as error:
            self.invoke(['--send', '--dry-run'])
        self.assertEqual(error.exception.code, 2)
