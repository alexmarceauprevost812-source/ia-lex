import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class ExecTests(unittest.TestCase):
    def test_manual_command_confirmation_and_no_ollama(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Mock(model='test')
            with patch.object(main, 'MEMORY_PATH', Path(temp)/'memory.json'), patch.object(main, 'OllamaBrain', return_value=fake), patch.object(main, 'confirm', side_effect=[False, True]) as confirmation, patch('builtins.input', side_effect=[f'/exec {sys.executable} --version', '/which python3', '/run', '/run', '/quit']), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main.main(), 0)
            self.assertEqual(confirmation.call_count, 2)
            fake.reply.assert_not_called()
            self.assertIn('Exécution annulée', output.getvalue())
            self.assertIn('Python', output.getvalue())

    def test_missing_program_not_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(main, 'MEMORY_PATH', Path(temp)/'memory.json'), patch.object(main, 'OllamaBrain', return_value=Mock(model='test')), patch.object(main, 'run_command') as run, patch('builtins.input', side_effect=['/exec ia-lex-nonexistent', '/run', '/quit']), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.main(), 0)
                run.assert_not_called()
