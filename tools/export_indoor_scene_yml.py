#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


SECTION_OFFSET = 0x88
FACE_DATA_SIZE_OFFSET = 0x68
SECTOR_R_DATA_SIZE_OFFSET = 0x6C
SECTOR_RL_DATA_SIZE_OFFSET = 0x70
DOORS_DATA_SIZE_OFFSET = 0x74
VERTEX_RECORD_SIZE = 0x06
FACE_PARAM_RECORD_SIZE = 0x24
FACE_PARAM_NAME_SIZE = 0x0A
TEXTURE_NAME_SIZE = 0x0A
SPRITE_NAME_SIZE = 0x20
OUTLINE_RECORD_SIZE = 0x0C
UNKNOWN9_RECORD_SIZE = 0x08

LOCATION_HEADER_SIZE = 40
INDOOR_VISIBLE_OUTLINES_BYTES = 875
ACTOR_RECORD_SIZE = 0x3CC
SPRITE_OBJECT_RECORD_SIZE = 0x70
CHEST_RECORD_SIZE = 5324
DOOR_RECORD_SIZE = 0x50
PERSISTENT_VARIABLES_SIZE = 0xC8
LOCATION_TIME_SIZE = 0x38
ACTOR_NAME_SIZE = 32
SPRITE_OBJECT_CONTAINING_ITEM_OFFSET = 0x24
SPRITE_OBJECT_CONTAINING_ITEM_SIZE = 0x24
CHEST_ITEMS_OFFSET = 0x04
CHEST_ITEMS_SIZE = 140 * 36
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
ACTOR_CARRIED_ITEM_ID_OFFSET = 0xB8
ACTOR_ALLY_OFFSET = 0x340
ACTOR_GROUP_OFFSET = 0x34C
ACTOR_UNIQUE_NAME_INDEX_OFFSET = 0x3BC
TICKS_PER_REALTIME_SECOND = 128


class ParseError(RuntimeError):
    pass


class ByteReader:
    def __init__(self, path: Path, data: bytes):
        self.path = path
        self.data = data

    def can_read(self, offset: int, byte_count: int) -> bool:
        if offset < 0 or byte_count < 0:
            return False
        if offset > len(self.data):
            return False
        return byte_count <= (len(self.data) - offset)

    def require(self, offset: int, byte_count: int, context: str) -> None:
        if not self.can_read(offset, byte_count):
            raise ParseError(
                f"{self.path.name}: truncated read for {context} at 0x{offset:X}, need {byte_count} bytes"
            )

    def read_u8(self, offset: int, context: str) -> int:
        self.require(offset, 1, context)
        return self.data[offset]

    def read_i8(self, offset: int, context: str) -> int:
        self.require(offset, 1, context)
        return struct.unpack_from("<b", self.data, offset)[0]

    def read_u16(self, offset: int, context: str) -> int:
        self.require(offset, 2, context)
        return struct.unpack_from("<H", self.data, offset)[0]

    def read_i16(self, offset: int, context: str) -> int:
        self.require(offset, 2, context)
        return struct.unpack_from("<h", self.data, offset)[0]

    def read_u32(self, offset: int, context: str) -> int:
        self.require(offset, 4, context)
        return struct.unpack_from("<I", self.data, offset)[0]

    def read_i32(self, offset: int, context: str) -> int:
        self.require(offset, 4, context)
        return struct.unpack_from("<i", self.data, offset)[0]

    def read_i64(self, offset: int, context: str) -> int:
        self.require(offset, 8, context)
        return struct.unpack_from("<q", self.data, offset)[0]

    def read_bytes(self, offset: int, byte_count: int, context: str) -> bytes:
        self.require(offset, byte_count, context)
        return self.data[offset:offset + byte_count]

    def matches_text(self, offset: int, text: bytes) -> bool:
        if not self.can_read(offset, len(text)):
            return False
        return self.data[offset:offset + len(text)] == text

    def is_zero_block(self, offset: int, byte_count: int) -> bool:
        if not self.can_read(offset, byte_count):
            return False
        return all(value == 0 for value in self.data[offset:offset + byte_count])

    def read_fixed_string(self, offset: int, max_length: int, context: str) -> str:
        raw = self.read_bytes(offset, max_length, context)
        output = bytearray()

        for value in raw:
            if value == 0:
                break
            if value < 32 or value > 126:
                break
            output.append(value)

        return output.decode("latin1").rstrip(" ")


def quote_yaml_string(value: str) -> str:
    return json.dumps(value)


def bytes_to_hex(value: bytes) -> str:
    return value.hex().upper()


def ticks_to_realtime_milliseconds(ticks: int) -> int:
    return ticks * 1000 // TICKS_PER_REALTIME_SECOND


def write_yaml_scalar(lines: list[str], indent: str, key: str, value: object) -> None:
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, str):
        rendered = quote_yaml_string(value)
    else:
        rendered = str(value)
    lines.append(f"{indent}{key}: {rendered}")


def append_position_block(lines: list[str], indent: str, key: str, position: dict[str, int]) -> None:
    lines.append(f"{indent}{key}:")
    lines.append(f"{indent}  x: {position['x']}")
    lines.append(f"{indent}  y: {position['y']}")
    lines.append(f"{indent}  z: {position['z']}")


def append_int_list(lines: list[str], indent: str, key: str, values: list[int]) -> None:
    rendered = ", ".join(str(value) for value in values)
    lines.append(f"{indent}{key}: [{rendered}]")


def write_atomic_text(path: Path, text: str) -> None:
    temporary_path = path.with_name(path.name + ".tmp")
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(path)


