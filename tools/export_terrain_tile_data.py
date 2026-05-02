#!/usr/bin/env python3

from __future__ import annotations

import argparse
import struct
from pathlib import Path


NAME_SIZE = 16
RECORD_SIZE = 26


def export_table(source_path: Path, target_path: Path) -> None:
    source_bytes = source_path.read_bytes()
    count = struct.unpack_from("<i", source_bytes, 0)[0]
    offset = 4

    lines = ["index\ttexture_name\ttile_id\tbitmap_id\ttileset\tvariant\tflags"]

    for index in range(count):
        texture_name = source_bytes[offset:offset + NAME_SIZE].split(b"\0", 1)[0].decode("latin1")
        tile_id, bitmap_id, tileset, variant, flags = struct.unpack_from("<HHHHH", source_bytes, offset + NAME_SIZE)
        lines.append(
            f"{index}\t{texture_name}\t{tile_id}\t{bitmap_id}\t{tileset}\t{variant}\t0x{flags:04x}"
        )
        offset += RECORD_SIZE

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export dtile*.bin into terrain tile data tables")
    parser.add_argument("--source-dir", help="directory containing dtile.bin, dtile2.bin, and dtile3.bin")
    parser.add_argument("--output-dir", help="directory for terrain_tile_data*.txt")
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source_dir = repo_root / "assets_dev" / "_legacy" / "tile_tables"
    fallback_source_dir = repo_root / "assets_dev" / "Data" / "EnglishT"
    target_dir = (
        Path(args.output_dir)
        if args.output_dir
        else repo_root / "assets_dev" / "Data" / "data_tables"
    )

    if args.source_dir:
        source_dir = Path(args.source_dir)
    elif not source_dir.exists():
        source_dir = fallback_source_dir

    export_table(source_dir / "dtile.bin", target_dir / "terrain_tile_data.txt")
    export_table(source_dir / "dtile2.bin", target_dir / "terrain_tile_data_2.txt")
    export_table(source_dir / "dtile3.bin", target_dir / "terrain_tile_data_3.txt")


if __name__ == "__main__":
    main()
