#!/usr/bin/env python3

from __future__ import annotations

import argparse
import struct
from pathlib import Path
from typing import Optional


NAVIGATION_HEADER = (
    "/ MapFile\tMinX\tMaxX\tMinY\tMaxY\tNorthMap\tNorthDays\tNorthHeading\t"
    "SouthMap\tSouthDays\tSouthHeading\tEastMap\tEastDays\tEastHeading\t"
    "WestMap\tWestDays\tWestHeading\tNorthX\tNorthY\tNorthZ\tSouthX\tSouthY\tSouthZ\t"
    "EastX\tEastY\tEastZ\tWestX\tWestY\tWestZ"
)

DEFAULT_MIN_X = -23143
DEFAULT_MAX_X = 23143
DEFAULT_MIN_Y = -23143
DEFAULT_MAX_Y = 23143

OBJECT_LIST_HEADER = [
    "// Name",
    "SpriteName",
    "ObjectId",
    "Radius",
    "Height",
    "LifetimeTicks",
    "Speed",
    "SpriteId",
    "ParticleTrailColor",
    "ParticleTrailRed",
    "ParticleTrailGreen",
    "ParticleTrailBlue",
    "Flags",
]

OBJECT_FLAG_NAMES = (
    (0x0001, "NoSprite"),
    (0x0002, "NoCollision"),
    (0x0004, "LifeTime"),
    (0x0008, "FTLifeTime"),
    (0x0010, "NoPickup"),
    (0x0020, "NoGravity"),
    (0x0040, "FlagOnIntercept"),
    (0x0080, "Bounce"),
    (0x0100, "TrailParticle"),
    (0x0200, "TrailFire"),
    (0x0400, "TrailLine"),
)


def read_tab_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []

    for line in read_legacy_text(path).splitlines():
        rows.append(line.rstrip("\r").split("\t"))

    return rows


def read_legacy_text(path: Path) -> str:
    data = path.read_bytes()

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def write_tab_rows(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(row).rstrip() for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def decode_object_flags(flags: int) -> str:
    tokens: list[str] = []
    remaining = flags

    for bit, name in OBJECT_FLAG_NAMES:
        if flags & bit:
            tokens.append(name)
            remaining &= ~bit

    if remaining != 0:
        tokens.append(f"0x{remaining:04x}")

    return ",".join(tokens) if tokens else "0"


def copy_table(source_path: Path, output_path: Path, strip_quotes: bool = False) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = read_legacy_text(source_path).replace("\r\n", "\n")

    if strip_quotes:
        text = text.replace('"', "")

    output_path.write_text(text, encoding="utf-8")


def world_map_files(maps_dir: Path, suffix: str) -> set[str]:
    return {path.name.lower() for path in maps_dir.glob(f"*{suffix}")}


def is_data_row(row: list[str]) -> bool:
    return bool(row and row[0].strip().isdigit())


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip())
    except ValueError:
        return default


def is_sound_row(row: list[str]) -> bool:
    return len(row) >= 2 and row[0].strip() and not row[0].startswith("/") and row[1].strip().isdigit()


def sound_name_key(value: str) -> str:
    return value.strip().lower()


# MMerge numbers MM6/MM7 house sounds 30000 + 10 * group, which reuses ids of MM8's own house sounds.
# Later duplicates of a house sound id move up by this offset instead of being dropped.
RELOCATED_HOUSE_SOUND_OFFSET = 15000


def mmerge_house_sound_names_by_group(expanded_sounds_path: Path) -> dict[int, str]:
    sound_names_by_group: dict[int, str] = {}

    for row in read_tab_rows(expanded_sounds_path):
        if not is_sound_row(row):
            continue

        sound_id = to_int(row[1])

        if sound_id < 30000:
            continue

        group_id = (sound_id - 30000) // 10
        sound_type = (sound_id - 30000) % 10

        if sound_type == 1:
            sound_names_by_group.setdefault(group_id, row[0].strip())

    return sound_names_by_group


