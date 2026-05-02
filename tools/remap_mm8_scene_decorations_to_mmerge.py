#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import struct
from collections import defaultdict
from pathlib import Path


SFT_RECORD_SIZE = 60
SFT_NAME_SIZE = 12


def decode_string(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("latin1").strip()


def normalize_name(value: str) -> str:
    return value.strip().lower()


def parse_decoration_table(path: Path) -> dict[int, dict[str, object]]:
    entries: dict[int, dict[str, object]] = {}

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.rstrip("\n").split("\t")

        if len(parts) < 13:
            continue

        number_text = parts[0].strip()

        if not number_text.isdigit():
            continue

        sprite_id_text = parts[12].strip()

        if not sprite_id_text.lstrip("-").isdigit():
            continue

        runtime_id = int(number_text) - 1
        entries[runtime_id] = {
            "internal_name": parts[1].strip(),
            "sprite_id": int(sprite_id_text),
        }

    return entries


def parse_sft_bin_sprite_names(path: Path) -> dict[int, str]:
    data = path.read_bytes()
    frame_count, _ = struct.unpack_from("<II", data, 0)
    sprite_names: dict[int, str] = {}

    for frame_index in range(frame_count):
        offset = 8 + frame_index * SFT_RECORD_SIZE
        sprite_names[frame_index] = decode_string(data[offset:offset + SFT_NAME_SIZE])

    return sprite_names


def parse_sprite_yml_names(rendering_dir: Path) -> dict[int, str]:
    sprite_names: dict[int, str] = {}
    sprite_id_pattern = re.compile(r"^\s*-\s+sprite_id:\s+(-?\d+)\s*$")
    sprite_name_pattern = re.compile(r"^\s+sprite_name:\s+\"(.*)\"\s*$")

    for path in sorted(rendering_dir.rglob("*.yml")):
        pending_sprite_id: int | None = None

        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            sprite_id_match = sprite_id_pattern.match(line)

            if sprite_id_match is not None:
                pending_sprite_id = int(sprite_id_match.group(1))
                continue

            sprite_name_match = sprite_name_pattern.match(line)

            if sprite_name_match is not None and pending_sprite_id is not None:
                sprite_names[pending_sprite_id] = sprite_name_match.group(1)
                pending_sprite_id = None

    return sprite_names


def build_remap(
    legacy_decorations: dict[int, dict[str, object]],
    legacy_sprite_names: dict[int, str],
    mmerge_decorations: dict[int, dict[str, object]],
    mmerge_sprite_names: dict[int, str],
) -> tuple[dict[int, int], list[str]]:
    by_exact_key: dict[tuple[str, str], int] = {}
    by_name: dict[str, list[int]] = defaultdict(list)
    warnings: list[str] = []

    for runtime_id, entry in mmerge_decorations.items():
        name = normalize_name(str(entry["internal_name"]))
        sprite_id = int(entry["sprite_id"])
        sprite_name = normalize_name(mmerge_sprite_names.get(sprite_id, ""))

        if name and sprite_name:
            key = (name, sprite_name)

            if key in by_exact_key:
                if key != ("null", "null"):
                    warnings.append(f"duplicate MMerge decoration key {key}: {by_exact_key[key]} and {runtime_id}")
            else:
                by_exact_key[key] = runtime_id

        if name:
            by_name[name].append(runtime_id)

    remap: dict[int, int] = {}

    for runtime_id, entry in legacy_decorations.items():
        name = normalize_name(str(entry["internal_name"]))
        sprite_id = int(entry["sprite_id"])
        sprite_name = normalize_name(legacy_sprite_names.get(sprite_id, ""))

        if not name:
            continue

        exact_match = by_exact_key.get((name, sprite_name))

        if exact_match is not None:
            remap[runtime_id] = exact_match
            continue

        name_matches = by_name.get(name, [])

        if len(name_matches) == 1:
            remap[runtime_id] = name_matches[0]

    return remap, warnings


def remap_scene_file(
    path: Path,
    source_path: Path | None,
    remap: dict[int, int],
    mmerge_decorations: dict[int, dict[str, object]],
    dry_run: bool,
) -> tuple[int, set[int]]:
    text = path.read_text(encoding="utf-8")
    source_decoration_ids = read_scene_decoration_ids(source_path) if source_path is not None else None
    used_unmapped: set[int] = set()
    changed_count = 0
    decoration_index = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal changed_count, decoration_index
        current_decoration_id = int(match.group(2))

        if source_decoration_ids is not None:
            if decoration_index >= len(source_decoration_ids):
                used_unmapped.add(current_decoration_id)
                decoration_index += 1
                return match.group(0)

            decoration_id = source_decoration_ids[decoration_index]
            decoration_index += 1
        else:
            decoration_id = current_decoration_id

        replacement_id = remap.get(decoration_id)

        if replacement_id is None:
            if decoration_id not in mmerge_decorations:
                used_unmapped.add(decoration_id)
            return match.group(0)

        if replacement_id == decoration_id:
            return match.group(0)

        changed_count += 1
        return f"{match.group(1)}{replacement_id}"

    updated_text = re.sub(r"^(\s*decoration_list_id:\s+)(\d+)\s*$", replace_match, text, flags=re.MULTILINE)

    if changed_count != 0 and not dry_run:
        path.write_text(updated_text, encoding="utf-8")

    return changed_count, used_unmapped


def read_scene_decoration_ids(path: Path | None) -> list[int] | None:
    if path is None:
        return None

    if not path.exists():
        return None

    decoration_ids: list[int] = []

    for match in re.finditer(r"^\s*decoration_list_id:\s+(\d+)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE):
        decoration_ids.append(int(match.group(1)))

    return decoration_ids


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remap MM8 scene decoration ids to the global MMerge DecList ids.")
    parser.add_argument("--legacy-decoration-table", required=True)
    parser.add_argument("--legacy-sft-bin", required=True)
    parser.add_argument("--mmerge-decoration-table", required=True)
    parser.add_argument("--mmerge-rendering-dir", required=True)
    parser.add_argument("--scene-dir", required=True)
    parser.add_argument(
        "--source-scene-dir",
        help="optional directory with original scene files; remap ids are read from these files and written to scene-dir",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    legacy_decorations = parse_decoration_table(Path(args.legacy_decoration_table))
    legacy_sprite_names = parse_sft_bin_sprite_names(Path(args.legacy_sft_bin))
    mmerge_decorations = parse_decoration_table(Path(args.mmerge_decoration_table))
    mmerge_sprite_names = parse_sprite_yml_names(Path(args.mmerge_rendering_dir))

    remap, warnings = build_remap(legacy_decorations, legacy_sprite_names, mmerge_decorations, mmerge_sprite_names)

    changed_total = 0
    used_unmapped_total: dict[int, int] = defaultdict(int)
    missing_source_files: list[str] = []

    scene_dir = Path(args.scene_dir)
    source_scene_dir = Path(args.source_scene_dir) if args.source_scene_dir else None

    for path in sorted(scene_dir.glob("*.scene.yml")):
        source_path = source_scene_dir / path.name if source_scene_dir is not None else None

        if source_path is not None and not source_path.exists():
            missing_source_files.append(path.name)
            continue

        changed_count, used_unmapped = remap_scene_file(path, source_path, remap, mmerge_decorations, args.dry_run)
        changed_total += changed_count

        for decoration_id in used_unmapped:
            used_unmapped_total[decoration_id] += 1

    for warning in warnings:
        print(f"warning: {warning}")

    print(f"legacy decoration ids mapped: {len(remap)} / {len(legacy_decorations)}")
    print(f"scene decoration references changed: {changed_total}")

    if used_unmapped_total:
        unmapped_text = ", ".join(str(decoration_id) for decoration_id in sorted(used_unmapped_total))
        print(f"warning: used scene decoration ids without mapping: {unmapped_text}")

    if missing_source_files:
        missing_text = ", ".join(missing_source_files)
        print(f"warning: source scene files missing: {missing_text}")

    return 1 if used_unmapped_total or missing_source_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
