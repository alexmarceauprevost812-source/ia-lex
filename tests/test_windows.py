import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import install
import assistant_tools


class WindowsTests(unittest.TestCase):
    def test_windows_shortcuts_and_app_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {'LOCALAPPDATA': temp}), contextlib.redirect_stdout(io.StringIO()):
                install.install_windows(Path(temp), Path(install.__file__).parent)
            app = Path(temp)/'IA-LEX/app'
            self.assertTrue((app/'main.py').is_file())
            self.assertTrue((app/'codework.py').is_file())
            self.assertIn('main.py', (app/'ia-lex.cmd').read_text())
            self.assertIn('Utilisation : bonjour ia-lex', (app/'bonjour.cmd').read_text())

    def test_windows_diagnostics_are_only_proposals(self):
        with patch('assistant_tools.os.name', 'nt'), patch('assistant_tools.shutil.which', return_value='powershell.exe'):
            plan = assistant_tools.diagnostic_plan()
            self.assertEqual(len(plan), 3)
            self.assertEqual(plan[0]['argv'][:3], ['powershell.exe', '-NoProfile', '-NonInteractive'])
