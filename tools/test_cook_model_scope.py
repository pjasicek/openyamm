import tempfile
import unittest
from pathlib import Path

from cook_models import source_models


class ModelCookScopeTest(unittest.TestCase):
    def test_full_production_cook_and_project_cook(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = root / 'engine/models/common.glb'
            mounted = root / 'worlds/live/world_items/models/drop.glb'
            preview = root / 'worlds/preview/models/actor.glb'
            for path in (engine, mounted, preview):
                path.parent.mkdir(parents=True)
                path.touch()
            self.assertEqual(source_models(root, None, {'live'}), [engine, mounted])
            self.assertEqual(source_models(root, 'worlds/preview/*', {'live'}), [preview])
            self.assertEqual(source_models(root, None), [engine, mounted, preview])


if __name__ == '__main__':
    unittest.main()
