import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main
from projects import Projects
from assistant_tools import diagnostic_plan, tool_guide


class TerminalTests(unittest.TestCase):
    def test_projects_validation_and_private_file(self):
        with tempfile.TemporaryDirectory() as temp:
            projects = Projects(Path(temp)/'projects')
            state = {'goal': 'test', 'cwd': temp, 'pending': [{'argv': ['echo', 'ok'], 'explanation': 'test'}], 'completed': [], 'messages': []}
            projects.save('test', state)
            self.assertEqual(projects.load('test'), state)
            self.assertEqual(projects.list(), ['test'])
            self.assertEqual(projects.path('test').stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                projects.save('../escape', state)
            projects.path('test').write_text(json.dumps(dict(state, pending=[{'argv': ['bad\ncommand'], 'explanation': 'x'}])))
            with self.assertRaises(ValueError):
                projects.load('test')

    def test_diagnostic_and_guide_only_propose(self):
        with patch('assistant_tools.shutil.which', return_value='/bin/program'):
            self.assertEqual(len(diagnostic_plan()), 5)
            description, plan = tool_guide('nmap', ['nmap'])
            self.assertIn('autorisé', description)
            self.assertEqual(plan[0]['argv'], ['man', '-P', 'cat', '--', 'nmap'])
            with self.assertRaises(ValueError):
                tool_guide('missing', ['nmap'])

    def test_resume_requires_new_confirmation(self):
        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            fake = Mock(model='test')
            with patch.object(main, 'MEMORY_PATH', Path(temp)/'memory.json'), patch.object(main, 'OllamaBrain', return_value=fake), patch.object(main, 'run_command') as run, patch.object(main, 'confirm', return_value=False), patch('assistant_tools.shutil.which', return_value='/bin/program'), patch('builtins.input', side_effect=['/diagnostic', '/project save demo', '/cancel', '/project load demo', '/run', '/quit']), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main.main(), 0)
                run.assert_not_called()
                fake.reply.assert_not_called()
                self.assertIn('Projet repris', output.getvalue())
                self.assertIn('Exécution annulée', output.getvalue())
        os.chdir(old_cwd)