def house_sound_base_ids_by_name(sound_catalog_path: Path) -> dict[str, int]:
    base_ids_by_name: dict[str, int] = {}
    seen_sound_ids: set[int] = set()

    for row in read_tab_rows(sound_catalog_path):
        if not is_sound_row(row):
            continue

        sound_id = to_int(row[1])

        if sound_id < 30000:
            continue

        if sound_id in seen_sound_ids:
            sound_id += RELOCATED_HOUSE_SOUND_OFFSET
        else:
            seen_sound_ids.add(sound_id)

        sound_type = sound_id % 100

        if sound_type == 1:
            base_ids_by_name.setdefault(sound_name_key(row[0]), sound_id - sound_type)

    return base_ids_by_name


def mmerge_house_sound_base_ids_by_group(expanded_sounds_path: Path, sound_catalog_path: Path) -> dict[int, int]:
    sound_names_by_group = mmerge_house_sound_names_by_group(expanded_sounds_path)
    base_ids_by_name = house_sound_base_ids_by_name(sound_catalog_path)
    base_ids_by_group: dict[int, int] = {}

    for group_id, sound_name in sound_names_by_group.items():
        base_id = base_ids_by_name.get(sound_name_key(sound_name))

        if base_id is None:
            base_id = 30000 + group_id * 10

        base_ids_by_group[group_id] = base_id

    return base_ids_by_group


def export_map_stats(source_path: Path, maps_dir: Path, output_path: Path) -> None:
    known_maps = world_map_files(maps_dir, ".odm") | world_map_files(maps_dir, ".blv")
    rows = read_tab_rows(source_path)
    output_rows: list[list[str]] = []

    for row in rows:
        if row and row[0].strip().isdigit():
            if len(row) <= 2 or row[2].strip().lower() not in known_maps:
                continue

            # Redbook track 1 is the non-audio CD/data track in the extracted MP3 layout.
            if len(row) > 28 and row[28].strip() == "1":
                row = list(row)
                row[28] = "0"

        output_rows.append(row)

    write_tab_rows(output_path, output_rows)


def set_navigation_edge(
    output_row: list[str],
    map_column: int,
    days_column: int,
    heading_column: int,
    source_row: list[str],
    source_map_column: int,
    source_days_column: int,
    heading: int,
    known_maps: set[str],
) -> None:
    destination_map = source_row[source_map_column].strip() if source_map_column < len(source_row) else ""
    travel_days = source_row[source_days_column].strip() if source_days_column < len(source_row) else ""

    if not destination_map or destination_map.lower() not in known_maps:
        output_row[map_column] = "0"
        output_row[days_column] = "0"
        output_row[heading_column] = "0"
        return

    output_row[map_column] = destination_map
    output_row[days_column] = travel_days if travel_days else "0"
    output_row[heading_column] = str(heading)


def blank_navigation_row(map_file: str) -> list[str]:
    return [
        map_file,
        str(DEFAULT_MIN_X),
        str(DEFAULT_MAX_X),
        str(DEFAULT_MIN_Y),
        str(DEFAULT_MAX_Y),
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ]


def export_map_navigation(source_path: Path, maps_dir: Path, output_path: Path) -> None:
    known_maps = world_map_files(maps_dir, ".odm")
    travel_rows: dict[str, list[str]] = {}

    for row in read_tab_rows(source_path):
        if not row:
            continue

        map_file = row[0].strip().lower()

        if map_file in known_maps:
            travel_rows[map_file] = row

    output_rows: list[list[str]] = [NAVIGATION_HEADER.split("\t")]

    for map_file in sorted(known_maps):
        source_row = travel_rows.get(map_file, [])
        output_row = blank_navigation_row(map_file)
        set_navigation_edge(output_row, 5, 6, 7, source_row, 1, 3, 0, known_maps)
        set_navigation_edge(output_row, 8, 9, 10, source_row, 4, 6, 180, known_maps)
        set_navigation_edge(output_row, 14, 15, 16, source_row, 7, 9, 270, known_maps)
        set_navigation_edge(output_row, 11, 12, 13, source_row, 10, 12, 90, known_maps)
        output_rows.append(output_row)

    write_tab_rows(output_path, output_rows)