def parse_location_header(reader: ByteReader) -> dict[str, int]:
    return {
        "respawn_count": reader.read_i32(0x00, "location respawn count"),
        "last_respawn_day": reader.read_i32(0x04, "location last respawn day"),
        "reputation": reader.read_i32(0x08, "location reputation"),
        "alert_status": reader.read_i32(0x0C, "location alert status"),
        "total_faces_count": reader.read_u32(0x10, "location total faces count"),
        "decoration_count": reader.read_u32(0x14, "location decoration count"),
        "bmodel_count": reader.read_u32(0x18, "location bmodel count"),
    }


def parse_u32_vector(reader: ByteReader, offset: int, count: int, context: str) -> tuple[list[int], int]:
    reader.require(offset, count * 4, context)
    values: list[int] = []

    for index in range(count):
        values.append(reader.read_u32(offset + index * 4, f"{context} {index}"))

    return values, offset + count * 4


def parse_u16_vector(reader: ByteReader, offset: int, count: int, context: str) -> tuple[list[int], int]:
    reader.require(offset, count * 2, context)
    values: list[int] = []

    for index in range(count):
        values.append(reader.read_u16(offset + index * 2, f"{context} {index}"))

    return values, offset + count * 2


def parse_actor_vector(reader: ByteReader, offset: int) -> tuple[list[dict[str, object]], int]:
    actor_count = reader.read_u32(offset, "actor count")
    data_offset = offset + 4
    reader.require(data_offset, actor_count * ACTOR_RECORD_SIZE, "actor records")
    actors: list[dict[str, object]] = []

    for actor_index in range(actor_count):
        actor_offset = data_offset + actor_index * ACTOR_RECORD_SIZE
        actor = {
            "actor_index": actor_index,
            "name": reader.read_fixed_string(actor_offset, ACTOR_NAME_SIZE, f"actor {actor_index} name"),
            "npc_id": reader.read_i16(actor_offset + ACTOR_NPC_ID_OFFSET, f"actor {actor_index} npc id"),
            "attributes": reader.read_u32(actor_offset + ACTOR_ATTRIBUTES_OFFSET, f"actor {actor_index} attributes"),
            "hp": reader.read_i16(actor_offset + ACTOR_HP_OFFSET, f"actor {actor_index} hp"),
            "hostility_type": reader.read_u8(
                actor_offset + ACTOR_HOSTILITY_TYPE_OFFSET,
                f"actor {actor_index} hostility type"
            ),
            "monster_info_id": reader.read_i16(
                actor_offset + ACTOR_MONSTER_INFO_ID_OFFSET,
                f"actor {actor_index} monster info id"
            ),
            "monster_id": reader.read_i16(actor_offset + ACTOR_MONSTER_ID_OFFSET, f"actor {actor_index} monster id"),
            "radius": reader.read_u16(actor_offset + ACTOR_RADIUS_OFFSET, f"actor {actor_index} radius"),
            "height": reader.read_u16(actor_offset + ACTOR_HEIGHT_OFFSET, f"actor {actor_index} height"),
            "move_speed": reader.read_u16(actor_offset + ACTOR_MOVE_SPEED_OFFSET, f"actor {actor_index} move speed"),
            "position": {
                "x": reader.read_i16(actor_offset + ACTOR_POSITION_OFFSET + 0, f"actor {actor_index} x"),
                "y": reader.read_i16(actor_offset + ACTOR_POSITION_OFFSET + 2, f"actor {actor_index} y"),
                "z": reader.read_i16(actor_offset + ACTOR_POSITION_OFFSET + 4, f"actor {actor_index} z"),
            },
            "sprite_ids": [],
            "sector_id": reader.read_i16(actor_offset + ACTOR_SECTOR_ID_OFFSET, f"actor {actor_index} sector id"),
            "current_action_animation": reader.read_u16(
                actor_offset + ACTOR_CURRENT_ACTION_ANIMATION_OFFSET,
                f"actor {actor_index} current action animation"
            ),
            "carried_item_id": reader.read_u32(
                actor_offset + ACTOR_CARRIED_ITEM_ID_OFFSET,
                f"actor {actor_index} carried item id"
            ),
            "group": reader.read_u32(actor_offset + ACTOR_GROUP_OFFSET, f"actor {actor_index} group"),
            "ally": reader.read_u32(actor_offset + ACTOR_ALLY_OFFSET, f"actor {actor_index} ally"),
            "unique_name_index": reader.read_i32(
                actor_offset + ACTOR_UNIQUE_NAME_INDEX_OFFSET,
                f"actor {actor_index} unique name index"
            ),
        }

        for sprite_index in range(4):
            actor["sprite_ids"].append(reader.read_u16(
                actor_offset + ACTOR_SPRITE_IDS_OFFSET + sprite_index * 2,
                f"actor {actor_index} sprite id {sprite_index}"
            ))

        actors.append(actor)

    return actors, data_offset + actor_count * ACTOR_RECORD_SIZE


