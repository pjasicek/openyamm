from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import yaml

import bake_decorations


class DecorationBakeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.assets = self.root / 'assets_dev'
        self.world = self.assets / 'worlds/mm6'
        self.output = self.root / 'masks'
        self.profile = dict(world='mm6', map='test.odm', azimuth=225)
        for directory in ('maps', 'events/maps', 'sprites'):
            (self.world / directory).mkdir(parents=True)
        (self.world / 'maps/test.odm').touch()
        (self.world / 'maps/test.scene.yml').write_text('{}')
        self.script = self.world / 'events/maps/test.lua'
        table = self.assets / 'engine/data_tables/decoration_data.txt'
        table.parent.mkdir(parents=True)
        table.write_text(
            '1\tnull\t-\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t-\n'
            '2\ttree\t-\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t-\n'
            '3\tpending\t-\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t-\n')
        frames = self.assets / 'engine/rendering/sprite_frame_data_common.yml'
        frames.parent.mkdir(parents=True)
        frames.write_text(yaml.safe_dump(dict(sprites=[dict(
            sprite_id=1, sprite_name='tree', frames=[dict(
                flags=['Image1'], texture_name='tree', palette_id=0, scale=1)])])))
        image = Image.new('P', (4, 8), 1)
        image.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
        image.save(self.world / 'sprites/tree.bmp')
        self.entities = [dict(index=0, name='tree', decoration_list_id=1,
                              event_id_primary=7, ai_attributes=0, facing=0,
                              position=dict(x=0, y=0, z=0))]

    def export(self):
        with patch.object(bake_decorations, 'ROOT', self.root), patch.object(
                bake_decorations, 'parse_odm_file', return_value=dict(payload=dict(entities=self.entities))):
            return bake_decorations.export_cards(self.profile, self.output)

    def test_legacy_bytes_in_comments_and_strings_do_not_hide_sprite_calls(self):
        self.script.write_bytes(
            b'-- NPCs \xb913\n'
            b'evt.SetMessage("Hero\x92s message: evt.SetSprite(999, 0)")\n'
            b'--[[ evt.SetSprite(998, 0) \x85 ]]\n'
            b'evt.SetSprite(7, 0, "0")\n')
        result = self.export()
        self.assertEqual(result['counts'], dict(casters=0, skipped=1))
        self.assertEqual(result['skip_reasons'], dict(can_be_hidden=1))
        self.assertNotIn('worlds/mm6/events/maps/test.lua', result['dependencies'])

    def test_gameplay_script_edits_do_not_change_bake_dependencies(self):
        self.script.write_text('evt.SetSprite(7, 1)\n')
        baseline = self.export()
        supplement = self.world / 'events/maps/test_mmmerge.lua'
        supplement.write_text('-- Gameplay-only supplement\nevt.Add("Gold", 10)\n')
        self.script.write_text('evt.SetSprite(7, 1)\nevt.Add("Gold", 20)\n')
        result = self.export()
        self.assertEqual(result, baseline)
        self.assertFalse(any(name.endswith('.lua') for name in result['dependencies']))
        self.assertIn('worlds/mm6/maps/test.odm', result['dependencies'])
        self.assertIn('worlds/mm6/maps/test.scene.yml', result['dependencies'])
        self.assertIn('worlds/mm6/sprites/tree.bmp', result['dependencies'])

    def test_visibility_only_names_keep_native_silhouette(self):
        baseline = self.export()['cards'][0]
        for arguments in ('7, 1', '7, true, ""', '7, 1, "0"'):
            with self.subTest(arguments=arguments):
                self.script.write_text('evt.SetSprite(' + arguments + ')\n')
                result = self.export()
                self.assertEqual(result['counts'], dict(casters=1, skipped=0))
                card = result['cards'][0]
                for field in ('width', 'height', 'mask', 'sources', 'policy'):
                    self.assertEqual(card[field], baseline[field])
                self.assertEqual(card['policy'], 'static')

    def test_empty_initial_name_is_null_regardless_of_raw_descriptor(self):
        self.entities[0]['name'] = ''
        for descriptor in (1, 2, 999):
            with self.subTest(descriptor=descriptor):
                self.entities[0]['decoration_list_id'] = descriptor
                result = self.export()
                self.assertEqual(result['counts'], dict(casters=0, skipped=1))
                self.assertEqual(result['skip_reasons'], dict(marker_or_no_visible_sprite=1))

    def test_unknown_replacement_still_fails(self):
        self.script.write_text('evt.SetSprite(7, 1, "missing_tree")\n')
        with self.assertRaisesRegex(ValueError, 'Unresolved decoration or sprite state: missing_tree'):
            self.export()


if __name__ == '__main__':
    unittest.main()