def export_mon_list(source_path: Path, output_path: Path) -> None:
    output_rows: list[list[str]] = [[
        "//Race Name",
        "Stand",
        "Walk",
        "Fidget",
        "Attack",
        "Wince",
        "Death",
        "Dead",
        "Height",
        "Speed",
        "Max Rad",
        "Avg Rad",
        "Alpha",
        "Red",
        "Green",
        "Blue",
        "SFX?",
        "Attack",
        "Die",
        "Stun",
        "Fidget",
    ]]

    for row in read_tab_rows(source_path):
        if not row or not row[0].strip().isdigit() or len(row) < 22:
            continue

        output_rows.append([
            row[13],
            row[14],
            row[15],
            row[21],
            row[16],
            row[18],
            row[19],
            row[20],
            row[1],
            row[3],
            row[2],
            row[2],
            row[8],
            row[7],
            row[6],
            row[5],
            "0",
            row[9],
            row[10],
            row[11],
            row[12],
        ])

    write_tab_rows(output_path, output_rows)


def export_world_sounds(source_path: Path, output_path: Path) -> None:
    output_rows: list[list[str]] = []
    seen_sound_ids: set[str] = set()

    for row in read_tab_rows(source_path):
        if len(row) < 2 or not row[1].strip().isdigit() or row[0].startswith("/"):
            output_rows.append(row)
            continue

        sound_id = row[1].strip()

        if sound_id in seen_sound_ids:
            if int(sound_id) < 30000:
                continue

            sound_id = str(int(sound_id) + RELOCATED_HOUSE_SOUND_OFFSET)

            if sound_id in seen_sound_ids:
                continue

            row = [row[0], sound_id, *row[2:]]

        seen_sound_ids.add(sound_id)
        output_rows.append(row)

    write_tab_rows(output_path, output_rows)


def read_object_binary_rows(binary_path: Path) -> dict[int, dict[str, object]]:
    data = binary_path.read_bytes()
    entry_count = struct.unpack_from("<I", data, 0)[0]
    rows: dict[int, dict[str, object]] = {}

    for index in range(entry_count):
        offset = 4 + index * 56
        name = data[offset:offset + 32].split(b"\0", 1)[0].decode("latin1", errors="ignore")
        object_id, radius, height, flags, sprite_id, lifetime_ticks, particle_trail_color, speed = (
            struct.unpack_from("<hhhHhhIh", data, offset + 0x20)
        )
        particle_trail_red, particle_trail_green, particle_trail_blue = struct.unpack_from(
            "<BBB", data, offset + 0x32
        )

        rows[object_id] = {
            "name": name,
            "radius": radius,
            "height": height,
            "flags": flags,
            "sprite_id": sprite_id,
            "lifetime_ticks": lifetime_ticks,
            "particle_trail_color": particle_trail_color,
            "speed": speed,
            "particle_trail_red": particle_trail_red,
            "particle_trail_green": particle_trail_green,
            "particle_trail_blue": particle_trail_blue,
        }

    return rows


def object_output_row(entry: dict[str, object], object_id: int, name: str, sprite_name: str) -> list[str]:
    return [
        name if name else str(entry["name"]),
        sprite_name if sprite_name else "null",
        str(object_id),
        str(entry["radius"]),
        str(entry["height"]),
        str(entry["lifetime_ticks"]),
        str(entry["speed"]),
        str(entry["sprite_id"]),
        f"0x{int(entry['particle_trail_color']):08x}",
        str(entry["particle_trail_red"]),
        str(entry["particle_trail_green"]),
        str(entry["particle_trail_blue"]),
        decode_object_flags(int(entry["flags"])),
    ]


