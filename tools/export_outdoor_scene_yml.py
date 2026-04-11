#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


VERSION_OFFSET = 0x40
VERSION_FIELD_SIZE = 16
MASTER_TILE_OFFSET = 0x5F
TILE_SET_LOOKUP_OFFSET = 0xA0
TERRAIN_SECTION_OFFSET = 0xB0
TERRAIN_SECTION_OFFSET_V8 = 0xB4
TERRAIN_WIDTH = 128
TERRAIN_HEIGHT = 128
TERRAIN_MAP_SIZE = TERRAIN_WIDTH * TERRAIN_HEIGHT
C_MAP1_SIZE = 0x20000
C_MAP2_SIZE = 0x10000
BMODEL_HEADER_SIZE = 0xBC
BMODEL_VERTEX_SIZE = 12
BMODEL_FACE_SIZE = 0x134
BMODEL_FACE_FLAGS_SIZE = 2
BMODEL_TEXTURE_NAME_SIZE = 10
BMODEL_BSP_NODE_SIZE = 8
BMODEL_FACE_VERTEX_INDICES_OFFSET = 0x20
BMODEL_FACE_TEXTURE_U_OFFSET = 0x48
BMODEL_FACE_TEXTURE_V_OFFSET = 0x70
BMODEL_FACE_ATTRIBUTES_OFFSET = 0x1C
BMODEL_FACE_BITMAP_INDEX_OFFSET = 0x110
BMODEL_FACE_TEXTURE_DELTA_U_OFFSET = 0x112
BMODEL_FACE_TEXTURE_DELTA_V_OFFSET = 0x114
BMODEL_FACE_COG_NUMBER_OFFSET = 0x122
BMODEL_FACE_COG_TRIGGERED_NUMBER_OFFSET = 0x124
BMODEL_FACE_COG_TRIGGER_OFFSET = 0x126
BMODEL_FACE_RESERVED_OFFSET = 0x128
BMODEL_FACE_NUM_VERTICES_OFFSET = 0x12E
BMODEL_FACE_POLYGON_TYPE_OFFSET = 0x12F
BMODEL_FACE_SHADE_OFFSET = 0x130
BMODEL_FACE_VISIBILITY_OFFSET = 0x131
ENTITY_NAME_SIZE = 0x20
VERSION6_ENTITY_SIZE = 0x1C
VERSION7_ENTITY_SIZE = 0x20
VERSION6_SPAWN_SIZE = 0x14
VERSION7_SPAWN_SIZE = 0x18
VERSION6_TAG = b"MM6 Outdoor v1.11"
VERSION7_TAG = b"MM6 Outdoor v7.00"

OUTDOOR_REVEAL_MAP_BYTES = 88 * 11 * 2
LOCATION_HEADER_SIZE = 40
ACTOR_RECORD_SIZE = 0x3CC
SPRITE_OBJECT_RECORD_SIZE = 0x70
CHEST_RECORD_SIZE = 5324
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
ACTOR_ALLY_OFFSET = 0x340
ACTOR_GROUP_OFFSET = 0x34C
ACTOR_UNIQUE_NAME_INDEX_OFFSET = 0x3BC


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
                f"{self.path.name}: truncated read for {context} at 0x{offset:X}, "
                f"need {byte_count} bytes"
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


def detect_outdoor_version(reader: ByteReader) -> int:
    if reader.matches_text(VERSION_OFFSET, VERSION6_TAG):
        return 6
    if reader.matches_text(VERSION_OFFSET, VERSION7_TAG):
        return 7
    if reader.is_zero_block(VERSION_OFFSET, VERSION_FIELD_SIZE):
        return 8
    raise ParseError(f"{reader.path.name}: not a recognized outdoor ODM file")


def quote_yaml_string(value: str) -> str:
    return json.dumps(value)


def bytes_to_hex(value: bytes) -> str:
    return value.hex().upper()


def write_yaml_scalar(lines: list[str], indent: str, key: str, value: object) -> None:
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, str):
        text = quote_yaml_string(value)
    else:
        text = str(value)
    lines.append(f"{indent}{key}: {text}")


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


