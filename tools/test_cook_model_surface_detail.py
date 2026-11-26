import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from cook_models import ROOT, Rules, plan_model, texture_uses, write_glb


class ModelSurfaceDetailTest(unittest.TestCase):
    def test_detail_remaps_its_texture_and_keeps_four_linear_channels(self):
        png = io.BytesIO()
        Image.new('RGBA', (8, 8), (94, 148, 164, 113)).save(png, format='PNG')
        data = png.getvalue()
        material = {'pbrMetallicRoughness': {'metallicRoughnessTexture': {'index': 1}},
                    'extras': {'openyamm_surface_detail': {'index': 1, 'tile_world_units': 144}}}
        document = {'asset': {'version': '2.0'}, 'materials': [material],
                    'buffers': [{'byteLength': len(data)}],
                    'bufferViews': [{'buffer': 0, 'byteLength': len(data)}],
                    'images': [{'name': 'grain', 'mimeType': 'image/png', 'bufferView': 0}],
                    'textures': [{'source': 0}, {'source': 0}]}
        rules = Rules(ROOT / 'tools/cook/model_textures.yml')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'worlds/hesper/models/detail.glb'
            path.parent.mkdir(parents=True)
            path.write_bytes(write_glb(document, data))
            planned = plan_model(rules, root, path, ('desktop', 'android'))
        surface = next(t for t in planned['textures'] if t['role'] == 'surface_detail')
        self.assertEqual(surface['semantic'], 'linear')
        self.assertTrue(surface['mips'])
        self.assertEqual(surface['decisions']['desktop'][0], 'bc7')
        self.assertEqual(surface['decisions']['android'][0], 'etc2_rgba')
        cooked_material = planned['document']['materials'][0]
        macro = cooked_material['pbrMetallicRoughness']['metallicRoughnessTexture']['index']
        detail = cooked_material['extras']['openyamm_surface_detail']
        self.assertNotEqual(macro, detail['index'])
        self.assertEqual(detail['tile_world_units'], 144)
        image = planned['document']['textures'][detail['index']]['source']
        self.assertEqual(planned['document']['images'][image]['uri'], f'textures/{surface["key"]}.oytex')
        material['extras']['openyamm_surface_detail']['index'] = -1
        with self.assertRaisesRegex(ValueError, 'surface detail'):
            texture_uses(document)


if __name__ == '__main__':
    unittest.main()
