#!/usr/bin/env python3

from __future__ import annotations

import struct
from pathlib import Path


HEADER_GROUP = "Monster Descriptor Data\tDescriptor\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
HEADER_COLUMNS = (
    "#\tInternalName\tHeight\tRadius\tMovementSpeed\tToHitRadius\tTintColor\t"
    "AttackSoundId\tDeathSoundId\tWinceSoundId\tAwareSoundId\t"
    "SpriteStanding\tSpriteWalking\tSpriteAttackMelee\tSpriteAttackRanged\t"
    "SpriteGotHit\tSpriteDying\tSpriteDead\tSpriteBored"
)

def read_binary_rows(binary_path: Path) -> dict[int, list[str]]:
    data = binary_path.read_bytes()
    entry_count = struct.unpack_from("<I", data, 0)[0]
    rows: dict[int, list[str]] = {}

    for index in range(entry_count):
        offset = 4 + index * 184
        monster_id = index + 1
        internal_name = data[offset + 0x14:offset + 0x14 + 32].split(b"\0", 1)[0].decode("latin1", errors="ignore")
        height, radius, movement_speed = struct.unpack_from("<HHH", data, offset + 0x00)
        to_hit_radius = struct.unpack_from("<h", data, offset + 0x06)[0]
        tint_color = struct.unpack_from("<I", data, offset + 0x08)[0]
        sound_ids = struct.unpack_from("<HHHH", data, offset + 0x0c)
        sprite_names = []

        for sprite_index in range(8):
            sprite_offset = offset + 0x54 + sprite_index * 10
            sprite_name = data[sprite_offset:sprite_offset + 10].split(b"\0", 1)[0].decode(
                "latin1",
                errors="ignore")
            sprite_names.append(sprite_name)

        rows[monster_id] = [
            str(monster_id),
            internal_name,
            str(height),
            str(radius),
            str(movement_speed),
            str(to_hit_radius),
            f"0x{tint_color:08x}",
            str(sound_ids[0]),
            str(sound_ids[1]),
            str(sound_ids[2]),
            str(sound_ids[3]),
            *sprite_names,
        ]

    return rows


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dmonlist.bin"
    monster_data_path = repo_root / "assets_dev" / "Data" / "data_tables" / "monster_data.txt"
    table_path = repo_root / "assets_dev" / "Data" / "data_tables" / "monster_descriptors.txt"
    binary_rows = read_binary_rows(binary_path)
    rendered_lines: list[str] = []

    source_lines = monster_data_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    for line_index, line in enumerate(source_lines):
        if line_index == 0:
            rendered_lines.append(HEADER_GROUP)
            continue

        if line_index == 1:
            rendered_lines.append(HEADER_COLUMNS)
            continue

        if line_index in (2, 3):
            rendered_lines.append("")
            continue

        if not line.strip():
            rendered_lines.append(line)
            continue

        row = line.split("\t")

        try:
            monster_id = int(row[0].strip())
        except (ValueError, IndexError):
            rendered_lines.append("")
            continue

        if monster_id in binary_rows:
            rendered_lines.append("\t".join(binary_rows[monster_id]))
        else:
            rendered_lines.append(str(monster_id))

    table_path.write_text("\n".join(rendered_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
