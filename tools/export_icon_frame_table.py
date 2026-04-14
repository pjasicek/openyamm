#!/usr/bin/env python3

from __future__ import annotations

import struct
from pathlib import Path


HEADER_COMMENT = (
    "// AnimationName is referenced by spell_fx.txt:Animation and portrait_fx_events.txt:Animation"
)
HEADER_COLUMNS = "AnimationName\tTextureName\tFrameLengthRaw\tAnimationLengthRaw\tFlags\tFlagNames"


def format_flag_names(flags: int) -> str:
    flag_names: list[str] = []

    if flags & 0x0001:
        flag_names.append("HasMore")

    if flags & 0x0004:
        flag_names.append("First")

    return "|".join(flag_names)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    legacy_binary_path = repo_root / "assets_dev" / "_legacy" / "bin_tables" / "dift.bin"
    fallback_binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dift.bin"
    binary_path = legacy_binary_path if legacy_binary_path.exists() else fallback_binary_path
    output_path = repo_root / "assets_dev" / "Data" / "data_tables" / "icon_frame_data.txt"

    data = binary_path.read_bytes()
    frame_count = struct.unpack_from("<I", data, 0)[0]
    current_animation_name = ""
    lines = [HEADER_COMMENT, HEADER_COLUMNS]

    for index in range(frame_count):
        offset = 4 + index * 32
        animation_name_bytes, texture_name_bytes, frame_length_raw, animation_length_raw, flags = struct.unpack_from(
            "<12s12shhH",
            data,
            offset
        )
        animation_name = animation_name_bytes.split(b"\0", 1)[0].decode("ascii", errors="ignore")
        texture_name = texture_name_bytes.split(b"\0", 1)[0].decode("ascii", errors="ignore")

        if animation_name:
            current_animation_name = animation_name

        lines.append(
            "\t".join(
                [
                    current_animation_name,
                    texture_name,
                    str(frame_length_raw),
                    str(animation_length_raw),
                    f"0x{flags:04x}",
                    format_flag_names(flags),
                ]
            )
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
