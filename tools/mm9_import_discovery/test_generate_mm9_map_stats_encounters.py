#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_mm9_map_stats_encounters as generator


def map_stats_row(row_id: str, world_id: str, map_number: str, slots: list[str]) -> str:
    fields = [""] * 48
    fields[0] = row_id
    fields[34] = world_id
    fields[35] = map_number
    for (picture_column, name_column), name in zip(generator.ENCOUNTER_COLUMNS, slots):
        fields[picture_column] = name
        fields[name_column] = name
    fields[18] = "3"
    fields[19] = "2-4"
    return "\t".join(fields)


class Mm9MapStatsEncounterTests(unittest.TestCase):
    def test_only_mm9_encounter_names_change(self) -> None:
        text = (
            map_stats_row("1", "", "", ["Goblin", "", "", ""]) + "\r\n"
            + map_stats_row("9021", "mm9", "21", ["Skeletoid", "DragonFlyMite", "", ""]) + "\r\n"
        )
        rewritten, changed = generator.rewrite_map_stats(
            text, {21: ["MM9 Skeleton", "MM9 Dragonfly", "", ""]}
        )

        self.assertEqual(changed, [9021])
        lines = rewritten.split("\r\n")
        self.assertEqual(lines[0], text.split("\r\n")[0])
        fields = lines[1].split("\t")
        self.assertEqual(fields[16:20], ["MM9 Skeleton", "MM9 Skeleton", "3", "2-4"])
        self.assertEqual(fields[20:22], ["MM9 Dragonfly", "MM9 Dragonfly"])
        self.assertEqual(rewritten.count("\r\n"), 2)

    def test_rewrite_is_idempotent(self) -> None:
        text = map_stats_row("9021", "mm9", "21", ["MM9 Skeleton", "", "", ""]) + "\n"
        rewritten, changed = generator.rewrite_map_stats(text, {21: ["MM9 Skeleton", "", "", ""]})

        self.assertEqual(rewritten, text)
        self.assertEqual(changed, [])

    def test_music_column_comes_from_mapstats(self) -> None:
        text = map_stats_row("9073", "mm9", "73", ["", "", "", ""]) + "\n"
        fields = text.rstrip("\n").split("\t")
        fields[generator.MUSIC_TRACK_COLUMN] = "90018"
        text = "\t".join(fields) + "\n"
        rewritten, changed = generator.rewrite_map_stats(text, {73: ["", "", "", ""]}, {73: 90017})

        self.assertEqual(changed, [9073])
        self.assertEqual(rewritten.split("\t")[generator.MUSIC_TRACK_COLUMN], "90017")

    def test_blank_music_track_inherits_the_entry_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "MAPSTATS.txt"
            path.write_text(
                "#\tName\tFile name\tMusic Track\n"
                "8\tGuberland\tGuberland\t7\n"
                "49\tTemple of Honk\tTempleOfHonk\t\n"
                "73\tThousand Terrors\t1000Terrors\t18\n",
                encoding="cp1252",
            )
            self.assertEqual(generator.mapstats_music(path), {8: 90006, 49: 90006, 73: 90017})


if __name__ == "__main__":
    unittest.main()