def parse_sprite_objects(reader: ByteReader, offset: int) -> tuple[list[dict[str, object]], int]:
    sprite_object_count = reader.read_u32(offset, "sprite object count")
    data_offset = offset + 4
    reader.require(data_offset, sprite_object_count * SPRITE_OBJECT_RECORD_SIZE, "sprite object records")
    sprite_objects: list[dict[str, object]] = []

    for sprite_object_index in range(sprite_object_count):
        object_offset = data_offset + sprite_object_index * SPRITE_OBJECT_RECORD_SIZE
        sprite_objects.append({
            "sprite_object_index": sprite_object_index,
            "sprite_id": reader.read_u16(object_offset + 0x00, f"sprite object {sprite_object_index} sprite id"),
            "object_description_id": reader.read_u16(
                object_offset + 0x02,
                f"sprite object {sprite_object_index} object description id"
            ),
            "position": {
                "x": reader.read_i32(object_offset + 0x04, f"sprite object {sprite_object_index} x"),
                "y": reader.read_i32(object_offset + 0x08, f"sprite object {sprite_object_index} y"),
                "z": reader.read_i32(object_offset + 0x0C, f"sprite object {sprite_object_index} z"),
            },
            "velocity": {
                "x": reader.read_i16(object_offset + 0x10, f"sprite object {sprite_object_index} velocity x"),
                "y": reader.read_i16(object_offset + 0x12, f"sprite object {sprite_object_index} velocity y"),
                "z": reader.read_i16(object_offset + 0x14, f"sprite object {sprite_object_index} velocity z"),
            },
            "yaw_angle": reader.read_u16(object_offset + 0x16, f"sprite object {sprite_object_index} yaw angle"),
            "sound_id": reader.read_u16(object_offset + 0x18, f"sprite object {sprite_object_index} sound id"),
            "attributes": reader.read_u16(object_offset + 0x1A, f"sprite object {sprite_object_index} attributes"),
            "sector_id": reader.read_i16(object_offset + 0x1C, f"sprite object {sprite_object_index} sector id"),
            "time_since_created": reader.read_u16(
                object_offset + 0x1E,
                f"sprite object {sprite_object_index} time since created"
            ),
            "temporary_lifetime": reader.read_i16(
                object_offset + 0x20,
                f"sprite object {sprite_object_index} temporary lifetime"
            ),
            "glow_radius_multiplier": reader.read_i16(
                object_offset + 0x22,
                f"sprite object {sprite_object_index} glow radius multiplier"
            ),
            "spell_id": reader.read_i32(object_offset + 0x48, f"sprite object {sprite_object_index} spell id"),
            "spell_level": reader.read_i32(object_offset + 0x4C, f"sprite object {sprite_object_index} spell level"),
            "spell_skill": reader.read_i32(object_offset + 0x50, f"sprite object {sprite_object_index} spell skill"),
            "field54": reader.read_i32(object_offset + 0x54, f"sprite object {sprite_object_index} field54"),
            "spell_caster_pid": reader.read_i32(
                object_offset + 0x58,
                f"sprite object {sprite_object_index} spell caster pid"
            ),
            "spell_target_pid": reader.read_i32(
                object_offset + 0x5C,
                f"sprite object {sprite_object_index} spell target pid"
            ),
            "lod_distance": reader.read_i8(object_offset + 0x60, f"sprite object {sprite_object_index} lod distance"),
            "spell_caster_ability": reader.read_i8(
                object_offset + 0x61,
                f"sprite object {sprite_object_index} spell caster ability"
            ),
            "initial_position": {
                "x": reader.read_i32(object_offset + 0x64, f"sprite object {sprite_object_index} initial x"),
                "y": reader.read_i32(object_offset + 0x68, f"sprite object {sprite_object_index} initial y"),
                "z": reader.read_i32(object_offset + 0x6C, f"sprite object {sprite_object_index} initial z"),
            },
            "raw_containing_item_hex": bytes_to_hex(
                reader.read_bytes(
                    object_offset + SPRITE_OBJECT_CONTAINING_ITEM_OFFSET,
                    SPRITE_OBJECT_CONTAINING_ITEM_SIZE,
                    f"sprite object {sprite_object_index} containing item"
                )
            ),
        })

    return sprite_objects, data_offset + sprite_object_count * SPRITE_OBJECT_RECORD_SIZE


def parse_chests(reader: ByteReader, offset: int) -> tuple[list[dict[str, object]], int]:
    chest_count = reader.read_u32(offset, "chest count")
    data_offset = offset + 4
    reader.require(data_offset, chest_count * CHEST_RECORD_SIZE, "chest records")
    chests: list[dict[str, object]] = []

    for chest_index in range(chest_count):
        chest_offset = data_offset + chest_index * CHEST_RECORD_SIZE
        inventory_matrix: list[int] = []

        for item_index in range(140):
            inventory_matrix.append(reader.read_i16(
                chest_offset + CHEST_INVENTORY_MATRIX_OFFSET + item_index * 2,
                f"chest {chest_index} inventory matrix {item_index}"
            ))

        chests.append({
            "chest_index": chest_index,
            "chest_type_id": reader.read_u16(chest_offset + 0x00, f"chest {chest_index} type id"),
            "flags": reader.read_u16(chest_offset + 0x02, f"chest {chest_index} flags"),
            "raw_items_hex": bytes_to_hex(
                reader.read_bytes(chest_offset + CHEST_ITEMS_OFFSET, CHEST_ITEMS_SIZE, f"chest {chest_index} items")
            ),
            "inventory_matrix": inventory_matrix,
        })

    return chests, data_offset + chest_count * CHEST_RECORD_SIZE


def parse_persistent_variables(reader: ByteReader, offset: int) -> tuple[dict[str, list[int]], int]:
    payload = reader.read_bytes(offset, PERSISTENT_VARIABLES_SIZE, "persistent variables")
    return {
        "map": list(payload[:75]),
        "decor": list(payload[75:75 + 125]),
    }, offset + PERSISTENT_VARIABLES_SIZE


def decode_map_extra(reserved: bytes) -> tuple[int, int]:
    if len(reserved) != 24:
        raise ParseError(f"expected 24 MapExtra reserved bytes, got {len(reserved)}")
    map_extra_bits_raw = struct.unpack_from("<I", reserved, 0)[0]
    ceiling = struct.unpack_from("<i", reserved, 4)[0]
    return map_extra_bits_raw, ceiling


