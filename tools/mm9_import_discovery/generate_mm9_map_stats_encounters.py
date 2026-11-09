#!/usr/bin/env python3
"""Name MM9 monster families in the MM9 map-stats encounter slots, and give each MM9 map its song.

The MM9 rows of the engine map_stats.txt (world_id mm9) carry MM9 MAPSTATS.txt's encounter monsters. This tool
rewrites their encounter picture and name columns: each MAPSTATS monster becomes its family's tier picture base
("MM9 Dragonfly"), which the runtime expands to "MM9 Dragonfly A|B|C" (see mm9_monster_families.yml). It also writes
their "Redbook Track" column from MAPSTATS's "Music Track" (N plays MM9-Song(N-1), track 90000 + N - 1:
import_mm9_world_music.track_for_mapstats_music). Encounter chances, difficulty and appear ranges and every other
column and row are left as they are. Run it on the engine table and on the converters' frozen original
(level_generation/projects/mm9r_common/original_tables/map_stats.txt), whose rows the map converters copy.
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path

import generate_mm9_monster_tables as monster_tables
from import_mm9_world_music import track_for_mapstats_music


WORLD_ID_COLUMN = 34
MM9_MAP_NUMBER_COLUMN = 35
# (picture, name) columns of the three classic encounter slots and MM9's fourth slot, which the MM9 rows carry in
# their trailing MAPSTATS columns.
ENCOUNTER_COLUMNS = ((16, 17), (20, 21), (24, 25), (40, 41))
MAPSTATS_MONSTER_COLUMNS = (15, 18, 21, 24)
MUSIC_TRACK_COLUMN = 28
MAPSTATS_FILE_COLUMN = 2
MAPSTATS_MUSIC_COLUMN = 3
# A blank Music Track keeps the previous map's song in MM9 (it is played again from its start). Temple of Honk is
# reached only from Guberland, so it gets Guberland's song (correct after loading a save there too).
MAPSTATS_MUSIC_FROM = {"templeofhonk": "guberland"}


def mapstats_music(path: Path) -> dict[int, int]:
    """{MM9 map number: OpenYAMM music track} from MAPSTATS's Music Track (0: none)."""
    with path.open(newline="", encoding="cp1252") as input_file:
        rows = list(csv.reader(input_file, delimiter="\t"))
    header = rows[0]
    if header[MAPSTATS_FILE_COLUMN] != "File name" or header[MAPSTATS_MUSIC_COLUMN] != "Music Track":
        raise ValueError(f"Unexpected MM9 MAPSTATS.txt schema in {path}")

    tracks: dict[int, int] = {}
    by_file: dict[str, int] = {}
    for row in rows[1:]:
        if row and row[0].strip().isdigit():
            cell = row[MAPSTATS_MUSIC_COLUMN].strip() if MAPSTATS_MUSIC_COLUMN < len(row) else ""
            tracks[int(row[0])] = track_for_mapstats_music(int(cell)) if cell.isdigit() else 0
            by_file[row[MAPSTATS_FILE_COLUMN].strip().lower()] = int(row[0])
    for stem, source in MAPSTATS_MUSIC_FROM.items():
        if stem in by_file and source in by_file and tracks[by_file[stem]] == 0:
            tracks[by_file[stem]] = tracks[by_file[source]]
    return tracks


def mapstats_monsters(path: Path) -> dict[int, list[str]]:
    with path.open(newline="", encoding="cp1252") as input_file:
        rows = list(csv.reader(input_file, delimiter="\t"))
    header = rows[0]
    if [header[column] for column in MAPSTATS_MONSTER_COLUMNS] != ["Mon 1", "Mon 2", "Mon 3", "Mon 4"]:
        raise ValueError(f"Unexpected MM9 MAPSTATS.txt schema in {path}")

    monsters: dict[int, list[str]] = {}
    for row in rows[1:]:
        if row and row[0].strip().isdigit():
            monsters[int(row[0])] = [
                row[column].strip() if column < len(row) else "" for column in MAPSTATS_MONSTER_COLUMNS
            ]
    return monsters


