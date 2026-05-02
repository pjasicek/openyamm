#!/usr/bin/env python3

from __future__ import annotations

import argparse
import struct
from pathlib import Path


HEADER_GROUP = "Portrait Frame Data\t\t\tTiming\tFlags"
HEADER_COLUMNS = "#\tTextureIndex\tFrameLengthRaw\tAnimationLengthRaw\tFlags"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export dpft.bin into portrait_frame_data.txt")
    parser.add_argument("--source-bin", help="path to dpft.bin")
    parser.add_argument("--output", help="path to portrait_frame_data.txt")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    legacy_binary_path = repo_root / "assets_dev" / "_legacy" / "bin_tables" / "dpft.bin"
    fallback_binary_path = repo_root / "assets_dev" / "Data" / "EnglishT" / "dpft.bin"
    binary_path = Path(args.source_bin) if args.source_bin else legacy_binary_path

    if not binary_path.exists() and not args.source_bin:
        binary_path = fallback_binary_path

    output_path = (
        Path(args.output)
        if args.output
        else repo_root / "assets_dev" / "Data" / "data_tables" / "portrait_frame_data.txt"
    )

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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