def parse_location_time_optional(reader: ByteReader, offset: int) -> dict[str, object]:
    location_time = {
        "last_visit_time": 0,
        "sky_texture_name": "",
        "day_bits_raw": 0,
        "fog_weak_distance": 0,
        "fog_strong_distance": 0,
        "map_extra_bits_raw": 0,
        "ceiling": 0,
    }

    if not reader.can_read(offset, LOCATION_TIME_SIZE):
        return location_time

    location_time["last_visit_time"] = reader.read_i64(offset + 0x00, "location time last visit time")
    location_time["sky_texture_name"] = reader.read_fixed_string(offset + 0x08, 12, "location time sky texture")
    location_time["day_bits_raw"] = reader.read_i32(offset + 0x14, "location time day bits")
    location_time["fog_weak_distance"] = reader.read_i32(offset + 0x18, "location time fog weak distance")
    location_time["fog_strong_distance"] = reader.read_i32(offset + 0x1C, "location time fog strong distance")
    reserved = reader.read_bytes(offset + 0x20, 24, "location time reserved")
    map_extra_bits_raw, ceiling = decode_map_extra(reserved)
    location_time["map_extra_bits_raw"] = map_extra_bits_raw
    location_time["ceiling"] = ceiling
    return location_time


def parse_indoor_doors(
    reader: ByteReader,
    offset: int,
    door_count: int,
    doors_data_size_bytes: int,
) -> tuple[list[dict[str, object]], list[int], int]:
    reader.require(offset, door_count * DOOR_RECORD_SIZE, "door records")
    door_headers: list[dict[str, object]] = []

    for door_index in range(door_count):
        door_offset = offset + door_index * DOOR_RECORD_SIZE
        door_headers.append({
            "door_index": door_index,
            "legacy_attributes": reader.read_u32(door_offset + 0x00, f"door {door_index} attributes"),
            "door_id": reader.read_u32(door_offset + 0x04, f"door {door_index} id"),
            "time_since_triggered_ms": ticks_to_realtime_milliseconds(
                reader.read_u32(door_offset + 0x08, f"door {door_index} time since triggered")
            ),
            "direction": {
                "x": reader.read_i32(door_offset + 0x0C, f"door {door_index} direction x"),
                "y": reader.read_i32(door_offset + 0x10, f"door {door_index} direction y"),
                "z": reader.read_i32(door_offset + 0x14, f"door {door_index} direction z"),
            },
            "move_length": reader.read_u32(door_offset + 0x18, f"door {door_index} move length"),
            "open_speed": reader.read_u32(door_offset + 0x1C, f"door {door_index} open speed"),
            "close_speed": reader.read_u32(door_offset + 0x20, f"door {door_index} close speed"),
            "num_vertices": reader.read_u16(door_offset + 0x44, f"door {door_index} num vertices"),
            "num_faces": reader.read_u16(door_offset + 0x46, f"door {door_index} num faces"),
            "num_sectors": reader.read_u16(door_offset + 0x48, f"door {door_index} num sectors"),
            "num_offsets": reader.read_u16(door_offset + 0x4A, f"door {door_index} num offsets"),
            "state": reader.read_u16(door_offset + 0x4C, f"door {door_index} state"),
        })

    data_offset = offset + door_count * DOOR_RECORD_SIZE
    doors_data_count = max(doors_data_size_bytes, 0) // 2
    reader.require(data_offset, doors_data_count * 2, "door data vectors")
    doors_data: list[int] = []

    for data_index in range(doors_data_count):
        doors_data.append(reader.read_i16(data_offset + data_index * 2, f"door data {data_index}"))

    cursor = 0
    active_doors: list[dict[str, object]] = []

    for door in door_headers:
        required_values = (
            door["num_vertices"]
            + door["num_faces"]
            + door["num_sectors"]
            + door["num_faces"] * 2
            + door["num_offsets"] * 3
        )

        if cursor + required_values > len(doors_data):
            raise ParseError(f"{reader.path.name}: door {door['door_index']} overruns doorsData payload")

        num_vertices = door["num_vertices"]
        num_faces = door["num_faces"]
        num_sectors = door["num_sectors"]
        num_offsets = door["num_offsets"]

        door["vertex_ids"] = [doors_data[cursor + index] for index in range(num_vertices)]
        cursor += num_vertices
        door["face_ids"] = [doors_data[cursor + index] for index in range(num_faces)]
        cursor += num_faces
        door["sector_ids"] = [doors_data[cursor + index] for index in range(num_sectors)]
        cursor += num_sectors
        door["delta_us"] = [doors_data[cursor + index] for index in range(num_faces)]
        cursor += num_faces
        door["delta_vs"] = [doors_data[cursor + index] for index in range(num_faces)]
        cursor += num_faces
        door["x_offsets"] = [doors_data[cursor + index] for index in range(num_offsets)]
        cursor += num_offsets
        door["y_offsets"] = [doors_data[cursor + index] for index in range(num_offsets)]
        cursor += num_offsets
        door["z_offsets"] = [doors_data[cursor + index] for index in range(num_offsets)]
        cursor += num_offsets

        has_geometry = num_vertices > 0 or num_faces > 0 or num_sectors > 0 or num_offsets > 0
        has_identity = door["door_id"] != 0 or door["legacy_attributes"] != 0 or door["state"] != 0

        if has_geometry or has_identity:
            active_doors.append(door)

    return active_doors, doors_data, data_offset + doors_data_count * 2