def encounter_pictures(
    mapstats: dict[int, list[str]], sources: dict[int, list[str]], families: monster_tables.MonsterFamilies
) -> dict[int, list[str]]:
    pictures: dict[int, list[str]] = {}
    unresolved: list[str] = []
    for map_number, names in sorted(mapstats.items()):
        slot_pictures = []
        for name in names:
            if not name:
                slot_pictures.append("")
                continue
            family = monster_tables.mapstats_family(name, sources, families)
            if family is None:
                unresolved.append(f"map {map_number}: {name}")
                slot_pictures.append("")
            else:
                slot_pictures.append(family.picture_base)
        pictures[map_number] = slot_pictures
    if unresolved:
        raise ValueError("MM9 MAPSTATS monsters without a family: " + ", ".join(unresolved))
    return pictures


def split_line(line: str) -> tuple[list[str], str]:
    body = line.rstrip("\r\n")
    return body.split("\t"), line[len(body):]


def rewrite_map_stats(
    map_stats_text: str, pictures: dict[int, list[str]], music: dict[int, int] | None = None
) -> tuple[str, list[int]]:
    lines = map_stats_text.splitlines(keepends=True)
    changed: list[int] = []
    for index, line in enumerate(lines):
        fields, ending = split_line(line)
        if len(fields) <= MM9_MAP_NUMBER_COLUMN or fields[WORLD_ID_COLUMN].strip() != "mm9":
            continue
        map_number = int(fields[MM9_MAP_NUMBER_COLUMN])
        if map_number not in pictures:
            raise ValueError(f"map_stats row {fields[0]} names MM9 map {map_number}, which MAPSTATS lacks")

        original = list(fields)
        for (picture_column, name_column), picture in zip(ENCOUNTER_COLUMNS, pictures[map_number]):
            if name_column >= len(fields):
                if picture:
                    raise ValueError(f"map_stats row {fields[0]} has no column for encounter {picture!r}")
                continue
            fields[picture_column] = picture
            fields[name_column] = picture
        if music is not None:
            fields[MUSIC_TRACK_COLUMN] = str(music[map_number]) if music.get(map_number) else ""
        if fields != original:
            lines[index] = "\t".join(fields) + ending
            changed.append(int(fields[0]))
    return "".join(lines), changed


def write_text(path: Path, text: str) -> None:
    # Replace the file instead of rewriting it in place: hard-linked staging copies keep their version.
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="latin-1") as output_file:
            output_file.write(text)
        os.chmod(temporary_name, path.stat().st_mode & 0o777)
        os.replace(temporary_name, path)
    except BaseException:
        os.unlink(temporary_name)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-monsters", type=Path, default=Path("mm9/extracted/DATA/DATA/MONSTERS.txt"))
    parser.add_argument("--source-map-stats", type=Path, default=Path("mm9/extracted/DATA/DATA/MAPSTATS.txt"))
    parser.add_argument(
        "--families", type=Path, default=Path("tools/mm9_import_discovery/mm9_monster_families.yml"),
    )
    parser.add_argument(
        "--map-stats", type=Path, nargs="+", default=[Path("assets_dev/engine/data_tables/map_stats.txt")],
    )
    args = parser.parse_args()

    sources = monster_tables.source_monsters(args.source_monsters)
    families = monster_tables.load_families(args.families, sources)
    pictures = encounter_pictures(mapstats_monsters(args.source_map_stats), sources, families)
    music = mapstats_music(args.source_map_stats)

    for map_stats in args.map_stats:
        # latin-1 round-trips every byte, so untouched rows and their line endings stay byte-identical.
        with map_stats.open(newline="", encoding="latin-1") as input_file:
            original_text = input_file.read()
        text, changed = rewrite_map_stats(original_text, pictures, music)
        if text != original_text:
            write_text(map_stats, text)
        print(f"Updated encounters and music of {len(changed)} MM9 map-stats rows in {map_stats}: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
