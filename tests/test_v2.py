import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import brain
import main
import runner
import install
from memory import Memory


class V2Tests(unittest.TestCase):
    def test_ollama_request_and_validation(self):
        client = brain.OllamaBrain()
        proposal = {'answer': 'Liste', 'commands': [{'argv': ['ls', '-l'], 'explanation': 'Liste les fichiers'}]}
        response = Mock()
        response.readline.side_effect = [json.dumps({'message': {'content': json.dumps(proposal)}, 'done': True}).encode()]
        client.opener = MagicMock()
        client.opener.open.return_value.__enter__.return_value = response
        self.assertEqual(client.reply('aide', [], ['ls']), proposal)
        request = client.opener.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertTrue(payload['stream'])
        self.assertEqual(payload['format'], brain.SCHEMA)
        self.assertEqual(request.full_url, 'http://127.0.0.1:11434/api/chat')
        with self.assertRaises(ValueError):
            brain.validate_reply({'answer': 'x', 'commands': [{'argv': ['ls\nrm'], 'explanation': 'x'}]})
        with self.assertRaises(ValueError):
            brain.OllamaBrain('https://example.com')
        response.readline.side_effect = [b'broken']
        with self.assertRaises(RuntimeError):
            client.reply('aide', [], [])

    def test_confirmation(self):
        with patch('sys.stdin.isatty', return_value=False):
            ask = Mock(return_value='OUI')
            self.assertFalse(runner.confirm(['echo'], ask))
            ask.assert_not_called()
        with patch('sys.stdin.isatty', return_value=True):
            self.assertFalse(runner.confirm(['echo'], lambda _: 'oui'))
            self.assertTrue(runner.confirm(['echo'], lambda _: 'OUI'))

    def test_runner_limits_and_literal_shell(self):
        r = runner.run_command([sys.executable, '-c', 'import sys; print(sys.argv[1])', '$(touch danger); | >'])
        self.assertEqual(r['code'], 0)
        self.assertIn('$(touch danger); | >', r['output'])
        r = runner.run_command([sys.executable, '-c', 'import time; time.sleep(2)'], timeout=.1)
        self.assertEqual(r['reason'], 'Délai dépassé')
        r = runner.run_command([sys.executable, '-c', 'print("x" * 20000)'], limit=100)
        self.assertEqual(len(r['output']), 100)
        self.assertEqual(r['reason'], 'Limite de sortie atteinte')
        with self.assertRaises(ValueError):
            runner.run_command(['ia-lex-nonexistent-tool'])

    def test_memory(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'memory.json'
            memory = Memory(path)
            for index in range(110):
                memory.add_exchange(str(index), 'ok')
            self.assertEqual(len(Memory(path).messages), 200)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            path.write_text('{broken')
            with self.assertRaises(ValueError):
                Memory(path)
            self.assertEqual(path.read_text(), '{broken')

    def test_cli_full_flow(self):
        with tempfile.TemporaryDirectory() as temp:
            memory_path = Path(temp) / 'memory.json'
            fake = Mock(model='test-local')
            fake.reply.side_effect = [
                {'answer': 'Teste', 'commands': [{'argv': [sys.executable, '-c', 'print("RESULT_OK")'], 'explanation': 'Test local'}]},
                {'answer': 'Résultat compris', 'commands': []},
            ]
            with patch.object(main, 'MEMORY_PATH', memory_path), patch.object(main, 'OllamaBrain', return_value=fake), patch.object(main, 'confirm', side_effect=[False, True]), patch('builtins.input', side_effect=['bonjour', '/run', '/plan', '/run', 'analyse le résultat', '/quit']), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main.main(), 0)
            self.assertIn('Exécution annulée', output.getvalue())
            self.assertIn('RESULT_OK', output.getvalue())
            self.assertIn('Résultat compris', output.getvalue())
            self.assertEqual(fake.reply.call_count, 2)
            self.assertTrue(any('RESULT_OK' in item['content'] for item in Memory(memory_path).messages))

    def test_failed_command_stops_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Mock(model='test')
            fake.reply.return_value = {'answer': 'Test', 'commands': [
                {'argv': [sys.executable, '-c', 'raise SystemExit(4)'], 'explanation': 'Erreur'},
                {'argv': ['echo', 'MUST_NOT_RUN'], 'explanation': 'Suite'},
            ]}
            with patch.object(main, 'MEMORY_PATH', Path(temp)/'memory.json'), patch.object(main, 'OllamaBrain', return_value=fake), patch.object(main, 'confirm', return_value=True), patch('builtins.input', side_effect=['test', '/run', '/run', '/quit']), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main.main(), 0)
            self.assertIn('Plan arrêté', output.getvalue())
            self.assertIn('Aucune commande en attente', output.getvalue())
            self.assertEqual(fake.reply.call_count, 1)

    def test_script_and_install(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'plan.py'
            marker = Path(temp)/'marker'
            plan = [{'argv': [sys.executable, '-c', f'from pathlib import Path; Path({str(marker)!r}).touch()'], 'explanation': 'Créer fichier'}]
            runner.export_script(plan, target)
            compile(target.read_text(), str(target), 'exec')
            result = subprocess.run([sys.executable, str(target)], input='OUI\n', text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(marker.exists())  # entrée redirigée => refus
            import runpy
            with patch('sys.stdin.isatty', return_value=True), patch('builtins.input', return_value='OUI'), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(target), run_name='__main__')
            self.assertTrue(marker.exists())
            with self.assertRaises(FileExistsError):
                runner.export_script(plan, target)
            with contextlib.redirect_stdout(io.StringIO()):
                install.install(temp)
                install.install(temp)
            env = dict(os.environ, IA_LEX_MEMORY_PATH=str(Path(temp)/'history.json'))
            result = subprocess.run([str(Path(temp)/'.local/bin/bonjour'), 'ia-lex'], input='/help\n/tools python\n/quit\n', text=True, capture_output=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('PERSONAL V2.3', result.stdout)
            self.assertIn('/run', result.stdout)
            (Path(temp)/'.local/bin/bonjour').unlink()
            (Path(temp)/'.local/bin/bonjour').write_text('existing tool')
            with self.assertRaises(FileExistsError):
                install.install(temp)


if __name__ == '__main__':
    unittest.main()
