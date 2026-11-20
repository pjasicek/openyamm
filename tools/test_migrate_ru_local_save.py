import struct
import tempfile
import unittest
from pathlib import Path

from migrate_ru_local_save import IMPORT_MAGIC, SOURCE_MAGIC, migrate, tagged_copy


class RuLocalSaveMigrationTests(unittest.TestCase):
    def test_tags_only_the_magic_and_keeps_version_and_payload(self):
        for version in (89, 90):
            data = SOURCE_MAGIC + struct.pack("<I", version) + bytes(range(256))
            self.assertEqual(tagged_copy(data), IMPORT_MAGIC + data[8:])

    def test_rejects_other_formats_and_versions(self):
        for data in (b"", b"OYSAVE1\0", IMPORT_MAGIC + struct.pack("<I", 90),
                     SOURCE_MAGIC + struct.pack("<I", 88), SOURCE_MAGIC + struct.pack("<I", 197)):
            with self.assertRaises(ValueError):
                tagged_copy(data)

    def test_preserves_original_and_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "old.oysav"
            destination = Path(directory) / "import.oysav"
            data = SOURCE_MAGIC + struct.pack("<I", 90) + b"payload"
            source.write_bytes(data)
            migrate(source, destination)
            self.assertEqual(source.read_bytes(), data)
            self.assertEqual(destination.read_bytes(), tagged_copy(data))
            with self.assertRaises(FileExistsError):
                migrate(source, destination)
            with self.assertRaises(ValueError):
                migrate(source, source)
            self.assertEqual(source.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
