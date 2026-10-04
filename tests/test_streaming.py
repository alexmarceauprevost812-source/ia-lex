import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain import OllamaBrain, answer_prefix


class StreamingTests(unittest.TestCase):
    def test_partial_escapes_and_unicode(self):
        self.assertEqual(answer_prefix('{"answer":"bon'), 'bon')
        self.assertEqual(answer_prefix('{"answer":"bon\\'), 'bon')
        text = json.dumps({'answer': 'Bonjour\n"Alex" 😀', 'commands': []})
        previous = ''
        for end in range(len(text) + 1):
            current = answer_prefix(text[:end])
            self.assertTrue(current.startswith(previous))
            previous = current
        self.assertEqual(previous, 'Bonjour\n"Alex" 😀')

    def test_stream_and_interruption(self):
        client = OllamaBrain()
        client.opener = MagicMock()
        response = client.opener.open.return_value.__enter__.return_value
        response.readline.side_effect = [
            json.dumps({'message': {'content': '{"answer":"Bon'}}).encode(),
            json.dumps({'message': {'content': 'jour","commands":[],"files":[]}'}, 'done': True}).encode(),
        ]
        fragments = []
        result = client.reply('salut', [], [], on_progress=fragments.append)
        self.assertEqual(fragments, ['Bon', 'jour'])
        self.assertEqual(result['answer'], 'Bonjour')
        response.readline.side_effect = [json.dumps({'message': {'content': '{"answer":"x'}}).encode(), b'']
        with self.assertRaises(RuntimeError):
            client.reply('test', [], [])
