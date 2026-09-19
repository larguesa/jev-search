import unittest, tempfile, pathlib, importlib.util

class Tests(unittest.TestCase):
    def test_explicit_utf8_lines(self):
        self.assertIsNotNone(importlib.util.find_spec('jev_search'), 'implementation missing')
        import jev_search as j
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'sample.txt'; p.write_text('Olá\n\nhello\n', encoding='utf8')
            self.assertEqual(j.load_files([str(p)]), [{'file':str(p),'line':1,'original':'Olá'}, {'file':str(p),'line':3,'original':'hello'}])

    def test_unsafe_inputs_rejected(self):
        import jev_search as j
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'data.txt'
            for raw in [b'a\x00b', b'\xff', b'x'*16385, b'a\n'*65, b'OPENROUTER_API_KEY=example', b'-----BEGIN PRIVATE KEY-----']:
                p.write_bytes(raw)
                with self.subTest(raw=raw[:20]), self.assertRaises(ValueError): j.load_files([str(p)])
            p.write_text('safe')
            for names in [[d], [str(p),str(p)]]:
                with self.assertRaises(ValueError): j.load_files(names)
            secret=pathlib.Path(d)/'.env.txt'; secret.write_text('safe')
            with self.assertRaises(ValueError): j.load_files([str(secret)])

    def test_symlink_rejected(self):
        import os, jev_search as j
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'data.txt'; p.write_text('safe')
            link=pathlib.Path(d)/'link.txt'
            try:
                link.symlink_to(p)
            except OSError as e:
                if os.name == 'nt' and e.winerror == 1314:
                    self.skipTest('Windows symlink privilege unavailable; junction tested separately')
                raise
            with self.assertRaisesRegex(ValueError, 'symlink'):
                j.load_files([str(link)])

    def test_decisions_contract(self):
        import jev_search as j, copy
        self.assertTrue(hasattr(j,'build_request'), 'request builder missing')
        rows=[{'file':'a.txt','line':1,'original':'hello'}]
        p=j.build_request(rows,'greeting')
        self.assertEqual(p['questions']['l0']['type'],'noul')
        self.assertNotIn('file',p['state']['lines']['l0'])
        for q in ['', 'x'*513, 'token=abc']:
            with self.assertRaises(ValueError): j.build_request(rows,q)
        good={'id':'gen-dec-test','model':'typesafe/jev-1.13-20260917','answers':{'l0':{'type':'noul','noul':0.9}},'usage':{'cost':0.001,'input_tokens':5,'output_tokens':1}}
        self.assertEqual(j.validate_response(good,rows)[0]['probability'],0.9)
        for v in [True,float('nan'),float('inf'),-0.1,1.1,'0.9']:
            bad=copy.deepcopy(good); bad['answers']['l0']['noul']=v
            with self.assertRaises(ValueError): j.validate_response(bad,rows)
        for field,value in [('model','other/model'),('answers',{}),('answers',dict(good['answers'],extra={'type':'noul','noul':0.5})),('usage',{'cost':True})]:
            bad=copy.deepcopy(good); bad[field]=value
            with self.assertRaises(ValueError): j.validate_response(bad,rows)

    def test_cli_dry_run_and_http(self):
        import jev_search as j, subprocess, sys, json
        self.assertTrue(hasattr(j,'send_request'),'HTTP implementation missing')
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'data.txt'; p.write_text('hello')
            run=subprocess.run([sys.executable,'-m','jev_search','--query','greeting',str(p)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)['mode'],'dry-run')
            for args in [['--max-requests','1.5'],['--max-requests','2'],['--send']]:
                run=subprocess.run([sys.executable,'-m','jev_search','--query','hello',str(p),*args],capture_output=True,text=True,env={})
                self.assertNotEqual(run.returncode,0)
        from unittest.mock import patch
        import urllib.error
        with patch('urllib.request.OpenerDirector.open',side_effect=urllib.error.URLError('offline')) as op:
            with self.assertRaises(ValueError): j.send_request({},'not-a-real-key')
            self.assertEqual(op.call_count,1)

    def test_benchmark_metrics(self):
        self.assertIsNotNone(importlib.util.find_spec('tests.benchmark'),'benchmark missing')
        from tests import benchmark as b
        self.assertEqual(b.metrics({1,2},{2,3}),{'tp':1,'fp':1,'fn':1,'precision':0.5,'recall':0.5})
        self.assertEqual(b.metrics(set(),{1})['precision'],0)
        self.assertTrue(hasattr(b,'run'),'benchmark runner missing')

    def test_match_flag(self):
        import jev_search as j
        d={'model':j.MODEL,'id':'gen-test','usage':{'cost':0,'input_tokens':0,'output_tokens':0},'answers':{'l0':{'type':'noul','noul':0.5}}}
        self.assertTrue(j.validate_response(d,[{'file':'f','line':1,'original':'s'}])[0].get('match'))

    def test_malformed_key_is_never_echoed(self):
        import jev_search as j
        from unittest.mock import patch
        for key in ['SYNTHETIC\nKEY','SYNTHETIC KEY','não-ascii','']:
            with patch('urllib.request.OpenerDirector.open') as op:
                with self.assertRaisesRegex(ValueError,'invalid inference credential') as error:
                    j.send_request({},key)
                self.assertNotIn('SYNTHETIC',str(error.exception)); op.assert_not_called()

if __name__=='__main__': unittest.main()