def export_object_list(source_text_path: Path, binary_path: Path, output_path: Path) -> None:
    binary_rows = read_object_binary_rows(binary_path)
    output_rows: list[list[str]] = [OBJECT_LIST_HEADER]
    seen_object_ids: set[int] = set()

    for row in read_tab_rows(source_text_path):
        if len(row) < 16 or not row[1].strip().isdigit():
            continue

        object_id = to_int(row[1])

        if object_id not in binary_rows:
            raise RuntimeError(f"Object id {object_id} from {source_text_path} not found in {binary_path}")

        output_rows.append(object_output_row(binary_rows[object_id], object_id, row[0].strip(), row[15].strip()))
        seen_object_ids.add(object_id)

    for object_id in sorted(binary_rows):
        if object_id in seen_object_ids:
            continue

        output_rows.append(object_output_row(binary_rows[object_id], object_id, "", "null"))

    write_tab_rows(output_path, output_rows)


def house_rows_by_id(house_data_path: Path) -> dict[int, list[str]]:
    houses: dict[int, list[str]] = {}

    for row in read_tab_rows(house_data_path):
        if not is_data_row(row):
            continue

        houses[to_int(row[0])] = row

    return houses


def npc_ids_by_house(npc_path: Path) -> dict[int, list[int]]:
    npc_ids: dict[int, list[int]] = {}

    for row in read_tab_rows(npc_path):
        if not is_data_row(row) or len(row) <= 6:
            continue

        house_id = to_int(row[6])

        if house_id <= 0:
            continue

        npc_ids.setdefault(house_id, []).append(to_int(row[0]))

    return npc_ids


def export_house_animations(
    house_data_path: Path,
    house_movies_path: Path,
    npc_path: Path,
    output_path: Path,
    video_roots: Optional[list[Path]] = None,
    house_sound_base_ids_by_group: Optional[dict[int, int]] = None,
) -> None:
    houses = house_rows_by_id(house_data_path)
    npc_ids = npc_ids_by_house(npc_path)
    house_movies: dict[int, list[str]] = {}
    available_video_stems: set[str] | None = None

    if video_roots is not None:
        available_video_stems = set()

        for video_root in video_roots:
            if not video_root.exists():
                continue

            for video_path in video_root.iterdir():
                if video_path.is_file() and video_path.suffix.lower() == ".ogv":
                    available_video_stems.add(video_path.stem.lower())

    for row in read_tab_rows(house_movies_path):
        if is_data_row(row):
            house_movies[to_int(row[0])] = row

    output_rows: list[list[str]] = [[
        "# House Id",
        "Animation Id",
        "Building Name",
        "NPC List",
        "Video Name",
        "Enter Sound",
        "Room Sound Id",
        "House Sound Base Id",
        "NPC Picture Id",
        "House Movie Type",
    ]]

    for house_id in sorted(houses):
        house = houses[house_id]
        animation_id = to_int(house[4]) if len(house) > 4 else 0
        movie = house_movies.get(animation_id, [])
        video_name = movie[1].strip() if len(movie) > 1 else ""
        if available_video_stems is not None and video_name.lower() not in available_video_stems:
            video_name = ""
        npc_picture_id = movie[2].strip() if len(movie) > 2 else ""
        house_movie_type = movie[3].strip() if len(movie) > 3 else ""
        movie_sound_group = to_int(movie[4]) if len(movie) > 4 else 0
        room_sound_id = movie[4].strip() if len(movie) > 4 and house_sound_base_ids_by_group is None else ""
        house_sound_base_id = ""
        if movie_sound_group > 0 and house_sound_base_ids_by_group is not None:
            house_sound_base_id_value = house_sound_base_ids_by_group.get(movie_sound_group)

            if house_sound_base_id_value is None:
                raise ValueError(f"unresolved MMerge house sound group {movie_sound_group}")

            house_sound_base_id = str(house_sound_base_id_value)

        resident_npcs = ",".join(str(npc_id) for npc_id in sorted(npc_ids.get(house_id, [])))
        building_name = house[5].strip() if len(house) > 5 else ""

        output_rows.append([
            str(house_id),
            str(animation_id),
            building_name,
            resident_npcs,
            video_name,
            "",
            room_sound_id,
            house_sound_base_id,
            npc_picture_id,
            house_movie_type,
        ])

    write_tab_rows(output_path, output_rows)