def can_parse_blv_layout(reader: ByteReader, layout: dict[str, int]) -> bool:
    offset = SECTION_OFFSET
    vertex_count = reader.read_i32(offset, "vertex count probe") if reader.can_read(offset, 4) else -1

    if vertex_count < 0:
        return False

    offset += 4 + vertex_count * VERTEX_RECORD_SIZE
    face_count = reader.read_i32(offset, "face count probe") if reader.can_read(offset, 4) else -1

    if face_count < 0:
        return False

    face_data_size = reader.read_i32(FACE_DATA_SIZE_OFFSET, "face data size probe") \
        if reader.can_read(FACE_DATA_SIZE_OFFSET, 4) else -1
    sector_r_data_size = reader.read_i32(SECTOR_R_DATA_SIZE_OFFSET, "sector r data size probe") \
        if reader.can_read(SECTOR_R_DATA_SIZE_OFFSET, 4) else -1
    sector_rl_data_size = reader.read_i32(SECTOR_RL_DATA_SIZE_OFFSET, "sector rl data size probe") \
        if reader.can_read(SECTOR_RL_DATA_SIZE_OFFSET, 4) else -1

    if face_data_size < 0 or sector_r_data_size < 0 or sector_rl_data_size < 0:
        return False

    offset += 4 + face_count * layout["face_record_size"]
    offset += face_data_size
    offset += face_count * TEXTURE_NAME_SIZE

    face_param_count = reader.read_i32(offset, "face param count probe") if reader.can_read(offset, 4) else -1

    if face_param_count < 0:
        return False

    offset += 4 + face_param_count * FACE_PARAM_RECORD_SIZE
    offset += face_param_count * FACE_PARAM_NAME_SIZE

    sector_count = reader.read_i32(offset, "sector count probe") if reader.can_read(offset, 4) else -1

    if sector_count < 0:
        return False

    offset += 4 + sector_count * layout["sector_record_size"]
    offset += sector_r_data_size
    offset += sector_rl_data_size

    sprite_header_count = reader.read_i32(offset, "sprite header count probe") if reader.can_read(offset, 4) else -1

    if sprite_header_count < 0:
        return False

    offset += 4
    sprite_count = reader.read_i32(offset, "sprite count probe") if reader.can_read(offset, 4) else -1

    if sprite_count < 0:
        return False

    offset += 4 + sprite_count * layout["sprite_record_size"]
    offset += sprite_count * SPRITE_NAME_SIZE

    light_count = reader.read_i32(offset, "light count probe") if reader.can_read(offset, 4) else -1

    if light_count < 0:
        return False

    offset += 4 + light_count * layout["light_record_size"]

    unknown9_count = reader.read_i32(offset, "unknown9 count probe") if reader.can_read(offset, 4) else -1

    if unknown9_count < 0:
        return False

    offset += 4 + unknown9_count * UNKNOWN9_RECORD_SIZE

    spawn_count = reader.read_i32(offset, "spawn count probe") if reader.can_read(offset, 4) else -1

    if spawn_count < 0:
        return False

    offset += 4 + spawn_count * layout["spawn_record_size"]

    outline_count = reader.read_i32(offset, "outline count probe") if reader.can_read(offset, 4) else -1

    if outline_count < 0:
        return False

    offset += 4 + outline_count * OUTLINE_RECORD_SIZE
    return offset == len(reader.data)


def detect_blv_layout(reader: ByteReader) -> dict[str, int]:
    layouts = (
        {"version": 6, "face_record_size": 0x50, "sector_record_size": 0x74, "sprite_record_size": 0x1C,
         "light_record_size": 0x0C, "spawn_record_size": 0x14},
        {"version": 7, "face_record_size": 0x60, "sector_record_size": 0x74, "sprite_record_size": 0x20,
         "light_record_size": 0x10, "spawn_record_size": 0x18},
        {"version": 8, "face_record_size": 0x60, "sector_record_size": 0x78, "sprite_record_size": 0x20,
         "light_record_size": 0x14, "spawn_record_size": 0x18},
    )

    for layout in layouts:
        if can_parse_blv_layout(reader, layout):
            return layout

    raise ParseError(f"{reader.path.name}: not a recognized indoor BLV file")


def parse_indoor_blv(path: Path) -> dict[str, object]:
    reader = ByteReader(path, path.read_bytes())
    layout = detect_blv_layout(reader)
    face_data_size_bytes = reader.read_i32(FACE_DATA_SIZE_OFFSET, "face data size")
    sector_data_size_bytes = reader.read_i32(SECTOR_R_DATA_SIZE_OFFSET, "sector data size")
    sector_light_data_size_bytes = reader.read_i32(SECTOR_RL_DATA_SIZE_OFFSET, "sector light data size")
    doors_data_size_bytes = reader.read_i32(DOORS_DATA_SIZE_OFFSET, "doors data size") if layout["version"] > 6 else 0

    offset = SECTION_OFFSET
    vertex_count = reader.read_i32(offset, "vertex count")
    offset += 4 + vertex_count * VERTEX_RECORD_SIZE

    face_count = reader.read_i32(offset, "face count")
    offset += 4
    face_headers_offset = offset
    offset += face_count * layout["face_record_size"]
    offset += face_data_size_bytes
    offset += face_count * TEXTURE_NAME_SIZE

    face_attributes: list[int] = []

    for face_index in range(face_count):
        header_offset = face_headers_offset + face_index * layout["face_record_size"]
        face_struct_offset = header_offset + 0x10 if layout["version"] > 6 else header_offset
        face_attributes.append(reader.read_u32(face_struct_offset + 0x1C, f"face {face_index} attributes"))

    face_param_count = reader.read_i32(offset, "face param count")
    offset += 4 + face_param_count * FACE_PARAM_RECORD_SIZE
    offset += face_param_count * FACE_PARAM_NAME_SIZE

    sector_count = reader.read_i32(offset, "sector count")
    offset += 4 + sector_count * layout["sector_record_size"]
    offset += sector_data_size_bytes
    offset += sector_light_data_size_bytes

    door_count = reader.read_i32(offset, "door count")
    offset += 4
    entity_count = reader.read_i32(offset, "entity count")

    return {
        "path": path,
        "version": layout["version"],
        "face_data_size_bytes": face_data_size_bytes,
        "sector_data_size_bytes": sector_data_size_bytes,
        "sector_light_data_size_bytes": sector_light_data_size_bytes,
        "doors_data_size_bytes": doors_data_size_bytes,
        "raw_face_count": face_count,
        "face_attributes": face_attributes,
        "vertex_count": vertex_count,
        "sector_count": sector_count,
        "door_count": door_count,
        "entity_count": entity_count,
    }


