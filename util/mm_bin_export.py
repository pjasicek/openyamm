#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
from pathlib import Path
from typing import Callable


class ByteReader:
    def __init__(self, data: bytes) -> None:
        self._data = data

    @property
    def size(self) -> int:
        return len(self._data)

    def require(self, offset: int, size: int) -> None:
        if offset < 0 or size < 0 or offset + size > len(self._data):
            raise ValueError(f"read out of bounds: offset={offset} size={size} total={len(self._data)}")

    def bytes(self, offset: int, size: int) -> bytes:
        self.require(offset, size)
        return self._data[offset: offset + size]

    def u8(self, offset: int) -> int:
        return self._data[offset]

    def i8(self, offset: int) -> int:
        return struct.unpack_from("<b", self._data, offset)[0]

    def u16(self, offset: int) -> int:
        return struct.unpack_from("<H", self._data, offset)[0]

    def i16(self, offset: int) -> int:
        return struct.unpack_from("<h", self._data, offset)[0]

    def u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self._data, offset)[0]

    def i32(self, offset: int) -> int:
        return struct.unpack_from("<i", self._data, offset)[0]

    def i64(self, offset: int) -> int:
        return struct.unpack_from("<q", self._data, offset)[0]

    def fixed_string(self, offset: int, size: int) -> str:
        raw = self.bytes(offset, size)
        end = raw.find(b"\0")
        if end >= 0:
            raw = raw[:end]
        return raw.decode("latin-1", errors="replace").rstrip(" ")

    def u16_array(self, offset: int, count: int) -> list[int]:
        self.require(offset, count * 2)
        return list(struct.unpack_from(f"<{count}H", self._data, offset))

    def i16_array(self, offset: int, count: int) -> list[int]:
        self.require(offset, count * 2)
        return list(struct.unpack_from(f"<{count}h", self._data, offset))

    def u32_array(self, offset: int, count: int) -> list[int]:
        self.require(offset, count * 4)
        return list(struct.unpack_from(f"<{count}I", self._data, offset))


def to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def make_document(
    format_name: str,
    input_path: Path,
    data: bytes,
    payload: dict,
) -> dict:
    return {
        "format": format_name,
        "input_path": str(input_path),
        "input_size": len(data),
        "payload": payload,
    }


def parse_counted_records(
    reader: ByteReader,
    record_size: int,
    parse_record: Callable[[ByteReader, int, int], dict],
) -> dict:
    if reader.size < 4:
        raise ValueError("file too small for count-prefixed table")

    count = reader.u32(0)
    payload_size = reader.size - 4

    if count == 0:
        return {
            "count": 0,
            "record_size": record_size,
            "entries": [],
            "trailing_bytes_base64": to_base64(reader.bytes(4, payload_size)),
        }

    required_size = 4 + count * record_size
    if reader.size < required_size:
        raise ValueError(
            f"table too small: count={count} record_size={record_size} required={required_size} actual={reader.size}"
        )

    entries = []
    for index in range(count):
        offset = 4 + index * record_size
        entries.append(parse_record(reader, offset, index))

    trailing = reader.bytes(required_size, reader.size - required_size)

    return {
        "count": count,
        "record_size": record_size,
        "entries": entries,
        "trailing_bytes_base64": to_base64(trailing) if trailing else "",
    }


