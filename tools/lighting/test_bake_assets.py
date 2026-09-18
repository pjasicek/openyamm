from pathlib import Path
import tempfile
import unittest

from bake_assets import bake_texture_paths


class BakeAssetTests(unittest.TestCase):
    def test_merged_package_precedence_and_native_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def asset(relative):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                return path

            active = asset('worlds/mm6/textures/shared.bmp')
            asset('engine/textures/shared.bmp')
            asset('worlds/mm8/textures/shared.bmp')
            engine = asset('engine/textures/base.bmp')
            asset('worlds/mm7/textures/base.bmp')
            other = asset('worlds/mm7/textures/trim11_32.bmp')
            merged = asset('worlds/mm8/textures/PENDING.bmp')
            asset('worlds/mm6/textures/6pending.bmp')
            ground = asset('worlds/mm6/terrain/shared.bmp')
            texture_only = asset('worlds/mm8/textures/WtrTyl.bmp')
            textures, terrain = bake_texture_paths(root, 'mm6')
            self.assertEqual(textures['shared'], active)
            self.assertEqual(textures['base'], engine)
            self.assertEqual(textures['trim11_32'], other)
            self.assertEqual(textures['pending'], merged)
            self.assertEqual(terrain['shared'], ground)
            self.assertEqual(terrain['wtrtyl'], texture_only)
            self.assertNotIn('absent', textures)


if __name__ == '__main__':
    unittest.main()
