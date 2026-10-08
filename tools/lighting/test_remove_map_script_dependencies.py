import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from convert_lighting_v3 import fnv
from refresh_sprite_table_dependency import dependencies
import remove_map_script_dependencies as migration


def lighting(deps, version=5, paired=True):
    pixels = b'\x80\x01\x02\x03\xff' + b'\x80\x04\x05\x06\xff'
    pages = struct.pack('<4I', 1, 1, 128, 5) + struct.pack('<4I', 1, 1, 133, 5)
    extension = b''
    if paired:
        if version >= 4:
            extension += struct.pack('<6f', 0, 0, 1, 1, 1, 1)
        extension += struct.pack('<II', 1, len(deps))
        extension += struct.pack('<' + ('13f' if version >= 4 else '9f'),
                                 *range(13 if version >= 4 else 9))
        for name, digest in deps:
            encoded = name.encode('utf-8')
            extension += struct.pack('<IQ', len(encoded), digest) + encoded
        if version >= 5:
            extension += struct.pack('<4I', 1, 1, 1, 5) + b'\x80\x07\x08\x09\xff'
    header = bytearray(96)
    header[:8] = b'OYMLIT1\0'
    struct.pack_into('<IIQ', header, 8, version, 96, fnv(b'geometry'))
    struct.pack_into('<12I', header, 24, 0, 0, 2, 0, 0, 0, 96, 128, 128, 128, 128,
                     138 + len(extension))
    struct.pack_into('<I', header, 76, int(paired))
    return bytes(header) + pages + pixels + extension


class MapScriptDependencyMigrationTests(unittest.TestCase):
    def test_all_versions_preserve_pixels_probes_and_other_dependencies(self):
        retained = [('worlds/mm6/maps/test.odm', fnv(b'geometry')),
                    ('engine/textures/tree.bmp', 123), ('engine/events/Global.lua', 456)]
        scripts = [('worlds/mm6/events/maps/test.lua', 7),
                   ('worlds/mm6/events/maps/test_mmmerge.lua', 8)]
        for version in (3, 4, 5):
            with self.subTest(version=version):
                source = lighting([scripts[0], retained[0], scripts[1], *retained[1:]], version)
                output, removed = migration.remove_script_dependencies(source)
                self.assertEqual(output, lighting(retained, version))
                self.assertEqual(removed, [name for name, _ in scripts])
                self.assertEqual([(name, digest) for name, digest, _ in dependencies(output)], retained)
                self.assertEqual(migration.remove_script_dependencies(output), (output, []))

    def test_unpaired_imported_lighting_is_unchanged(self):
        source = lighting([], version=3, paired=False)
        self.assertEqual(migration.remove_script_dependencies(source), (source, []))

    def test_invalid_size_and_removal_of_all_dependencies_are_rejected(self):
        source = lighting([('worlds/mm6/events/maps/test.lua', 7)])
        with self.assertRaisesRegex(ValueError, 'Invalid lighting file size'):
            migration.remove_script_dependencies(source[:-1])
        with self.assertRaisesRegex(ValueError, 'must retain'):
            migration.remove_script_dependencies(source)

    def test_stale_retained_texture_blocks_all_writes_then_valid_migration_keeps_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / 'assets'
            maps = assets / 'worlds/mm6/maps'
            maps.mkdir(parents=True)
            texture = assets / 'engine/textures/tree.bmp'
            texture.parent.mkdir(parents=True)
            texture.write_bytes(b'wrong texture')
            old = lighting([('worlds/mm6/events/maps/test.lua', 7),
                            ('engine/textures/tree.bmp', fnv(b'correct texture'))])
            paths = [maps / 'a.lighting', maps / 'b.lighting']
            for path in paths:
                path.write_bytes(old)
            backup = root / 'backup'
            report = root / 'report.json'
            argv = ['migration', '--assets-root', str(assets), '--backup-root', str(backup),
                    '--report', str(report)]
            with patch('sys.argv', argv), self.assertRaisesRegex(ValueError, 'retained dependency is stale'):
                migration.main()
            self.assertFalse(backup.exists())
            self.assertFalse(report.exists())
            self.assertTrue(all(path.read_bytes() == old for path in paths))
            texture.write_bytes(b'correct texture')
            with patch('sys.argv', argv), contextlib.redirect_stdout(io.StringIO()):
                migration.main()
            for path in paths:
                self.assertEqual((backup / path.relative_to(assets)).read_bytes(), old)
                self.assertEqual(path.read_bytes(), lighting([('engine/textures/tree.bmp', fnv(texture.read_bytes()))]))
            self.assertEqual(len(json.loads(report.read_text())['sidecars']), 2)


if __name__ == '__main__':
    unittest.main()
