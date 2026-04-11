#!/usr/bin/env python3

from __future__ import annotations

import struct
from pathlib import Path


HEADER_GROUP = "Portrait Frame Data\t\t\tTiming\tFlags"
HEADER_COLUMNS = "#\tTextureIndex\tFrameLengthRaw\tAnimationLengthRaw\tFlags"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dpft.bin"
    output_path = repo_root / "assets_dev" / "Data" / "data_tables" / "portrait_frame_data.txt"

    data = binary_path.read_bytes()
    frame_count = struct.unpack_from("<I", data, 0)[0]
    lines = [HEADER_GROUP, HEADER_COLUMNS, ""]

    for index in range(frame_count):
        offset = 4 + index * 10
        portrait_id, texture_index, frame_length_raw, animation_length_raw, flags = struct.unpack_from(
            "<HHhhH",
            data,
            offset
        )
        lines.append(
            "\t".join(
                [
                    str(portrait_id),
                    str(texture_index),
                    str(frame_length_raw),
                    str(animation_length_raw),
                    f"0x{flags:04x}",
                ]
            )
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
