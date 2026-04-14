#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import struct
from pathlib import Path


RECORD_SIZE = 60
NAME_SIZE = 12

FLAG_NAMES = [
    (0x00000001, "HasMore"),
    (0x00000002, "Lit"),
    (0x00000004, "First"),
    (0x00000010, "Image1"),
    (0x00000020, "Center"),
    (0x00000040, "Fidget"),
    (0x00000080, "Loaded"),
    (0x00000100, "Mirror0"),
    (0x00000200, "Mirror1"),
    (0x00000400, "Mirror2"),
    (0x00000800, "Mirror3"),
    (0x00001000, "Mirror4"),
    (0x00002000, "Mirror5"),
    (0x00004000, "Mirror6"),
    (0x00008000, "Mirror7"),
    (0x00010000, "Images3"),
    (0x00020000, "Glowing"),
    (0x00040000, "Transparent"),
]


def decode_string(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("latin1").strip().lower()


def decode_flags(flags: int) -> list[str]:
    return [name for bit, name in FLAG_NAMES if flags & bit]


def format_float(value: float) -> str:
    if value.is_integer():
        return f"{value:.1f}"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def quote_yaml_string(value: str) -> str:
    return json.dumps(value)


def monster_family_root(name: str) -> str | None:
    match = re.match(r"^(m\d{3})[a-z]?", name)

    if match is None:
        return None

    return match.group(1)


def append_frame_lines(lines: list[str], frame: dict[str, object], indent: str) -> None:
    lines.append(f"{indent}- texture_name: {quote_yaml_string(frame['texture_name'])}")
    lines.append(f"{indent}  frame_length_raw: {frame['frame_length_raw']}")

    if frame["flags"]:
        flag_text = ", ".join(frame["flags"])
        lines.append(f"{indent}  flags: [{flag_text}]")

    if frame["scale"] != 1.0:
        lines.append(f"{indent}  scale: {format_float(frame['scale'])}")

    if frame["glow_radius"] != 0:
        lines.append(f"{indent}  glow_radius: {frame['glow_radius']}")

    if frame["palette_id"] != 0:
        lines.append(f"{indent}  palette_id: {frame['palette_id']}")


def build_group_lines(group: dict[str, object]) -> list[str]:
    lines = [
        f"  - sprite_id: {group['sprite_id']}",
        f"    sprite_name: {quote_yaml_string(group['sprite_name'])}",
    ]

    if group["animation_length_raw"] != 0:
        lines.append(f"    animation_length_raw: {group['animation_length_raw']}")

    lines.append("    frames:")

    for frame in group["frames"]:
        append_frame_lines(lines, frame, "      ")

    return lines


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    legacy_binary_path = repo_root / "assets_dev" / "_legacy" / "bin_tables" / "dsft.bin"
    fallback_binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dsft.bin"
    binary_path = legacy_binary_path if legacy_binary_path.exists() else fallback_binary_path
    rendering_path = repo_root / "assets_dev" / "Data" / "rendering"
    common_output_path = rendering_path / "sprite_frame_data_common.yml"
    family_output_dir = rendering_path / "sprite_frames" / "monsters"

    data = binary_path.read_bytes()
    frame_count, _ = struct.unpack_from("<II", data, 0)
    common_groups: list[dict[str, object]] = []
    family_groups: dict[str, list[dict[str, object]]] = {}

    family_output_dir.mkdir(parents=True, exist_ok=True)

    for existing_file in family_output_dir.glob("*.yml"):
        existing_file.unlink()

    frame_index = 0

    while frame_index < frame_count:
        offset = 8 + frame_index * RECORD_SIZE
        sprite_name = decode_string(data[offset:offset + NAME_SIZE])
        scale_fixed, flags, glow_radius, palette_id, frame_length_raw, animation_length_raw = struct.unpack_from(
            "<iihh2xhh",
            data,
            offset + 40,
        )

        group = {
            "sprite_id": frame_index,
            "sprite_name": sprite_name,
            "animation_length_raw": animation_length_raw,
            "frames": [],
        }
        family_root = monster_family_root(sprite_name)

        while True:
            offset = 8 + frame_index * RECORD_SIZE
            texture_name = decode_string(data[offset + 12:offset + 24])
            scale_fixed, flags, glow_radius, palette_id, frame_length_raw, _ = struct.unpack_from(
                "<iihh2xhh",
                data,
                offset + 40,
            )

            frame = {
                "texture_name": texture_name,
                "frame_length_raw": frame_length_raw,
                "flags": decode_flags(flags),
                "scale": scale_fixed / 65536.0,
                "glow_radius": glow_radius,
                "palette_id": palette_id,
            }
            group["frames"].append(frame)

            if family_root is None:
                family_root = monster_family_root(texture_name)

            has_more = (flags & 0x00000001) != 0
            frame_index += 1

            if not has_more:
                break

        if family_root is None:
            common_groups.append(group)
        else:
            family_groups.setdefault(family_root, []).append(group)

    common_lines = [
        "# Common sprite frame groups used by decorations, objects, spells, and shared effects.",
        "# sprite_id is the first frame index referenced by runtime tables.",
        "sprites:",
    ]

    for group in common_groups:
        common_lines.extend(build_group_lines(group))

    common_output_path.write_text("\n".join(common_lines) + "\n", encoding="utf-8")

    for family_root, groups in sorted(family_groups.items()):
        family_lines = [
            f"# Monster sprite frame groups for family {family_root}.",
            "# sprite_id is the first frame index referenced by runtime tables.",
            "sprites:",
        ]

        for group in groups:
            family_lines.extend(build_group_lines(group))

        (family_output_dir / f"{family_root}.yml").write_text("\n".join(family_lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
