"""Offline regression checks for the public release."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests import benchmark
import jev_search


class ReleaseTests(unittest.TestCase):
    def test_portable_skill_contract(self):
        root = Path(__file__).resolve().parent.parent
        path = root / 'skills' / 'jev-search' / 'SKILL.md'
        self.assertTrue(path.is_file(), 'portable skill missing')
        skill = path.read_text(encoding='utf8')
        self.assertTrue(skill.startswith('---\nname: jev-search\n'))
        self.assertIn('\n---\n', skill[4:])
        for required in ['description:', 'lexical', 'JEV_SEARCH_API_KEY',
                         'discovery directory', 'pinned checkout', '--dry-run',
                         'Real search is the default', '1 to 8', '16,384',
                         '64 physical lines', '2,048', '512', '60,000',
                         '.txt', '.md', '.csv', '.jsonl', '.log']:
            with self.subTest(required=required):
                self.assertIn(required, skill)

    def test_portable_skill_source_package_contract(self):
        import tomllib
        root = Path(__file__).resolve().parent.parent
        skill = 'skills/jev-search/SKILL.md'
        manifest = (root / 'MANIFEST.in').read_text(encoding='utf8').splitlines()
        self.assertIn('include ' + skill, manifest)
        metadata = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf8'))
        self.assertEqual(metadata['tool']['setuptools']['py-modules'], ['jev_search'])
        self.assertFalse(metadata['tool']['setuptools']['include-package-data'])
        # Git-only policy is absent from the source archive by design.
        if (root / '.gitignore').is_file():
            ignores = (root / '.gitignore').read_text(encoding='utf8').splitlines()
            for entry in ['!/skills/', '/skills/*', '!/skills/jev-search/',
                          '/skills/jev-search/*', '!/' + skill]:
                self.assertIn(entry, ignores)
        for document in ['README.md', 'docs/install.md']:
            text = (root / document).read_text(encoding='utf8')
            self.assertIn(skill, text)
            self.assertIn('pinned checkout', text)
            self.assertIn('does not automatically install', text)

    def test_public_test_layout(self):
        import importlib.util
        root = Path(__file__).resolve().parent
        if root.name == 'tests':
            root = root.parent
        self.assertTrue((root / 'tests' / '__init__.py').is_file())
        self.assertIsNotNone(importlib.util.find_spec('tests.benchmark'))
        for name in ['synthetic.txt', 'intents.json', 'benchmark-summary.json']:
            self.assertTrue((root / 'tests' / 'fixtures' / name).is_file(), name)
            self.assertFalse((root / name).exists(), name)

    def test_log_files_use_the_same_safety_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'application.log'
            path.write_text('checkout failed\n', encoding='utf8')
            self.assertEqual(jev_search.load_files([str(path)])[0]['original'], 'checkout failed')
            path.write_text('token=synthetic-example', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'possible secret'):
                jev_search.load_files([str(path)])

    def test_benchmark_requires_fresh_output_and_keeps_only_aggregates(self):
        rows = jev_search.load_files([str(Path(__file__).parent / 'fixtures' / 'synthetic.txt')])
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
        for flags in [[], ['--dry-run']]:
            with patch('jev_search.send_request') as send, patch('sys.argv', ['benchmark.py', *flags]), contextlib.redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(benchmark.main(), 0)
                data = json.loads(stream.getvalue())
                self.assertEqual(data['mode'], 'dry-run')
                self.assertEqual(data['requests'], 6)
                send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
