#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
from pathlib import Path


SECTION_OFFSET = 0x88
FACE_DATA_SIZE_OFFSET = 0x68
SECTOR_RDATA_SIZE_OFFSET = 0x6C
SECTOR_RL_DATA_SIZE_OFFSET = 0x70
TEXTURE_NAME_SIZE = 10
FACE_PARAM_RECORD_SIZE = 0x24
FACE_PARAM_NAME_SIZE = 0x0A
OUTLINE_RECORD_SIZE = 0x0C
UNKNOWN9_RECORD_SIZE = 0x08
VERTEX_RECORD_SIZE = 0x06
SPRITE_NAME_SIZE = 0x20
INDOOR_VISIBLE_OUTLINES_BYTES = 875
DOOR_RECORD_SIZE = 0x50

VERSION_OFFSET = 0x40
VERSION_FIELD_SIZE = 16
MASTER_TILE_OFFSET = 0x5F
TILE_SET_LOOKUP_OFFSET = 0xA0
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
VERSION6_SPAWN_SIZE = 0x14
VERSION7_SPAWN_SIZE = 0x18

LOCATION_HEADER_SIZE = 40
ACTOR_RECORD_SIZE = 0x3CC
SPRITE_OBJECT_RECORD_SIZE = 0x70
CHEST_RECORD_SIZE = 5324
PERSISTENT_VARIABLES_SIZE = 0xC8
LOCATION_TIME_SIZE = 0x38
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
        self.require(offset, 1)
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

    def f32(self, offset: int) -> float:
        return struct.unpack_from("<f", self._data, offset)[0]

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


def advance_offset(offset: int, byte_count: int, total_size: int) -> int:
    if byte_count < 0 or byte_count > total_size - offset:
        raise ValueError(f"advance out of bounds: offset={offset} byte_count={byte_count} total={total_size}")
    return offset + byte_count


def make_document(format_name: str, input_path: Path, data: bytes, payload: dict) -> dict:
    return {
        "format": format_name,
        "input_path": str(input_path),
        "input_size": len(data),
        "payload": payload,
    }


def ticks_to_realtime_milliseconds(ticks: int) -> int:
    return ticks * 1000 // TICKS_PER_REALTIME_SECOND


def detect_outdoor_odm_version(reader: ByteReader) -> int | None:
    version_field = reader.bytes(VERSION_OFFSET, VERSION_FIELD_SIZE)
    if version_field.startswith(VERSION6_TAG):
        return 6
    if version_field.startswith(VERSION7_TAG):
        return 7
    if version_field == b"\0" * VERSION_FIELD_SIZE:
        return 8
    return None


def read_texture_name(reader: ByteReader, offset: int) -> str:
    return reader.fixed_string(offset, TEXTURE_NAME_SIZE)


def detect_indoor_layout(reader: ByteReader) -> dict:
    layouts = [
        {"version": 6, "face_record_size": 0x50, "sector_record_size": 0x74, "sprite_record_size": 0x1C,
         "light_record_size": 0x0C, "spawn_record_size": 0x14},
        {"version": 7, "face_record_size": 0x60, "sector_record_size": 0x74, "sprite_record_size": 0x20,
         "light_record_size": 0x10, "spawn_record_size": 0x18},
        {"version": 8, "face_record_size": 0x60, "sector_record_size": 0x78, "sprite_record_size": 0x20,
         "light_record_size": 0x14, "spawn_record_size": 0x18},
    ]

    for layout in layouts:
        try:
            cursor = SECTION_OFFSET
            vertex_count = reader.i32(cursor)
            if vertex_count < 0:
                continue
            cursor += 4 + vertex_count * VERTEX_RECORD_SIZE

            face_count = reader.i32(cursor)
            if face_count < 0:
                continue
            cursor += 4 + face_count * layout["face_record_size"]

            face_data_size = reader.i32(FACE_DATA_SIZE_OFFSET)
            sector_data_size = reader.i32(SECTOR_RDATA_SIZE_OFFSET)
            sector_light_data_size = reader.i32(SECTOR_RL_DATA_SIZE_OFFSET)
            if face_data_size < 0 or sector_data_size < 0 or sector_light_data_size < 0:
                continue

            cursor += face_data_size
            cursor += face_count * TEXTURE_NAME_SIZE

            face_param_count = reader.i32(cursor)
            if face_param_count < 0:
                continue
            cursor += 4 + face_param_count * FACE_PARAM_RECORD_SIZE + face_param_count * FACE_PARAM_NAME_SIZE

            sector_count = reader.i32(cursor)
            if sector_count < 0:
                continue
            cursor += 4 + sector_count * layout["sector_record_size"]
            cursor += sector_data_size + sector_light_data_size

            door_count = reader.i32(cursor)
            sprite_count = reader.i32(cursor + 4)
            if door_count < 0 or sprite_count < 0:
                continue
            cursor += 8 + sprite_count * layout["sprite_record_size"] + sprite_count * SPRITE_NAME_SIZE

            light_count = reader.i32(cursor)
            if light_count < 0:
                continue
            cursor += 4 + light_count * layout["light_record_size"]

            bsp_node_count = reader.i32(cursor)
            if bsp_node_count < 0:
                continue
            cursor += 4 + bsp_node_count * UNKNOWN9_RECORD_SIZE

            spawn_count = reader.i32(cursor)
            if spawn_count < 0:
                continue
            cursor += 4 + spawn_count * layout["spawn_record_size"]

            outline_count = reader.i32(cursor)
            if outline_count < 0:
                continue
            cursor += 4 + outline_count * OUTLINE_RECORD_SIZE

            if cursor == reader.size:
                return layout
        except Exception:
            continue

    raise ValueError("unable to detect indoor map layout")