def parse_outdoor_odm(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    reader = ByteReader(path, data)
    version = detect_outdoor_version(reader)

    model: dict[str, object] = {
        "path": path,
        "version": version,
        "sky_texture": reader.read_fixed_string(0x60, 32, "sky texture"),
        "ground_tileset_name": reader.read_fixed_string(0x80, 32, "ground tileset name"),
        "master_tile": reader.read_u8(MASTER_TILE_OFFSET, "master tile"),
        "tile_set_lookup_indices": [],
        "bmodels": [],
        "entities": [],
        "spawns": [],
    }

    for lookup_index in range(4):
        raw_value = reader.read_i32(
            TILE_SET_LOOKUP_OFFSET + lookup_index * 4,
            f"tile set lookup index {lookup_index}"
        )
        model["tile_set_lookup_indices"].append((raw_value >> 16) & 0xFFFF)

    offset = TERRAIN_SECTION_OFFSET_V8 if version == 8 else TERRAIN_SECTION_OFFSET
    reader.read_bytes(offset, TERRAIN_MAP_SIZE, "height map")
    offset += TERRAIN_MAP_SIZE
    reader.read_bytes(offset, TERRAIN_MAP_SIZE, "tile map")
    offset += TERRAIN_MAP_SIZE
    attribute_map = reader.read_bytes(offset, TERRAIN_MAP_SIZE, "attribute map")
    offset += TERRAIN_MAP_SIZE

    if version > 6:
        terrain_normal_count = reader.read_i32(offset, "terrain normal count")
        if terrain_normal_count < 0:
            raise ParseError(f"{path.name}: negative terrain normal count {terrain_normal_count}")
        offset += 4
        reader.read_bytes(offset, C_MAP1_SIZE, "someOtherMap")
        offset += C_MAP1_SIZE
        reader.read_bytes(offset, C_MAP2_SIZE, "normalMap")
        offset += C_MAP2_SIZE
        reader.read_bytes(offset, terrain_normal_count * 12, "normals")
        offset += terrain_normal_count * 12

    bmodel_count = reader.read_i32(offset, "bmodel count")
    if bmodel_count < 0:
        raise ParseError(f"{path.name}: negative bmodel count {bmodel_count}")
    offset += 4

    bmodel_headers_offset = offset
    offset += bmodel_count * BMODEL_HEADER_SIZE
    reader.require(
        bmodel_headers_offset,
        bmodel_count * BMODEL_HEADER_SIZE,
        "bmodel headers"
    )

    for bmodel_index in range(bmodel_count):
        header_offset = bmodel_headers_offset + bmodel_index * BMODEL_HEADER_SIZE
        vertex_count = reader.read_i32(header_offset + 0x44, f"bmodel {bmodel_index} vertex count")
        face_count = reader.read_i32(header_offset + 0x4C, f"bmodel {bmodel_index} face count")
        bsp_node_count = reader.read_i32(header_offset + 0x5C, f"bmodel {bmodel_index} bsp node count")

        if vertex_count < 0 or face_count < 0 or bsp_node_count < 0:
            raise ParseError(
                f"{path.name}: invalid counts in bmodel {bmodel_index}: "
                f"vertices={vertex_count}, faces={face_count}, bsp_nodes={bsp_node_count}"
            )

        bmodel = {
            "index": bmodel_index,
            "face_count_header": face_count,
            "faces": [],
        }

        vertices: list[tuple[int, int, int]] = []

        for vertex_index in range(vertex_count):
            vertex_offset = offset + vertex_index * BMODEL_VERTEX_SIZE
            vertex_x = reader.read_i32(vertex_offset + 0, f"bmodel {bmodel_index} vertex {vertex_index} x")
            vertex_y = reader.read_i32(vertex_offset + 4, f"bmodel {bmodel_index} vertex {vertex_index} y")
            vertex_z = reader.read_i32(vertex_offset + 8, f"bmodel {bmodel_index} vertex {vertex_index} z")
            vertices.append((vertex_x, vertex_y, vertex_z))

        offset += vertex_count * BMODEL_VERTEX_SIZE

        faces_offset = offset
        face_flags_offset = faces_offset + face_count * BMODEL_FACE_SIZE
        face_texture_names_offset = face_flags_offset + face_count * BMODEL_FACE_FLAGS_SIZE
        reader.require(faces_offset, face_count * BMODEL_FACE_SIZE, f"bmodel {bmodel_index} faces")
        reader.require(
            face_texture_names_offset,
            face_count * BMODEL_TEXTURE_NAME_SIZE,
            f"bmodel {bmodel_index} face texture names"
        )

        for face_index in range(face_count):
            face_offset = faces_offset + face_index * BMODEL_FACE_SIZE
            num_vertices = reader.read_u8(
                face_offset + BMODEL_FACE_NUM_VERTICES_OFFSET,
                f"bmodel {bmodel_index} face {face_index} vertex count"
            )

            if num_vertices < 2 or num_vertices > 20:
                continue

            attributes = reader.read_u32(
                face_offset + BMODEL_FACE_ATTRIBUTES_OFFSET,
                f"bmodel {bmodel_index} face {face_index} attributes"
            )
            bitmap_index = reader.read_i16(
                face_offset + BMODEL_FACE_BITMAP_INDEX_OFFSET,
                f"bmodel {bmodel_index} face {face_index} bitmap index"
            )
            texture_delta_u = reader.read_i16(
                face_offset + BMODEL_FACE_TEXTURE_DELTA_U_OFFSET,
                f"bmodel {bmodel_index} face {face_index} texture delta U"
            )
            texture_delta_v = reader.read_i16(
                face_offset + BMODEL_FACE_TEXTURE_DELTA_V_OFFSET,
                f"bmodel {bmodel_index} face {face_index} texture delta V"
            )
            cog_number = reader.read_u16(
                face_offset + BMODEL_FACE_COG_NUMBER_OFFSET,
                f"bmodel {bmodel_index} face {face_index} cog number"
            )
            cog_triggered_number = reader.read_u16(
                face_offset + BMODEL_FACE_COG_TRIGGERED_NUMBER_OFFSET,
                f"bmodel {bmodel_index} face {face_index} cog triggered number"
            )
            cog_trigger = reader.read_u16(
                face_offset + BMODEL_FACE_COG_TRIGGER_OFFSET,
                f"bmodel {bmodel_index} face {face_index} cog trigger"
            )
            reserved = reader.read_u16(
                face_offset + BMODEL_FACE_RESERVED_OFFSET,
                f"bmodel {bmodel_index} face {face_index} reserved"
            )
            polygon_type = reader.read_u8(
                face_offset + BMODEL_FACE_POLYGON_TYPE_OFFSET,
                f"bmodel {bmodel_index} face {face_index} polygon type"
            )
            shade = reader.read_u8(
                face_offset + BMODEL_FACE_SHADE_OFFSET,
                f"bmodel {bmodel_index} face {face_index} shade"
            )
            visibility = reader.read_u8(
                face_offset + BMODEL_FACE_VISIBILITY_OFFSET,
                f"bmodel {bmodel_index} face {face_index} visibility"
            )

            vertex_ids: list[int] = []
            valid_vertex_ids = True

            for face_vertex_index in range(num_vertices):
                vertex_id_offset = (
                    face_offset
                    + BMODEL_FACE_VERTEX_INDICES_OFFSET
                    + face_vertex_index * 2
                )
                vertex_id = reader.read_u16(
                    vertex_id_offset,
                    f"bmodel {bmodel_index} face {face_index} vertex id {face_vertex_index}"
                )
                if vertex_id >= len(vertices):
                    valid_vertex_ids = False
                    break
                vertex_ids.append(vertex_id)
                reader.read_i16(
                    face_offset + BMODEL_FACE_TEXTURE_U_OFFSET + face_vertex_index * 2,
                    f"bmodel {bmodel_index} face {face_index} texture U {face_vertex_index}"
                )
                reader.read_i16(
                    face_offset + BMODEL_FACE_TEXTURE_V_OFFSET + face_vertex_index * 2,
                    f"bmodel {bmodel_index} face {face_index} texture V {face_vertex_index}"
                )

            texture_name = reader.read_fixed_string(
                face_texture_names_offset + face_index * BMODEL_TEXTURE_NAME_SIZE,
                BMODEL_TEXTURE_NAME_SIZE,
                f"bmodel {bmodel_index} face {face_index} texture name"
            )

            if valid_vertex_ids and len(vertex_ids) >= 2:
                bmodel["faces"].append({
                    "index": len(bmodel["faces"]),
                    "attributes": attributes,
                    "bitmap_index": bitmap_index,
                    "texture_delta_u": texture_delta_u,
                    "texture_delta_v": texture_delta_v,
                    "cog_number": cog_number,
                    "cog_triggered_number": cog_triggered_number,
                    "cog_trigger": cog_trigger,
                    "reserved": reserved,
                    "polygon_type": polygon_type,
                    "shade": shade,
                    "visibility": visibility,
                    "texture_name": texture_name,
                })

        offset += face_count * BMODEL_FACE_SIZE
        offset += face_count * BMODEL_FACE_FLAGS_SIZE
        offset += face_count * BMODEL_TEXTURE_NAME_SIZE

        reader.require(offset, bsp_node_count * BMODEL_BSP_NODE_SIZE, f"bmodel {bmodel_index} bsp nodes")
        offset += bsp_node_count * BMODEL_BSP_NODE_SIZE
        model["bmodels"].append(bmodel)

    entity_count = reader.read_i32(offset, "entity count")
    if entity_count < 0:
        raise ParseError(f"{path.name}: negative entity count {entity_count}")
    offset += 4

    entity_size = VERSION6_ENTITY_SIZE if version == 6 else VERSION7_ENTITY_SIZE
    entity_data_offset = offset
    reader.require(entity_data_offset, entity_count * entity_size, "entity data")
    offset += entity_count * entity_size
    entity_names_offset = offset
    reader.require(entity_names_offset, entity_count * ENTITY_NAME_SIZE, "entity names")
    offset += entity_count * ENTITY_NAME_SIZE

    for entity_index in range(entity_count):
        entity_offset = entity_data_offset + entity_index * entity_size
        entity = {
            "entity_index": entity_index,
            "name": reader.read_fixed_string(
                entity_names_offset + entity_index * ENTITY_NAME_SIZE,
                ENTITY_NAME_SIZE,
                f"entity {entity_index} name"
            ),
            "decoration_list_id": reader.read_u16(entity_offset + 0x00, f"entity {entity_index} decoration list id"),
            "ai_attributes": reader.read_u16(entity_offset + 0x02, f"entity {entity_index} ai attributes"),
            "position": {
                "x": reader.read_i32(entity_offset + 0x04, f"entity {entity_index} x"),
                "y": reader.read_i32(entity_offset + 0x08, f"entity {entity_index} y"),
                "z": reader.read_i32(entity_offset + 0x0C, f"entity {entity_index} z"),
            },
            "facing": reader.read_i32(entity_offset + 0x10, f"entity {entity_index} facing"),
            "event_id_primary": reader.read_u16(entity_offset + 0x14, f"entity {entity_index} event id primary"),
            "event_id_secondary": reader.read_u16(entity_offset + 0x16, f"entity {entity_index} event id secondary"),
            "variable_primary": reader.read_u16(entity_offset + 0x18, f"entity {entity_index} variable primary"),
            "variable_secondary": reader.read_u16(entity_offset + 0x1A, f"entity {entity_index} variable secondary"),
            "special_trigger": 0,
        }

        if version > 6:
            entity["special_trigger"] = reader.read_u16(
                entity_offset + 0x1C,
                f"entity {entity_index} special trigger"
            )

        model["entities"].append(entity)

    id_list_count = reader.read_i32(offset, "IDList count")
    if id_list_count < 0:
        raise ParseError(f"{path.name}: negative IDList count {id_list_count}")
    offset += 4
    reader.require(offset, id_list_count * 2, "IDList")
    offset += id_list_count * 2
    reader.require(offset, TERRAIN_MAP_SIZE * 4, "OMAP")
    offset += TERRAIN_MAP_SIZE * 4

    spawn_count = reader.read_i32(offset, "spawn count")
    if spawn_count < 0:
        raise ParseError(f"{path.name}: negative spawn count {spawn_count}")
    offset += 4

    spawn_size = VERSION6_SPAWN_SIZE if version == 6 else VERSION7_SPAWN_SIZE
    spawn_data_offset = offset
    reader.require(spawn_data_offset, spawn_count * spawn_size, "spawn data")

    for spawn_index in range(spawn_count):
        spawn_offset = spawn_data_offset + spawn_index * spawn_size
        spawn = {
            "spawn_index": spawn_index,
            "position": {
                "x": reader.read_i32(spawn_offset + 0x00, f"spawn {spawn_index} x"),
                "y": reader.read_i32(spawn_offset + 0x04, f"spawn {spawn_index} y"),
                "z": reader.read_i32(spawn_offset + 0x08, f"spawn {spawn_index} z"),
            },
            "radius": reader.read_u16(spawn_offset + 0x0C, f"spawn {spawn_index} radius"),
            "type_id": reader.read_u16(spawn_offset + 0x0E, f"spawn {spawn_index} type id"),
            "index": reader.read_u16(spawn_offset + 0x10, f"spawn {spawn_index} index"),
            "attributes": reader.read_u16(spawn_offset + 0x12, f"spawn {spawn_index} attributes"),
            "group": 0,
        }
        if version > 6:
            spawn["group"] = reader.read_u32(spawn_offset + 0x14, f"spawn {spawn_index} group")
        model["spawns"].append(spawn)

    terrain_attribute_overrides: list[dict[str, object]] = []

    for cell_index, raw_value in enumerate(attribute_map):
        if raw_value == 0:
            continue
        terrain_attribute_overrides.append({
            "x": cell_index % TERRAIN_WIDTH,
            "y": cell_index // TERRAIN_WIDTH,
            "legacy_attributes": raw_value,
            "burn": (raw_value & 0x01) != 0,
            "water": (raw_value & 0x02) != 0,
        })

    interactive_faces: list[dict[str, int]] = []

    for bmodel in model["bmodels"]:
        for face in bmodel["faces"]:
            if (
                face["attributes"] == 0
                and face["cog_number"] == 0
                and face["cog_triggered_number"] == 0
                and face["cog_trigger"] == 0
            ):
                continue
            interactive_faces.append({
                "bmodel_index": bmodel["index"],
                "face_index": face["index"],
                "legacy_attributes": face["attributes"],
                "cog_number": face["cog_number"],
                "cog_triggered_number": face["cog_triggered_number"],
                "cog_trigger": face["cog_trigger"],
            })

    model["terrain_attribute_overrides"] = terrain_attribute_overrides
    model["interactive_faces"] = interactive_faces
    return model


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
            "attributes": reader.read_u32(
                actor_offset + ACTOR_ATTRIBUTES_OFFSET,
                f"actor {actor_index} attributes"
            ),
            "hp": reader.read_i16(actor_offset + ACTOR_HP_OFFSET, f"actor {actor_index} hp"),
            "hostility_type": reader.read_u8(
                actor_offset + ACTOR_HOSTILITY_TYPE_OFFSET,
                f"actor {actor_index} hostility type"
            ),
            "monster_info_id": reader.read_i16(
                actor_offset + ACTOR_MONSTER_INFO_ID_OFFSET,
                f"actor {actor_index} monster info id"
            ),
            "monster_id": reader.read_i16(
                actor_offset + ACTOR_MONSTER_ID_OFFSET,
                f"actor {actor_index} monster id"
            ),
            "radius": reader.read_u16(actor_offset + ACTOR_RADIUS_OFFSET, f"actor {actor_index} radius"),
            "height": reader.read_u16(actor_offset + ACTOR_HEIGHT_OFFSET, f"actor {actor_index} height"),
            "move_speed": reader.read_u16(
                actor_offset + ACTOR_MOVE_SPEED_OFFSET,
                f"actor {actor_index} move speed"
            ),
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
            "spell_level": reader.read_i32(
                object_offset + 0x4C,
                f"sprite object {sprite_object_index} spell level"
            ),
            "spell_skill": reader.read_i32(
                object_offset + 0x50,
                f"sprite object {sprite_object_index} spell skill"
            ),
            "field54": reader.read_i32(object_offset + 0x54, f"sprite object {sprite_object_index} field54"),
            "spell_caster_pid": reader.read_i32(
                object_offset + 0x58,
                f"sprite object {sprite_object_index} spell caster pid"
            ),
            "spell_target_pid": reader.read_i32(
                object_offset + 0x5C,
                f"sprite object {sprite_object_index} spell target pid"
            ),
            "lod_distance": reader.read_i8(
                object_offset + 0x60,
                f"sprite object {sprite_object_index} lod distance"
            ),
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
                reader.read_bytes(
                    chest_offset + CHEST_ITEMS_OFFSET,
                    CHEST_ITEMS_SIZE,
                    f"chest {chest_index} raw items"
                )
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


def parse_outdoor_ddm(path: Path, odm_model: dict[str, object]) -> dict[str, object]:
    data = path.read_bytes()
    reader = ByteReader(path, data)
    location = parse_location_header(reader)

    total_face_count = sum(len(bmodel["faces"]) for bmodel in odm_model["bmodels"])

    def validate_optional_header_count(field_name: str, actual: int, expected: int) -> None:
        if actual == 0:
            return
        if actual != expected:
            raise ParseError(
                f"{path.name}: DDM {field_name} {actual} does not match expected {expected}"
            )

    validate_optional_header_count("totalFacesCount", location["total_faces_count"], total_face_count)
    validate_optional_header_count("decorationCount", location["decoration_count"], len(odm_model["entities"]))
    validate_optional_header_count("bmodelCount", location["bmodel_count"], len(odm_model["bmodels"]))

    offset = LOCATION_HEADER_SIZE
    reader.read_bytes(offset, OUTDOOR_REVEAL_MAP_BYTES, "outdoor reveal map")
    offset += OUTDOOR_REVEAL_MAP_BYTES

    face_attributes, offset = parse_u32_vector(reader, offset, total_face_count, "face attribute override")
    decoration_flags, offset = parse_u16_vector(
        reader,
        offset,
        len(odm_model["entities"]),
        "decoration flag"
    )
    actors, offset = parse_actor_vector(reader, offset)
    sprite_objects, offset = parse_sprite_objects(reader, offset)
    chests, offset = parse_chests(reader, offset)
    variables, offset = parse_persistent_variables(reader, offset)
    location_time = parse_location_time_optional(reader, offset)

    if len(face_attributes) != total_face_count:
        raise ParseError(
            f"{path.name}: expected {total_face_count} face attribute overrides, got {len(face_attributes)}"
        )

    if len(decoration_flags) != len(odm_model["entities"]):
        raise ParseError(
            f"{path.name}: expected {len(odm_model['entities'])} decoration flags, got "
            f"{len(decoration_flags)}"
        )

    face_attribute_overrides: list[dict[str, int]] = []
    flat_face_index = 0

    for bmodel in odm_model["bmodels"]:
        for face in bmodel["faces"]:
            override_value = face_attributes[flat_face_index]
            flat_face_index += 1
            if override_value == face["attributes"]:
                continue
            face_attribute_overrides.append({
                "bmodel_index": bmodel["index"],
                "face_index": face["index"],
                "legacy_attributes": override_value,
            })

    return {
        "path": path,
        "location": {
            "respawn_count": location["respawn_count"],
            "last_respawn_day": location["last_respawn_day"],
            "reputation": location["reputation"],
            "alert_status": location["alert_status"],
        },
        "decoration_flags": decoration_flags,
        "face_attribute_overrides": face_attribute_overrides,
        "actors": actors,
        "sprite_objects": sprite_objects,
        "chests": chests,
        "variables": variables,
        "location_time": location_time,
    }


def build_scene_model(odm_model: dict[str, object], ddm_model: dict[str, object]) -> dict[str, object]:
    location_time = ddm_model["location_time"]
    day_bits_raw = location_time["day_bits_raw"]
    map_extra_bits_raw = location_time["map_extra_bits_raw"]
    sky_texture = location_time["sky_texture_name"] or odm_model["sky_texture"]

    entities: list[dict[str, object]] = []

    for entity, initial_decoration_flag in zip(odm_model["entities"], ddm_model["decoration_flags"]):
        combined = dict(entity)
        combined["position"] = dict(entity["position"])
        combined["initial_decoration_flag"] = initial_decoration_flag
        entities.append(combined)

    spawns: list[dict[str, object]] = []

    for spawn in odm_model["spawns"]:
        copied_spawn = dict(spawn)
        copied_spawn["position"] = dict(spawn["position"])
        spawns.append(copied_spawn)

    actors: list[dict[str, object]] = []

    for actor in ddm_model["actors"]:
        copied_actor = dict(actor)
        copied_actor["position"] = dict(actor["position"])
        copied_actor["sprite_ids"] = list(actor["sprite_ids"])
        actors.append(copied_actor)

    sprite_objects: list[dict[str, object]] = []

    for sprite_object in ddm_model["sprite_objects"]:
        copied_sprite_object = dict(sprite_object)
        copied_sprite_object["position"] = dict(sprite_object["position"])
        copied_sprite_object["velocity"] = dict(sprite_object["velocity"])
        copied_sprite_object["initial_position"] = dict(sprite_object["initial_position"])
        sprite_objects.append(copied_sprite_object)

    chests: list[dict[str, object]] = []

    for chest in ddm_model["chests"]:
        copied_chest = dict(chest)
        copied_chest["inventory_matrix"] = list(chest["inventory_matrix"])
        chests.append(copied_chest)

    return {
        "format_version": 1,
        "kind": "outdoor_scene",
        "source": {
            "geometry_file": odm_model["path"].name,
            "legacy_companion_file": ddm_model["path"].name,
        },
        "environment": {
            "sky_texture": sky_texture,
            "ground_tileset_name": odm_model["ground_tileset_name"],
            "master_tile": odm_model["master_tile"],
            "tile_set_lookup_indices": list(odm_model["tile_set_lookup_indices"]),
            "day_bits_raw": day_bits_raw,
            "map_extra_bits_raw": map_extra_bits_raw,
            "flags": {
                "foggy": (day_bits_raw & 0x1) != 0,
                "raining": (map_extra_bits_raw & 0x1) != 0,
                "snowing": (map_extra_bits_raw & 0x2) != 0,
                "underwater": (map_extra_bits_raw & 0x4) != 0,
                "no_terrain": (map_extra_bits_raw & 0x8) != 0,
                "always_dark": (map_extra_bits_raw & 0x10) != 0,
                "always_light": (map_extra_bits_raw & 0x20) != 0,
                "always_foggy": (map_extra_bits_raw & 0x40) != 0,
                "red_fog": (map_extra_bits_raw & 0x80) != 0,
            },
            "fog": {
                "weak_distance": location_time["fog_weak_distance"],
                "strong_distance": location_time["fog_strong_distance"],
            },
            "ceiling": location_time["ceiling"],
        },
        "terrain": {
            "attribute_overrides": odm_model["terrain_attribute_overrides"],
        },
        "bmodel_faces": {
            "interactive_faces": odm_model["interactive_faces"],
        },
        "entities": entities,
        "spawns": spawns,
        "initial_state": {
            "location": ddm_model["location"],
            "face_attribute_overrides": ddm_model["face_attribute_overrides"],
            "actors": actors,
            "sprite_objects": sprite_objects,
            "chests": chests,
            "variables": {
                "map": list(ddm_model["variables"]["map"]),
                "decor": list(ddm_model["variables"]["decor"]),
            },
        },
    }


def validate_scene_model(scene_model: dict[str, object]) -> None:
    terrain_overrides = scene_model["terrain"]["attribute_overrides"]

    for entry in terrain_overrides:
        if not (0 <= entry["x"] < TERRAIN_WIDTH and 0 <= entry["y"] < TERRAIN_HEIGHT):
            raise ParseError(
                f"terrain attribute override out of range: x={entry['x']} y={entry['y']}"
            )

    tile_set_lookup_indices = scene_model["environment"]["tile_set_lookup_indices"]
    if len(tile_set_lookup_indices) != 4:
        raise ParseError(
            f"expected 4 tile set lookup indices, got {len(tile_set_lookup_indices)}"
        )


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
    write_yaml_scalar(lines, "  ", "ground_tileset_name", environment["ground_tileset_name"])
    write_yaml_scalar(lines, "  ", "master_tile", environment["master_tile"])
    append_int_list(lines, "  ", "tile_set_lookup_indices", environment["tile_set_lookup_indices"])
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

    lines.append("terrain:")
    attribute_overrides = scene_model["terrain"]["attribute_overrides"]
    if not attribute_overrides:
        lines.append("  attribute_overrides: []")
    else:
        lines.append("  attribute_overrides:")
        for entry in attribute_overrides:
            lines.append(f"    - x: {entry['x']}")
            lines.append(f"      y: {entry['y']}")
            lines.append(f"      legacy_attributes: {entry['legacy_attributes']}")
            write_yaml_scalar(lines, "      ", "burn", entry["burn"])
            write_yaml_scalar(lines, "      ", "water", entry["water"])

    lines.append("bmodel_faces:")
    interactive_faces = scene_model["bmodel_faces"]["interactive_faces"]
    if not interactive_faces:
        lines.append("  interactive_faces: []")
    else:
        lines.append("  interactive_faces:")
        for entry in interactive_faces:
            lines.append(f"    - bmodel_index: {entry['bmodel_index']}")
            lines.append(f"      face_index: {entry['face_index']}")
            lines.append(f"      legacy_attributes: {entry['legacy_attributes']}")
            lines.append(f"      cog_number: {entry['cog_number']}")
            lines.append(f"      cog_triggered_number: {entry['cog_triggered_number']}")
            lines.append(f"      cog_trigger: {entry['cog_trigger']}")

    entities = scene_model["entities"]
    if not entities:
        lines.append("entities: []")
    else:
        lines.append("entities:")
        for entity in entities:
            lines.append(f"  - entity_index: {entity['entity_index']}")
            write_yaml_scalar(lines, "    ", "name", entity["name"])
            lines.append(f"    decoration_list_id: {entity['decoration_list_id']}")
            lines.append(f"    ai_attributes: {entity['ai_attributes']}")
            append_position_block(lines, "    ", "position", entity["position"])
            lines.append(f"    facing: {entity['facing']}")
            lines.append(f"    event_id_primary: {entity['event_id_primary']}")
            lines.append(f"    event_id_secondary: {entity['event_id_secondary']}")
            lines.append(f"    variable_primary: {entity['variable_primary']}")
            lines.append(f"    variable_secondary: {entity['variable_secondary']}")
            lines.append(f"    special_trigger: {entity['special_trigger']}")
            lines.append(f"    initial_decoration_flag: {entity['initial_decoration_flag']}")

    spawns = scene_model["spawns"]
    if not spawns:
        lines.append("spawns: []")
    else:
        lines.append("spawns:")
        for spawn in spawns:
            lines.append(f"  - spawn_index: {spawn['spawn_index']}")
            append_position_block(lines, "    ", "position", spawn["position"])
            lines.append(f"    radius: {spawn['radius']}")
            lines.append(f"    type_id: {spawn['type_id']}")
            lines.append(f"    index: {spawn['index']}")
            lines.append(f"    attributes: {spawn['attributes']}")
            lines.append(f"    group: {spawn['group']}")

    initial_state = scene_model["initial_state"]
    lines.append("initial_state:")
    lines.append("  location:")
    write_yaml_scalar(lines, "    ", "respawn_count", initial_state["location"]["respawn_count"])
    write_yaml_scalar(lines, "    ", "last_respawn_day", initial_state["location"]["last_respawn_day"])
    write_yaml_scalar(lines, "    ", "reputation", initial_state["location"]["reputation"])
    write_yaml_scalar(lines, "    ", "alert_status", initial_state["location"]["alert_status"])

    face_attribute_overrides = initial_state["face_attribute_overrides"]
    if not face_attribute_overrides:
        lines.append("  face_attribute_overrides: []")
    else:
        lines.append("  face_attribute_overrides:")
        for entry in face_attribute_overrides:
            lines.append(f"    - bmodel_index: {entry['bmodel_index']}")
            lines.append(f"      face_index: {entry['face_index']}")
            lines.append(f"      legacy_attributes: {entry['legacy_attributes']}")

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
            write_yaml_scalar(
                lines,
                "      ",
                "raw_containing_item_hex",
                sprite_object["raw_containing_item_hex"]
            )

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

    lines.append("  variables:")
    append_int_list(lines, "    ", "map", initial_state["variables"]["map"])
    append_int_list(lines, "    ", "decor", initial_state["variables"]["decor"])
    return "\n".join(lines) + "\n"


def derive_paths(args: argparse.Namespace, repo_root: Path) -> tuple[Path, Path, Path]:
    if args.odm:
        odm_path = Path(args.odm)
        ddm_path = Path(args.ddm) if args.ddm else odm_path.with_suffix(".ddm")
        output_path = Path(args.output) if args.output else odm_path.with_suffix(".scene.yml")
        return odm_path, ddm_path, output_path

    if args.map_base:
        map_base = Path(args.map_base)
        output_path = Path(args.output) if args.output else map_base.with_suffix(".scene.yml")
        return map_base.with_suffix(".odm"), map_base.with_suffix(".ddm"), output_path

    input_dir = Path(args.input_dir) if args.input_dir else repo_root / "assets_dev" / "Data" / "games"
    map_name = args.map
    if map_name is None:
        raise ParseError("either --odm, --map-base, or --map must be provided")
    output_path = Path(args.output) if args.output else input_dir / f"{map_name}.scene.yml"
    return input_dir / f"{map_name}.odm", input_dir / f"{map_name}.ddm", output_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export outdoor ODM + DDM into .scene.yml")
    parser.add_argument("--odm", help="path to XX.odm")
    parser.add_argument("--ddm", help="path to XX.ddm; defaults next to --odm")
    parser.add_argument("--output", help="path to XX.scene.yml; defaults next to --odm")
    parser.add_argument("--map-base", help="path without extension, e.g. assets_dev/Data/games/out01")
    parser.add_argument("--input-dir", help="directory containing map files for --map mode")
    parser.add_argument("--map", help="map basename for --input-dir mode, e.g. out01")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    try:
        odm_path, ddm_path, output_path = derive_paths(args, repo_root)

        if not odm_path.is_file():
            raise ParseError(f"missing ODM file: {odm_path}")
        if not ddm_path.is_file():
            raise ParseError(f"missing DDM file: {ddm_path}")

        odm_model = parse_outdoor_odm(odm_path)
        ddm_model = parse_outdoor_ddm(ddm_path, odm_model)
        scene_model = build_scene_model(odm_model, ddm_model)
        validate_scene_model(scene_model)
        output_text = render_scene_yaml(scene_model)
        write_atomic_text(output_path, output_text)
    except ParseError as error:
        parser.exit(1, f"{error}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
