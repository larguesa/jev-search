"""Offline ranking contracts; HTTP is simulated, never paid."""
import json
import unittest
from tests import test_evolution


class RankingTests(unittest.TestCase):
    def test_frozen_evidence_recomputes_without_inference(self):
        from tests import ranking_benchmark as b
        import hashlib
        fixture = json.loads(b.FIXTURE.read_bytes())
        evidence = json.loads(b.FIXTURE.with_name('ranking-results.json').read_text())
        self.assertEqual(hashlib.sha256(b.FIXTURE.read_bytes()).hexdigest(), evidence['fixture_sha256'])
        self.assertEqual(len(evidence['runs']), len(fixture['tasks']))
        for task, result in zip(fixture['tasks'], evidence['runs']):
            self.assertEqual(task['id'], result['task'])
            scores = [result['provider_response']['answers'][f'l{i}']['noul'] for i in range(len(task['candidates']))]
            matches = [i for i, score in enumerate(scores) if score >= fixture['design']['threshold']]
            k = fixture['design']['k']
            self.assertEqual(result['selected']['baseline'], matches[:k])
            self.assertEqual(result['selected']['ranked'], sorted(matches, key=lambda i: -scores[i])[:k])
            for arm in ['baseline', 'ranked']:
                self.assertEqual(result[arm], b.metrics(result['selected'][arm], [c['grade'] for c in task['candidates']], k))
        self.assertEqual(evidence['summary'], b.summarize(evidence['runs']))
        self.assertFalse(evidence['summary']['passes_exploratory_gate'])

    def test_rank_edge_cases_preserve_error_and_empty_match_semantics(self):
        from unittest.mock import patch
        import jev_search as j
        for k in ['0', '65', 'not-an-integer']:
            with self.subTest(k=k), self.assertRaises(SystemExit) as caught:
                test_evolution.EvolutionTests().invoke(['--top-k', k])
            self.assertEqual(caught.exception.code, 2)
        response = {'model': j.MODEL, 'id': 'gen-test', 'usage': {'cost': 0, 'input_tokens': 1, 'output_tokens': 0},
                    'answers': {f'l{i}': {'type': 'noul', 'noul': .49} for i in range(20)}}
        status, out, err, transport = self.invoke(['--rank'], {'JEV_SEARCH_API_KEY': 'synthetic-key'}, response)
        self.assertEqual(status, 0, err)
        self.assertEqual(json.loads(out)['ranked_results'], [])
        self.assertEqual(len(json.loads(out)['results']), 20)
        with patch('jev_search.load_files', side_effect=ValueError('no nonblank lines')):
            status, out, err, transport = self.invoke(['--rank'])
        self.assertEqual(status, 1)
        self.assertFalse(out)
        self.assertIsNone(json.loads(err)['unjudged']['candidates'])
        transport.assert_not_called()

    def invoke(self, *args, **kwargs):
        try:
            return test_evolution.EvolutionTests().invoke(*args, **kwargs)
        except SystemExit as error:
            self.fail(f'CLI rejected requested feature: exit {error.code}')

    def test_benchmark_live_path_freezes_inputs_and_uses_cli_ranking_once_per_task(self):
        from tests import ranking_benchmark as b
        self.assertTrue(hasattr(b, 'run'), 'live study runner missing')
        import contextlib, io, tempfile, types
        from pathlib import Path
        from unittest.mock import patch
        import jev_search as j
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'new-study'
            def simulated_cli(command, **kwargs):
                self.assertEqual((output / 'frozen.json').read_bytes(), b.FIXTURE.read_bytes())
                self.assertIn('--top-k', command)
                response = {'id': 'gen-private-test-id', 'model': j.MODEL,
                            'usage': {'cost': .001, 'input_tokens': 10, 'output_tokens': 0, 'extra': 'private-nested-metadata'},
                            'answers': {f'l{i}': {'type': 'noul', 'noul': score, 'extra': 'private-nested-metadata'}
                                        for i, score in enumerate([.1, .6, .9, .8, .1, .1, .1, .1])}}
                out, err = io.StringIO(), io.StringIO()
                with patch('sys.argv', command[2:]), patch.dict('os.environ', {'JEV_SEARCH_API_KEY': 'synthetic-key'}), \
                        patch('jev_search.send_request', return_value=(json.dumps(response).encode(), .25)), \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    status = j.main()
                return types.SimpleNamespace(returncode=status, stdout=out.getvalue(), stderr=err.getvalue())
            with patch('subprocess.run', side_effect=simulated_cli) as transport:
                evidence = b.run(output)
                self.assertEqual(transport.call_count, 6)
                with self.assertRaises(FileExistsError):
                    b.run(output)
                self.assertEqual(transport.call_count, 6)
            self.assertEqual(evidence['summary']['requests'], 6)
            for item in evidence['runs']:
                self.assertEqual(item['selected']['baseline'], [1, 2])
                self.assertEqual(item['selected']['ranked'], [2, 3])
            public = json.dumps(evidence)
            self.assertNotIn('gen-private', public)
            self.assertNotIn('private-nested-metadata', public)
            self.assertNotIn(directory, public)
            self.assertIn('gen-private', (output / 'refund-details.stdout.json').read_text())
            self.assertEqual(json.loads((output / 'public-results.json').read_text()), evidence)
            self.assertEqual(json.loads((output / 'status.json').read_text()), {'complete': True, 'attempts': 6})

    def test_benchmark_send_requires_explicit_new_output(self):
        from tests import ranking_benchmark as b
        import contextlib, io
        from unittest.mock import patch
        with patch('sys.argv', ['ranking_benchmark', '--send', '--output', 'new-run']), \
                patch('tests.ranking_benchmark.run', return_value={'summary': {'requests': 6}}) as run, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            try:
                status = b.main()
            except SystemExit:
                self.fail('benchmark has no explicit send entry point')
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out.getvalue()), {'requests': 6})
        run.assert_called_once()
        self.assertEqual(str(run.call_args.args[0]), 'new-run')

    def test_benchmark_relative_directory_becomes_absolute_for_child(self):
        from tests import ranking_benchmark as b
        import os, tempfile, types
        from pathlib import Path
        from unittest.mock import patch
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                def inspect_path(command, **kwargs):
                    self.assertTrue(Path(command[-1]).is_absolute(), 'child input path must be absolute')
                    return types.SimpleNamespace(returncode=1, stdout='', stderr='{}')
                with patch('subprocess.run', side_effect=inspect_path):
                    with self.assertRaisesRegex(ValueError, 'incomplete'):
                        b.run('relative-run')
            finally:
                os.chdir(previous)

    def test_benchmark_failure_is_persisted_and_never_retried(self):
        from tests import ranking_benchmark as b
        import tempfile, types
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'failed-study'
            failure = types.SimpleNamespace(returncode=1, stdout='', stderr='{"error":"network failure"}')
            with patch('subprocess.run', return_value=failure) as transport:
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    b.run(output)
                self.assertEqual(transport.call_count, 1)
            self.assertEqual((output / 'refund-details.stderr.json').read_text(), failure.stderr)
            status = json.loads((output / 'status.json').read_text())
            self.assertFalse(status['complete'])
            self.assertEqual(status['attempts'], 1)
            self.assertFalse((output / 'public-results.json').exists())

    def test_ranking_benchmark_defaults_offline(self):
        from tests import ranking_benchmark as b
        self.assertTrue(hasattr(b, 'main'), 'offline entry point missing')
        import contextlib, io
        from unittest.mock import patch
        with patch('sys.argv', ['ranking_benchmark']), patch('subprocess.run') as run, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(b.main(), 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data['mode'], 'dry-run')
        self.assertEqual(data['design']['requests'], 6)
        self.assertEqual(len(data['fixture_sha256']), 64)
        run.assert_not_called()

    def test_benchmark_summarizes_all_pairs_without_hiding_regressions(self):
        from tests import ranking_benchmark as b
        self.assertTrue(hasattr(b, 'summarize'), 'paired summary missing')
        rows = [{'latency_seconds': 1.0, 'cost_usd': .01,
                 'baseline': b.metrics([0, 1], [1, 1, 2], 2),
                 'ranked': b.metrics([2, 0], [1, 1, 2], 2)},
                {'latency_seconds': 3.0, 'cost_usd': .02,
                 'baseline': b.metrics([0, 1], [2, 2, 1], 2),
                 'ranked': b.metrics([2, 1], [2, 2, 1], 2)}]
        summary = b.summarize(rows)
        self.assertEqual(summary['requests'], 2)
        self.assertEqual(summary['cost_usd'], .03)
        self.assertEqual(summary['latency_seconds']['median'], 2)
        self.assertEqual(summary['ndcg_outcomes'], {'wins': 1, 'ties': 0, 'losses': 1})
        self.assertEqual(summary['baseline']['false_sufficient'], 1)
        self.assertEqual(summary['ranked']['false_sufficient'], 0)
        self.assertEqual(summary['baseline']['precision_at_k'], 1)
        self.assertEqual(summary['ranked']['precision_at_k'], 1)

    def test_ranking_metrics_distinguish_relevance_from_answer_support(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('tests.ranking_benchmark'), 'ranking benchmark missing')
        from tests import ranking_benchmark as b
        good = b.metrics([2, 1], [1, 0, 2], 2)
        self.assertEqual(good['precision_at_k'], .5)
        self.assertEqual(good['recall'], .5)
        self.assertEqual(good['answer_complete_precision_at_k'], .5)
        self.assertFalse(good['false_sufficient'])
        self.assertFalse(good['false_insufficient'])
        import math
        self.assertAlmostEqual(good['ndcg_at_k'], 3 / (3 + 1 / math.log2(3)))
        partial = b.metrics([0], [1, 0, 2], 2)
        self.assertTrue(partial['false_sufficient'])
        self.assertFalse(partial['false_insufficient'])
        self.assertEqual(partial['precision_at_k'], .5)
        empty = b.metrics([], [1, 0, 2], 2)
        self.assertTrue(empty['false_insufficient'])
        self.assertFalse(empty['false_sufficient'])
        self.assertEqual(b.metrics([], [0, 0], 2)['ndcg_at_k'], 0)

    def test_failure_marks_all_loaded_candidates_unjudged_without_partial_scores(self):
        from pathlib import Path
        import jev_search as j
        response = {'model': j.MODEL, 'id': 'gen-test',
                    'usage': {'cost': 0, 'input_tokens': 1, 'output_tokens': 0},
                    'answers': {'l0': {'type': 'noul', 'noul': .99}}}
        status, out, err, transport = self.invoke(['--rank'], {'JEV_SEARCH_API_KEY': 'synthetic-key'}, response)
        self.assertEqual(status, 1)
        self.assertFalse(out)
        data = json.loads(err)
        self.assertIn('incomplete answer IDs', data['error'])
        rows = j.load_files([str(Path(__file__).parent / 'fixtures/synthetic.txt')])
        self.assertEqual(data.get('unjudged'), {'reason': 'evaluation-failed',
            'candidates': [f'l{i}' for i in range(len(rows))]})
        self.assertNotIn('results', data)
        self.assertNotIn('probability', err)
        self.assertNotIn('original', err)
        self.assertEqual(transport.call_count, 1)

    def test_dry_run_marks_candidates_unjudged_not_nonmatches(self):
        status, out, err, transport = self.invoke(['--dry-run', '--top-k', '2'])
        self.assertEqual(status, 0, err)
        data = json.loads(out)
        self.assertEqual(data.get('unjudged'), {
            'reason': 'dry-run',
            'candidates': [f'l{i}' for i in range(len(data['rows']))]})
        self.assertNotIn('ranked_results', data)
        self.assertNotIn('results', data)
        transport.assert_not_called()

    def test_top_k_implies_rank_without_discarding_originals(self):
        status, out, err, transport = self.invoke(['--top-k', '2'], {'JEV_SEARCH_API_KEY': 'synthetic-key'})
        self.assertEqual(status, 0, err)
        data = json.loads(out)
        self.assertEqual(len(data['results']), 20)
        self.assertEqual(data['ranked_results'], data['results'][:2])
        self.assertEqual(transport.call_count, 1)

    def test_rank_is_stable_preserves_complete_results_and_request(self):
        response = {'model': 'typesafe/jev-1.13', 'id': 'gen-test',
                    'usage': {'cost': 0, 'input_tokens': 1, 'output_tokens': 0},
                    'answers': {f'l{i}': {'type': 'noul', 'noul': score}
                                for i, score in enumerate([.6, .9, .9, .49] + [.1] * 16)}}
        env = {'JEV_SEARCH_API_KEY': 'synthetic-key'}
        status, out, err, transport = self.invoke(env=env, response=response)
        self.assertEqual(status, 0, err)
        baseline = json.loads(out)
        self.assertNotIn('ranked_results', baseline)
        status, out, err, ranked_transport = self.invoke(['--rank'], env, response)
        self.assertEqual(status, 0, err)
        ranked = json.loads(out)
        self.assertEqual(ranked['results'], baseline['results'])
        self.assertEqual(ranked['raw_response'], baseline['raw_response'])
        self.assertEqual(ranked['ranked_results'], [baseline['results'][i] for i in [1, 2, 0]])
        self.assertEqual(ranked_transport.call_count, 1)
        self.assertEqual(ranked_transport.call_args.args[0].data, transport.call_args.args[0].data)
