import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import codework
import main
from brain import validate_reply


class CodeTests(unittest.TestCase):
    def test_create_replace_backup_and_stale(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            proposal = {'path': 'src/hello.py', 'content': 'print("bonjour")\n', 'explanation': 'Créer un programme'}
            edit = codework.prepare(root, proposal)
            self.assertFalse((root/'src').exists())
            self.assertIn('+print', codework.preview(edit))
            target, backup = codework.apply(edit, root/'backups')
            self.assertIsNone(backup)
            self.assertEqual(target.read_text(), proposal['content'])
            target.chmod(0o755)
            edit = codework.prepare(root, dict(proposal, content='print("salut")\n'))
            target, backup = codework.apply(edit, root/'backups')
            self.assertEqual(backup.read_text(), proposal['content'])
            self.assertEqual(target.stat().st_mode & 0o777, 0o755)
            edit = codework.prepare(root, proposal)
            target.write_text('changement externe')
            with self.assertRaises(ValueError):
                codework.apply(edit, root/'backups')
            self.assertEqual(target.read_text(), 'changement externe')

    def test_paths_binary_and_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for path in ('../escape', '/etc/passwd'):
                with self.assertRaises(ValueError):
                    codework.target_path(root, path)
            (root/'link').symlink_to('/tmp')
            with self.assertRaises(ValueError):
                codework.target_path(root, 'link/file')
            (root/'binary').write_bytes(b'\x00test')
            with self.assertRaises(ValueError):
                codework.read_file(root, 'binary')
            with self.assertRaises(ValueError):
                validate_reply({'answer': 'x', 'commands': [], 'files': [{'path': 'a', 'content': 2, 'explanation': 'x'}]})

    def test_cli_code_requires_confirmation(self):
        old = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp:
                os.chdir(temp)
                fake = Mock(model='test')
                fake.reply.return_value = {'answer': 'Code proposé', 'commands': [], 'files': [{'path': 'project/app.py', 'content': 'print("ok")\n', 'explanation': 'Créer le fichier'}]}
                with patch.object(main, 'MEMORY_PATH', Path(temp)/'memory.json'), patch.object(main, 'OllamaBrain', return_value=fake), patch.object(main, 'confirm', side_effect=[False, True]) as approval, patch('builtins.input', side_effect=['crée un programme', '/diff', '/apply', '/apply', '/quit']), contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(main.main(), 0)
                self.assertEqual(approval.call_count, 2)
                self.assertIn('Écriture annulée', output.getvalue())
                self.assertEqual((Path(temp)/'project/app.py').read_text(), 'print("ok")\n')
        finally:
            os.chdir(old)
