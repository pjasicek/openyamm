#!/usr/bin/env python3

from __future__ import annotations

import csv
import struct
import sys
from pathlib import Path


FLAG_NAMES = (
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

HEADER_LINE = (
    "// Name\tSpriteName\tObjectId\tRadius\tHeight\tLifetimeTicks\tSpeed\tSpriteId\t"
    "ParticleTrailColor\tParticleTrailRed\tParticleTrailGreen\tParticleTrailBlue\tFlags"
)


def decode_flags(flags: int) -> str:
    tokens: list[str] = []
    remaining = flags

    for bit, name in FLAG_NAMES:
        if flags & bit:
            tokens.append(name)
            remaining &= ~bit

    if remaining != 0:
        tokens.append(f"0x{remaining:04x}")

    return ",".join(tokens) if tokens else "0"


def read_binary_rows(binary_path: Path) -> dict[int, dict[str, object]]:
    data = binary_path.read_bytes()
    entry_count = struct.unpack_from("<I", data, 0)[0]
    rows: dict[int, dict[str, object]] = {}

    for index in range(entry_count):
        offset = 4 + index * 56
        name = data[offset:offset + 32].split(b"\0", 1)[0].decode("latin1", errors="ignore")
        object_id, radius, height, flags, sprite_id, lifetime_ticks, particle_trail_color, speed = \
            struct.unpack_from("<hhhHhhIh", data, offset + 0x20)
        particle_trail_red, particle_trail_green, particle_trail_blue = struct.unpack_from(
            "<BBB", data, offset + 0x32
        )

        rows[object_id] = {
            "name": name,
            "radius": radius,
            "height": height,
            "lifetime_ticks": lifetime_ticks,
            "speed": speed,
            "sprite_id": sprite_id,
            "particle_trail_color": particle_trail_color,
            "particle_trail_red": particle_trail_red,
            "particle_trail_green": particle_trail_green,
            "particle_trail_blue": particle_trail_blue,
            "flags": flags,
        }

    return rows


def parse_template_rows(template_path: Path) -> list[tuple[str, int | None, str | None]]:
    result: list[tuple[str, int | None, str | None]] = []

    with template_path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")

            if not line:
                result.append(("blank", None, None))
                continue

            if line.lstrip().startswith("//"):
                result.append(("comment", None, line))
                continue

            row = next(csv.reader([line], delimiter="\t"))

            if len(row) < 3:
                result.append(("blank", None, None))
                continue

            try:
                object_id = int(row[2].strip())
            except ValueError:
                result.append(("comment", None, f"// {line}"))
                continue

            sprite_name = row[1].strip() if len(row) > 1 else "null"
            result.append(("data", object_id, sprite_name))

    return result


def format_row(entry: dict[str, object], sprite_name: str | None) -> str:
    sprite_name_value = sprite_name if sprite_name else "null"

    return (
        f"{entry['name']}\t"
        f"{sprite_name_value}\t"
        f"{entry['object_id']}\t"
        f"{entry['radius']}\t"
        f"{entry['height']}\t"
        f"{entry['lifetime_ticks']}\t"
        f"{entry['speed']}\t"
        f"{entry['sprite_id']}\t"
        f"0x{int(entry['particle_trail_color']):08x}\t"
        f"{entry['particle_trail_red']}\t"
        f"{entry['particle_trail_green']}\t"
        f"{entry['particle_trail_blue']}\t"
        f"{decode_flags(int(entry['flags']))}"
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    legacy_binary_path = repo_root / "assets_dev" / "_legacy" / "bin_tables" / "dobjlist.bin"
    fallback_binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dobjlist.bin"
    binary_path = legacy_binary_path if legacy_binary_path.exists() else fallback_binary_path
    table_path = repo_root / "assets_dev" / "Data" / "data_tables" / "object_list.txt"

    binary_rows = read_binary_rows(binary_path)
    template_rows = parse_template_rows(table_path)
    rendered_lines: list[str] = []
    seen_object_ids: set[int] = set()

    for kind, object_id, payload in template_rows:
        if kind == "blank":
            rendered_lines.append("")
            continue

        if kind == "comment":
            comment = payload if payload is not None else ""

            if comment.startswith("// Name\t"):
                rendered_lines.append(HEADER_LINE)
            else:
                rendered_lines.append(comment)

            continue

        if object_id is None or object_id not in binary_rows:
            raise RuntimeError(f"Object id {object_id} not found in {binary_path}")

        entry = dict(binary_rows[object_id])
        entry["object_id"] = object_id
        rendered_lines.append(format_row(entry, payload))
        seen_object_ids.add(object_id)

    for object_id in sorted(binary_rows):
        if object_id in seen_object_ids:
            continue

        entry = dict(binary_rows[object_id])
        entry["object_id"] = object_id
        rendered_lines.append(format_row(entry, "null"))

    table_path.write_text("\n".join(rendered_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