def parse_indoor_dlv(path: Path, blv_model: dict[str, object]) -> dict[str, object]:
    reader = ByteReader(path, path.read_bytes())
    location = parse_location_header(reader)

    def validate_optional_header_count(field_name: str, actual: int, expected: int) -> None:
        if actual == 0:
            return
        if actual != expected:
            raise ParseError(f"{path.name}: DLV {field_name} {actual} does not match expected {expected}")

    validate_optional_header_count("totalFacesCount", location["total_faces_count"], blv_model["raw_face_count"])
    validate_optional_header_count("decorationCount", location["decoration_count"], blv_model["entity_count"])
    validate_optional_header_count("bmodelCount", location["bmodel_count"], 0)

    offset = LOCATION_HEADER_SIZE
    visible_outlines = reader.read_bytes(offset, INDOOR_VISIBLE_OUTLINES_BYTES, "visible outlines")
    offset += INDOOR_VISIBLE_OUTLINES_BYTES
    face_attributes, offset = parse_u32_vector(reader, offset, blv_model["raw_face_count"], "face attribute override")
    decoration_flags, offset = parse_u16_vector(reader, offset, blv_model["entity_count"], "decoration flag")
    actors, offset = parse_actor_vector(reader, offset)
    sprite_objects, offset = parse_sprite_objects(reader, offset)
    chests, offset = parse_chests(reader, offset)
    doors, _doors_data, offset = parse_indoor_doors(
        reader,
        offset,
        blv_model["door_count"],
        blv_model["doors_data_size_bytes"]
    )
    variables, offset = parse_persistent_variables(reader, offset)
    location_time = parse_location_time_optional(reader, offset)

    return {
        "path": path,
        "location": location,
        "visible_outlines": visible_outlines,
        "face_attributes": face_attributes,
        "decoration_flags": decoration_flags,
        "actors": actors,
        "sprite_objects": sprite_objects,
        "chests": chests,
        "doors": doors,
        "variables": variables,
        "location_time": location_time,
    }


def build_scene_model(blv_model: dict[str, object], dlv_model: dict[str, object]) -> dict[str, object]:
    location_time = dlv_model["location_time"]
    face_attribute_overrides: list[dict[str, int]] = []

    for face_index, current_value in enumerate(dlv_model["face_attributes"]):
        if current_value == blv_model["face_attributes"][face_index]:
            continue
        face_attribute_overrides.append({
            "face_index": face_index,
            "legacy_attributes": current_value,
        })

    decoration_flags: list[dict[str, int]] = []

    for entity_index, flag in enumerate(dlv_model["decoration_flags"]):
        if flag == 0:
            continue
        decoration_flags.append({
            "entity_index": entity_index,
            "flag": flag,
        })

    return {
        "format_version": 1,
        "kind": "indoor_scene",
        "source": {
            "geometry_file": blv_model["path"].name,
            "legacy_companion_file": dlv_model["path"].name,
        },
        "environment": {
            "sky_texture": location_time["sky_texture_name"],
            "day_bits_raw": location_time["day_bits_raw"],
            "map_extra_bits_raw": location_time["map_extra_bits_raw"],
            "flags": {
                "foggy": (location_time["day_bits_raw"] & 0x01) != 0,
                "raining": (location_time["map_extra_bits_raw"] & 0x01) != 0,
                "snowing": (location_time["map_extra_bits_raw"] & 0x02) != 0,
                "underwater": (location_time["map_extra_bits_raw"] & 0x04) != 0,
                "no_terrain": (location_time["map_extra_bits_raw"] & 0x08) != 0,
                "always_dark": (location_time["map_extra_bits_raw"] & 0x10) != 0,
                "always_light": (location_time["map_extra_bits_raw"] & 0x20) != 0,
                "always_foggy": (location_time["map_extra_bits_raw"] & 0x40) != 0,
                "red_fog": (location_time["map_extra_bits_raw"] & 0x80) != 0,
            },
            "fog": {
                "weak_distance": location_time["fog_weak_distance"],
                "strong_distance": location_time["fog_strong_distance"],
            },
            "ceiling": location_time["ceiling"],
        },
        "initial_state": {
            "location": {
                "respawn_count": dlv_model["location"]["respawn_count"],
                "last_respawn_day": dlv_model["location"]["last_respawn_day"],
                "reputation": dlv_model["location"]["reputation"],
                "alert_status": dlv_model["location"]["alert_status"],
            },
            "visible_outlines": {
                "bitset_hex": bytes_to_hex(dlv_model["visible_outlines"]),
            },
            "face_attribute_overrides": face_attribute_overrides,
            "decoration_flags": decoration_flags,
            "actors": dlv_model["actors"],
            "sprite_objects": dlv_model["sprite_objects"],
            "chests": dlv_model["chests"],
            "doors": dlv_model["doors"],
            "variables": dlv_model["variables"],
        },
    }


