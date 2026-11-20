import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_creature_review as review


class ReviewCommandTests(unittest.TestCase):
    def test_scoped_commands_and_rejected_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            creatures = root / 'level_generation/creatures'
            project = creatures / 'test_bull'
            viewer = project / 'review/viewer'
            viewer.mkdir(parents=True)
            (viewer / 'manifest.json').write_text(json.dumps({'clips': {'Walking': {'duration': 1}},
                'default_clip': 'Walking', 'models': [{'id': 'bull_b', 'sha256': 'b' * 64}]}))
            with patch.object(review, 'REPO', root), patch.object(review, 'CREATURES', creatures):
                args = review.command(project, 'shots', 8912, ['walk:Walking:0.5:left:body'])
                self.assertEqual(args[-1], 'walk:Walking:0.5:left:body')
                self.assertEqual(args[-2], str(project / 'review/shots'))
                self.assertTrue(args[-3].startswith('http://127.0.0.1:8912/'))
                self.assertIn('#', review.command(project, 'check', 8912, [], 'bull_b')[-1])
                with self.assertRaises(ValueError):
                    review.command(project, 'check', 8912, [], 'missing')
                for shot in ('../escape:Walking:0:left:body', 'x:Walking:nan:left:body',
                             'x:Walking:2:left:body', 'x:Missing:0:left:body',
                             'x:Walking:0:injected:body'):
                    with self.subTest(shot=shot), self.assertRaises(ValueError):
                        review.command(project, 'shots', 8912, [shot])
                for path, port in ((root, 8912), (viewer, 8912), (project, 80)):
                    with self.assertRaises(ValueError):
                        review.command(path, 'check', port, [])
                (project / 'review/shots').symlink_to(root, target_is_directory=True)
                with self.assertRaises(ValueError):
                    review.command(project, 'shots', 8912, ['walk:Walking:0:left:body'])


if __name__ == '__main__':
    unittest.main()
