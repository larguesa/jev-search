"""Offline regression checks for the public release."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmark
import jev_search


class ReleaseTests(unittest.TestCase):
    def test_log_files_use_the_same_safety_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'application.log'
            path.write_text('checkout failed\n', encoding='utf8')
            self.assertEqual(jev_search.load_files([str(path)])[0]['original'], 'checkout failed')
            path.write_text('token=synthetic-example', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'possible secret'):
                jev_search.load_files([str(path)])

    def test_benchmark_requires_fresh_output_and_keeps_only_aggregates(self):
        rows = jev_search.load_files([str(Path(__file__).parent / 'synthetic.txt')])
        response = {
            'id': 'gen-synthetic-not-for-publication', 'model': jev_search.MODEL,
            'usage': {'cost': 0.001, 'input_tokens': 10, 'output_tokens': 1},
            'answers': {f'l{i}': {'type': 'noul', 'noul': 0.1} for i in range(len(rows))},
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'new-run'
            with patch('jev_search.send_request', return_value=(json.dumps(response).encode(), 0.1)) as send:
                summary = benchmark.run('synthetic-test-key', output=output)
                self.assertEqual(send.call_count, 6)
                self.assertEqual(summary['requests'], 6)
                self.assertEqual(set(p.name for p in output.iterdir()), {'benchmark.json'})
                saved = (output / 'benchmark.json').read_text()
                for private in ['gen-synthetic', 'generation_ids', 'usage', 'file', str(Path.cwd())]:
                    self.assertNotIn(private, saved)
                with self.assertRaises(FileExistsError):
                    benchmark.run('synthetic-test-key', output=output)
                self.assertEqual(send.call_count, 6)

    def test_benchmark_cli_defaults_to_offline(self):
        with patch('jev_search.send_request') as send, patch('sys.argv', ['benchmark.py']), contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(benchmark.main(), 0)
            data = json.loads(stream.getvalue())
            self.assertEqual(data['mode'], 'dry-run')
            self.assertEqual(data['requests'], 6)
            send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