def parse_dchest(reader: ByteReader) -> dict:
    record_size = 36

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        texture_id = reader.i16(offset + 34)
        texture_name = ""
        if texture_id > 0:
            texture_name = f"chest{texture_id:02d}"

        return {
            "index": index,
            "name": reader.fixed_string(offset + 0, 32),
            "width": reader.u8(offset + 32),
            "height": reader.u8(offset + 33),
            "texture_id": texture_id,
            "texture_name": texture_name,
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_ddeclist(reader: ByteReader) -> dict:
    record_size = 84

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        return {
            "index": index,
            "internal_name": reader.fixed_string(offset + 0x00, 32),
            "hint": reader.fixed_string(offset + 0x20, 32),
            "type": reader.i16(offset + 0x40),
            "height": reader.u16(offset + 0x42),
            "radius": reader.i16(offset + 0x44),
            "light_radius": reader.i16(offset + 0x46),
            "sprite_id": reader.u16(offset + 0x48),
            "flags": reader.u16(offset + 0x4A),
            "sound_id": reader.i16(offset + 0x4C),
            "pad_mm6": reader.i16(offset + 0x4E),
            "colored_light_red": reader.u8(offset + 0x50),
            "colored_light_green": reader.u8(offset + 0x51),
            "colored_light_blue": reader.u8(offset + 0x52),
            "pad_mm7": reader.u8(offset + 0x53),
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_dift(reader: ByteReader) -> dict:
    record_size = 32

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        frame_length_raw = reader.i16(offset + 24)
        animation_length_raw = reader.i16(offset + 26)

        return {
            "index": index,
            "animation_name": reader.fixed_string(offset + 0, 12),
            "texture_name": reader.fixed_string(offset + 12, 12),
            "frame_length_raw": frame_length_raw,
            "frame_length_ticks": frame_length_raw * 8,
            "animation_length_raw": animation_length_raw,
            "animation_length_ticks": animation_length_raw * 8,
            "flags": reader.i16(offset + 28),
            "texture_id": reader.u16(offset + 30),
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_dmonlist(reader: ByteReader) -> dict:
    record_size = 152

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        sprite_names = []
        for sprite_index in range(8):
            sprite_names.append(reader.fixed_string(offset + 0x34 + sprite_index * 10, 10))

        unused_sprite_names = []
        for sprite_index in range(2):
            unused_sprite_names.append(reader.fixed_string(offset + 0x84 + sprite_index * 10, 10))

        return {
            "index": index,
            "height": reader.u16(offset + 0x00),
            "radius": reader.u16(offset + 0x02),
            "movement_speed": reader.u16(offset + 0x04),
            "to_hit_radius": reader.i16(offset + 0x06),
            "tint_color": reader.u32(offset + 0x08),
            "sound_sample_ids": reader.u16_array(offset + 0x0C, 4),
            "internal_name": reader.fixed_string(offset + 0x14, 32),
            "sprite_names": sprite_names,
            "unused_sprite_names": unused_sprite_names,
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_dobjlist(reader: ByteReader) -> dict:
    record_size = 56

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        return {
            "index": index,
            "name_unused": reader.fixed_string(offset + 0x00, 32),
            "object_id": reader.i16(offset + 0x20),
            "radius": reader.i16(offset + 0x22),
            "height": reader.i16(offset + 0x24),
            "flags": reader.u16(offset + 0x26),
            "sprite_id": reader.u16(offset + 0x28),
            "lifetime_ticks": reader.i16(offset + 0x2A),
            "particle_trail_color_32": reader.u32(offset + 0x2C),
            "speed": reader.i16(offset + 0x30),
            "particle_trail_red": reader.u8(offset + 0x32),
            "particle_trail_green": reader.u8(offset + 0x33),
            "particle_trail_blue": reader.u8(offset + 0x34),
            "padding_bytes": list(reader.bytes(offset + 0x35, 3)),
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_doverlay(reader: ByteReader) -> dict:
    record_size = 8

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        return {
            "index": index,
            "overlay_id": reader.u16(offset + 0),
            "overlay_type": reader.u16(offset + 2),
            "sprite_frameset_id": reader.u16(offset + 4),
            "sprite_frameset_group": reader.i16(offset + 6),
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_dpft(reader: ByteReader) -> dict:
    record_size = 10

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        return {
            "index": index,
            "portrait_id": reader.u16(offset + 0),
            "texture_index": reader.u16(offset + 2),
            "frame_length_raw": reader.i16(offset + 4),
            "frame_length_ticks": reader.i16(offset + 4) * 8,
            "animation_length_raw": reader.i16(offset + 6),
            "animation_length_ticks": reader.i16(offset + 6) * 8,
            "flags": reader.i16(offset + 8),
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_dsft(reader: ByteReader) -> dict:
    if reader.size < 8:
        raise ValueError("file too small for dsft header")

    frame_count = reader.u32(0)
    eframe_count = reader.u32(4)
    record_size = 60
    frames_size = frame_count * record_size
    eframes_size = eframe_count * 2
    required_size = 8 + frames_size + eframes_size

    if reader.size < required_size:
        raise ValueError(
            f"dsft too small: frames={frame_count} eframes={eframe_count} required={required_size} actual={reader.size}"
        )

    frames = []
    for index in range(frame_count):
        offset = 8 + index * record_size
        scale_fixed = reader.i32(offset + 0x28)
        frame_length_raw = reader.i16(offset + 0x36)
        animation_length_raw = reader.i16(offset + 0x38)

        frames.append(
            {
                "index": index,
                "sprite_name": reader.fixed_string(offset + 0x00, 12),
                "texture_name": reader.fixed_string(offset + 0x0C, 12),
                "hardware_sprite_ids": reader.i16_array(offset + 0x18, 8),
                "scale_fixed": scale_fixed,
                "scale": scale_fixed / 65536.0,
                "flags": reader.i32(offset + 0x2C),
                "glow_radius": reader.i16(offset + 0x30),
                "palette_id": reader.i16(offset + 0x32),
                "palette_index": reader.i16(offset + 0x34),
                "frame_length_raw": frame_length_raw,
                "frame_length_ticks": frame_length_raw * 8,
                "animation_length_raw": animation_length_raw,
                "animation_length_ticks": animation_length_raw * 8,
                "padding": reader.i16(offset + 0x3A),
            }
        )

    eframe_offset = 8 + frames_size
    eframes = reader.u16_array(eframe_offset, eframe_count)
    trailing = reader.bytes(required_size, reader.size - required_size)

    return {
        "frame_count": frame_count,
        "eframe_count": eframe_count,
        "frame_record_size": record_size,
        "frames": frames,
        "eframes": eframes,
        "trailing_bytes_base64": to_base64(trailing) if trailing else "",
    }


def parse_dsounds(reader: ByteReader) -> dict:
    if reader.size < 4:
        raise ValueError("file too small for dsounds header")

    count = reader.u32(0)
    payload_size = reader.size - 4

    if count == 0:
        return {
            "count": 0,
            "record_size": 0,
            "entries": [],
            "trailing_bytes_base64": to_base64(reader.bytes(4, payload_size)),
        }

    if payload_size % count != 0:
        raise ValueError(f"dsounds payload not divisible by count: payload={payload_size} count={count}")

    record_size = payload_size // count
    if record_size < 32:
        raise ValueError(f"dsounds record size unexpectedly small: {record_size}")

    entries = []
    for index in range(count):
        offset = 4 + index * record_size
        name = reader.fixed_string(offset + 0, 32)
        word_count = (record_size - 32) // 4
        words = reader.u32_array(offset + 32, word_count)

        entry = {
            "index": index,
            "name": name,
            "record_size": record_size,
            "u32_words": words,
        }

        if word_count >= 22:
            entry["sound_id_guess"] = words[0]
            entry["type_guess"] = words[1]
            entry["flags_guess"] = words[2]
            entry["sound_data_guess"] = words[3:20]
            entry["sound3d_id_guess"] = words[20]
            entry["decompressed_guess"] = words[21]
            entry["extra_words"] = words[22:]

        entries.append(entry)

    return {
        "count": count,
        "record_size": record_size,
        "entries": entries,
        "trailing_bytes_base64": "",
    }


def parse_dtft(reader: ByteReader) -> dict:
    record_size = 20

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        return {
            "index": index,
            "texture_name": reader.fixed_string(offset + 0, 12),
            "texture_id": reader.i16(offset + 12),
            "frame_length_raw": reader.i16(offset + 14),
            "frame_length_ticks": reader.i16(offset + 14) * 8,
            "animation_length_raw": reader.i16(offset + 16),
            "animation_length_ticks": reader.i16(offset + 16) * 8,
            "flags": reader.i16(offset + 18),
        }

    return parse_counted_records(reader, record_size, parse_record)


def parse_dtile(reader: ByteReader) -> dict:
    record_size = 26

    def parse_record(reader: ByteReader, offset: int, index: int) -> dict:
        return {
            "index": index,
            "texture_name": reader.fixed_string(offset + 0, 16),
            "tile_id": reader.u16(offset + 16),
            "bitmap_id": reader.u16(offset + 18),
            "tileset": reader.u16(offset + 20),
            "variant": reader.u16(offset + 22),
            "flags": reader.u16(offset + 24),
        }

    return parse_counted_records(reader, record_size, parse_record)


PARSERS: dict[str, Callable[[ByteReader], dict]] = {
    "dchest": parse_dchest,
    "ddeclist": parse_ddeclist,
    "dift": parse_dift,
    "dmonlist": parse_dmonlist,
    "dobjlist": parse_dobjlist,
    "doverlay": parse_doverlay,
    "dpft": parse_dpft,
    "dsft": parse_dsft,
    "dsounds": parse_dsounds,
    "dtft": parse_dtft,
    "dtile": parse_dtile,
    "dtile2": parse_dtile,
    "dtile3": parse_dtile,
}


def export_file(format_name: str, input_path: Path) -> dict:
    data = input_path.read_bytes()
    reader = ByteReader(data)
    parser = PARSERS[format_name]
    payload = parser(reader)
    return make_document(format_name, input_path, data, payload)


def write_json(document: dict, output_path: Path | None) -> None:
    text = json.dumps(document, indent=2, sort_keys=False)
    if output_path is None:
        sys.stdout.write(text)
        sys.stdout.write("\n")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text + "\n", encoding="utf-8")


def build_argument_parser(format_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Export {format_name}.bin to JSON."
    )
    parser.add_argument("input", type=Path, help="Input binary file path")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path (defaults to stdout)")
    return parser


def main_for_format(format_name: str) -> int:
    parser = build_argument_parser(format_name)
    args = parser.parse_args()
    document = export_file(format_name, args.input)
    write_json(document, args.output)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenYAMM EnglishT bin file to JSON.")
    parser.add_argument("format", choices=sorted(PARSERS.keys()), help="Binary table format")
    parser.add_argument("input", type=Path, help="Input binary file path")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path (defaults to stdout)")
    args = parser.parse_args()

    document = export_file(args.format, args.input)
    write_json(document, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
