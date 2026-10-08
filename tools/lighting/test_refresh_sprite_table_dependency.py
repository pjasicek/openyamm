from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from convert_lighting_v3 import fnv
import refresh_sprite_table_dependency as refresh


class SpriteTableDependencyRefreshTests(unittest.TestCase):
    def test_script_selected_sprite_is_still_checked_without_script_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / 'assets'
            before = root / 'before.yml'
            old = yaml.safe_dump(dict(sprites=[dict(
                sprite_id=2, sprite_name='creature', frames=[dict(texture_name='old_texture')])])).encode()
            before.write_bytes(old)
            table = assets / refresh.TABLE
            table.parent.mkdir(parents=True)
            table.write_bytes(old.replace(b'old_texture', b'new_texture'))
            decoration = assets / 'engine/data_tables/decoration_data.txt'
            decoration.parent.mkdir(parents=True)
            decoration.write_text('1\ttree\t-\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\n')
            sidecar = assets / 'worlds/mm6/maps/test.lighting'
            sidecar.parent.mkdir(parents=True)
            source = bytes(32)
            sidecar.write_bytes(source)
            script = assets / 'worlds/mm6/events/maps/test_mmmerge.lua'
            script.parent.mkdir(parents=True)
            script.write_text('evt.SetSprite(7, 1, "creature")\n')
            argv = ['refresh', '--assets-root', str(assets), '--before', str(before),
                    '--backup-root', str(root / 'backup'), '--report', str(root / 'report.json')]
            with patch('sys.argv', argv), patch.object(
                    refresh, 'dependencies', return_value=[(refresh.TABLE, fnv(old), 0)]), \
                    self.assertRaisesRegex(ValueError, 'selected by a baked map script'):
                refresh.main()
            self.assertEqual(sidecar.read_bytes(), source)
            self.assertFalse((root / 'backup').exists())


if __name__ == '__main__':
    unittest.main()