def render_scene_yaml(scene_model: dict[str, object]) -> str:
    lines: list[str] = []
    write_yaml_scalar(lines, "", "format_version", scene_model["format_version"])
    write_yaml_scalar(lines, "", "kind", scene_model["kind"])
    lines.append("source:")
    write_yaml_scalar(lines, "  ", "geometry_file", scene_model["source"]["geometry_file"])
    write_yaml_scalar(lines, "  ", "legacy_companion_file", scene_model["source"]["legacy_companion_file"])

    environment = scene_model["environment"]
    lines.append("environment:")
    write_yaml_scalar(lines, "  ", "sky_texture", environment["sky_texture"])
    write_yaml_scalar(lines, "  ", "day_bits_raw", environment["day_bits_raw"])
    write_yaml_scalar(lines, "  ", "map_extra_bits_raw", environment["map_extra_bits_raw"])
    lines.append("  flags:")

    for key in (
        "foggy",
        "raining",
        "snowing",
        "underwater",
        "no_terrain",
        "always_dark",
        "always_light",
        "always_foggy",
        "red_fog",
    ):
        write_yaml_scalar(lines, "    ", key, environment["flags"][key])

    lines.append("  fog:")
    write_yaml_scalar(lines, "    ", "weak_distance", environment["fog"]["weak_distance"])
    write_yaml_scalar(lines, "    ", "strong_distance", environment["fog"]["strong_distance"])
    write_yaml_scalar(lines, "  ", "ceiling", environment["ceiling"])

    initial_state = scene_model["initial_state"]
    lines.append("initial_state:")
    lines.append("  location:")
    write_yaml_scalar(lines, "    ", "respawn_count", initial_state["location"]["respawn_count"])
    write_yaml_scalar(lines, "    ", "last_respawn_day", initial_state["location"]["last_respawn_day"])
    write_yaml_scalar(lines, "    ", "reputation", initial_state["location"]["reputation"])
    write_yaml_scalar(lines, "    ", "alert_status", initial_state["location"]["alert_status"])
    lines.append("  visible_outlines:")
    write_yaml_scalar(lines, "    ", "bitset_hex", initial_state["visible_outlines"]["bitset_hex"])

    face_attribute_overrides = initial_state["face_attribute_overrides"]
    if not face_attribute_overrides:
        lines.append("  face_attribute_overrides: []")
    else:
        lines.append("  face_attribute_overrides:")
        for entry in face_attribute_overrides:
            lines.append(f"    - face_index: {entry['face_index']}")
            lines.append(f"      legacy_attributes: {entry['legacy_attributes']}")

    decoration_flags = initial_state["decoration_flags"]
    if not decoration_flags:
        lines.append("  decoration_flags: []")
    else:
        lines.append("  decoration_flags:")
        for entry in decoration_flags:
            lines.append(f"    - entity_index: {entry['entity_index']}")
            lines.append(f"      flag: {entry['flag']}")

    actors = initial_state["actors"]
    if not actors:
        lines.append("  actors: []")
    else:
        lines.append("  actors:")
        for actor in actors:
            lines.append(f"    - actor_index: {actor['actor_index']}")
            write_yaml_scalar(lines, "      ", "name", actor["name"])
            lines.append(f"      npc_id: {actor['npc_id']}")
            lines.append(f"      attributes: {actor['attributes']}")
            lines.append(f"      hp: {actor['hp']}")
            lines.append(f"      hostility_type: {actor['hostility_type']}")
            lines.append(f"      monster_info_id: {actor['monster_info_id']}")
            lines.append(f"      monster_id: {actor['monster_id']}")
            lines.append(f"      radius: {actor['radius']}")
            lines.append(f"      height: {actor['height']}")
            lines.append(f"      move_speed: {actor['move_speed']}")
            append_position_block(lines, "      ", "position", actor["position"])
            append_int_list(lines, "      ", "sprite_ids", actor["sprite_ids"])
            lines.append(f"      sector_id: {actor['sector_id']}")
            lines.append(f"      current_action_animation: {actor['current_action_animation']}")
            lines.append(f"      carried_item_id: {actor['carried_item_id']}")
            lines.append(f"      group: {actor['group']}")
            lines.append(f"      ally: {actor['ally']}")
            lines.append(f"      unique_name_index: {actor['unique_name_index']}")

    sprite_objects = initial_state["sprite_objects"]
    if not sprite_objects:
        lines.append("  sprite_objects: []")
    else:
        lines.append("  sprite_objects:")
        for sprite_object in sprite_objects:
            lines.append(f"    - sprite_object_index: {sprite_object['sprite_object_index']}")
            lines.append(f"      sprite_id: {sprite_object['sprite_id']}")
            lines.append(f"      object_description_id: {sprite_object['object_description_id']}")
            append_position_block(lines, "      ", "position", sprite_object["position"])
            append_position_block(lines, "      ", "velocity", sprite_object["velocity"])
            lines.append(f"      yaw_angle: {sprite_object['yaw_angle']}")
            lines.append(f"      sound_id: {sprite_object['sound_id']}")
            lines.append(f"      attributes: {sprite_object['attributes']}")
            lines.append(f"      sector_id: {sprite_object['sector_id']}")
            lines.append(f"      time_since_created: {sprite_object['time_since_created']}")
            lines.append(f"      temporary_lifetime: {sprite_object['temporary_lifetime']}")
            lines.append(f"      glow_radius_multiplier: {sprite_object['glow_radius_multiplier']}")
            lines.append(f"      spell_id: {sprite_object['spell_id']}")
            lines.append(f"      spell_level: {sprite_object['spell_level']}")
            lines.append(f"      spell_skill: {sprite_object['spell_skill']}")
            lines.append(f"      field54: {sprite_object['field54']}")
            lines.append(f"      spell_caster_pid: {sprite_object['spell_caster_pid']}")
            lines.append(f"      spell_target_pid: {sprite_object['spell_target_pid']}")
            lines.append(f"      lod_distance: {sprite_object['lod_distance']}")
            lines.append(f"      spell_caster_ability: {sprite_object['spell_caster_ability']}")
            append_position_block(lines, "      ", "initial_position", sprite_object["initial_position"])
            write_yaml_scalar(lines, "      ", "raw_containing_item_hex", sprite_object["raw_containing_item_hex"])

    chests = initial_state["chests"]
    if not chests:
        lines.append("  chests: []")
    else:
        lines.append("  chests:")
        for chest in chests:
            lines.append(f"    - chest_index: {chest['chest_index']}")
            lines.append(f"      chest_type_id: {chest['chest_type_id']}")
            lines.append(f"      flags: {chest['flags']}")
            write_yaml_scalar(lines, "      ", "raw_items_hex", chest["raw_items_hex"])
            append_int_list(lines, "      ", "inventory_matrix", chest["inventory_matrix"])

    doors = initial_state["doors"]
    if not doors:
        lines.append("  doors: []")
    else:
        lines.append("  doors:")
        for door in doors:
            lines.append(f"    - door_index: {door['door_index']}")
            lines.append(f"      legacy_attributes: {door['legacy_attributes']}")
            lines.append(f"      door_id: {door['door_id']}")
            lines.append(f"      time_since_triggered_ms: {door['time_since_triggered_ms']}")
            append_position_block(lines, "      ", "direction", door["direction"])
            lines.append(f"      move_length: {door['move_length']}")
            lines.append(f"      open_speed: {door['open_speed']}")
            lines.append(f"      close_speed: {door['close_speed']}")
            lines.append(f"      state: {door['state']}")
            append_int_list(lines, "      ", "vertex_ids", door["vertex_ids"])
            append_int_list(lines, "      ", "face_ids", door["face_ids"])
            append_int_list(lines, "      ", "sector_ids", door["sector_ids"])
            append_int_list(lines, "      ", "delta_us", door["delta_us"])
            append_int_list(lines, "      ", "delta_vs", door["delta_vs"])
            append_int_list(lines, "      ", "x_offsets", door["x_offsets"])
            append_int_list(lines, "      ", "y_offsets", door["y_offsets"])
            append_int_list(lines, "      ", "z_offsets", door["z_offsets"])

    lines.append("  variables:")
    append_int_list(lines, "    ", "map", initial_state["variables"]["map"])
    append_int_list(lines, "    ", "decor", initial_state["variables"]["decor"])
    return "\n".join(lines) + "\n"


