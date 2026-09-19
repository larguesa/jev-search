"""Native filesystem regression checks, no network or credentials."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import jev_search as j


@unittest.skipUnless(os.name == 'nt', 'Windows filesystem')
class WindowsTests(unittest.TestCase):
    def test_binary_utf8_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'ação com espaços.txt'
            p.write_bytes('Olá\r\nworld\r\n'.encode('utf8'))
            self.assertEqual([r['original'] for r in j.load_files([str(p)])], ['Olá', 'world'])

    def test_junction_ancestor_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / 'target'
            target.mkdir()
            (target / 'data.txt').write_text('safe')
            link = root / 'junction'
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], check=True, capture_output=True)
            try:
                with self.assertRaisesRegex(ValueError, 'reparse|symlink'):
                    j.load_files([str(link / 'data.txt')])
            finally:
                link.rmdir()

    def test_alternate_stream_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'data.txt'
            p.write_text('safe')
            stream = str(p) + ':extra.txt'
            with open(stream, 'w') as f:
                f.write('hidden data')
            with self.assertRaisesRegex(ValueError, 'filename'):
                j.load_files([stream])

    def test_device_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'filename'):
            j.load_files(['NUL.txt'])
