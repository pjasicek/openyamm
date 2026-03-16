#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
from pathlib import Path


OUTDOOR_REVEAL_MAP_BYTES = 88 * 11 * 2
LOCATION_HEADER_SIZE = 40
ACTOR_RECORD_SIZE = 0x3CC
SPRITE_OBJECT_RECORD_SIZE = 0x70
CHEST_RECORD_SIZE = 5324
PERSISTENT_VARIABLES_SIZE = 0xC8
LOCATION_TIME_SIZE = 0x38
VERSION_OFFSET = 0x40
VERSION_FIELD_SIZE = 16
MASTER_TILE_OFFSET = 0x5F
TERRAIN_SECTION_OFFSET = 0xB0
TERRAIN_SECTION_OFFSET_V8 = 0xB4
TERRAIN_MAP_SIZE = 0x4000
CMAP1_SIZE = 0x20000
CMAP2_SIZE = 0x10000
BMODEL_HEADER_SIZE = 0xBC
BMODEL_VERTEX_SIZE = 12
BMODEL_FACE_SIZE = 0x134
BMODEL_FACE_FLAGS_SIZE = 2
BMODEL_TEXTURE_NAME_SIZE = 10
BMODEL_BSP_NODE_SIZE = 8
ENTITY_NAME_SIZE = 0x20
VERSION6_ENTITY_SIZE = 0x1C
VERSION7_ENTITY_SIZE = 0x20
SPRITE_OBJECT_CONTAINING_ITEM_OFFSET = 0x1C
SPRITE_OBJECT_CONTAINING_ITEM_SIZE = 0x30
CHEST_ITEMS_OFFSET = 0x04
CHEST_ITEMS_SIZE = 140 * 38
CHEST_INVENTORY_MATRIX_OFFSET = CHEST_ITEMS_OFFSET + CHEST_ITEMS_SIZE
ACTOR_NPC_ID_OFFSET = 0x20
ACTOR_ATTRIBUTES_OFFSET = 0x24
ACTOR_HP_OFFSET = 0x28
ACTOR_HOSTILITY_TYPE_OFFSET = 0x2C
ACTOR_MONSTER_INFO_ID_OFFSET = 0x6A
ACTOR_MONSTER_ID_OFFSET = 0x7C
ACTOR_RADIUS_OFFSET = 0x90
ACTOR_HEIGHT_OFFSET = 0x92
ACTOR_MOVE_SPEED_OFFSET = 0x94
ACTOR_POSITION_OFFSET = 0x96
ACTOR_SPRITE_IDS_OFFSET = 0xD4
ACTOR_SECTOR_ID_OFFSET = 0xDC
ACTOR_CURRENT_ACTION_ANIMATION_OFFSET = 0xDE
ACTOR_ALLY_OFFSET = 0x340
ACTOR_GROUP_OFFSET = 0x344
ACTOR_UNIQUE_NAME_INDEX_OFFSET = 0x34C
TICKS_PER_REALTIME_SECOND = 128
VERSION6_TAG = b"MM6 Outdoor v1.11"
VERSION7_TAG = b"MM6 Outdoor v7.00"


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


def ticks_to_realtime_milliseconds(ticks: int) -> int:
    return ticks * 1000 // TICKS_PER_REALTIME_SECOND


def advance_offset(offset: int, byte_count: int, total_size: int) -> int:
    if byte_count < 0 or byte_count > total_size - offset:
        raise ValueError(f"advance out of bounds: offset={offset} byte_count={byte_count} total={total_size}")
    return offset + byte_count


def detect_outdoor_odm_version(reader: ByteReader) -> int | None:
    version_field = reader.bytes(VERSION_OFFSET, VERSION_FIELD_SIZE)
    if version_field.startswith(VERSION6_TAG):
        return 6
    if version_field.startswith(VERSION7_TAG):
        return 7
    if version_field == b"\0" * VERSION_FIELD_SIZE:
        return 8
    return None