def parse_odm_file(input_path: Path) -> dict:
    data = input_path.read_bytes()
    reader = ByteReader(data)
    version = detect_outdoor_odm_version(reader)
    if version is None:
        raise ValueError("unsupported outdoor map version")

    payload: dict = {
        "version": version,
        "name": reader.fixed_string(0x00, 32),
        "file_name": reader.fixed_string(0x20, 32),
        "description": reader.fixed_string(0x40, 32),
        "sky_texture": reader.fixed_string(0x60, 32),
        "ground_tileset_name": reader.fixed_string(0x80, 32),
        "master_tile": reader.u8(MASTER_TILE_OFFSET),
    }

    tile_set_lookup_indices = []
    for lookup_index in range(4):
        raw = reader.i32(TILE_SET_LOOKUP_OFFSET + lookup_index * 4)
        tile_set_lookup_indices.append((raw >> 16) & 0xFFFF)
    payload["tile_set_lookup_indices"] = tile_set_lookup_indices

    cursor = TERRAIN_SECTION_OFFSET_V8 if version == 8 else TERRAIN_SECTION_OFFSET
    payload["height_map"] = list(reader.bytes(cursor, TERRAIN_MAP_SIZE))
    cursor += TERRAIN_MAP_SIZE
    payload["tile_map"] = list(reader.bytes(cursor, TERRAIN_MAP_SIZE))
    cursor += TERRAIN_MAP_SIZE
    payload["attribute_map"] = list(reader.bytes(cursor, TERRAIN_MAP_SIZE))
    cursor += TERRAIN_MAP_SIZE

    terrain_normal_count = 0
    if version > 6:
        terrain_normal_count = reader.i32(cursor)
        cursor += 4
        payload["terrain_normal_count"] = terrain_normal_count
        payload["some_other_map"] = reader.u32_array(cursor, CMAP1_SIZE // 4)
        cursor += CMAP1_SIZE
        payload["normal_map"] = reader.u16_array(cursor, CMAP2_SIZE // 2)
        cursor += CMAP2_SIZE
        normals = []
        for normal_index in range(terrain_normal_count * 3):
            normals.append(reader.f32(cursor + normal_index * 4))
        payload["normals"] = normals
        cursor += terrain_normal_count * 12
    else:
        payload["terrain_normal_count"] = 0
        payload["some_other_map"] = []
        payload["normal_map"] = []
        payload["normals"] = []

    bmodel_count = reader.i32(cursor)
    cursor += 4
    payload["bmodel_count"] = bmodel_count
    bmodel_headers_offset = cursor
    cursor += bmodel_count * BMODEL_HEADER_SIZE

    bmodels = []
    total_faces_count = 0

    for index in range(bmodel_count):
        header_offset = bmodel_headers_offset + index * BMODEL_HEADER_SIZE
        vertex_count = reader.i32(header_offset + 0x44)
        face_count = reader.i32(header_offset + 0x4C)
        bsp_node_count = reader.i32(header_offset + 0x5C)
        total_faces_count += max(face_count, 0)

        vertices = []
        for vertex_index in range(vertex_count):
            vertex_offset = cursor + vertex_index * BMODEL_VERTEX_SIZE
            vertices.append(
                {
                    "x": reader.i32(vertex_offset + 0),
                    "y": reader.i32(vertex_offset + 4),
                    "z": reader.i32(vertex_offset + 8),
                }
            )
        cursor += vertex_count * BMODEL_VERTEX_SIZE

        faces_offset = cursor
        face_flags_offset = faces_offset + face_count * BMODEL_FACE_SIZE
        face_texture_names_offset = face_flags_offset + face_count * BMODEL_FACE_FLAGS_SIZE
        faces = []

        for face_index in range(face_count):
            face_offset = faces_offset + face_index * BMODEL_FACE_SIZE
            num_vertices = reader.u8(face_offset + 0x12E)
            vertex_indices = []
            texture_us = []
            texture_vs = []

            for local_index in range(num_vertices):
                vertex_indices.append(reader.u16(face_offset + 0x20 + local_index * 2))
                texture_us.append(reader.i16(face_offset + 0x48 + local_index * 2))
                texture_vs.append(reader.i16(face_offset + 0x70 + local_index * 2))

            faces.append(
                {
                    "index": face_index,
                    "attributes": reader.u32(face_offset + 0x1C),
                    "vertex_count": num_vertices,
                    "vertex_indices": vertex_indices,
                    "texture_us": texture_us,
                    "texture_vs": texture_vs,
                    "bitmap_index": reader.i16(face_offset + 0x110),
                    "texture_delta_u": reader.i16(face_offset + 0x112),
                    "texture_delta_v": reader.i16(face_offset + 0x114),
                    "cog_number": reader.u16(face_offset + 0x122),
                    "cog_triggered_number": reader.u16(face_offset + 0x124),
                    "cog_trigger": reader.u16(face_offset + 0x126),
                    "reserved": reader.u16(face_offset + 0x128),
                    "polygon_type": reader.u8(face_offset + 0x12F),
                    "shade": reader.u8(face_offset + 0x130),
                    "visibility": reader.u8(face_offset + 0x131),
                    "flags_raw": reader.u16(face_flags_offset + face_index * 2),
                    "texture_name": reader.fixed_string(
                        face_texture_names_offset + face_index * BMODEL_TEXTURE_NAME_SIZE,
                        BMODEL_TEXTURE_NAME_SIZE,
                    ),
                    "raw_record_base64": to_base64(reader.bytes(face_offset, BMODEL_FACE_SIZE)),
                }
            )

        cursor += face_count * BMODEL_FACE_SIZE
        face_flags = reader.u16_array(cursor, face_count)
        cursor += face_count * BMODEL_FACE_FLAGS_SIZE
        cursor += face_count * BMODEL_TEXTURE_NAME_SIZE

        bsp_nodes = []
        for node_index in range(bsp_node_count):
            node_offset = cursor + node_index * BMODEL_BSP_NODE_SIZE
            bsp_nodes.append(
                {
                    "front": reader.i16(node_offset + 0),
                    "back": reader.i16(node_offset + 2),
                    "face_id_offset": reader.i16(node_offset + 4),
                    "face_count": reader.i16(node_offset + 6),
                }
            )
        cursor += bsp_node_count * BMODEL_BSP_NODE_SIZE

        bmodels.append(
            {
                "index": index,
                "name": reader.fixed_string(header_offset + 0x00, 0x20),
                "secondary_name": reader.fixed_string(header_offset + 0x20, 0x20),
                "vertex_count": vertex_count,
                "face_count": face_count,
                "bsp_node_count": bsp_node_count,
                "position": {
                    "x": reader.i32(header_offset + 0x68),
                    "y": reader.i32(header_offset + 0x6C),
                    "z": reader.i32(header_offset + 0x70),
                },
                "bounds_min": {
                    "x": reader.i32(header_offset + 0x74),
                    "y": reader.i32(header_offset + 0x78),
                    "z": reader.i32(header_offset + 0x7C),
                },
                "bounds_max": {
                    "x": reader.i32(header_offset + 0x80),
                    "y": reader.i32(header_offset + 0x84),
                    "z": reader.i32(header_offset + 0x88),
                },
                "bounding_center": {
                    "x": reader.i32(header_offset + 0xA8),
                    "y": reader.i32(header_offset + 0xAC),
                    "z": reader.i32(header_offset + 0xB0),
                },
                "bounding_radius": reader.i32(header_offset + 0xB4),
                "vertices": vertices,
                "faces": faces,
                "face_flags": face_flags,
                "bsp_nodes": bsp_nodes,
                "raw_header_base64": to_base64(reader.bytes(header_offset, BMODEL_HEADER_SIZE)),
            }
        )

    payload["bmodels"] = bmodels
    payload["total_faces_count"] = total_faces_count

    entity_count = reader.i32(cursor)
    cursor += 4
    payload["entity_count"] = entity_count
    entity_size = VERSION6_ENTITY_SIZE if version == 6 else VERSION7_ENTITY_SIZE
    entity_data_offset = cursor
    cursor += entity_count * entity_size
    entity_names_offset = cursor
    cursor += entity_count * ENTITY_NAME_SIZE

    entities = []
    for entity_index in range(entity_count):
        entity_offset = entity_data_offset + entity_index * entity_size
        entities.append(
            {
                "index": entity_index,
                "decoration_list_id": reader.u16(entity_offset + 0x00),
                "ai_attributes": reader.u16(entity_offset + 0x02),
                "position": {
                    "x": reader.i32(entity_offset + 0x04),
                    "y": reader.i32(entity_offset + 0x08),
                    "z": reader.i32(entity_offset + 0x0C),
                },
                "facing": reader.i32(entity_offset + 0x10),
                "event_id_primary": reader.u16(entity_offset + 0x14),
                "event_id_secondary": reader.u16(entity_offset + 0x16),
                "variable_primary": reader.u16(entity_offset + 0x18),
                "variable_secondary": reader.u16(entity_offset + 0x1A),
                "special_trigger": reader.u16(entity_offset + 0x1C) if version > 6 else 0,
                "name": reader.fixed_string(entity_names_offset + entity_index * ENTITY_NAME_SIZE, ENTITY_NAME_SIZE),
                "raw_record_base64": to_base64(reader.bytes(entity_offset, entity_size)),
            }
        )
    payload["entities"] = entities

    id_list_count = reader.i32(cursor)
    cursor += 4
    payload["id_list_count"] = id_list_count
    payload["decoration_pid_list"] = reader.u16_array(cursor, id_list_count)
    cursor += id_list_count * 2
    payload["decoration_map"] = reader.u32_array(cursor, TERRAIN_MAP_SIZE)
    cursor += TERRAIN_MAP_SIZE * 4

    spawn_count = reader.i32(cursor)
    cursor += 4
    payload["spawn_count"] = spawn_count
    spawn_size = VERSION6_SPAWN_SIZE if version == 6 else VERSION7_SPAWN_SIZE
    spawns = []

    for spawn_index in range(spawn_count):
        spawn_offset = cursor + spawn_index * spawn_size
        spawns.append(
            {
                "index": spawn_index,
                "position": {
                    "x": reader.i32(spawn_offset + 0x00),
                    "y": reader.i32(spawn_offset + 0x04),
                    "z": reader.i32(spawn_offset + 0x08),
                },
                "radius": reader.u16(spawn_offset + 0x0C),
                "type_id": reader.u16(spawn_offset + 0x0E),
                "spawn_index": reader.u16(spawn_offset + 0x10),
                "attributes": reader.u16(spawn_offset + 0x12),
                "group": reader.u32(spawn_offset + 0x14) if version > 6 else 0,
                "raw_record_base64": to_base64(reader.bytes(spawn_offset, spawn_size)),
            }
        )
    cursor += spawn_count * spawn_size
    payload["spawns"] = spawns
    payload["trailing_bytes_base64"] = to_base64(reader.bytes(cursor, reader.size - cursor)) if cursor < reader.size else ""

    return make_document("odm", input_path, data, payload)


def parse_blv_file(input_path: Path) -> dict:
    data = input_path.read_bytes()
    reader = ByteReader(data)
    layout = detect_indoor_layout(reader)

    payload: dict = {
        "version": layout["version"],
        "face_data_size_bytes": reader.i32(FACE_DATA_SIZE_OFFSET),
        "sector_data_size_bytes": reader.i32(SECTOR_RDATA_SIZE_OFFSET),
        "sector_light_data_size_bytes": reader.i32(SECTOR_RL_DATA_SIZE_OFFSET),
        "doors_data_size_bytes": reader.i32(0x74) if layout["version"] > 6 else 0,
    }

    cursor = SECTION_OFFSET
    vertex_count = reader.i32(cursor)
    cursor += 4
    vertices = []
    for vertex_index in range(vertex_count):
        vertex_offset = cursor + vertex_index * VERTEX_RECORD_SIZE
        vertices.append(
            {
                "x": reader.i16(vertex_offset + 0),
                "y": reader.i16(vertex_offset + 2),
                "z": reader.i16(vertex_offset + 4),
            }
        )
    cursor += vertex_count * VERTEX_RECORD_SIZE
    payload["vertices"] = vertices

    face_count = reader.i32(cursor)
    payload["raw_face_count"] = face_count
    cursor += 4
    face_headers_offset = cursor
    cursor += face_count * layout["face_record_size"]

    face_data_size = payload["face_data_size_bytes"]
    face_data_offset = cursor
    cursor += face_data_size

    face_texture_names_offset = cursor
    cursor += face_count * TEXTURE_NAME_SIZE

    face_param_count = reader.i32(cursor)
    cursor += 4
    face_params_offset = cursor
    face_param_names_offset = face_params_offset + face_param_count * FACE_PARAM_RECORD_SIZE
    cursor += face_param_count * FACE_PARAM_RECORD_SIZE
    cursor += face_param_count * FACE_PARAM_NAME_SIZE

    face_params = []
    for face_param_index in range(face_param_count):
        param_offset = face_params_offset + face_param_index * FACE_PARAM_RECORD_SIZE
        face_params.append(
            {
                "index": face_param_index,
                "texture_frame_table_index": reader.u16(param_offset + 0x10),
                "texture_frame_table_cog": reader.u16(param_offset + 0x12),
                "texture_delta_u": reader.i16(param_offset + 0x14),
                "texture_delta_v": reader.i16(param_offset + 0x16),
                "cog_number": reader.u16(param_offset + 0x18),
                "cog_triggered": reader.u16(param_offset + 0x1A),
                "cog_trigger_type": reader.u16(param_offset + 0x1C),
                "light_level": reader.u16(param_offset + 0x22),
                "name": reader.fixed_string(face_param_names_offset + face_param_index * FACE_PARAM_NAME_SIZE, FACE_PARAM_NAME_SIZE),
                "raw_record_base64": to_base64(reader.bytes(param_offset, FACE_PARAM_RECORD_SIZE)),
            }
        )

    face_data_cursor = face_data_offset
    faces = []
    for face_index in range(face_count):
        header_offset = face_headers_offset + face_index * layout["face_record_size"]
        face_struct_offset = header_offset + 0x10 if layout["version"] > 6 else header_offset
        vertex_per_face_count = reader.u8(face_struct_offset + 0x4D)
        stream_stride = (vertex_per_face_count + 1) * 2
        raw_stream_size = stream_stride * 6
        raw_stream = reader.bytes(face_data_cursor, raw_stream_size) if raw_stream_size > 0 else b""

        vertex_stream = []
        stream1 = []
        stream2 = []
        stream3 = []
        texture_us = []
        texture_vs = []
        if vertex_per_face_count > 0:
            vertex_stream = reader.i16_array(face_data_cursor + stream_stride * 0, vertex_per_face_count + 1)
            stream1 = reader.i16_array(face_data_cursor + stream_stride * 1, vertex_per_face_count + 1)
            stream2 = reader.i16_array(face_data_cursor + stream_stride * 2, vertex_per_face_count + 1)
            stream3 = reader.i16_array(face_data_cursor + stream_stride * 3, vertex_per_face_count + 1)
            texture_us = reader.i16_array(face_data_cursor + stream_stride * 4, vertex_per_face_count + 1)
            texture_vs = reader.i16_array(face_data_cursor + stream_stride * 5, vertex_per_face_count + 1)

        face_param_index = reader.u16(face_struct_offset + 0x38)
        faces.append(
            {
                "index": face_index,
                "attributes": reader.u32(face_struct_offset + 0x1C),
                "face_param_index": face_param_index,
                "room_number": reader.u16(face_struct_offset + 0x3C),
                "room_behind_number": reader.u16(face_struct_offset + 0x3E),
                "facet_type": reader.u8(face_struct_offset + 0x4C),
                "vertex_per_face_count": vertex_per_face_count,
                "is_portal": (reader.u32(face_struct_offset + 0x1C) & 0x1) != 0,
                "texture_name": read_texture_name(reader, face_texture_names_offset + face_index * TEXTURE_NAME_SIZE),
                "vertex_indices": vertex_stream[:vertex_per_face_count],
                "texture_us": texture_us[:vertex_per_face_count],
                "texture_vs": texture_vs[:vertex_per_face_count],
                "vertex_stream_raw": vertex_stream,
                "stream1_raw": stream1,
                "stream2_raw": stream2,
                "stream3_raw": stream3,
                "face_param": face_params[face_param_index] if face_param_index < len(face_params) else None,
                "raw_header_base64": to_base64(reader.bytes(header_offset, layout["face_record_size"])),
                "raw_stream_base64": to_base64(raw_stream),
            }
        )
        face_data_cursor += raw_stream_size

    payload["face_params"] = face_params
    payload["faces"] = faces

    sector_count = reader.i32(cursor)
    cursor += 4
    payload["sector_count"] = sector_count
    sectors = []
    for sector_index in range(sector_count):
        sector_offset = cursor + sector_index * layout["sector_record_size"]
        sectors.append(
            {
                "index": sector_index,
                "flags": reader.i32(sector_offset + 0x00),
                "floor_count": reader.u16(sector_offset + 0x04),
                "wall_count": reader.u16(sector_offset + 0x0C),
                "ceiling_count": reader.u16(sector_offset + 0x14),
                "portal_count": reader.i16(sector_offset + 0x24),
                "face_count": reader.u16(sector_offset + 0x2C),
                "non_bsp_face_count": reader.u16(sector_offset + 0x2E),
                "decoration_count": reader.u16(sector_offset + 0x44),
                "light_count": reader.u16(sector_offset + 0x54),
                "water_level": reader.i16(sector_offset + 0x5C),
                "mist_level": reader.i16(sector_offset + 0x5E),
                "light_distance_multiplier": reader.i16(sector_offset + 0x60),
                "min_ambient_light_level": reader.i16(sector_offset + 0x62),
                "first_bsp_node": reader.i16(sector_offset + 0x64),
                "raw_record_base64": to_base64(reader.bytes(sector_offset, layout["sector_record_size"])),
            }
        )
    cursor += sector_count * layout["sector_record_size"]
    payload["sectors"] = sectors

    sector_data_size = payload["sector_data_size_bytes"]
    sector_light_data_size = payload["sector_light_data_size_bytes"]
    payload["sector_data"] = reader.u16_array(cursor, sector_data_size // 2)
    cursor += sector_data_size
    payload["sector_light_data"] = reader.u16_array(cursor, sector_light_data_size // 2)
    cursor += sector_light_data_size

    door_count = reader.i32(cursor)
    cursor += 4
    payload["door_count"] = door_count

    sprite_count = reader.i32(cursor)
    cursor += 4
    payload["sprite_count"] = sprite_count
    sprite_data_offset = cursor
    cursor += sprite_count * layout["sprite_record_size"]
    sprite_names_offset = cursor
    cursor += sprite_count * SPRITE_NAME_SIZE

    entities = []
    for sprite_index in range(sprite_count):
        sprite_offset = sprite_data_offset + sprite_index * layout["sprite_record_size"]
        entities.append(
            {
                "index": sprite_index,
                "decoration_list_id": reader.u16(sprite_offset + 0x00),
                "ai_attributes": reader.u16(sprite_offset + 0x02),
                "position": {
                    "x": reader.i32(sprite_offset + 0x04),
                    "y": reader.i32(sprite_offset + 0x08),
                    "z": reader.i32(sprite_offset + 0x0C),
                },
                "facing": reader.i32(sprite_offset + 0x10),
                "event_id_primary": reader.u16(sprite_offset + 0x14),
                "event_id_secondary": reader.u16(sprite_offset + 0x16),
                "variable_primary": reader.u16(sprite_offset + 0x18),
                "variable_secondary": reader.u16(sprite_offset + 0x1A),
                "special_trigger": reader.u16(sprite_offset + 0x1C) if layout["version"] > 6 else 0,
                "name": reader.fixed_string(sprite_names_offset + sprite_index * SPRITE_NAME_SIZE, SPRITE_NAME_SIZE),
                "raw_record_base64": to_base64(reader.bytes(sprite_offset, layout["sprite_record_size"])),
            }
        )
    payload["entities"] = entities

    light_count = reader.i32(cursor)
    cursor += 4
    payload["light_count"] = light_count
    lights = []
    for light_index in range(light_count):
        light_offset = cursor + light_index * layout["light_record_size"]
        light = {
            "index": light_index,
            "x": reader.i16(light_offset + 0x00),
            "y": reader.i16(light_offset + 0x02),
            "z": reader.i16(light_offset + 0x04),
            "radius": reader.i16(light_offset + 0x06),
            "red": reader.u8(light_offset + 0x08),
            "green": reader.u8(light_offset + 0x09),
            "blue": reader.u8(light_offset + 0x0A),
            "type": reader.u8(light_offset + 0x0B),
            "attributes": reader.i16(light_offset + 0x0C) if layout["version"] > 6 else 0,
            "brightness": reader.i16(light_offset + 0x0E) if layout["version"] > 6 else reader.u16(light_offset + 0x0A),
            "raw_record_base64": to_base64(reader.bytes(light_offset, layout["light_record_size"])),
        }
        lights.append(light)
    cursor += light_count * layout["light_record_size"]
    payload["lights"] = lights

    bsp_node_count = reader.i32(cursor)
    cursor += 4
    payload["bsp_node_count"] = bsp_node_count
    bsp_nodes = []
    for node_index in range(bsp_node_count):
        node_offset = cursor + node_index * UNKNOWN9_RECORD_SIZE
        bsp_nodes.append(
            {
                "index": node_index,
                "front": reader.i16(node_offset + 0x00),
                "back": reader.i16(node_offset + 0x02),
                "face_id_offset": reader.i16(node_offset + 0x04),
                "face_count": reader.i16(node_offset + 0x06),
            }
        )
    cursor += bsp_node_count * UNKNOWN9_RECORD_SIZE
    payload["bsp_nodes"] = bsp_nodes

    spawn_count = reader.i32(cursor)
    cursor += 4
    payload["spawn_count"] = spawn_count
    spawns = []
    for spawn_index in range(spawn_count):
        spawn_offset = cursor + spawn_index * layout["spawn_record_size"]
        spawns.append(
            {
                "index": spawn_index,
                "position": {
                    "x": reader.i32(spawn_offset + 0x00),
                    "y": reader.i32(spawn_offset + 0x04),
                    "z": reader.i32(spawn_offset + 0x08),
                },
                "radius": reader.u16(spawn_offset + 0x0C),
                "type_id": reader.u16(spawn_offset + 0x0E),
                "spawn_index": reader.u16(spawn_offset + 0x10),
                "attributes": reader.u16(spawn_offset + 0x12),
                "group": reader.u32(spawn_offset + 0x14) if layout["version"] > 6 else 0,
                "raw_record_base64": to_base64(reader.bytes(spawn_offset, layout["spawn_record_size"])),
            }
        )
    cursor += spawn_count * layout["spawn_record_size"]
    payload["spawns"] = spawns

    outline_count = reader.i32(cursor)
    cursor += 4
    payload["outline_count"] = outline_count
    outlines = []
    for outline_index in range(outline_count):
        outline_offset = cursor + outline_index * OUTLINE_RECORD_SIZE
        outlines.append(
            {
                "index": outline_index,
                "vertex1_id": reader.u16(outline_offset + 0x00),
                "vertex2_id": reader.u16(outline_offset + 0x02),
                "face1_id": reader.u16(outline_offset + 0x04),
                "face2_id": reader.u16(outline_offset + 0x06),
                "z": reader.i16(outline_offset + 0x08),
                "flags": reader.u16(outline_offset + 0x0A),
            }
        )
    cursor += outline_count * OUTLINE_RECORD_SIZE
    payload["outlines"] = outlines
    payload["trailing_bytes_base64"] = to_base64(reader.bytes(cursor, reader.size - cursor)) if cursor < reader.size else ""

    return make_document("blv", input_path, data, payload)


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
        "containing_item_base64": to_base64(reader.bytes(offset + SPRITE_OBJECT_CONTAINING_ITEM_OFFSET, SPRITE_OBJECT_CONTAINING_ITEM_SIZE)),
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


def parse_door_data(reader: ByteReader, offset: int, door_count: int, doors_data_size_bytes: int) -> tuple[list[dict], list[int], int]:
    doors = []
    for door_index in range(door_count):
        door_offset = offset + door_index * DOOR_RECORD_SIZE
        doors.append(
            {
                "slot_index": door_index,
                "attributes": reader.u32(door_offset + 0x00),
                "door_id": reader.u32(door_offset + 0x04),
                "time_since_triggered_ticks": reader.u32(door_offset + 0x08),
                "time_since_triggered_ms": ticks_to_realtime_milliseconds(reader.u32(door_offset + 0x08)),
                "direction_x": reader.i32(door_offset + 0x0C),
                "direction_y": reader.i32(door_offset + 0x10),
                "direction_z": reader.i32(door_offset + 0x14),
                "move_length": reader.u32(door_offset + 0x18),
                "open_speed": reader.u32(door_offset + 0x1C),
                "close_speed": reader.u32(door_offset + 0x20),
                "num_vertices": reader.u16(door_offset + 0x44),
                "num_faces": reader.u16(door_offset + 0x46),
                "num_sectors": reader.u16(door_offset + 0x48),
                "num_offsets": reader.u16(door_offset + 0x4A),
                "state": reader.u16(door_offset + 0x4C),
                "raw_record_base64": to_base64(reader.bytes(door_offset, DOOR_RECORD_SIZE)),
            }
        )

    cursor = offset + door_count * DOOR_RECORD_SIZE
    doors_data_count = max(doors_data_size_bytes, 0) // 2
    doors_data = reader.i16_array(cursor, doors_data_count)
    cursor += doors_data_size_bytes

    data_cursor = 0
    for door in doors:
        num_vertices = door["num_vertices"]
        num_faces = door["num_faces"]
        num_sectors = door["num_sectors"]
        num_offsets = door["num_offsets"]
        door["vertex_ids"] = [int(value) & 0xFFFF for value in doors_data[data_cursor:data_cursor + num_vertices]]
        data_cursor += num_vertices
        door["face_ids"] = [int(value) & 0xFFFF for value in doors_data[data_cursor:data_cursor + num_faces]]
        data_cursor += num_faces
        door["sector_ids"] = [int(value) & 0xFFFF for value in doors_data[data_cursor:data_cursor + num_sectors]]
        data_cursor += num_sectors
        door["delta_us"] = doors_data[data_cursor:data_cursor + num_faces]
        data_cursor += num_faces
        door["delta_vs"] = doors_data[data_cursor:data_cursor + num_faces]
        data_cursor += num_faces
        door["x_offsets"] = doors_data[data_cursor:data_cursor + num_offsets]
        data_cursor += num_offsets
        door["y_offsets"] = doors_data[data_cursor:data_cursor + num_offsets]
        data_cursor += num_offsets
        door["z_offsets"] = doors_data[data_cursor:data_cursor + num_offsets]
        data_cursor += num_offsets

    return doors, doors_data, cursor


def parse_dlv_file(input_path: Path, companion_path: Path | None) -> dict:
    data = input_path.read_bytes()
    reader = ByteReader(data)

    if companion_path is None:
        guessed_path = input_path.with_suffix(".blv")
        if guessed_path.exists():
            companion_path = guessed_path

    if companion_path is None:
        raise ValueError("dlv export requires companion .blv file")

    blv_document = parse_blv_file(companion_path)
    blv_payload = blv_document["payload"]

    cursor = LOCATION_HEADER_SIZE
    visible_outlines = reader.bytes(cursor, INDOOR_VISIBLE_OUTLINES_BYTES)
    cursor += INDOOR_VISIBLE_OUTLINES_BYTES

    face_attributes = reader.u32_array(cursor, blv_payload["raw_face_count"])
    cursor += blv_payload["raw_face_count"] * 4

    decoration_flags = reader.u16_array(cursor, blv_payload["sprite_count"])
    cursor += blv_payload["sprite_count"] * 2

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

    doors, doors_data, cursor = parse_door_data(
        reader,
        cursor,
        blv_payload["door_count"],
        blv_payload["doors_data_size_bytes"],
    )

    map_vars = list(reader.bytes(cursor + 0, 75))
    decor_vars = list(reader.bytes(cursor + 75, 125))
    cursor += PERSISTENT_VARIABLES_SIZE

    location_time = None
    if cursor + LOCATION_TIME_SIZE <= reader.size:
        location_time = parse_location_time(reader, cursor)
        cursor += LOCATION_TIME_SIZE

    payload = {
        "location_header": parse_location_header(reader),
        "companion_blv": str(companion_path),
        "visible_outlines_base64": to_base64(visible_outlines),
        "face_attributes": face_attributes,
        "decoration_flags": decoration_flags,
        "actor_count": actor_count,
        "actors": actors,
        "sprite_object_count": sprite_object_count,
        "sprite_objects": sprite_objects,
        "chest_count": chest_count,
        "chests": chests,
        "door_count": blv_payload["door_count"],
        "doors": doors,
        "doors_data": doors_data,
        "event_variables": {
            "map_vars": map_vars,
            "decor_vars": decor_vars,
        },
        "location_time": location_time,
        "trailing_bytes_base64": to_base64(reader.bytes(cursor, reader.size - cursor)) if cursor < reader.size else "",
    }

    return make_document("dlv", input_path, data, payload)


def export_file(format_name: str, input_path: Path, companion_path: Path | None) -> dict:
    if format_name == "odm":
        return parse_odm_file(input_path)
    if format_name == "blv":
        return parse_blv_file(input_path)
    if format_name == "dlv":
        return parse_dlv_file(input_path, companion_path)
    raise ValueError(f"unsupported format: {format_name}")


def write_json(document: dict, output_path: Path | None) -> None:
    text = json.dumps(document, indent=2, sort_keys=False)
    if output_path is None:
        sys.stdout.write(text)
        sys.stdout.write("\n")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text + "\n", encoding="utf-8")


def build_argument_parser(format_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Export {format_name} to JSON.")
    parser.add_argument("input", type=Path, help="Input file path")
    parser.add_argument("--companion", type=Path, help="Optional companion map file path")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path (defaults to stdout)")
    return parser


def main_for_format(format_name: str) -> int:
    parser = build_argument_parser(format_name)
    args = parser.parse_args()
    document = export_file(format_name, args.input, args.companion)
    write_json(document, args.output)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenYAMM map file to JSON.")
    parser.add_argument("format", choices=["odm", "blv", "dlv"], help="Map format")
    parser.add_argument("input", type=Path, help="Input file path")
    parser.add_argument("--companion", type=Path, help="Optional companion map file path")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path (defaults to stdout)")
    args = parser.parse_args()
    document = export_file(args.format, args.input, args.companion)
    write_json(document, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
