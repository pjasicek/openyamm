#!/usr/bin/env python3

from __future__ import annotations

import struct
from pathlib import Path


RECORD_SIZE = 20
NAME_SIZE = 12


def decode_flags(flags: int) -> str:
    names: list[str] = []
    if flags & 0x0001:
        names.append("HasMore")
    if flags & 0x0002:
        names.append("First")
    return ",".join(names)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dtft.bin"
    target_path = repo_root / "assets_dev" / "Data" / "data_tables" / "texture_frame_data.txt"
    source_bytes = source_path.read_bytes()
    count = struct.unpack_from("<i", source_bytes, 0)[0]
    offset = 4

    lines = ["TextureName\tTextureId\tFrameLengthRaw\tAnimationLengthRaw\tFlags\tFlagNames"]

    for _ in range(count):
        texture_name = source_bytes[offset:offset + NAME_SIZE].split(b"\0", 1)[0].decode("latin1")
        texture_id, frame_length_raw, animation_length_raw, flags = struct.unpack_from(
            "<hhhh",
            source_bytes,
            offset + NAME_SIZE,
        )
        lines.append(
            f"{texture_name}\t{texture_id}\t{frame_length_raw}\t{animation_length_raw}\t"
            f"0x{flags:x}\t{decode_flags(flags)}"
        )
        offset += RECORD_SIZE

    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