def derive_outdoor_context_from_odm(odm_path: Path) -> dict:
    data = odm_path.read_bytes()
    reader = ByteReader(data)
    version = detect_outdoor_odm_version(reader)
    if version is None:
        raise ValueError(f"unsupported outdoor map version in {odm_path}")

    offset = TERRAIN_SECTION_OFFSET_V8 if version == 8 else TERRAIN_SECTION_OFFSET
    offset = advance_offset(offset, TERRAIN_MAP_SIZE, reader.size)
    offset = advance_offset(offset, TERRAIN_MAP_SIZE, reader.size)
    offset = advance_offset(offset, TERRAIN_MAP_SIZE, reader.size)

    if version > 6:
        terrain_normal_count = reader.i32(offset)
        if terrain_normal_count < 0:
            raise ValueError(f"invalid terrain normal count in {odm_path}: {terrain_normal_count}")
        offset = advance_offset(offset, 4, reader.size)
        offset = advance_offset(offset, CMAP1_SIZE, reader.size)
        offset = advance_offset(offset, CMAP2_SIZE, reader.size)
        offset = advance_offset(offset, terrain_normal_count * 12, reader.size)

    bmodel_count = reader.i32(offset)
    if bmodel_count < 0:
        raise ValueError(f"invalid bmodel count in {odm_path}: {bmodel_count}")
    offset = advance_offset(offset, 4, reader.size)

    bmodel_headers_offset = offset
    offset = advance_offset(offset, bmodel_count * BMODEL_HEADER_SIZE, reader.size)

    total_faces_count = 0
    for index in range(bmodel_count):
        header_offset = bmodel_headers_offset + index * BMODEL_HEADER_SIZE
        vertex_count = reader.i32(header_offset + 0x44)
        face_count = reader.i32(header_offset + 0x4C)
        bsp_node_count = reader.i32(header_offset + 0x5C)

        if vertex_count < 0 or face_count < 0 or bsp_node_count < 0:
            raise ValueError(
                f"invalid bmodel counts in {odm_path}: bmodel={index} vertices={vertex_count} "
                f"faces={face_count} bsp_nodes={bsp_node_count}"
            )

        total_faces_count += face_count
        offset = advance_offset(offset, vertex_count * BMODEL_VERTEX_SIZE, reader.size)
        offset = advance_offset(offset, face_count * BMODEL_FACE_SIZE, reader.size)
        offset = advance_offset(offset, face_count * BMODEL_FACE_FLAGS_SIZE, reader.size)
        offset = advance_offset(offset, face_count * BMODEL_TEXTURE_NAME_SIZE, reader.size)
        offset = advance_offset(offset, bsp_node_count * BMODEL_BSP_NODE_SIZE, reader.size)

    entity_count = reader.i32(offset)
    if entity_count < 0:
        raise ValueError(f"invalid entity count in {odm_path}: {entity_count}")
    offset = advance_offset(offset, 4, reader.size)

    entity_size = VERSION6_ENTITY_SIZE if version == 6 else VERSION7_ENTITY_SIZE
    offset = advance_offset(offset, entity_count * entity_size, reader.size)
    offset = advance_offset(offset, entity_count * ENTITY_NAME_SIZE, reader.size)

    return {
        "odm_path": str(odm_path),
        "odm_version": version,
        "total_faces_count": total_faces_count,
        "decoration_count": entity_count,
        "bmodel_count": bmodel_count,
    }


def parse_location_header(reader: ByteReader) -> dict:
    return {
        "respawn_count": reader.i32(0x00),
        "last_respawn_day": reader.i32(0x04),
        "reputation": reader.i32(0x08),
        "alert_status": reader.i32(0x0C),
        "total_faces_count": reader.u32(0x10),
        "decoration_count": reader.u32(0x14),
        "bmodel_count": reader.u32(0x18),
        "field_1c": reader.i32(0x1C),
        "field_20": reader.i32(0x20),
        "field_24": reader.i32(0x24),
    }