def resolve_dlv_path(
    blv_path: Path,
    explicit_dlv_path: Path | None,
    explicit_dlv_dir: Path | None,
) -> Path:
    if explicit_dlv_path is not None:
        return explicit_dlv_path
    if explicit_dlv_dir is not None:
        return explicit_dlv_dir / f"{blv_path.stem}.dlv"
    return blv_path.with_suffix(".dlv")


def derive_paths(args: argparse.Namespace, repo_root: Path) -> tuple[Path, Path, Path]:
    explicit_dlv_path = Path(args.dlv) if args.dlv else None
    explicit_dlv_dir = Path(args.dlv_dir) if args.dlv_dir else None

    if args.blv:
        blv_path = Path(args.blv)
        dlv_path = resolve_dlv_path(blv_path, explicit_dlv_path, explicit_dlv_dir)
        output_path = Path(args.output) if args.output else blv_path.with_suffix(".scene.yml")
        return blv_path, dlv_path, output_path

    if args.map_base:
        map_base = Path(args.map_base)
        output_path = Path(args.output) if args.output else map_base.with_suffix(".scene.yml")
        blv_path = map_base.with_suffix(".blv")
        dlv_path = resolve_dlv_path(blv_path, explicit_dlv_path, explicit_dlv_dir)
        return blv_path, dlv_path, output_path

    input_dir = Path(args.input_dir) if args.input_dir else repo_root / "assets_dev" / "Data" / "games"
    map_name = args.map

    if map_name is None:
        raise ParseError("either --blv, --map-base, or --map must be provided")

    output_path = Path(args.output) if args.output else input_dir / f"{map_name}.scene.yml"
    blv_path = input_dir / f"{map_name}.blv"
    dlv_path = resolve_dlv_path(blv_path, explicit_dlv_path, explicit_dlv_dir)
    return blv_path, dlv_path, output_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export indoor BLV + DLV into .scene.yml")
    parser.add_argument("--blv", help="path to XX.blv")
    parser.add_argument("--dlv", help="path to XX.dlv; overrides sibling companion lookup")
    parser.add_argument("--dlv-dir", help="directory containing XX.dlv companions keyed by map stem")
    parser.add_argument("--output", help="path to XX.scene.yml; defaults next to --blv")
    parser.add_argument("--map-base", help="path without extension, e.g. assets_dev/Data/games/d01")
    parser.add_argument("--input-dir", help="directory containing map files for --map mode")
    parser.add_argument("--map", help="map basename for --input-dir mode, e.g. d01")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    try:
        blv_path, dlv_path, output_path = derive_paths(args, repo_root)

        if not blv_path.is_file():
            raise ParseError(f"missing BLV file: {blv_path}")
        if not dlv_path.is_file():
            raise ParseError(f"missing DLV file: {dlv_path}")

        blv_model = parse_indoor_blv(blv_path)
        dlv_model = parse_indoor_dlv(dlv_path, blv_model)
        scene_model = build_scene_model(blv_model, dlv_model)
        output_text = render_scene_yaml(scene_model)
        write_atomic_text(output_path, output_text)
    except ParseError as error:
        parser.exit(1, f"{error}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
