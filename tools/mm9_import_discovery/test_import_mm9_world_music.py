#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from import_mm9_world_music import import_music, selected_music_imports, track_for_mapstats_music


class Mm9WorldMusicImportTests(unittest.TestCase):
    def test_imports_numbered_tracks_into_the_mm9_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            output = root / "output"
            source.mkdir()
            (source / "MM9-Song01.mp3").write_bytes(b"first")
            (source / "MM9-Song07.MP3").write_bytes(b"seventh")
            (source / "readme.txt").write_text("ignored", encoding="utf-8")

            imports = selected_music_imports(source)
            self.assertEqual(
                [(entry.source_track, entry.destination_track) for entry in imports],
                [(1, 90001), (7, 90007)])

            copied, unchanged = import_music(imports, output, check=False)
            self.assertEqual((copied, unchanged), (2, 0))
            self.assertEqual((output / "90001.mp3").read_bytes(), b"first")
            self.assertEqual((output / "90007.mp3").read_bytes(), b"seventh")

            copied, unchanged = import_music(imports, output, check=True)
            self.assertEqual((copied, unchanged), (0, 2))

    def test_mapstats_music_track_n_is_song_n_minus_one(self) -> None:
        self.assertEqual(track_for_mapstats_music(2), 90001)
        self.assertEqual(track_for_mapstats_music(7), 90006)
        self.assertEqual(track_for_mapstats_music(18), 90017)
        self.assertEqual(track_for_mapstats_music(1), 0)
        self.assertEqual(track_for_mapstats_music(0), 0)


if __name__ == "__main__":
    unittest.main()