def parse_actor(reader: ByteReader, offset: int, index: int) -> dict:
    return {
        "index": index,
        "name": reader.fixed_string(offset + 0x00, 32),
        "npc_id": reader.i16(offset + ACTOR_NPC_ID_OFFSET),
        "attributes": reader.u32(offset + ACTOR_ATTRIBUTES_OFFSET),
        "hp": reader.i16(offset + ACTOR_HP_OFFSET),
        "hostility_type": reader.u8(offset + ACTOR_HOSTILITY_TYPE_OFFSET),
        "monster_info_id": reader.i16(offset + ACTOR_MONSTER_INFO_ID_OFFSET),
        "monster_id": reader.i16(offset + ACTOR_MONSTER_ID_OFFSET),
        "radius": reader.u16(offset + ACTOR_RADIUS_OFFSET),
        "height": reader.u16(offset + ACTOR_HEIGHT_OFFSET),
        "move_speed": reader.u16(offset + ACTOR_MOVE_SPEED_OFFSET),
        "position": {
            "x": reader.i16(offset + ACTOR_POSITION_OFFSET + 0),
            "y": reader.i16(offset + ACTOR_POSITION_OFFSET + 2),
            "z": reader.i16(offset + ACTOR_POSITION_OFFSET + 4),
        },
        "sprite_ids": reader.u16_array(offset + ACTOR_SPRITE_IDS_OFFSET, 4),
        "sector_id": reader.i16(offset + ACTOR_SECTOR_ID_OFFSET),
        "current_action_animation": reader.u16(offset + ACTOR_CURRENT_ACTION_ANIMATION_OFFSET),
        "ally": reader.u32(offset + ACTOR_ALLY_OFFSET),
        "group": reader.u32(offset + ACTOR_GROUP_OFFSET),
        "unique_name_index": reader.i32(offset + ACTOR_UNIQUE_NAME_INDEX_OFFSET),
        "raw_record_base64": to_base64(reader.bytes(offset, ACTOR_RECORD_SIZE)),
    }


def parse_sprite_object(reader: ByteReader, offset: int, index: int) -> dict:
    return {
        "index": index,
        "sprite_id": reader.u16(offset + 0x00),
        "object_description_id": reader.u16(offset + 0x02),
        "position": {
            "x": reader.i32(offset + 0x04),
            "y": reader.i32(offset + 0x08),
            "z": reader.i32(offset + 0x0C),
        },
        "velocity": {
            "x": reader.i16(offset + 0x10),
            "y": reader.i16(offset + 0x12),
            "z": reader.i16(offset + 0x14),
        },
        "yaw_angle": reader.u16(offset + 0x16),
        "sound_id": reader.u16(offset + 0x18),
        "attributes": reader.u16(offset + 0x1A),
        "sector_id": reader.i16(offset + 0x1C),
        "time_since_created": reader.u16(offset + 0x1E),
        "temporary_lifetime": reader.i16(offset + 0x20),
        "glow_radius_multiplier": reader.i16(offset + 0x22),
        "containing_item_base64": to_base64(
            reader.bytes(offset + SPRITE_OBJECT_CONTAINING_ITEM_OFFSET, SPRITE_OBJECT_CONTAINING_ITEM_SIZE)
        ),
        "spell_id": reader.i32(offset + 0x4C),
        "spell_level": reader.i32(offset + 0x50),
        "spell_skill": reader.i32(offset + 0x54),
        "field_54": reader.i32(offset + 0x58),
        "spell_caster_pid": reader.i32(offset + 0x5C),
        "spell_target_pid": reader.i32(offset + 0x60),
        "lod_distance": reader.i8(offset + 0x64),
        "spell_caster_ability": reader.i8(offset + 0x65),
        "initial_position": {
            "x": reader.i32(offset + 0x68),
            "y": reader.i32(offset + 0x6C),
            "z": reader.i32(offset + 0x70),
        },
        "raw_record_base64": to_base64(reader.bytes(offset, SPRITE_OBJECT_RECORD_SIZE)),
    }


def parse_chest(reader: ByteReader, offset: int, index: int) -> dict:
    return {
        "index": index,
        "chest_type_id": reader.u16(offset + 0x00),
        "flags": reader.u16(offset + 0x02),
        "raw_items_base64": to_base64(reader.bytes(offset + CHEST_ITEMS_OFFSET, CHEST_ITEMS_SIZE)),
        "inventory_matrix": reader.i16_array(offset + CHEST_INVENTORY_MATRIX_OFFSET, 140),
        "raw_record_base64": to_base64(reader.bytes(offset, CHEST_RECORD_SIZE)),
    }


def parse_location_time(reader: ByteReader, offset: int) -> dict:
    return {
        "last_visit_time": reader.i64(offset + 0x00),
        "sky_texture_name": reader.fixed_string(offset + 0x08, 12),
        "weather_flags": reader.i32(offset + 0x14),
        "fog_weak_distance": reader.i32(offset + 0x18),
        "fog_strong_distance": reader.i32(offset + 0x1C),
        "reserved_base64": to_base64(reader.bytes(offset + 0x20, 24)),
    }


