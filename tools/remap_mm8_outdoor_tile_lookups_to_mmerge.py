#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path


TILE_SET_LOOKUP_OFFSET = 0xA0
TILE_SET_LOOKUP_COUNT = 4
TILE_SET_WIDTH = 36


def parse_tile_table(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.rstrip("\n").split("\t")

        if len(parts) < 7 or not parts[0].strip().isdigit():
            continue

        index = int(parts[0].strip())

        while len(rows) <= index:
            rows.append(("", "", ""))

        rows[index] = (
            parts[1].strip().lower(),
            parts[5].strip().lower(),
            parts[6].strip().lower(),
        )

    return rows


def score_tile_group(source: list[tuple[str, str, str]], target: list[tuple[str, str, str]], source_base: int, target_base: int) -> int:
    score = 0

    for offset in range(TILE_SET_WIDTH):
        source_index = source_base + offset
        target_index = target_base + offset

        if source_index >= len(source) or target_index >= len(target):
            return -1

        source_texture, source_variant, source_flags = source[source_index]
        target_texture, target_variant, target_flags = target[target_index]

        if source_texture == target_texture and source_variant == target_variant and source_flags == target_flags:
            score += 4
        elif source_texture == target_texture and source_variant == target_variant:
            score += 3
        elif source_texture == target_texture:
            score += 1

    return score


def find_best_group_mapping(
    source: list[tuple[str, str, str]],
    target: list[tuple[str, str, str]],
    source_base: int,
) -> int | None:
    if source_base < 0 or source_base + TILE_SET_WIDTH > len(source):
        return None

    best_base: int | None = None
    best_score = -1

    for target_base in range(0, len(target) - TILE_SET_WIDTH + 1):
        score = score_tile_group(source, target, source_base, target_base)

        if score > best_score:
            best_score = score
            best_base = target_base

    if best_base is None or best_score <= 0:
        return None

    return best_base


def read_scene_master_tile(path: Path) -> int | None:
    match = re.search(r"^\s*master_tile:\s+(\d+)\s*$", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def remap_scene_lookup_indices(path: Path, remap: dict[int, int], dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    changed_count = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal changed_count
        values = [int(value.strip()) for value in match.group(1).split(",")]
        mapped_values = [remap.get(value, value) for value in values]

        if mapped_values == values:
            return match.group(0)

        changed_count += sum(1 for left, right in zip(values, mapped_values) if left != right)
        return "  tile_set_lookup_indices: [" + ", ".join(str(value) for value in mapped_values) + "]"

    updated_text = re.sub(
        r"^\s*tile_set_lookup_indices:\s+\[([0-9,\s]+)\]\s*$",
        replace_match,
        text,
        flags=re.MULTILINE,
    )

    if changed_count != 0 and not dry_run:
        path.write_text(updated_text, encoding="utf-8")

    return changed_count


def remap_odm_lookup_indices(path: Path, remap: dict[int, int], dry_run: bool) -> int:
    data = bytearray(path.read_bytes())
    changed_count = 0

    for lookup_index in range(TILE_SET_LOOKUP_COUNT):
        offset = TILE_SET_LOOKUP_OFFSET + lookup_index * 4
        value = struct.unpack_from("<i", data, offset)[0]
        lookup_value = (value >> 16) & 0xffff
        mapped_value = remap.get(lookup_value, lookup_value)

        if mapped_value == lookup_value:
            continue

        value = (value & 0x0000ffff) | (mapped_value << 16)
        struct.pack_into("<i", data, offset, value)
        changed_count += 1

    if changed_count != 0 and not dry_run:
        path.write_bytes(data)

    return changed_count


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remap MM8 outdoor tile lookup bases to the merged MMerge Tile table.")
    parser.add_argument("--legacy-data-tables-dir", required=True)
    parser.add_argument("--mmerge-tile-table", required=True)
    parser.add_argument("--scene-dir", required=True)
    parser.add_argument("--apply", action="store_true", help="write changes; default is a dry run")
    parser.add_argument("--dry-run", action="store_true", help="kept for explicit dry-run calls")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    legacy_tables_dir = Path(args.legacy_data_tables_dir)
    legacy_tables = {
        0: parse_tile_table(legacy_tables_dir / "terrain_tile_data.txt"),
        1: parse_tile_table(legacy_tables_dir / "terrain_tile_data_2.txt"),
        2: parse_tile_table(legacy_tables_dir / "terrain_tile_data_3.txt"),
    }
    mmerge_table = parse_tile_table(Path(args.mmerge_tile_table))
    scene_dir = Path(args.scene_dir)
    dry_run = not args.apply or args.dry_run

    remaps: dict[int, dict[int, int]] = {0: {}, 1: {}, 2: {}}

    for scene_path in sorted(scene_dir.glob("*.scene.yml")):
        master_tile = read_scene_master_tile(scene_path)

        if master_tile not in legacy_tables:
            continue

        text = scene_path.read_text(encoding="utf-8")
        lookup_match = re.search(r"^\s*tile_set_lookup_indices:\s+\[([0-9,\s]+)\]\s*$", text, flags=re.MULTILINE)

        if lookup_match is None:
            continue

        for value in [int(item.strip()) for item in lookup_match.group(1).split(",")]:
            if value in remaps[master_tile]:
                continue

            mapped_value = find_best_group_mapping(legacy_tables[master_tile], mmerge_table, value)

            if mapped_value is not None:
                remaps[master_tile][value] = mapped_value

    scene_changes = 0
    odm_changes = 0

    for scene_path in sorted(scene_dir.glob("*.scene.yml")):
        master_tile = read_scene_master_tile(scene_path)

        if master_tile not in remaps:
            continue

        remap = remaps[master_tile]
        scene_changes += remap_scene_lookup_indices(scene_path, remap, dry_run)

        odm_path = scene_path.with_name(scene_path.name.replace(".scene.yml", ".odm"))

        if odm_path.exists():
            odm_changes += remap_odm_lookup_indices(odm_path, remap, dry_run)

    for master_tile, remap in remaps.items():
        if remap:
            remap_text = ", ".join(f"{source}->{target}" for source, target in sorted(remap.items()))
            print(f"master_tile {master_tile}: {remap_text}")

    print(f"scene lookup references changed: {scene_changes}")
    print(f"odm lookup references changed: {odm_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