def collect_world_video_roots(worlds_root: Path) -> list[Path]:
    video_roots: list[Path] = []

    if not worlds_root.exists():
        return video_roots

    for world_dir in sorted(path for path in worlds_root.iterdir() if path.is_dir()):
        videos_dir = world_dir / "videos"
        video_roots.extend([
            videos_dir / "Houses",
            videos_dir / "legacy",
            videos_dir / "Transitions",
        ])

    return video_roots


def export_direct_tables(legacy_tables_dir: Path, data_tables_dir: Path) -> None:
    direct_tables = {
        "NPCData.txt": "npc.txt",
        "NPCGreet.txt": "npc_greet.txt",
        "NPCNews.txt": "npc_news.txt",
        "NPCTopic.txt": "npc_topic.txt",
        "NPCText.txt": "npc_topic_text.txt",
        "roster.txt": "roster.txt",
    }
    english_direct_tables = {
        "Autonote.txt": "autonote.txt",
        "Awards.txt": "awards.txt",
        "NPCGroup.txt": "npc_group.txt",
        "Quests.txt": "quests.txt",
        "Trans.txt": "trans.txt",
        "history.txt": "history.txt",
    }

    for source_name, output_name in direct_tables.items():
        copy_table(legacy_tables_dir / source_name, data_tables_dir / output_name, source_name == "NPCTopic.txt")

    for source_name, output_name in english_direct_tables.items():
        copy_table(legacy_tables_dir / source_name, data_tables_dir / "english" / output_name)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export MM6-derived support tables from MMerge sources")
    parser.add_argument("--world-dir", default="assets_dev/worlds/mm6", help="source MM6 world directory")
    parser.add_argument(
        "--output-dir",
        default="assets_dev/engine/data_tables",
        help="target flat engine data table directory",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    world_dir = Path(args.world_dir)
    legacy_tables_dir = world_dir / "_legacy" / "tables"
    maps_dir = world_dir / "maps"
    data_tables_dir = Path(args.output_dir)

    export_map_stats(legacy_tables_dir / "MapStats.txt", maps_dir, data_tables_dir / "map_stats.txt")
    export_map_navigation(
        legacy_tables_dir / "Outdoor travels.txt",
        maps_dir,
        data_tables_dir / "map_navigation.txt",
    )
    export_mon_list(legacy_tables_dir / "MonList.txt", data_tables_dir / "mon_list.txt")
    export_object_list(
        legacy_tables_dir / "ObjList.txt",
        world_dir / "_legacy" / "bin_tables" / "dobjlist.bin",
        data_tables_dir / "object_list.txt",
    )
    export_world_sounds(legacy_tables_dir / "sounds.txt", data_tables_dir / "sounds.txt")
    export_direct_tables(legacy_tables_dir, data_tables_dir)
    export_house_animations(
        data_tables_dir / "house_data.txt",
        legacy_tables_dir / "House Movies.txt",
        data_tables_dir / "npc.txt",
        data_tables_dir / "house_animations.txt",
        collect_world_video_roots(world_dir.parent),
        mmerge_house_sound_base_ids_by_group(
            legacy_tables_dir / "Sounds.txt",
            legacy_tables_dir / "sounds.txt",
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