def export_ddm(input_path: Path, odm_path: Path | None) -> dict:
    data = input_path.read_bytes()
    reader = ByteReader(data)

    if reader.size < LOCATION_HEADER_SIZE + OUTDOOR_REVEAL_MAP_BYTES:
        raise ValueError("ddm file is too small to be an outdoor delta")

    location_header = parse_location_header(reader)
    companion_context = None
    companion_path = odm_path

    if companion_path is None:
        guessed_path = input_path.with_suffix(".odm")
        if guessed_path.exists():
            companion_path = guessed_path

    if companion_path is not None:
        companion_context = derive_outdoor_context_from_odm(companion_path)

    cursor = LOCATION_HEADER_SIZE

    fully_revealed_cells = reader.bytes(cursor, OUTDOOR_REVEAL_MAP_BYTES // 2)
    cursor += OUTDOOR_REVEAL_MAP_BYTES // 2
    partially_revealed_cells = reader.bytes(cursor, OUTDOOR_REVEAL_MAP_BYTES // 2)
    cursor += OUTDOOR_REVEAL_MAP_BYTES // 2

    total_faces_count = location_header["total_faces_count"]
    decoration_count = location_header["decoration_count"]

    if companion_context is not None:
        total_faces_count = companion_context["total_faces_count"]
        decoration_count = companion_context["decoration_count"]

    if total_faces_count < 0 or decoration_count < 0:
        raise ValueError("invalid ddm counts")

    face_attributes = reader.u32_array(cursor, total_faces_count)
    cursor += total_faces_count * 4

    decoration_flags = reader.u16_array(cursor, decoration_count)
    cursor += decoration_count * 2

    actor_count = reader.u32(cursor)
    cursor += 4
    actors = []
    for actor_index in range(actor_count):
        actor_offset = cursor + actor_index * ACTOR_RECORD_SIZE
        actors.append(parse_actor(reader, actor_offset, actor_index))
    cursor += actor_count * ACTOR_RECORD_SIZE

    sprite_object_count = reader.u32(cursor)
    cursor += 4
    sprite_objects = []
    for object_index in range(sprite_object_count):
        object_offset = cursor + object_index * SPRITE_OBJECT_RECORD_SIZE
        sprite_objects.append(parse_sprite_object(reader, object_offset, object_index))
    cursor += sprite_object_count * SPRITE_OBJECT_RECORD_SIZE

    chest_count = reader.u32(cursor)
    cursor += 4
    chests = []
    for chest_index in range(chest_count):
        chest_offset = cursor + chest_index * CHEST_RECORD_SIZE
        chests.append(parse_chest(reader, chest_offset, chest_index))
    cursor += chest_count * CHEST_RECORD_SIZE

    event_variables_offset = cursor
    map_vars = list(reader.bytes(event_variables_offset + 0, 75))
    decor_vars = list(reader.bytes(event_variables_offset + 75, 125))
    cursor += PERSISTENT_VARIABLES_SIZE

    location_time = None
    if cursor + LOCATION_TIME_SIZE <= reader.size:
        location_time = parse_location_time(reader, cursor)
        cursor += LOCATION_TIME_SIZE

    trailing = reader.bytes(cursor, reader.size - cursor)

    return {
        "format": "ddm",
        "input_path": str(input_path),
        "input_size": len(data),
        "payload": {
            "mode": "outdoor",
            "location_header": location_header,
            "companion_context": companion_context,
            "fully_revealed_cells_base64": to_base64(fully_revealed_cells),
            "partially_revealed_cells_base64": to_base64(partially_revealed_cells),
            "face_attributes": face_attributes,
            "decoration_flags": decoration_flags,
            "actor_count": actor_count,
            "actors": actors,
            "sprite_object_count": sprite_object_count,
            "sprite_objects": sprite_objects,
            "chest_count": chest_count,
            "chests": chests,
            "event_variables": {
                "map_vars": map_vars,
                "decor_vars": decor_vars,
            },
            "location_time": location_time,
            "trailing_bytes_base64": to_base64(trailing) if trailing else "",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export outdoor .ddm map delta to JSON.")
    parser.add_argument("input", type=Path, help="Input .ddm file path")
    parser.add_argument("--odm", type=Path, help="Companion outdoor .odm file path")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path (defaults to stdout)")
    args = parser.parse_args()

    document = export_ddm(args.input, args.odm)
    text = json.dumps(document, indent=2, sort_keys=False)

    if args.output is None:
        sys.stdout.write(text)
        sys.stdout.write("\n")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
