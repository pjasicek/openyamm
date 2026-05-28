#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath


HEADER_FORMAT = "<cc60scc60sccc10IB"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
RESOURCE_ENTRY = 0
DIRECTORY_ENTRY = 1


@dataclass
class RezEntry:
    path: str
    offset: int
    size: int
    timestamp: int
    resource_id: int
    resource_type: int


def read_c_string(data: bytes, offset: int) -> tuple[str, int]:
    end = data.index(0, offset)
    return data[offset:end].decode("latin-1"), end + 1


def type_to_extension(resource_type: int) -> str:
    raw = resource_type.to_bytes(4, "little")
    length = 0
    for index in range(3, -1, -1):
        if raw[index] != 0:
            length = index + 1
            break
    return raw[:length][::-1].decode("latin-1").lower()


def safe_output_path(root: Path, rez_path: str, resource_type: int) -> Path:
    normalized = rez_path.replace("\\", "/").lstrip("/")
    parts = PureWindowsPath(normalized).parts
    clean_parts = []
    for part in parts:
        if part in ("", ".", ".."):
            continue
        clean_parts.append(part)

    if not clean_parts:
        raise ValueError(f"invalid empty REZ path: {rez_path!r}")

    output = root.joinpath(*clean_parts)
    if not output.suffix:
        extension = type_to_extension(resource_type)
        if extension:
            output = output.with_suffix("." + extension)

    resolved_root = root.resolve()
    resolved_output_parent = output.parent.resolve()
    if resolved_root != resolved_output_parent and resolved_root not in resolved_output_parent.parents:
        raise ValueError(f"refusing to write outside output root: {rez_path!r}")

    return output


def read_directory(f, path_prefix: str, offset: int, size: int) -> list[RezEntry]:
    f.seek(offset)
    block = f.read(size)
    if len(block) != size:
        raise ValueError(f"short directory read at {offset}, expected {size}, got {len(block)}")

    entries = []
    subdirs = []
    pos = 0
    while pos < len(block):
        if pos + 4 > len(block):
            raise ValueError(f"truncated directory entry at {offset + pos}")

        entry_type = struct.unpack_from("<I", block, pos)[0]
        pos += 4

        if entry_type == DIRECTORY_ENTRY:
            dir_offset, dir_size, timestamp = struct.unpack_from("<III", block, pos)
            pos += 12
            name, pos = read_c_string(block, pos)
            dir_path = f"{path_prefix}/{name}" if path_prefix else name
            subdirs.append((dir_path, dir_offset, dir_size, timestamp))
        elif entry_type == RESOURCE_ENTRY:
            item_offset, item_size, timestamp, resource_id, resource_type, key_count = struct.unpack_from(
                "<IIIIII", block, pos
            )
            pos += 24
            name, pos = read_c_string(block, pos)
            _description, pos = read_c_string(block, pos)
            pos += key_count * 4

            item_path = f"{path_prefix}/{name}" if path_prefix else name
            entries.append(
                RezEntry(
                    path=item_path,
                    offset=item_offset,
                    size=item_size,
                    timestamp=timestamp,
                    resource_id=resource_id,
                    resource_type=resource_type,
                )
            )
        else:
            raise ValueError(f"unknown directory entry type {entry_type} at {offset + pos - 4}")

    for dir_path, dir_offset, dir_size, _timestamp in subdirs:
        entries.extend(read_directory(f, dir_path, dir_offset, dir_size))

    return entries


def read_rez_entries(rez_path: Path) -> list[RezEntry]:
    with rez_path.open("rb") as f:
        header_data = f.read(HEADER_SIZE)
        if len(header_data) != HEADER_SIZE:
            raise ValueError(f"{rez_path} is too small to be a LithTech REZ")

        header = struct.unpack(HEADER_FORMAT, header_data)
        cr1, _lf1, file_type, _cr2, lf2, _title, _cr3, _lf3, eof, *rest = header
        values = rest[:-1]
        file_format_version = values[0]
        root_dir_offset = values[1]
        root_dir_size = values[2]

        if cr1 != b"\r" or lf2 != b"\n" or eof != b"\x1a" or file_format_version != 1:
            title = file_type.decode("latin-1", errors="replace").strip()
            raise ValueError(f"{rez_path} does not look like a supported REZ v1 file: {title!r}")

        return read_directory(f, "", root_dir_offset, root_dir_size)


def extract_rez(rez_path: Path, output_dir: Path, list_only: bool) -> list[RezEntry]:
    entries = read_rez_entries(rez_path)
    if list_only:
        return entries

    output_dir.mkdir(parents=True, exist_ok=True)
    with rez_path.open("rb") as f:
        for entry in entries:
            output_path = safe_output_path(output_dir, entry.path, entry.resource_type)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            f.seek(entry.offset)
            data = f.read(entry.size)
            if len(data) != entry.size:
                raise ValueError(f"short resource read for {entry.path}: expected {entry.size}, got {len(data)}")
            output_path.write_bytes(data)

    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract LithTech REZ v1 archives used by MM9.")
    parser.add_argument("rez", type=Path, help="Input .REZ file")
    parser.add_argument("output_dir", type=Path, nargs="?", help="Output directory")
    parser.add_argument("--list", action="store_true", help="List entries without extracting")
    args = parser.parse_args()

    if not args.list and args.output_dir is None:
        parser.error("output_dir is required unless --list is used")

    entries = extract_rez(args.rez, args.output_dir or Path("."), args.list)
    total_size = sum(entry.size for entry in entries)
    print(f"{args.rez}: {len(entries)} resources, {total_size} bytes")
    if args.list:
        for entry in entries:
            suffix = type_to_extension(entry.resource_type)
            print(f"{entry.size:10d} {suffix:4s} {entry.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
