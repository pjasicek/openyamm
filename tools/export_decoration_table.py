#!/usr/bin/env python3

from __future__ import annotations

import struct
from pathlib import Path


HEADER_GROUP = "Decoration Data\t\t\tDescriptor\t\t\t\t\t\t\tComments\t"
HEADER_COLUMNS = (
    "#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\tLightGreen\tLightBlue\t"
    "SoundId\tFlags\tSpriteId\tComments"
)


def read_fixed_string(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("latin1", errors="ignore")


def parse_bin_rows(binary_path: Path) -> dict[int, dict[str, int | str]]:
    data = binary_path.read_bytes()
    entry_count = struct.unpack_from("<I", data, 0)[0]
    rows: dict[int, dict[str, int | str]] = {}

    for index in range(entry_count):
        offset = 4 + index * 84
        rows[index + 1] = {
            "internal_name": read_fixed_string(data[offset + 0x00:offset + 0x20]),
            "hint": read_fixed_string(data[offset + 0x20:offset + 0x40]),
            "type": struct.unpack_from("<h", data, offset + 0x40)[0],
            "height": struct.unpack_from("<H", data, offset + 0x42)[0],
            "radius": struct.unpack_from("<h", data, offset + 0x44)[0],
            "light_radius": struct.unpack_from("<h", data, offset + 0x46)[0],
            "sprite_id": struct.unpack_from("<H", data, offset + 0x48)[0],
            "flags": struct.unpack_from("<H", data, offset + 0x4A)[0],
            "sound_id": struct.unpack_from("<h", data, offset + 0x4C)[0],
            "light_red": data[offset + 0x50],
            "light_green": data[offset + 0x51],
            "light_blue": data[offset + 0x52],
        }

    return rows


def parse_text_overrides(text_path: Path) -> dict[int, dict[str, str]]:
    overrides: dict[int, dict[str, str]] = {}

    for line in text_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split("\t")

        if not parts or not parts[0].strip().isdigit():
            continue

        number = int(parts[0].strip())
        if len(parts) >= 14:
            overrides[number] = {
                "label": parts[1].strip(),
                "hint": parts[2].strip(),
                "flags": parts[11].strip(),
                "comments": parts[13].strip(),
            }
        else:
            overrides[number] = {
                "label": parts[1].strip() if len(parts) > 1 else "",
                "hint": parts[2].strip() if len(parts) > 2 else "",
                "flags": parts[10].strip() if len(parts) > 10 else "",
                "comments": parts[11].strip() if len(parts) > 11 else "",
            }

    return overrides


def format_flags(flag_text: str, flag_value: int) -> str:
    if flag_text:
        return flag_text

    if flag_value == 0:
        return "0"

    names: list[str] = []

    if flag_value & 0x0001:
        names.append("MoveThrough")
    if flag_value & 0x0002:
        names.append("DontDraw")
    if flag_value & 0x0004:
        names.append("FlickerSlow")
    if flag_value & 0x0008:
        names.append("FlickerAverage")
    if flag_value & 0x0010:
        names.append("FlickerFast")
    if flag_value & 0x0020:
        names.append("Marker")
    if flag_value & 0x0040:
        names.append("SlowLoop")
    if flag_value & 0x0080:
        names.append("EmitFire")
    if flag_value & 0x0100:
        names.append("SoundOnDawn")
    if flag_value & 0x0200:
        names.append("SoundOnDusk")
    if flag_value & 0x0400:
        names.append("EmitSmoke")

    known_mask = 0x07FF
    unknown_bits = flag_value & ~known_mask

    if unknown_bits != 0:
        names.append(f"0x{unknown_bits:04x}")

    return ",".join(names)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "ddeclist.bin"
    output_path = repo_root / "assets_dev" / "Data" / "data_tables" / "decoration_data.txt"
    legacy_text_path = repo_root / "assets_dev" / "Data" / "data_tables" / "dec_list.txt"

    bin_rows = parse_bin_rows(binary_path)
    if output_path.exists():
        text_overrides = parse_text_overrides(output_path)
    else:
        text_overrides = parse_text_overrides(legacy_text_path)

    lines = [HEADER_GROUP, HEADER_COLUMNS, ""]

    for number in sorted(bin_rows):
        binary_row = bin_rows[number]
        override = text_overrides.get(number, {})

        internal_name = override.get("label") or str(binary_row["internal_name"])
        hint = override.get("hint") or str(binary_row["hint"])
        flags = format_flags(override.get("flags", ""), int(binary_row["flags"]))
        comments = override.get("comments", "")

        lines.append(
            "\t".join(
                [
                    str(number),
                    internal_name,
                    hint,
                    str(binary_row["type"]),
                    str(binary_row["radius"]),
                    str(binary_row["height"]),
                    str(binary_row["light_radius"]),
                    str(binary_row["light_red"]),
                    str(binary_row["light_green"]),
                    str(binary_row["light_blue"]),
                    str(binary_row["sound_id"]),
                    flags,
                    str(binary_row["sprite_id"]),
                    comments,
                ]
            )
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
