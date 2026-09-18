#!/usr/bin/env python3
"""
Transcode a LithTech 2.x/MM9 DAT v66 world into an OpenYAMM outdoor ODM shell.

This is a discovery/import tool. It intentionally writes the existing OpenYAMM
ODM layout so the editor can load the result without a runtime format fork, and
puts MM9-specific source metadata into sidecars.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from convert_abc_model import AbcModel, read_abc
from mm9_item_sources import (
    MM9_BARREL_LIQUID_TEXTURES,
    Mm9ItemIdMap,
    Mm9ItemSourceManifest,
    build_mm9_item_source_manifest,
)
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


DAT_VERSION_LT2 = 66

TERRAIN_MAP_SIZE = 0x4000
CMAP1_SIZE = 0x20000
CMAP2_SIZE = 0x10000
BMODEL_HEADER_SIZE = 0xBC
BMODEL_FACE_SIZE = 0x134
BMODEL_FACE_FLAGS_SIZE = 2
BMODEL_TEXTURE_NAME_SIZE = 10
ODM_ENTITY_SIZE = 0x20
ODM_ENTITY_NAME_SIZE = 0x20
MAX_BMODEL_FACE_VERTICES = 20
OUTDOOR_FACE_PLANE_SCALE = 65536.0
OUTDOOR_POLYGON_VERTICAL_WALL = 0x1
OUTDOOR_POLYGON_FLOOR = 0x3
OUTDOOR_POLYGON_IN_BETWEEN_FLOOR_AND_WALL = 0x4
OUTDOOR_POLYGON_CEILING = 0x5
OUTDOOR_POLYGON_IN_BETWEEN_CEILING_AND_WALL = 0x6
OUTDOOR_FLAT_FACE_NORMAL_Z = 0.999
OUTDOOR_SLOPED_FACE_NORMAL_Z = 0.45
MODEL_SOURCE_EXTENSIONS = {".abc", ".lta", ".ltb"}
I32_MIN = -2147483648
I32_MAX = 2147483647
FACE_ATTRIBUTE_FLUID = 0x00000010
FACE_ATTRIBUTE_SECRET = 0x00000002
FACE_ATTRIBUTE_INVISIBLE = 0x00002000
FACE_ATTRIBUTE_ANIMATED = 0x00004000
FACE_ATTRIBUTE_HAS_HINT = 0x00100000
FACE_ATTRIBUTE_CLICKABLE = 0x02000000
FACE_ATTRIBUTE_UNTOUCHABLE = 0x20000000
ODM_FACE_RESERVED_NOT_A_STEP = 0x0001
MM9_MECHANISM_EVENT_ID_BASE = 30000
MM9_MONSTER_ID_BASE = 9000
ACTOR_ATTRIBUTE_INVISIBLE = 0x00010000
ACTOR_ATTRIBUTE_AGGRESSOR = 0x00080000
MM9_SPR_HEADER_SIZE = 20
OUTDOOR_NAVIGATION_MAGIC = b"OYMNAV1\0"
OUTDOOR_NAVIGATION_VERSION = 1
OUTDOOR_NAVIGATION_HEADER_SIZE = 48
OUTDOOR_NAVIGATION_RECORD_SIZE = 24
OUTDOOR_NAVIGATION_KIND_FLOOR = 1
OUTDOOR_NAVIGATION_KIND_BARRIER = 2
OUTDOOR_NAVIGATION_FLAG_WALKABLE = 0x01
OUTDOOR_NAVIGATION_FLAG_BLOCKING = 0x02
OUTDOOR_NAVIGATION_FLAG_DYNAMIC = 0x04
OUTDOOR_NAVIGATION_MIN_WALKABLE_NORMAL_Z = 0.65
OUTDOOR_RENDER_MAGIC = b"OYMREN1\0"
OUTDOOR_RENDER_VERSION = 1
OUTDOOR_RENDER_HEADER_SIZE = 48
OUTDOOR_RENDER_RECORD_SIZE = 24
OUTDOOR_RENDER_CELL_SIZE = 4096
OUTDOOR_RENDER_FLAG_DYNAMIC = 0x01
OUTDOOR_RENDER_FLAG_TRANSLUCENT = 0x02
OUTDOOR_LIGHTING_MAGIC = b"OYMLIT1\0"
OUTDOOR_LIGHTING_VERSION = 3
OUTDOOR_LIGHTING_HEADER_SIZE = 96
OUTDOOR_LIGHTING_PAGE_RECORD_SIZE = 16
OUTDOOR_LIGHTING_FACE_RECORD_SIZE = 24
OUTDOOR_LIGHTING_VERTEX_RECORD_SIZE = 12
OUTDOOR_LIGHTING_LIGHT_RECORD_SIZE = 80
OUTDOOR_LIGHTING_ATLAS_MAX_WIDTH = 1024
OUTDOOR_LIGHTING_FACE_HAS_LIGHTMAP = 0x01
OUTDOOR_LIGHTING_LIGHT_POINT = 0
OUTDOOR_LIGHTING_LIGHT_DIRECTIONAL = 1
OUTDOOR_LIGHTING_LIGHT_OBJECTS = 0x01
OUTDOOR_LIGHTING_LIGHT_FAST_OBJECTS = 0x02
OUTDOOR_LIGHTING_LIGHT_STATIC_OBJECT_ELIGIBLE = 0x04
OUTDOOR_LIGHTING_LIGHT_GLOBAL_OBJECT = 0x20
LT_SURFACE_FLAG_INVISIBLE = 0x00000004
LT_SURFACE_FLAG_TRANSPARENT = 0x00000008
LT_SURFACE_FLAG_NOT_A_STEP = 0x00400000
MM9_MECHANISM_CLASS_KINDS = {
    "Door": "linear_door",
    "RotatingDoor": "rotating_door",
    "WeightedLift": "weighted_lift",
    "Button": "linear_button",
    "Switch": "rotating_switch",
    "RotatingBrush": "rotating_brush",
    "InvisibleBrush": "collision_volume",
}
MM9_INTERACTIVE_MECHANISM_KINDS = {
    "linear_door",
    "linear_button",
    "weighted_lift",
    "rotating_door",
    "rotating_switch",
    "rotating_brush",
}
MM9_DESTRUCTIBLE_CLASS_NAMES = {"DestructableBrush", "DestructibleBrush"}
MM9_DESTRUCTIBLE_TRIGGER_MESSAGES = {
    "damageon": "damage_on",
    "damageoff": "damage_off",
    "damage": "damage",
    "destroy": "destroy",
    "remove": "remove",
}


class DatParseError(RuntimeError):
    pass


class BinaryReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0

    def tell(self) -> int:
        return self.offset

    def seek(self, offset: int) -> None:
        if offset < 0 or offset > len(self.data):
            raise DatParseError(f"seek out of range: {offset}")
        self.offset = offset

    def skip(self, byte_count: int) -> None:
        self.seek(self.offset + byte_count)

    def read(self, byte_count: int) -> bytes:
        if byte_count < 0 or self.offset + byte_count > len(self.data):
            raise DatParseError(f"read out of range at {self.offset} size {byte_count}")
        result = self.data[self.offset:self.offset + byte_count]
        self.offset += byte_count
        return result

    def unpack(self, fmt: str) -> tuple[Any, ...]:
        size = struct.calcsize(fmt)
        return struct.unpack_from(fmt, self.read(size))

    def u8(self) -> int:
        return self.unpack("<B")[0]

    def u16(self) -> int:
        return self.unpack("<H")[0]

    def u32(self) -> int:
        return self.unpack("<I")[0]

    def i32(self) -> int:
        return self.unpack("<i")[0]

    def f32(self) -> float:
        return self.unpack("<f")[0]

    def vec3(self) -> tuple[float, float, float]:
        return self.unpack("<fff")

    def quat(self) -> tuple[float, float, float, float]:
        return self.unpack("<ffff")

    def string(self, length_is_short: bool = True) -> str:
        length = self.u16() if length_is_short else self.u32()
        raw = self.read(length)
        return raw.split(b"\0", 1)[0].decode("ascii", errors="replace")

    def null_string(self) -> str:
        start = self.offset
        while self.offset < len(self.data) and self.data[self.offset] != 0:
            self.offset += 1
        raw = self.data[start:self.offset]
        if self.offset < len(self.data):
            self.offset += 1
        return raw.decode("ascii", errors="replace")


@dataclass
class WorldInfo:
    properties: str
    light_map_grid_size: float
    extents_min: tuple[float, float, float]
    extents_max: tuple[float, float, float]


@dataclass
class Surface:
    uv_origin: tuple[float, float, float]
    uv_u: tuple[float, float, float]
    uv_v: tuple[float, float, float]
    texture_index: int
    unknown: int
    flags: int
    unknown2: int
    texture_flags: int
    effect_name: str = ""
    effect_param: str = ""


@dataclass
class Plane:
    normal: tuple[float, float, float]
    distance: float


@dataclass
class DiskVert:
    vertex_index: int
    dummy: bytes


@dataclass
class Poly:
    center: tuple[float, float, float]
    lightmap_width: int
    lightmap_height: int
    unknown_flag: int
    unknown_list: list[int]
    surface_index: int
    plane_index: int
    disk_verts: list[DiskVert]
    lightmap_pixels_bgra: list[int] = field(default_factory=list)


@dataclass
class UserPortal:
    name: str
    center: tuple[float, float, float]
    dims: tuple[float, float, float]
    unknown_int_1: int
    unknown_int_2: int
    unknown_short: int


@dataclass
class LeafPortalData:
    portal_id: int
    contents: bytes


@dataclass
class LeafPolygonRef:
    world_model_index: int
    poly_index: int
    raw_entry: int


@dataclass
class WorldLeaf:
    count: int
    index: int | None
    portal_data: list[LeafPortalData]
    polygon_entries: list[int]
    unknown: int

    def polygon_refs(self) -> list[LeafPolygonRef]:
        return [
            LeafPolygonRef(
                world_model_index=entry & 0xFFFF,
                poly_index=entry >> 16,
                raw_entry=entry,
            )
            for entry in self.polygon_entries
        ]

    def polygon_ref_indices(self) -> list[int]:
        return [polygon_ref.poly_index for polygon_ref in self.polygon_refs()]


@dataclass
class WorldNode:
    poly_index: int
    leaf_index: int
    front_index: int
    back_index: int


@dataclass
class WorldBsp:
    name: str
    textures: list[str]
    points: list[tuple[float, float, float]]
    point_normals: list[tuple[float, float, float]]
    planes: list[Plane]
    surfaces: list[Surface]
    polies: list[Poly]
    leaves: list[WorldLeaf]
    nodes: list[WorldNode]
    user_portals: list[UserPortal]
    min_box: tuple[float, float, float]
    max_box: tuple[float, float, float]
    world_translation: tuple[float, float, float]
    root_node_index: int
    section_count: int
    counts: dict[str, int]
    pblock_table: "PBlockTableSummary"


@dataclass
class PBlockTableSummary:
    dim_a: int
    dim_b: int
    dim_c: int
    min_box: tuple[float, float, float]
    max_box: tuple[float, float, float]
    record_count: int


@dataclass
class ObjectProperty:
    name: str
    code: int
    flags: int
    declared_data_length: int
    raw_data: bytes
    value: Any
    decoded: bool = True
    decode_error: str = ""


@dataclass
class WorldObject:
    name: str
    data_length: int
    properties: list[ObjectProperty]
    trailing_data: bytes = b""


@dataclass(frozen=True)
class Mm9AuthoredFogState:
    enabled: bool
    near_distance: int
    far_distance: int
    color: tuple[int, int, int]


@dataclass
class DatWorld:
    path: Path
    version: int
    object_data_pos: int
    render_data_pos: int
    world_model_pos: int
    world_info: WorldInfo
    world_models: list[WorldBsp]
    objects: list[WorldObject]
    lightmap_stats: dict[str, int] = field(default_factory=dict)

    @property
    def light_animation_data_pos(self) -> int:
        # The second v66 header offset was historically called render_data_pos in this importer. Local MM9 DATs
        # identify it as the legacy LightAnim_BASE payload instead of the later LithTech render-world stream.
        return self.render_data_pos


@dataclass
class PartyStartPoint:
    start_index: int
    source_object_index: int
    source_name: str
    source_position_lt: list[float]
    position: tuple[int, int, int]
    source_rotation_lt: list[float]
    direction_yaw_units: int
    direction_degrees: float
    team_number: int
    player_number: int
    move_player_to_floor: bool


@dataclass
class ExportedLight:
    source_object_index: int
    source_class: str
    source_name: str
    source_position_lt: tuple[float, float, float]
    position: tuple[int, int, int]
    source_radius_lt: float
    radius: int
    color: tuple[int, int, int]
    effective_color: tuple[int, int, int]
    light_type: str
    light_objects: bool
    fast_light_objects: bool
    static_object_light_eligible: bool
    global_object_light: bool
    light_group: str
    source_rotation_lt: tuple[float, float, float, float]
    fov_degrees: float
    brightness_scale: float
    object_brightness_scale: float
    cast_shadows: bool
    clip_light: bool


@dataclass
class LightmapAtlasRect:
    page_index: int
    x: int
    y: int
    width: int
    height: int


@dataclass
class LightmapAtlasPage:
    width: int
    height: int
    pixels_bgra: list[int]


@dataclass
class OutdoorLightingFace:
    bmodel_index: int
    face_index: int
    page_index: int
    has_lightmap: bool
    vertex_uvs: list[tuple[float, float]]
    vertex_colors_abgr: list[int]


@dataclass
class OdmVertex:
    x: int
    y: int
    z: int


@dataclass
class OdmFace:
    vertex_indices: list[int]
    texture_us: list[int]
    texture_vs: list[int]
    texture_alias: str
    bitmap_index: int
    polygon_type: int
    attributes: int
    plane_normal: tuple[int, int, int]
    plane_distance: int
    reserved: int = 0


@dataclass
class OdmBModel:
    name: str
    source_model_index: int = 0
    source_model_name: str = ""
    source_world_translation_lt: tuple[float, float, float] = (0.0, 0.0, 0.0)
    source_world_info_flags: int = 0
    perception_difficulty: int | None = None
    vertices: list[OdmVertex] = field(default_factory=list)
    faces: list[OdmFace] = field(default_factory=list)
    source_poly_for_face: list[int] = field(default_factory=list)
    source_surface_for_face: list[int] = field(default_factory=list)
    source_surface_flags_for_face: list[int] = field(default_factory=list)
    source_texture_index_for_face: list[int] = field(default_factory=list)
    source_barrel_liquid_for_face: list[bool] = field(default_factory=list)
    source_texture_flags_for_face: list[int] = field(default_factory=list)
    source_collision_role_for_face: list[str] = field(default_factory=list)
    source_render_role_for_face: list[str] = field(default_factory=list)


@dataclass
class OdmEntity:
    name: str
    decoration_list_id: int
    ai_attributes: int
    x: int
    y: int
    z: int
    facing: int
    event_id_primary: int = 0
    event_id_secondary: int = 0
    variable_primary: int = 0
    variable_secondary: int = 0
    special_trigger: int = 0
    initial_decoration_flag: int = 0


@dataclass
class BakedModelInstance:
    source_object_index: int
    source_class: str
    source_name: str
    source_model: str
    source_skin: str
    bmodel_index: int
    bmodel_name: str
    kind: str
    destructible: bool = False
    placement_kind: str = ""
    source_position_lt: list[float] = field(default_factory=list)
    bake_position_lt: list[float] = field(default_factory=list)
    visual_offset_lt: list[float] = field(default_factory=list)
    variant_index: int = 0


@dataclass(frozen=True)
class FaceRole:
    attributes: int
    collision_role: str
    render_role: str


@dataclass(frozen=True)
class Mm9NpcReplacement:
    source_number: int
    object_class: str
    role: str
    hit_points: int
    legacy_actor_id: int
    height: int
    radius: int


@dataclass(frozen=True)
class Mm9MonsterReplacement:
    source_number: int
    object_class: str
    source_model: str
    source_skins: tuple[str, ...]
    display_name: str
    runtime_monster_id: int
    hit_points: int
    hostility: int
    move_speed: int
    height: int
    radius: int
    source_rank: str = ""
    source_variant: str = ""


@dataclass(frozen=True)
class LtFloorTriangle:
    vertices: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


@dataclass(frozen=True)
class LtModelBounds:
    min: tuple[float, float, float]
    max: tuple[float, float, float]


@dataclass(frozen=True)
class LtModelPlacementInfo:
    bounds: LtModelBounds
    binding_origin: tuple[float, float, float]
    binding_extents: tuple[float, float, float]


@dataclass(frozen=True)
class LtPlacementSupport:
    source_object_index: int
    source_name: str
    center: tuple[float, float, float]
    half_extents: tuple[float, float, float]


@dataclass
class BakedModelWorkItem:
    object_index: int
    source_class: str
    source_name: str
    source_model: str
    source_skin: str
    position_lt: list[float]
    raw_position_lt: list[float]
    rotation_lt: list[float]
    uniform_scale: float
    visual_offset_lt: tuple[float, float, float]
    placement_kind: str
    abc_model: AbcModel
    placement_info: LtModelPlacementInfo | None
    plant_or_tree_source: bool
    move_to_floor: bool
    solid: bool
    ray_hit: bool
    variant_index: int = 0


def read_world_tree_layout(reader: BinaryReader, current_byte: int, current_bit: int) -> tuple[int, int]:
    if current_bit == 8:
        current_byte = reader.u8()
        current_bit = 0

    subdivide = (current_byte & (1 << current_bit)) != 0
    current_bit += 1

    if subdivide:
        for _ in range(4):
            current_byte, current_bit = read_world_tree_layout(reader, current_byte, current_bit)

    return current_byte, current_bit


def read_world_tree(reader: BinaryReader) -> None:
    reader.vec3()
    reader.vec3()
    reader.u32()
    reader.u32()
    read_world_tree_layout(reader, 0, 8)


def read_leaf(reader: BinaryReader) -> WorldLeaf:
    count = reader.u16()
    index = None
    portal_data = []
    if count == 0xFFFF:
        index = reader.u16()
    else:
        for _ in range(count):
            portal_id = reader.u16()
            size = reader.u16()
            portal_data.append(LeafPortalData(portal_id=portal_id, contents=reader.read(size)))

    polygon_count = reader.u32()
    polygon_entries = [reader.u32() for _ in range(polygon_count)]
    unknown = reader.u32()
    return WorldLeaf(
        count=count,
        index=index,
        portal_data=portal_data,
        polygon_entries=polygon_entries,
        unknown=unknown,
    )


def read_surface(reader: BinaryReader) -> Surface:
    uv_origin = reader.vec3()
    uv_u = reader.vec3()
    uv_v = reader.vec3()
    texture_index = reader.u16()
    unknown = reader.u32()
    flags = reader.u32()
    unknown2 = reader.u32()
    use_effects = reader.u8()
    effect_name = ""
    effect_param = ""
    if use_effects > 0:
        effect_name = reader.string()
        effect_param = reader.string()
    texture_flags = reader.u16()
    return Surface(
        uv_origin=uv_origin,
        uv_u=uv_u,
        uv_v=uv_v,
        texture_index=texture_index,
        unknown=unknown,
        flags=flags,
        unknown2=unknown2,
        texture_flags=texture_flags,
        effect_name=effect_name,
        effect_param=effect_param,
    )


def read_poly(reader: BinaryReader, vertex_count: int) -> Poly:
    center = reader.vec3()
    lightmap_width = reader.u16()
    lightmap_height = reader.u16()
    unknown_flag = reader.u16()
    unknown_list = [reader.u16() for _ in range(unknown_flag * 2)]
    surface_index = reader.u16()
    plane_index = reader.u16()
    disk_verts = []
    for _ in range(vertex_count):
        disk_verts.append(DiskVert(vertex_index=reader.u16(), dummy=reader.read(3)))
    return Poly(
        center=center,
        lightmap_width=lightmap_width,
        lightmap_height=lightmap_height,
        unknown_flag=unknown_flag,
        unknown_list=unknown_list,
        surface_index=surface_index,
        plane_index=plane_index,
        disk_verts=disk_verts,
    )


def read_node(reader: BinaryReader) -> WorldNode:
    return WorldNode(
        poly_index=reader.u32(),
        leaf_index=reader.u16(),
        front_index=reader.u32(),
        back_index=reader.u32(),
    )


def read_user_portal(reader: BinaryReader) -> UserPortal:
    name = reader.string()
    unknown_int_1 = reader.u32()
    unknown_int_2 = 0
    unknown_short = reader.u16()
    center = reader.vec3()
    dims = reader.vec3()
    return UserPortal(
        name=name,
        center=center,
        dims=dims,
        unknown_int_1=unknown_int_1,
        unknown_int_2=unknown_int_2,
        unknown_short=unknown_short,
    )


def skip_pblock_table(reader: BinaryReader) -> PBlockTableSummary:
    dim_a = reader.u32()
    dim_b = reader.u32()
    dim_c = reader.u32()
    min_box = reader.vec3()
    max_box = reader.vec3()
    record_count = dim_a * dim_b * dim_c
    if record_count > 10_000_000:
        raise DatParseError(f"implausible pblock record count: {record_count}")
    for _ in range(record_count):
        size = reader.u16()
        reader.u16()
        reader.skip(size * 6)
    return PBlockTableSummary(
        dim_a=dim_a,
        dim_b=dim_b,
        dim_c=dim_c,
        min_box=min_box,
        max_box=max_box,
        record_count=record_count,
    )


def read_world_bsp(reader: BinaryReader) -> WorldBsp:
    world_info_flags = reader.u32()
    unknown_value = reader.u32()
    world_name = reader.string()

    count_names = [
        "point_count",
        "plane_count",
        "surface_count",
        "user_portal_count",
        "poly_count",
        "leaf_count",
        "vert_count",
        "total_vis_list_size",
        "leaf_list_count",
        "node_count",
    ]
    counts = {name: reader.u32() for name in count_names}
    counts["world_info_flags"] = world_info_flags
    counts["unknown_value"] = unknown_value
    counts["unknown_value_2"] = reader.u32()
    counts["unknown_value_3"] = reader.u32()

    min_box = reader.vec3()
    max_box = reader.vec3()
    world_translation = reader.vec3()

    name_length = reader.u32()
    texture_count = reader.u32()
    counts["name_length"] = name_length
    counts["texture_count"] = texture_count
    textures = [reader.null_string() for _ in range(texture_count)]

    poly_vertex_counts = []
    for _ in range(counts["poly_count"]):
        poly_vertex_counts.append(reader.u8() + reader.u8())

    leaves = [read_leaf(reader) for _ in range(counts["leaf_count"])]

    planes = []
    for _ in range(counts["plane_count"]):
        planes.append(Plane(normal=reader.vec3(), distance=reader.f32()))

    surfaces = [read_surface(reader) for _ in range(counts["surface_count"])]
    polies = [read_poly(reader, poly_vertex_counts[index]) for index in range(counts["poly_count"])]

    nodes = [read_node(reader) for _ in range(counts["node_count"])]

    user_portals = [read_user_portal(reader) for _ in range(counts["user_portal_count"])]

    points = []
    point_normals = []
    for _ in range(counts["point_count"]):
        points.append(reader.vec3())
        point_normals.append(reader.vec3())

    pblock_table = skip_pblock_table(reader)
    root_node_index = reader.u32()
    section_count = reader.u32()
    counts["root_node_index"] = root_node_index
    counts["section_count"] = section_count

    return WorldBsp(
        name=world_name,
        textures=textures,
        points=points,
        point_normals=point_normals,
        planes=planes,
        surfaces=surfaces,
        polies=polies,
        leaves=leaves,
        nodes=nodes,
        user_portals=user_portals,
        min_box=min_box,
        max_box=max_box,
        world_translation=world_translation,
        root_node_index=root_node_index,
        section_count=section_count,
        counts=counts,
        pblock_table=pblock_table,
    )


def rgb555_to_bgra(color: int) -> int:
    value = color & 0x7FFF
    red5 = (value >> 10) & 0x1F
    green5 = (value >> 5) & 0x1F
    blue5 = value & 0x1F
    red = (red5 << 3) | (red5 >> 2)
    green = (green5 << 3) | (green5 >> 2)
    blue = (blue5 << 3) | (blue5 >> 2)
    return 0xFF000000 | (red << 16) | (green << 8) | blue


def decode_mm9_v66_lightmap(data: bytes) -> list[int]:
    pixels: list[int] = []
    offset = 0

    while offset < len(data):
        if offset + 2 > len(data):
            raise DatParseError("MM9 v66 lightmap ends inside an RGB555 word")
        color = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        repeat_count = 1
        if color & 0x8000:
            if offset >= len(data):
                raise DatParseError("MM9 v66 lightmap run is missing its repeat count")
            repeat_count = data[offset]
            offset += 1
        pixels.extend([rgb555_to_bgra(color)] * repeat_count)

    return pixels


def read_mm9_v66_base_lightmaps(
    reader: BinaryReader,
    offset: int,
    world_models: list[WorldBsp],
) -> dict[str, int]:
    stats = {
        "lightmap_affected_polies": 0,
        "lightmap_frames": 0,
        "lightmap_compressed_bytes": 0,
        "lightmap_decoded_texels": 0,
        "lightmap_base_polies": 0,
    }
    if offset == 0:
        return stats

    reader.seek(offset)
    affected_poly_count = reader.u32()
    frame_count = reader.u32()
    frame_data_bytes = reader.u32()
    first_animation_poly_count = reader.u32()
    animation_count = reader.u32()
    if animation_count != 1:
        raise DatParseError(f"expected one MM9 v66 light animation, got {animation_count}")

    animation_name = reader.string()
    if animation_name != "LightAnim_BASE":
        raise DatParseError(f"expected LightAnim_BASE, got {animation_name!r}")
    reader.u32()
    animation_frame_count = reader.u32()
    poly_ref_count = reader.u32()
    if poly_ref_count != first_animation_poly_count or animation_frame_count != frame_count:
        raise DatParseError("MM9 v66 light animation header counts disagree")

    poly_refs = [(reader.u16(), reader.u16()) for _ in range(poly_ref_count)]
    compressed_bytes = 0
    decoded_texels = 0
    for lightmap_index in range(animation_frame_count * poly_ref_count):
        compressed_size = reader.u32()
        compressed_data = reader.read(compressed_size)
        pixels = decode_mm9_v66_lightmap(compressed_data)
        compressed_bytes += compressed_size
        decoded_texels += len(pixels)
        world_model_index, poly_index = poly_refs[lightmap_index % poly_ref_count]
        if world_model_index >= len(world_models) or poly_index >= len(world_models[world_model_index].polies):
            raise DatParseError("MM9 v66 lightmap polygon reference is out of range")
        poly = world_models[world_model_index].polies[poly_index]
        expected_texels = poly.lightmap_width * poly.lightmap_height
        if len(pixels) != expected_texels:
            raise DatParseError(
                f"MM9 v66 lightmap size mismatch for model {world_model_index} poly {poly_index}: "
                f"decoded {len(pixels)}, expected {expected_texels}"
            )
        if lightmap_index < poly_ref_count:
            poly.lightmap_pixels_bgra = pixels

    if affected_poly_count != poly_ref_count or compressed_bytes != frame_data_bytes:
        raise DatParseError("MM9 v66 light animation payload counts disagree")
    if reader.tell() != len(reader.data):
        raise DatParseError("unparsed data follows the MM9 v66 light animation payload")

    stats.update({
        "lightmap_affected_polies": affected_poly_count,
        "lightmap_frames": frame_count,
        "lightmap_compressed_bytes": compressed_bytes,
        "lightmap_decoded_texels": decoded_texels,
        "lightmap_base_polies": poly_ref_count,
    })
    return stats


def read_property_value(reader: BinaryReader, code: int) -> Any:
    if code == 0:
        return reader.string()
    if code in (1, 2):
        return list(reader.vec3())
    if code == 3:
        return reader.f32()
    if code == 5:
        return reader.u8()
    if code in (4, 6, 9):
        return reader.u32()
    if code == 7:
        return list(reader.quat())
    raise DatParseError(f"unknown object property code {code}")


def decode_property_value(raw_data: bytes, code: int) -> tuple[Any, bool, str]:
    reader = BinaryReader(raw_data)
    try:
        value = read_property_value(reader, code)
    except DatParseError as exc:
        return None, False, str(exc)

    if reader.tell() > len(raw_data):
        return None, False, f"property decoder overread code {code}"
    return value, True, ""


def normalize_mm9_property_value(name: str, code: int, raw_data: bytes, value: Any) -> Any:
    """Decode shipped MM9 properties whose registered LithTech type disagrees with their authored bytes."""
    if name.casefold() == "traveldays" and code == 6 and len(raw_data) == 4:
        travel_days = struct.unpack("<f", raw_data)[0]
        if math.isfinite(travel_days) and travel_days.is_integer():
            return int(travel_days)
    return value


def read_world_objects(reader: BinaryReader) -> list[WorldObject]:
    objects = []
    count = reader.u32()
    for _ in range(count):
        object_start = reader.tell()
        data_length = reader.u16()
        object_end = reader.tell() + data_length
        name = reader.string()
        property_count = reader.u32()
        properties = []
        for _ in range(property_count):
            prop_name = reader.string()
            code = reader.u8()
            flags = reader.u32()
            declared_data_length = reader.u16()
            value_start = reader.tell()
            decoded = True
            decode_error = ""
            try:
                value = read_property_value(reader, code)
            except DatParseError as exc:
                decoded = False
                decode_error = str(exc)
                value = None
                available_length = max(0, min(declared_data_length, object_end - value_start))
                reader.seek(value_start)
                reader.skip(available_length)
            raw_data = reader.data[value_start:reader.tell()]
            if decoded:
                value = normalize_mm9_property_value(prop_name, code, raw_data, value)
            properties.append(ObjectProperty(
                name=prop_name,
                code=code,
                flags=flags,
                declared_data_length=declared_data_length,
                raw_data=raw_data,
                value=value,
                decoded=decoded,
                decode_error=decode_error,
            ))
        if reader.tell() > object_end:
            raise DatParseError(
                f"object {name} at {object_start} overread declared payload by {reader.tell() - object_end} bytes"
            )
        trailing_data = reader.read(object_end - reader.tell()) if reader.tell() < object_end else b""
        objects.append(WorldObject(name=name, data_length=data_length, properties=properties, trailing_data=trailing_data))
    return objects


def read_dat_world(path: Path) -> DatWorld:
    reader = BinaryReader(path.read_bytes())
    version = reader.u32()
    if version != DAT_VERSION_LT2:
        raise DatParseError(f"expected DAT v66, got {version}")

    object_data_pos = reader.u32()
    render_data_pos = reader.u32()
    reader.skip(8 * 4)

    world_info = WorldInfo(
        properties=reader.string(length_is_short=False),
        light_map_grid_size=reader.f32(),
        extents_min=reader.vec3(),
        extents_max=reader.vec3(),
    )
    read_world_tree(reader)
    world_model_pos = reader.tell()

    objects: list[WorldObject] = []
    try:
        reader.seek(object_data_pos)
        objects = read_world_objects(reader)
    except DatParseError as exc:
        print(f"warning: could not parse object data at {object_data_pos}: {exc}")

    reader.seek(world_model_pos)
    world_model_count = reader.u32()
    world_models = []
    for _ in range(world_model_count):
        next_world_model_pos = reader.u32()
        reader.skip(32)
        model = read_world_bsp(reader)
        world_models.append(model)
        if model.section_count > 0:
            reader.seek(next_world_model_pos)

    lightmap_stats = read_mm9_v66_base_lightmaps(reader, render_data_pos, world_models)

    return DatWorld(
        path=path,
        version=version,
        object_data_pos=object_data_pos,
        render_data_pos=render_data_pos,
        world_model_pos=world_model_pos,
        world_info=world_info,
        world_models=world_models,
        objects=objects,
        lightmap_stats=lightmap_stats,
    )


def lt_to_odm(vertex: tuple[float, float, float], scale: float) -> OdmVertex:
    # LithTech v66 uses X/Z as the horizontal plane and Y as height.
    return OdmVertex(
        x=int(round(vertex[0] * scale)),
        y=int(round(vertex[2] * scale)),
        z=int(round(vertex[1] * scale)),
    )


def lt_vec_to_odm_tuple(vertex: list[float] | tuple[float, float, float], scale: float) -> tuple[int, int, int]:
    return (
        int(round(vertex[0] * scale)),
        int(round(vertex[2] * scale)),
        int(round(vertex[1] * scale)),
    )


def lt_rotation_to_openyamm_yaw_degrees(rotation: list[float] | tuple[float, ...]) -> float:
    if len(rotation) < 2:
        return 0.0

    yaw_degrees = -math.degrees(float(rotation[1]))
    return yaw_degrees % 360.0


def lt_rotation_to_openyamm_yaw_units(rotation: list[float] | tuple[float, ...]) -> int:
    return int(round(lt_rotation_to_openyamm_yaw_degrees(rotation) * 2048.0 / 360.0)) % 2048


def quat_multiply(
    lhs: tuple[float, float, float, float],
    rhs: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    lx, ly, lz, lw = lhs
    rx, ry, rz, rw = rhs
    return (
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
        lw * rw - lx * rx - ly * ry - lz * rz,
    )


def axis_angle_quat(axis: tuple[float, float, float], angle: float) -> tuple[float, float, float, float]:
    half_angle = angle * 0.5
    sin_half = math.sin(half_angle)
    return (
        axis[0] * sin_half,
        axis[1] * sin_half,
        axis[2] * sin_half,
        math.cos(half_angle),
    )


def normalize_quat(quat: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    length = math.sqrt(sum(component * component for component in quat))
    if length <= 0.000001:
        return (0.0, 0.0, 0.0, 1.0)
    return tuple(component / length for component in quat)


def lt_rotation_to_odm_quat(rotation: list[float] | tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    if len(rotation) != 4:
        return (0.0, 0.0, 0.0, 1.0)

    rx, ry, rz, rw = (float(rotation[0]), float(rotation[1]), float(rotation[2]), float(rotation[3]))
    if abs(rx) < 0.000001 and abs(ry) < 0.000001 and abs(rz) < 0.000001 and abs(rw) < 0.000001:
        return (0.0, 0.0, 0.0, 1.0)

    length = math.sqrt(rx * rx + ry * ry + rz * rz + rw * rw)
    if abs(length - 1.0) < 0.001 and abs(rw) > 0.000001:
        return normalize_quat((rx, rz, ry, rw))

    # MM9 DAT object Rotation is stored as LithTech Euler radians in a four-float property, not as a unit quaternion.
    # LithTech uses Y as up; ODM/OpenYAMM uses Z as up after the X/Z/Y coordinate conversion. The swap reverses
    # handedness, so source yaw around LithTech Y maps to negative yaw around ODM Z.
    qx = axis_angle_quat((1.0, 0.0, 0.0), rx)
    qy = axis_angle_quat((0.0, 1.0, 0.0), rz)
    qz = axis_angle_quat((0.0, 0.0, 1.0), -ry)
    return normalize_quat(quat_multiply(qz, quat_multiply(qy, qx)))


def vec_sub(left: OdmVertex, right: OdmVertex) -> tuple[float, float, float]:
    return (float(left.x - right.x), float(left.y - right.y), float(left.z - right.z))


def vec_cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def vec_dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def vec_sub_lt(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def vec_len(value: tuple[float, float, float]) -> float:
    return math.sqrt(vec_dot(value, value))


def clamp_i16(value: int) -> int:
    return max(-32768, min(32767, value))


def clamp_i32(value: int) -> int:
    return max(I32_MIN, min(I32_MAX, value))


def uv_float_to_i16(value: float, texture_extent: int) -> int:
    if not math.isfinite(value):
        return 0

    return clamp_i16(int(round(value * texture_extent)))


def compute_plane(vertices: list[OdmVertex], indices: list[int]) -> tuple[tuple[int, int, int], int]:
    if len(indices) < 3:
        return (0, 0, 0), 0
    unit = compute_unit_normal(vertices, indices)
    if unit is None:
        return (0, 0, 0), 0
    a = vertices[indices[0]]
    distance = unit[0] * a.x + unit[1] * a.y + unit[2] * a.z
    return (
        int(round(unit[0] * OUTDOOR_FACE_PLANE_SCALE)),
        int(round(unit[1] * OUTDOOR_FACE_PLANE_SCALE)),
        int(round(unit[2] * OUTDOOR_FACE_PLANE_SCALE)),
    ), int(round(distance * OUTDOOR_FACE_PLANE_SCALE))


def compute_unit_normal(vertices: list[OdmVertex], indices: list[int]) -> tuple[float, float, float] | None:
    if len(indices) < 3:
        return None
    a = vertices[indices[0]]
    for index in range(1, len(indices) - 1):
        b = vertices[indices[index]]
        c = vertices[indices[index + 1]]
        normal = vec_cross(vec_sub(b, a), vec_sub(c, a))
        length = vec_len(normal)
        if length > 0.0001:
            return (normal[0] / length, normal[1] / length, normal[2] / length)
    return None


def transformed_lt_plane_normal(plane: Plane) -> tuple[float, float, float] | None:
    normal = (plane.normal[0], plane.normal[2], plane.normal[1])
    length = vec_len(normal)
    if length <= 0.0001:
        return None
    return (normal[0] / length, normal[1] / length, normal[2] / length)


def classify_polygon_type(vertices: list[OdmVertex], indices: list[int]) -> int:
    if len(indices) < 3:
        return 0
    normal = compute_unit_normal(vertices, indices)
    if normal is None:
        return 0
    normal_z = normal[2]
    if normal_z >= OUTDOOR_FLAT_FACE_NORMAL_Z:
        return OUTDOOR_POLYGON_FLOOR
    if normal_z >= OUTDOOR_SLOPED_FACE_NORMAL_Z:
        return OUTDOOR_POLYGON_IN_BETWEEN_FLOOR_AND_WALL
    if normal_z <= -OUTDOOR_FLAT_FACE_NORMAL_Z:
        return OUTDOOR_POLYGON_CEILING
    if normal_z <= -OUTDOOR_SLOPED_FACE_NORMAL_Z:
        return OUTDOOR_POLYGON_IN_BETWEEN_CEILING_AND_WALL
    return OUTDOOR_POLYGON_VERTICAL_WALL


def dot3(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def opq_to_pixel_uv(
    vertex: tuple[float, float, float],
    origin: tuple[float, float, float],
    axis_u: tuple[float, float, float],
    axis_v: tuple[float, float, float],
    texture_width: int,
    texture_height: int,
) -> tuple[int, int]:
    point = (vertex[0] - origin[0], vertex[1] - origin[1], vertex[2] - origin[2])
    u = dot3(point, axis_u) / max(1, texture_width)
    v = dot3(point, axis_v) / max(1, texture_height)
    return clamp_i16(int(round(u * texture_width))), clamp_i16(int(round(v * texture_height)))


def texture_key(name: str) -> str:
    return name.replace("\\", "/").lower()


def build_texture_size_index(extracted_root: Path | None) -> dict[str, tuple[int, int, Path]]:
    if extracted_root is None:
        return {}

    result: dict[str, tuple[int, int, Path]] = {}
    basename_entries: dict[str, tuple[int, int, Path] | None] = {}

    roots = [
        (extracted_root / "TEXTURES" / "TEXTURES", "textures"),
        (extracted_root / "SKINS" / "SKINS", "skins"),
        (extracted_root / "SPRITETEXTURES" / "SPRITETEXTURES", "spritetextures"),
    ]
    for texture_root, virtual_prefix in roots:
        if not texture_root.exists():
            continue
        for path in sorted(texture_root.rglob("*.dtx")):
            if not path.is_file():
                continue
            with path.open("rb") as handle:
                header = handle.read(12)
            if len(header) < 12:
                continue
            file_type, version, width, height = struct.unpack_from("<iiHH", header)
            if file_type != 0 or version != -5 or width <= 0 or height <= 0:
                continue
            entry = (width, height, path)
            rel = path.relative_to(texture_root).as_posix()
            rel_no_ext = str(Path(rel).with_suffix("")).replace("\\", "/")
            for key in [
                rel_no_ext,
                rel,
                f"{virtual_prefix}/{rel_no_ext}",
                f"{virtual_prefix}/{rel}",
            ]:
                result[texture_key(key)] = entry

            stem = Path(rel).stem
            basename_key = texture_key(f"basename/{stem}")
            if basename_key in basename_entries and basename_entries[basename_key] != entry:
                basename_entries[basename_key] = None
            else:
                basename_entries[basename_key] = entry

            if virtual_prefix == "spritetextures":
                sprite_stem = re.sub(r"_[0-9]+$", "", stem)
                result.setdefault(texture_key(f"spriteframe/{sprite_stem}"), entry)

    for key, entry in basename_entries.items():
        if entry is not None:
            result[key] = entry
    return result


def parse_spr_frame_paths(path: Path) -> tuple[int, list[str]]:
    data = path.read_bytes()
    if len(data) < MM9_SPR_HEADER_SIZE:
        return 0, []

    frame_count, frames_per_second = struct.unpack_from("<II", data, 0)
    offset = MM9_SPR_HEADER_SIZE
    frames: list[str] = []
    for _ in range(frame_count):
        if offset + 2 > len(data):
            break
        frame_length = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        if frame_length <= 0 or offset + frame_length > len(data):
            break
        frame_path = data[offset:offset + frame_length].decode("ascii", errors="ignore")
        offset += frame_length
        if frame_path:
            frames.append(frame_path)
    return frames_per_second, frames


def build_sprite_animation_index(extracted_root: Path | None) -> dict[str, dict[str, Any]]:
    if extracted_root is None:
        return {}
    sprite_root = extracted_root / "SPRITES" / "SPRITES"
    if not sprite_root.exists():
        return {}

    result: dict[str, dict[str, Any]] = {}
    frame_owners: dict[str, dict[str, Any] | None] = {}
    for path in sorted(sprite_root.rglob("*.spr")):
        if not path.is_file():
            continue
        frames_per_second, frames = parse_spr_frame_paths(path)
        if not frames:
            continue
        rel = path.relative_to(sprite_root).as_posix()
        rel_no_ext = str(Path(rel).with_suffix("")).replace("\\", "/")
        entry = {
            "frames_per_second": frames_per_second,
            "frames": frames,
            "physical_path": str(path),
        }
        for key in [
            rel_no_ext,
            rel,
            f"sprites/{rel_no_ext}",
            f"sprites/{rel}",
            f"basename/{Path(rel).stem}",
        ]:
            result[texture_key(key)] = entry

        for frame_source in frames:
            frame_key = texture_key(frame_source)
            if frame_key not in frame_owners:
                frame_owners[frame_key] = entry
            elif frame_owners[frame_key] != entry:
                frame_owners[frame_key] = None

    for frame_key, entry in frame_owners.items():
        if entry is not None:
            result[f"frame/{frame_key}"] = entry
    return result


def read_dtx_header_metadata(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 164:
        return {}
    file_type, version, width, height = struct.unpack_from("<iiHH", data, 0)
    if file_type != 0 or version != -5 or width <= 0 or height <= 0:
        return {}
    mipmap_count, light_flag = struct.unpack_from("<HH", data, 12)
    dtx_flags = struct.unpack_from("<H", data, 16)[0]
    unknown = struct.unpack_from("<H", data, 18)[0]
    surface_flag = struct.unpack_from("<i", data, 20)[0]
    texture_group = data[24]
    mipmaps_used = data[25]
    if mipmaps_used == 0:
        mipmaps_used = mipmap_count
    bpp = data[26]
    non_s3tc_offset = data[27]
    ui_mipmap_offset = data[28]
    texture_priority = struct.unpack_from("<b", data, 29)[0]
    detail_scale = struct.unpack_from("<f", data, 30)[0]
    detail_angle = struct.unpack_from("<h", data, 34)[0]
    command_raw = data[36:164]
    command_string = ""
    if command_raw and command_raw[0] != 0:
        command_string = command_raw.split(b"\0", 1)[0].decode("ascii", errors="replace")
    return {
        "dtx_mipmap_count": mipmap_count,
        "dtx_light_flag": light_flag,
        "dtx_flags": dtx_flags,
        "dtx_unknown": unknown,
        "dtx_surface_flag": surface_flag,
        "dtx_texture_group": texture_group,
        "dtx_mipmaps_used": mipmaps_used,
        "dtx_bpp": bpp,
        "dtx_non_s3tc_offset": non_s3tc_offset,
        "dtx_ui_mipmap_offset": ui_mipmap_offset,
        "dtx_texture_priority": texture_priority,
        "dtx_detail_scale": detail_scale,
        "dtx_detail_angle": detail_angle,
        "dtx_command_string": command_string,
    }


def rgb565_to_rgb(value: int) -> tuple[int, int, int]:
    red = ((value >> 11) & 0x1F) * 255 // 31
    green = ((value >> 5) & 0x3F) * 255 // 63
    blue = (value & 0x1F) * 255 // 31
    return red, green, blue


def decode_dxt_colors(block: bytes) -> list[tuple[int, int, int, int]]:
    color_0, color_1 = struct.unpack_from("<HH", block, 0)
    red_0, green_0, blue_0 = rgb565_to_rgb(color_0)
    red_1, green_1, blue_1 = rgb565_to_rgb(color_1)
    colors = [
        (red_0, green_0, blue_0, 255),
        (red_1, green_1, blue_1, 255),
    ]
    if color_0 > color_1:
        colors.append(((2 * red_0 + red_1) // 3, (2 * green_0 + green_1) // 3, (2 * blue_0 + blue_1) // 3, 255))
        colors.append(((red_0 + 2 * red_1) // 3, (green_0 + 2 * green_1) // 3, (blue_0 + 2 * blue_1) // 3, 255))
    else:
        colors.append(((red_0 + red_1) // 2, (green_0 + green_1) // 2, (blue_0 + blue_1) // 2, 255))
        colors.append((0, 0, 0, 0))
    return colors


def decode_dxt1(data: bytes, width: int, height: int) -> bytearray:
    pixels = bytearray(width * height * 4)
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    offset = 0
    for block_y in range(blocks_y):
        for block_x in range(blocks_x):
            block = data[offset:offset + 8]
            offset += 8
            if len(block) < 8:
                return pixels
            colors = decode_dxt_colors(block)
            indices = struct.unpack_from("<I", block, 4)[0]
            for row in range(4):
                for col in range(4):
                    x = block_x * 4 + col
                    y = block_y * 4 + row
                    if x >= width or y >= height:
                        continue
                    color = colors[(indices >> (2 * (row * 4 + col))) & 0x03]
                    pixel_offset = (y * width + x) * 4
                    pixels[pixel_offset:pixel_offset + 4] = bytes(color)
    return pixels


def decode_dxt5_alpha(block: bytes) -> list[int]:
    alpha_0 = block[0]
    alpha_1 = block[1]
    alphas = [alpha_0, alpha_1]
    if alpha_0 > alpha_1:
        for index in range(1, 7):
            alphas.append(((7 - index) * alpha_0 + index * alpha_1) // 7)
    else:
        for index in range(1, 5):
            alphas.append(((5 - index) * alpha_0 + index * alpha_1) // 5)
        alphas.extend([0, 255])
    alpha_bits = int.from_bytes(block[2:8], "little")
    result = []
    for index in range(16):
        result.append(alphas[(alpha_bits >> (3 * index)) & 0x07])
    return result


def decode_dxt5(data: bytes, width: int, height: int) -> bytearray:
    pixels = bytearray(width * height * 4)
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    offset = 0
    for block_y in range(blocks_y):
        for block_x in range(blocks_x):
            block = data[offset:offset + 16]
            offset += 16
            if len(block) < 16:
                return pixels
            alphas = decode_dxt5_alpha(block[:8])
            colors = decode_dxt_colors(block[8:])
            indices = struct.unpack_from("<I", block, 12)[0]
            for row in range(4):
                for col in range(4):
                    x = block_x * 4 + col
                    y = block_y * 4 + row
                    if x >= width or y >= height:
                        continue
                    local_index = row * 4 + col
                    color = colors[(indices >> (2 * local_index)) & 0x03]
                    pixel_offset = (y * width + x) * 4
                    pixels[pixel_offset:pixel_offset + 4] = bytes((color[0], color[1], color[2], alphas[local_index]))
    return pixels


def make_placeholder_pixels(width: int, height: int, alias: str) -> bytearray:
    seed = sum(alias.encode("ascii", errors="ignore"))
    red = 64 + (seed * 37) % 160
    green = 64 + (seed * 17) % 160
    blue = 64 + (seed * 29) % 160
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            shade = 32 if ((x // 8) + (y // 8)) % 2 else 0
            pixels += bytes((min(255, red + shade), min(255, green + shade), min(255, blue + shade), 255))
    return pixels


def decode_dtx_pixels(path: Path, alias: str) -> tuple[int, int, bytearray, str]:
    data = path.read_bytes()
    if len(data) < 164:
        raise DatParseError(f"DTX too small: {path}")
    file_type, version = struct.unpack_from("<ii", data, 0)
    width, height = struct.unpack_from("<HH", data, 8)
    bpp = data[26]
    if file_type != 0 or version != -5 or width <= 0 or height <= 0:
        raise DatParseError(f"not a DTX v2 texture: {path}")
    payload = data[164:]
    if bpp == 4:
        return width, height, decode_dxt1(payload, width, height), "dxt1"
    if bpp == 6:
        return width, height, decode_dxt5(payload, width, height), "dxt5"
    if bpp in {0, 3} and len(payload) >= width * height * 4:
        pixels = bytearray()
        for offset in range(0, width * height * 4, 4):
            blue, green, red, alpha = payload[offset:offset + 4]
            pixels += bytes((red, green, blue, alpha))
        return width, height, pixels, "bgra32"
    return width, height, make_placeholder_pixels(width, height, alias), f"placeholder_bpp_{bpp}"


def write_bmp(path: Path, width: int, height: int, pixels_rgba: bytearray) -> None:
    row_stride = width * 4
    pixel_bytes = bytearray()
    for y in range(height - 1, -1, -1):
        row_offset = y * width * 4
        for x in range(width):
            red, green, blue, alpha = pixels_rgba[row_offset + x * 4:row_offset + x * 4 + 4]
            pixel_bytes += bytes((blue, green, red, alpha))

    file_header_size = 14
    dib_header_size = 40
    pixel_offset = file_header_size + dib_header_size
    file_size = pixel_offset + len(pixel_bytes)
    header = bytearray()
    header += b"BM"
    header += struct.pack("<IHHI", file_size, 0, 0, pixel_offset)
    header += struct.pack("<IiiHHIIiiII", dib_header_size, width, height, 1, 32, 0, len(pixel_bytes), 0, 0, 0, 0)
    path.write_bytes(header + pixel_bytes)


def write_alias_bitmaps(bitmap_dir: Path, alias_metadata: dict[str, dict[str, Any]]) -> dict[str, str]:
    bitmap_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}
    for alias, metadata in sorted(alias_metadata.items()):
        physical_path = metadata.get("physical_path", "")
        if not physical_path:
            width = int(metadata.get("width", 128))
            height = int(metadata.get("height", 128))
            pixels = make_placeholder_pixels(width, height, alias)
            mode = "placeholder_missing_source"
        else:
            width, height, pixels, mode = decode_dtx_pixels(Path(physical_path), alias)
        write_bmp(bitmap_dir / f"{alias}.bmp", width, height, pixels)
        results[alias] = mode
    return results


def find_texture_size(
    texture_sizes: dict[str, tuple[int, int, Path]],
    texture_name: str,
) -> tuple[int, int, str]:
    def without_prefix(value: str, prefix: str) -> str:
        return value[len(prefix):] if value.startswith(prefix) else value

    normalized = texture_key(texture_name)
    candidates = [
        normalized,
        without_prefix(normalized, "textures/"),
        without_prefix(normalized, "tex/"),
        normalized + ".dtx",
        without_prefix(normalized, "textures/") + ".dtx",
        without_prefix(normalized, "tex/") + ".dtx",
    ]
    if normalized.endswith(".spr"):
        candidates.append(f"spriteframe/{Path(normalized).stem}")
    candidates.append(f"basename/{Path(normalized).stem}")
    for candidate in candidates:
        found = texture_sizes.get(candidate)
        if found:
            return found[0], found[1], str(found[2])
    return 256, 256, ""


def alias_base(texture_name: str) -> str:
    stem = Path(texture_name.replace("\\", "/")).stem
    cleaned = re.sub(r"[^A-Za-z0-9]", "", stem).upper()
    return cleaned or "TEX"


def base36(value: int, width: int) -> str:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = ""
    while value:
        value, digit = divmod(value, len(alphabet))
        result = alphabet[digit] + result
    return result.rjust(width, "0")[-width:]


def global_texture_alias(texture_name: str, collision_index: int = 0) -> str:
    base = alias_base(texture_name)[:4].ljust(4, "0")
    key = texture_key(texture_name).encode("utf-8")
    hash_value = zlib.crc32(key) & 0xFFFFFFFF
    if collision_index:
        hash_value = zlib.crc32(str(collision_index).encode("ascii"), hash_value) & 0xFFFFFFFF
    return f"{base}{base36(hash_value, 6)}"[:BMODEL_TEXTURE_NAME_SIZE]


def build_aliases(texture_names: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    used: set[str] = set()
    for texture_name in texture_names:
        alias = ""
        for index in range(1000):
            candidate = global_texture_alias(texture_name, index)
            if candidate not in used:
                alias = candidate
                break
        if not alias:
            raise RuntimeError("could not allocate texture alias")
        aliases[texture_name] = alias
        used.add(alias)
    return aliases


def allocate_texture_alias(texture_name: str, used_aliases: set[str]) -> str:
    for index in range(1000):
        candidate = global_texture_alias(texture_name, index)
        if candidate not in used_aliases:
            used_aliases.add(candidate)
            return candidate
    raise RuntimeError("could not allocate texture alias")


def build_dtx_size_index(root: Path) -> dict[str, tuple[int, int, Path]]:
    result: dict[str, tuple[int, int, Path]] = {}
    if not root.exists():
        return result

    for path in root.rglob("*.dtx"):
        if not path.is_file():
            continue
        with path.open("rb") as handle:
            header = handle.read(12)
        if len(header) < 12:
            continue
        file_type, version, width, height = struct.unpack_from("<iiHH", header)
        if file_type != 0 or version != -5 or width <= 0 or height <= 0:
            continue
        rel = path.relative_to(root).as_posix()
        rel_no_ext = str(Path(rel).with_suffix("")).replace("\\", "/")
        result[texture_key(rel_no_ext)] = (width, height, path)
        result[texture_key(rel)] = (width, height, path)
    return result


def build_case_insensitive_file_index(root: Path, suffix: str) -> dict[str, Path]:
    if not root.exists():
        return {}
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() != suffix.lower():
            continue
        result[path.relative_to(root).as_posix().lower()] = path
    return result


def normalize_model_source_key(source_model: str) -> str:
    normalized = normalize_lithtech_virtual_path(source_model, lowercase=True)
    if normalized.startswith("models/"):
        normalized = normalized[len("models/"):]
    return normalized


def resolve_source_model_path(model_index: dict[str, Path], source_model: str) -> Path | None:
    key = normalize_model_source_key(source_model)
    found = model_index.get(key)
    if found is not None:
        return found

    path = Path(key)
    stripped_stem = re.sub(r"\d+$", "", path.stem)
    if stripped_stem and stripped_stem != path.stem:
        fallback = str(path.with_name(stripped_stem + path.suffix)).replace("\\", "/").lower()
        return model_index.get(fallback)
    return None


def normalize_skin_source_key(source_skin: str) -> str:
    normalized = normalize_lithtech_virtual_path(source_skin, lowercase=True)
    if normalized.startswith("skins/"):
        normalized = normalized[len("skins/"):]
    return normalized


def resolve_skin_texture(
    skin_index: dict[str, tuple[int, int, Path]],
    source_skin: str,
) -> tuple[int, int, str]:
    key = normalize_skin_source_key(source_skin)
    candidates = [
        key,
        str(Path(key).with_suffix("")).replace("\\", "/"),
    ]
    for candidate in candidates:
        found = skin_index.get(texture_key(candidate))
        if found:
            return found[0], found[1], str(found[2])
    return 256, 256, ""


def source_skin_for_material(source_skin: str, material_index: int) -> str:
    skins = [part.strip() for part in source_skin.split(";") if part.strip()]
    if not skins:
        return ""
    if material_index < len(skins):
        return skins[material_index]
    return skins[0]


def normalize_model_role_name(model_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", model_name.lower())


def is_skipped_world_model_name(model_name: str) -> bool:
    compact_model = normalize_model_role_name(model_name)
    return (
        compact_model.startswith("aitrk")
        or compact_model.startswith("rail")
        or compact_model.startswith("todsky")
        or compact_model.startswith("skybox")
        or compact_model == "sky"
        or compact_model == "visbsp"
    )


def is_rail_helper_texture(texture_name: str) -> bool:
    texture = texture_key(texture_name)
    return texture == "rail.dtx" or texture.endswith("/rail.dtx")


def is_green_screen_helper_texture(texture_name: str) -> bool:
    texture = texture_key(texture_name)
    return texture == "greenscreen.dtx" or texture.endswith("/greenscreen.dtx")


def is_water_sprite_texture(texture_name: str) -> bool:
    texture = texture_key(texture_name)
    return texture.startswith("sprites/water/") or texture.startswith("spritetextures/water/")


def is_water_marker_texture(texture_name: str) -> bool:
    texture = texture_key(texture_name)
    return texture == "watermarker.dtx" or texture.endswith("/watermarker.dtx")


def is_sky_marker_texture(texture_name: str) -> bool:
    texture = texture_key(texture_name)
    return texture == "skymarker.dtx" or texture.endswith("/skymarker.dtx")


def is_plant_foliage_texture(texture_name: str) -> bool:
    texture = texture_key(texture_name)
    texture_stem = Path(texture).stem.lower()
    if "plantsandtrees/" not in texture:
        return False
    if "bark" in texture_stem or "trunk" in texture_stem:
        return False
    return (
        "branch" in texture_stem
        or "leaf" in texture_stem
        or "leaves" in texture_stem
        or "bush" in texture_stem
        or "flower" in texture_stem
    )


def is_plant_model_source(model_name: str) -> bool:
    model = texture_key(model_name)
    return "plantsandtrees/" in model


def should_skip_face_role(face_role: FaceRole) -> bool:
    return face_role.collision_role in {
        "navigation_helper",
        "visibility_helper",
        "sound_helper",
        "water_helper",
        "water_marker",
        "sky_marker",
    }


def resolve_sprite_animation_frames(
    sprite_index: dict[str, dict[str, Any]],
    texture_sizes: dict[str, tuple[int, int, Path]],
    source_texture: str,
) -> list[dict[str, Any]]:
    normalized = texture_key(source_texture)
    candidates = [
        normalized,
        str(Path(normalized).with_suffix("")).replace("\\", "/"),
        f"basename/{Path(normalized).stem}",
        f"frame/{normalized}",
    ]
    entry: dict[str, Any] | None = None
    for candidate in candidates:
        found = sprite_index.get(candidate)
        if found is not None:
            entry = found
            break
    if entry is None:
        return []

    frames: list[dict[str, Any]] = []
    frames_per_second = int(entry.get("frames_per_second", 0) or 0)
    for frame_source in entry.get("frames", []):
        width, height, physical_path = find_texture_size(texture_sizes, str(frame_source))
        frames.append({
            "source_texture": str(frame_source),
            "width": width,
            "height": height,
            "physical_path": physical_path,
            "frames_per_second": frames_per_second,
        })
    return frames


def classify_face_role(model_name: str, texture_name: str, surface_flags: int) -> FaceRole:
    normalized_model = model_name.lower()
    compact_model = normalize_model_role_name(model_name)
    normalized_texture = texture_name.replace("\\", "/").lower()
    texture_stem = Path(normalized_texture).stem
    explicit_invisible = (surface_flags & LT_SURFACE_FLAG_INVISIBLE) != 0
    invisible_texture = texture_stem.startswith("invisib") or texture_stem == "invisible"

    if normalized_model.startswith("aitrk"):
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "navigation_helper",
            "hidden",
        )

    if compact_model.startswith("aibarrier"):
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "ai_barrier",
            "hidden",
        )

    if compact_model.startswith("perceptionbrush"):
        if texture_stem in {"perception", "perception2"}:
            return FaceRole(
                FACE_ATTRIBUTE_SECRET | FACE_ATTRIBUTE_ANIMATED | FACE_ATTRIBUTE_UNTOUCHABLE,
                "secret_perception",
                "visible",
            )

        return FaceRole(
            FACE_ATTRIBUTE_SECRET | FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "secret_perception",
            "hidden",
        )

    if texture_stem == "soundonly":
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "sound_helper",
            "hidden",
        )

    if is_water_sprite_texture(texture_name):
        return FaceRole(
            FACE_ATTRIBUTE_FLUID | FACE_ATTRIBUTE_ANIMATED,
            "water_surface",
            "visible",
        )

    if is_water_marker_texture(texture_name):
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "water_marker",
            "hidden",
        )

    if is_sky_marker_texture(texture_name):
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "sky_marker",
            "hidden",
        )

    if is_plant_foliage_texture(texture_name):
        return FaceRole(
            FACE_ATTRIBUTE_UNTOUCHABLE,
            "visual_non_collision",
            "visible",
        )

    if compact_model == "visbsp":
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "visibility_helper",
            "hidden",
        )

    if compact_model == "physicsbsp":
        if explicit_invisible or invisible_texture:
            return FaceRole(FACE_ATTRIBUTE_INVISIBLE, "physics_hull", "hidden")
        return FaceRole(0, "physics_hull", "visible")

    if normalized_model.startswith("bluewater") or texture_stem.startswith("water"):
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "water_helper",
            "hidden",
        )

    if explicit_invisible:
        return FaceRole(FACE_ATTRIBUTE_INVISIBLE, "invisible_collision", "hidden")

    if normalized_model == "ocean":
        return FaceRole(
            FACE_ATTRIBUTE_FLUID | FACE_ATTRIBUTE_ANIMATED,
            "water_surface",
            "visible",
        )

    if invisible_texture:
        return FaceRole(FACE_ATTRIBUTE_INVISIBLE, "invisible_collision", "hidden")

    return FaceRole(0, "world_geometry", "visible")


def classify_face_attributes(model_name: str, texture_name: str, surface_flags: int) -> int:
    return classify_face_role(model_name, texture_name, surface_flags).attributes


def rotate_vec_by_quat(
    vector: tuple[float, float, float],
    quat: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    qx, qy, qz, qw = quat
    vx, vy, vz = vector

    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)

    return (
        vx + qw * tx + (qy * tz - qz * ty),
        vy + qw * ty + (qz * tx - qx * tz),
        vz + qw * tz + (qx * ty - qy * tx),
    )


def transform_model_vertex_to_odm(
    local_lt: tuple[float, float, float],
    position_lt: list[float],
    rotation_lt: list[float],
    uniform_scale: float,
    coordinate_scale: float,
    model_translation_lt: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> OdmVertex:
    translated_local_lt = (
        local_lt[0] + model_translation_lt[0],
        local_lt[1] + model_translation_lt[1],
        local_lt[2] + model_translation_lt[2],
    )
    local = lt_to_odm(translated_local_lt, coordinate_scale * uniform_scale)
    rotated = rotate_vec_by_quat(
        (float(local.x), float(local.y), float(local.z)),
        lt_rotation_to_odm_quat(rotation_lt),
    )
    position = lt_vec_to_odm_tuple(position_lt, coordinate_scale)
    return OdmVertex(
        x=int(round(rotated[0] + position[0])),
        y=int(round(rotated[1] + position[1])),
        z=int(round(rotated[2] + position[2])),
    )


def abc_static_model_translation_lt(abc_model: AbcModel) -> tuple[float, float, float]:
    placement_info = abc_static_model_placement_info(abc_model)
    if placement_info is None:
        return (0.0, 0.0, 0.0)
    return placement_info.binding_origin


def abc_static_model_half_dims_lt(abc_model: AbcModel) -> tuple[float, float, float] | None:
    placement_info = abc_static_model_placement_info(abc_model)
    if placement_info is None:
        return None
    return placement_info.binding_extents


def abc_lod0_bounds_lt(abc_model: AbcModel) -> LtModelBounds | None:
    rows: list[tuple[float, float, float]] = []
    for piece in abc_model.pieces:
        if not piece.lods:
            continue
        rows.extend(tuple(float(value) for value in vertex.position) for vertex in piece.lods[0].vertices)

    if not rows:
        return None

    return LtModelBounds(
        min=tuple(min(row[index] for row in rows) for index in range(3)),
        max=tuple(max(row[index] for row in rows) for index in range(3)),
    )


def abc_static_model_placement_binding(abc_model: AbcModel) -> Any | None:
    if not abc_model.anim_bindings:
        return None

    for binding in abc_model.anim_bindings:
        if binding.name.lower() == "world":
            return binding
    return abc_model.anim_bindings[0]


def abc_static_model_placement_info(abc_model: AbcModel) -> LtModelPlacementInfo | None:
    bounds = abc_lod0_bounds_lt(abc_model)
    binding = abc_static_model_placement_binding(abc_model)
    if bounds is None and binding is None:
        return None

    if binding is None:
        assert bounds is not None
        half_extents = tuple(max(0.0, (bounds.max[index] - bounds.min[index]) * 0.5) for index in range(3))
        return LtModelPlacementInfo(bounds=bounds, binding_origin=(0.0, 0.0, 0.0), binding_extents=half_extents)

    binding_origin = tuple(float(value) for value in binding.origin)
    binding_extents = tuple(max(0.0, float(value)) for value in binding.extents)
    if bounds is None:
        bounds = LtModelBounds(
            min=tuple(binding_origin[index] - binding_extents[index] for index in range(3)),
            max=tuple(binding_origin[index] + binding_extents[index] for index in range(3)),
        )

    return LtModelPlacementInfo(bounds=bounds, binding_origin=binding_origin, binding_extents=binding_extents)


def lt_model_bounds_half_extents(bounds: LtModelBounds) -> tuple[float, float, float]:
    return tuple(max(0.0, (bounds.max[index] - bounds.min[index]) * 0.5) for index in range(3))


def vec3_list_property(value: Any) -> list[float] | None:
    if isinstance(value, list) and len(value) >= 3:
        return [float(value[index]) for index in range(3)]
    return None


def explicit_dims_extents_lt(properties: dict[str, Any]) -> tuple[float, float, float] | None:
    dims = vec3_list_property(properties.get("dims"))
    if dims is None:
        return None
    return tuple(max(0.5, abs(dims[index])) for index in range(3))


def placement_extents_lt(
    properties: dict[str, Any],
    placement_info: LtModelPlacementInfo | None,
) -> tuple[float, float, float]:
    explicit = explicit_dims_extents_lt(properties)
    if explicit is not None:
        return explicit
    if placement_info is not None and all(value > 0.0 for value in placement_info.binding_extents):
        return placement_info.binding_extents
    if placement_info is not None:
        return lt_model_bounds_half_extents(placement_info.bounds)
    return (64.0, 64.0, 64.0)


def placement_half_dims_lt(
    properties: dict[str, Any],
    placement_info: LtModelPlacementInfo | None,
    uniform_scale: float,
) -> tuple[float, float, float]:
    scale = abs(uniform_scale)
    return tuple(value * scale for value in placement_extents_lt(properties, placement_info))


def placement_skip_key(value: Any) -> str:
    return str(value or "").lower()


def object_skips_floor_placement(source_class: str, source_name: str) -> bool:
    class_name = placement_skip_key(source_class)
    name = placement_skip_key(source_name)
    return (
        "terrain" in class_name
        or "physicsbsp" in class_name
        or "visbsp" in class_name
        or "airail" in class_name
        or "sky" in class_name
        or "trigger" in class_name
        or "volumebrush" in class_name
        or "terrain" in name
        or "physicsbsp" in name
        or "visbsp" in name
        or "rail" in name
        or "sky" in name
        or "trigger" in name
    )


def is_plant_or_tree_prop_source(source_class: str, source_model: str) -> bool:
    return source_class.lower() == "prop" and is_plant_model_source(source_model)


def is_decorative_plant_or_tree_prop(
    source_class: str,
    source_model: str,
    properties: dict[str, Any],
    move_to_floor: bool,
) -> bool:
    if source_class.lower() != "prop" or move_to_floor:
        return False
    if not truthy_property(properties.get("rayhit"), False):
        return False
    if truthy_property(properties.get("solid"), False):
        return False
    if not truthy_property(properties.get("visible"), True):
        return False
    return is_plant_model_source(source_model)


def source_model_is_authored_floor_contact(source_model: str) -> bool:
    normalized = normalize_model_source_key(source_model)
    return normalized in {
        "props/barstool1.abc",
        "props/chair.abc",
        "props/chair02.abc",
        "props/chair03.abc",
        "props/chair_fordesk02.abc",
        "props/table01.abc",
        "props/table_bench.abc",
        "props/tableround.abc",
        "props/tabletrestle.abc",
    }


def transformed_model_aabb_lt(
    position: list[float],
    rotation: list[float],
    uniform_scale: float,
    bounds: LtModelBounds,
    model_translation_lt: tuple[float, float, float],
) -> LtModelBounds:
    quat = lt_rotation_to_odm_quat(rotation)
    min_values: list[float] | None = None
    max_values: list[float] | None = None
    scale = abs(uniform_scale)
    for x in (bounds.min[0], bounds.max[0]):
        for y in (bounds.min[1], bounds.max[1]):
            for z in (bounds.min[2], bounds.max[2]):
                local = lt_to_odm(
                    (
                        x + model_translation_lt[0],
                        y + model_translation_lt[1],
                        z + model_translation_lt[2],
                    ),
                    scale,
                )
                rotated = rotate_vec_by_quat((float(local.x), float(local.y), float(local.z)), quat)
                world = [
                    float(position[0]) + rotated[0],
                    float(position[1]) + rotated[2],
                    float(position[2]) + rotated[1],
                ]
                if min_values is None or max_values is None:
                    min_values = list(world)
                    max_values = list(world)
                else:
                    for index in range(3):
                        min_values[index] = min(min_values[index], world[index])
                        max_values[index] = max(max_values[index], world[index])

    assert min_values is not None and max_values is not None
    return LtModelBounds(min=tuple(min_values), max=tuple(max_values))


def truthy_property(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off", "none"}
    return default


def is_actor_like_model_instance(source_class: str, source_model: str) -> bool:
    source_class_lower = source_class.lower()
    source_model_key = normalize_model_source_key(source_model)

    if source_model_key.startswith(("props/", "pickupitems/", "modelprops/")):
        return False

    allowed_classes = {
        "prop",
        "candleprop",
        "torch",
        "treasurechest",
        "destructableprop",
        "destructibleprop",
    }
    if source_class_lower in allowed_classes:
        return False

    return True


def baked_model_kind(source_class: str, source_model: str) -> str:
    source_class_lower = source_class.lower()
    source_model_key = normalize_model_source_key(source_model)
    if source_class_lower in {"destructableprop", "destructibleprop"}:
        return "destructible_prop"
    if source_class_lower == "treasurechest" or "chest" in Path(source_model_key).stem.lower():
        return "chest"
    if source_model_key.startswith("pickupitems/"):
        return "pickup"
    return "static_prop"


def should_bake_model_instance(source_class: str, source_model: str) -> bool:
    return not is_actor_like_model_instance(source_class, source_model)


def floor_collision_role_for_move_to_floor(role: str) -> bool:
    return role in {
        "world_geometry",
        "physics_hull",
        "invisible_collision",
        "secret_perception",
    }


def build_floor_support_triangles(dat_world: DatWorld) -> list[LtFloorTriangle]:
    triangles: list[LtFloorTriangle] = []
    for model in dat_world.world_models:
        if is_skipped_world_model_name(model.name):
            continue

        for poly in model.polies:
            if len(poly.disk_verts) < 3:
                continue
            if poly.surface_index >= len(model.surfaces):
                continue

            surface = model.surfaces[poly.surface_index]
            if surface.texture_index >= len(model.textures):
                continue

            texture_name = model.textures[surface.texture_index]
            if is_rail_helper_texture(texture_name):
                continue

            role = classify_face_role(model.name, texture_name, surface.flags)
            if not floor_collision_role_for_move_to_floor(role.collision_role):
                continue

            source_indices = [disk_vert.vertex_index for disk_vert in poly.disk_verts]
            if any(index >= len(model.points) for index in source_indices):
                continue

            for fan_index in range(1, len(source_indices) - 1):
                triangles.append(LtFloorTriangle((
                    model.points[source_indices[0]],
                    model.points[source_indices[fan_index]],
                    model.points[source_indices[fan_index + 1]],
                )))

    return triangles


def point_inside_triangle_lt(
    point: tuple[float, float, float],
    triangle: LtFloorTriangle,
) -> bool:
    a, b, c = triangle.vertices
    v0 = vec_sub_lt(c, a)
    v1 = vec_sub_lt(b, a)
    v2 = vec_sub_lt(point, a)

    dot00 = vec_dot(v0, v0)
    dot01 = vec_dot(v0, v1)
    dot02 = vec_dot(v0, v2)
    dot11 = vec_dot(v1, v1)
    dot12 = vec_dot(v1, v2)
    denominator = dot00 * dot11 - dot01 * dot01
    if abs(denominator) <= 0.000001:
        return False

    inverse_denominator = 1.0 / denominator
    u = (dot11 * dot02 - dot01 * dot12) * inverse_denominator
    v = (dot00 * dot12 - dot01 * dot02) * inverse_denominator
    return u >= -0.0001 and v >= -0.0001 and u + v <= 1.0001


def intersect_vertical_floor_lt(
    position: list[float],
    triangle: LtFloorTriangle,
    max_drop_distance: float,
) -> float | None:
    if len(position) != 3:
        return None

    origin = (float(position[0]), float(position[1]), float(position[2]))
    a, b, c = triangle.vertices
    normal = vec_cross(vec_sub_lt(b, a), vec_sub_lt(c, a))
    if abs(normal[1]) <= 0.000001:
        return None

    ray_direction = (0.0, -1.0, 0.0)
    denominator = vec_dot(ray_direction, normal)
    if abs(denominator) <= 0.000001:
        return None

    distance = vec_dot(vec_sub_lt(a, origin), normal) / denominator
    if distance < -0.0001 or distance > max_drop_distance:
        return None

    hit = (origin[0], origin[1] - distance, origin[2])
    if not point_inside_triangle_lt(hit, triangle):
        return None
    return hit[1]


def move_position_to_floor_lt(
    position: list[float],
    half_dims_lt: tuple[float, float, float] | None,
    floor_triangles: list[LtFloorTriangle],
    max_drop_distance: float = 10000.0,
    placement_bias: float = 0.1,
) -> tuple[list[float], str]:
    if len(position) != 3 or half_dims_lt is None:
        return position, "missing_dims"

    best_floor_y: float | None = None
    for triangle in floor_triangles:
        floor_y = intersect_vertical_floor_lt(position, triangle, max_drop_distance)
        if floor_y is None:
            continue
        if best_floor_y is None or floor_y > best_floor_y:
            best_floor_y = floor_y

    if best_floor_y is None:
        return position, "no_support"

    moved_position = [float(position[0]), float(position[1]), float(position[2])]
    distance_to_floor = moved_position[1] - best_floor_y
    if distance_to_floor > half_dims_lt[1]:
        moved_position[1] = best_floor_y + half_dims_lt[1] + placement_bias
        return moved_position, "snapped"
    return moved_position, "already_supported"


def floor_y_under_position_lt(
    position: list[float],
    floor_triangles: list[LtFloorTriangle],
    max_drop_distance: float = 10000.0,
) -> float | None:
    best_floor_y: float | None = None
    for triangle in floor_triangles:
        floor_y = intersect_vertical_floor_lt(position, triangle, max_drop_distance)
        if floor_y is None:
            continue
        if best_floor_y is None or floor_y > best_floor_y:
            best_floor_y = floor_y
    return best_floor_y


def intersect_vertical_floor_any_direction_lt(
    position: list[float],
    triangle: LtFloorTriangle,
    max_vertical_distance: float,
) -> float | None:
    if len(position) != 3:
        return None

    origin = (float(position[0]), float(position[1]), float(position[2]))
    a, b, c = triangle.vertices
    normal = vec_cross(vec_sub_lt(b, a), vec_sub_lt(c, a))
    if abs(normal[1]) <= 0.000001:
        return None

    floor_y = a[1] - (normal[0] * (origin[0] - a[0]) + normal[2] * (origin[2] - a[2])) / normal[1]
    if abs(origin[1] - floor_y) > max_vertical_distance:
        return None

    hit = (origin[0], floor_y, origin[2])
    if not point_inside_triangle_lt(hit, triangle):
        return None
    return floor_y


def floor_y_near_position_lt(
    position: list[float],
    floor_triangles: list[LtFloorTriangle],
    max_vertical_distance: float = 10000.0,
) -> float | None:
    best_floor_y: float | None = None
    best_distance: float | None = None
    for triangle in floor_triangles:
        floor_y = intersect_vertical_floor_any_direction_lt(position, triangle, max_vertical_distance)
        if floor_y is None:
            continue
        distance = abs(float(position[1]) - floor_y)
        if (
            best_distance is None
            or distance < best_distance - 0.0001
            or (abs(distance - best_distance) <= 0.0001 and (best_floor_y is None or floor_y > best_floor_y))
        ):
            best_floor_y = floor_y
            best_distance = distance
    return best_floor_y


def move_position_to_model_support_lt(
    position: list[float],
    source_object_index: int,
    half_dims_lt: tuple[float, float, float],
    model_supports: list[LtPlacementSupport],
    max_drop_distance: float = 10000.0,
    placement_bias: float = 0.1,
) -> tuple[list[float], str, float | None]:
    best_support: LtPlacementSupport | None = None
    best_distance: float | None = None

    for support in model_supports:
        if support.source_object_index == source_object_index:
            continue
        if support.half_extents[0] + 0.1 < half_dims_lt[0]:
            continue
        if support.half_extents[2] + 0.1 < half_dims_lt[2]:
            continue
        if position[0] < support.center[0] - support.half_extents[0]:
            continue
        if position[0] > support.center[0] + support.half_extents[0]:
            continue
        if position[2] < support.center[2] - support.half_extents[2]:
            continue
        if position[2] > support.center[2] + support.half_extents[2]:
            continue

        floor_y = support.center[1] + support.half_extents[1]
        distance = float(position[1]) - floor_y
        if floor_y > float(position[1]) + 0.1:
            continue
        if distance < -0.000001 or distance > max_drop_distance:
            continue
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_support = support

    if best_support is None or best_distance is None:
        return position, "no_support", None

    floor_y = best_support.center[1] + best_support.half_extents[1]
    moved_position = [float(position[0]), float(position[1]), float(position[2])]
    if best_distance > half_dims_lt[1]:
        moved_position[1] = floor_y + half_dims_lt[1] + placement_bias
        return moved_position, "snapped", best_distance
    return moved_position, "already_supported", best_distance


def model_support_for_work_item(work_item: BakedModelWorkItem) -> LtPlacementSupport | None:
    if work_item.plant_or_tree_source or work_item.placement_info is None:
        return None

    if not (work_item.solid or work_item.ray_hit):
        return None

    model_translation_lt = tuple(
        work_item.placement_info.binding_origin[index] + work_item.visual_offset_lt[index]
        for index in range(3)
    )
    bounds = transformed_model_aabb_lt(
        work_item.position_lt,
        work_item.rotation_lt,
        work_item.uniform_scale,
        work_item.placement_info.bounds,
        model_translation_lt,
    )
    center = tuple((bounds.min[index] + bounds.max[index]) * 0.5 for index in range(3))
    half_extents = tuple((bounds.max[index] - bounds.min[index]) * 0.5 for index in range(3))
    if object_skips_floor_placement(work_item.source_class, work_item.source_name):
        return None
    return LtPlacementSupport(
        source_object_index=work_item.object_index,
        source_name=work_item.source_name,
        center=center,
        half_extents=half_extents,
    )


def build_model_supports(work_items: list[BakedModelWorkItem]) -> list[LtPlacementSupport]:
    supports: list[LtPlacementSupport] = []
    for work_item in work_items:
        support = model_support_for_work_item(work_item)
        if support is not None:
            supports.append(support)
    return supports


def apply_model_support_floor_pass(
    work_items: list[BakedModelWorkItem],
    properties_by_object_index: dict[int, dict[str, Any]],
    floor_triangles: list[LtFloorTriangle],
) -> None:
    model_supports = build_model_supports(work_items)
    for work_item in work_items:
        properties = properties_by_object_index.get(work_item.object_index, {})
        if not work_item.move_to_floor:
            continue
        if object_skips_floor_placement(work_item.source_class, work_item.source_name):
            continue
        half_dims = placement_half_dims_lt(properties, work_item.placement_info, work_item.uniform_scale)
        world_position, world_status = move_position_to_floor_lt(work_item.raw_position_lt, half_dims, floor_triangles)
        model_position, model_status, model_distance = move_position_to_model_support_lt(
            work_item.raw_position_lt,
            work_item.object_index,
            half_dims,
            model_supports,
        )
        use_model = False
        if model_status in {"snapped", "already_supported"}:
            if world_status not in {"snapped", "already_supported"}:
                use_model = True
            elif work_item.source_class.lower() == "prop":
                use_model = True
            else:
                world_distance = max(0.0, float(work_item.raw_position_lt[1]) - float(world_position[1]))
                use_model = model_distance is not None and model_distance < world_distance

        if use_model:
            work_item.position_lt = model_position
            work_item.placement_kind = f"move_to_floor_model_{model_status}"
        elif world_status in {"snapped", "already_supported"}:
            work_item.position_lt = world_position
            work_item.placement_kind = f"move_to_floor_world_{world_status}"


def bmodel_name_for_baked_object(source_object_index: int, source_name: str, kind: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", source_name).strip("_") or f"Object{source_object_index}"
    return f"MM9_{kind}_{source_object_index}_{cleaned}"[:32]


def ensure_alias_metadata(
    source_texture: str,
    texture_size_index: dict[str, tuple[int, int, Path]],
    aliases_by_source: dict[str, str],
    alias_metadata: dict[str, dict[str, Any]],
    used_aliases: set[str],
) -> str:
    existing = aliases_by_source.get(source_texture)
    if existing:
        return existing

    alias = allocate_texture_alias(source_texture, used_aliases)
    width, height, physical_path = find_texture_size(texture_size_index, source_texture)
    metadata = {
        "source_texture": source_texture,
        "width": width,
        "height": height,
        "physical_path": physical_path,
    }
    if physical_path:
        metadata.update(read_dtx_header_metadata(Path(physical_path)))
    alias_metadata[alias] = metadata
    aliases_by_source[source_texture] = alias
    return alias


def append_baked_model_face(
    bmodel: OdmBModel,
    source_poly_index: int,
    texture_alias: str,
    texture_size: tuple[int, int],
    vertices: list[OdmVertex],
    face_uvs: list[tuple[float, float]],
    face_role: FaceRole,
    source_material_index: int,
    barrel_liquid: bool,
) -> bool:
    base_index = len(bmodel.vertices)
    bmodel.vertices.extend(vertices)
    triangle_indices = [base_index, base_index + 1, base_index + 2]
    if compute_unit_normal(bmodel.vertices, triangle_indices) is None:
        del bmodel.vertices[base_index:]
        return False

    texture_width, texture_height = texture_size
    plane_normal, plane_distance = compute_plane(bmodel.vertices, triangle_indices)
    face = OdmFace(
        vertex_indices=triangle_indices,
        texture_us=[uv_float_to_i16(uv[0], texture_width) for uv in face_uvs],
        texture_vs=[uv_float_to_i16(uv[1], texture_height) for uv in face_uvs],
        texture_alias=texture_alias,
        bitmap_index=0,
        polygon_type=classify_polygon_type(bmodel.vertices, triangle_indices),
        attributes=face_role.attributes,
        plane_normal=plane_normal,
        plane_distance=clamp_i32(plane_distance),
        reserved=0,
    )
    bmodel.faces.append(face)
    bmodel.source_poly_for_face.append(source_poly_index)
    bmodel.source_surface_for_face.append(-1)
    bmodel.source_surface_flags_for_face.append(0)
    bmodel.source_texture_index_for_face.append(source_material_index)
    bmodel.source_barrel_liquid_for_face.append(barrel_liquid)
    bmodel.source_texture_flags_for_face.append(0)
    bmodel.source_collision_role_for_face.append(face_role.collision_role)
    bmodel.source_render_role_for_face.append(face_role.render_role)
    return True


def reverse_polygon_winding(indices: list[int], uvs: list[tuple[int, int]]) -> tuple[list[int], list[tuple[int, int]]]:
    if len(indices) <= 1:
        return list(indices), list(uvs)
    return [indices[0]] + list(reversed(indices[1:])), [uvs[0]] + list(reversed(uvs[1:]))


def triangulate_polygon_fan(
    source_indices: list[int],
    source_uvs: list[tuple[int, int]],
) -> list[tuple[list[int], list[tuple[int, int]]]]:
    triangles: list[tuple[list[int], list[tuple[int, int]]]] = []
    for fan_index in range(1, len(source_indices) - 1):
        triangles.append((
            [source_indices[0], source_indices[fan_index], source_indices[fan_index + 1]],
            [source_uvs[0], source_uvs[fan_index], source_uvs[fan_index + 1]],
        ))
    return triangles


def source_polygon_can_be_preserved_as_ngon(source_indices: list[int]) -> bool:
    if len(source_indices) < 4:
        return False

    return len(set(source_indices)) == len(source_indices)


def append_source_face(
    bmodel: OdmBModel,
    indices: list[int],
    uvs: list[tuple[int, int]],
    texture_alias: str,
    bitmap_index: int,
    face_role: FaceRole,
    poly_index: int,
    source_surface_index: int,
    surface: Surface,
    source_texture_index: int,
    stats: dict[str, int],
) -> bool:
    if compute_unit_normal(bmodel.vertices, indices) is None:
        stats["skipped_degenerate_triangles"] += 1
        return False

    plane_normal, plane_distance = compute_plane(bmodel.vertices, indices)
    clamped_plane_distance = clamp_i32(plane_distance)
    if clamped_plane_distance != plane_distance:
        stats["clamped_plane_distances"] += 1
    face = OdmFace(
        vertex_indices=indices,
        texture_us=[uv[0] for uv in uvs],
        texture_vs=[uv[1] for uv in uvs],
        texture_alias=texture_alias,
        bitmap_index=bitmap_index,
        polygon_type=classify_polygon_type(bmodel.vertices, indices),
        attributes=face_role.attributes,
        plane_normal=plane_normal,
        plane_distance=clamped_plane_distance,
        reserved=ODM_FACE_RESERVED_NOT_A_STEP if (surface.flags & LT_SURFACE_FLAG_NOT_A_STEP) != 0 else 0,
    )
    bmodel.faces.append(face)
    bmodel.source_poly_for_face.append(poly_index)
    bmodel.source_surface_for_face.append(source_surface_index)
    bmodel.source_surface_flags_for_face.append(surface.flags)
    bmodel.source_texture_index_for_face.append(source_texture_index)
    bmodel.source_barrel_liquid_for_face.append(False)
    bmodel.source_texture_flags_for_face.append(surface.texture_flags)
    bmodel.source_collision_role_for_face.append(face_role.collision_role)
    bmodel.source_render_role_for_face.append(face_role.render_role)
    stats["emitted_faces"] += 1
    if len(indices) > 3:
        stats["preserved_source_ngon_faces"] += 1
    if face_role.collision_role == "world_geometry":
        stats["faces_world_geometry"] += 1
    elif face_role.collision_role == "physics_hull":
        stats["faces_physics_hull"] += 1
    elif face_role.collision_role == "invisible_collision":
        stats["faces_invisible_collision"] += 1
    elif face_role.collision_role == "visibility_helper":
        stats["faces_visibility_helper"] += 1
        stats["faces_non_collision_helper"] += 1
    elif face_role.collision_role == "navigation_helper":
        stats["faces_navigation_helper"] += 1
        stats["faces_non_collision_helper"] += 1
    elif face_role.collision_role == "secret_perception":
        stats["faces_secret_perception"] += 1
    elif face_role.collision_role == "water_surface":
        stats["faces_water_surface"] += 1
    elif face_role.collision_role == "visual_non_collision":
        stats["faces_visual_non_collision"] += 1
    elif face_role.collision_role == "ai_barrier":
        stats["faces_ai_barrier"] += 1
    else:
        stats["faces_non_collision_helper"] += 1
    return True


def bake_abc_model_instance(
    abc_model: AbcModel,
    object_index: int,
    source_class: str,
    source_name: str,
    source_model: str,
    source_skin: str,
    position: list[float],
    rotation: list[float],
    uniform_scale: float,
    coordinate_scale: float,
    texture_size_index: dict[str, tuple[int, int, Path]],
    aliases_by_source: dict[str, str],
    alias_metadata: dict[str, dict[str, Any]],
    used_aliases: set[str],
    source_model_index: int,
    visual_offset_lt: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> OdmBModel:
    kind = baked_model_kind(source_class, source_model)
    bmodel = OdmBModel(
        name=bmodel_name_for_baked_object(object_index, source_name, kind),
        source_model_index=source_model_index,
        source_model_name=source_model,
        source_world_translation_lt=(float(position[0]), float(position[1]), float(position[2])),
        source_world_info_flags=0,
    )

    source_poly_index = 0
    binding_translation_lt = abc_static_model_translation_lt(abc_model)
    model_translation_lt = tuple(binding_translation_lt[index] + visual_offset_lt[index] for index in range(3))
    for piece in abc_model.pieces:
        if not piece.lods:
            continue
        is_barrel_liquid = (
            source_class.lower() == "barrel"
            and piece.material_index == 1
            and piece.name.lower() == "liquid"
        )
        skin = MM9_BARREL_LIQUID_TEXTURES[-1] if is_barrel_liquid else source_skin_for_material(
            source_skin, piece.material_index)
        if not skin:
            skin = f"Skins/{normalize_model_source_key(source_model)}"
            skin = str(Path(skin).with_suffix(".dtx")).replace("\\", "/")
        texture_alias = ensure_alias_metadata(
            skin,
            texture_size_index,
            aliases_by_source,
            alias_metadata,
            used_aliases,
        )
        texture_width = int(alias_metadata[texture_alias]["width"])
        texture_height = int(alias_metadata[texture_alias]["height"])
        face_role = classify_face_role(bmodel.name, skin, 0)
        if is_barrel_liquid:
            face_role = FaceRole(FACE_ATTRIBUTE_UNTOUCHABLE, "visual_non_collision", "visible")
        elif face_role.collision_role == "world_geometry":
            face_role = FaceRole(0, "baked_model_instance", "visible")
        lod = piece.lods[0]
        for face in lod.faces:
            vertices: list[OdmVertex] = []
            uvs: list[tuple[float, float]] = []
            for face_vertex in face.vertices:
                if face_vertex.vertex_index >= len(lod.vertices):
                    continue
                source_vertex = lod.vertices[face_vertex.vertex_index]
                vertices.append(transform_model_vertex_to_odm(
                    source_vertex.position,
                    position,
                    rotation,
                    uniform_scale,
                    coordinate_scale,
                    model_translation_lt,
                ))
                uvs.append(face_vertex.uv)
            if len(vertices) != 3:
                continue
            append_baked_model_face(
                bmodel,
                source_poly_index,
                texture_alias,
                (texture_width, texture_height),
                [vertices[0], vertices[2], vertices[1]],
                [uvs[0], uvs[2], uvs[1]],
                face_role,
                piece.material_index,
                is_barrel_liquid,
            )
            source_poly_index += 1

    return bmodel


def bind_mm9_barrel_geometry(
    manifest: Mm9ItemSourceManifest,
    bmodels: list[OdmBModel],
    baked_instances: list[BakedModelInstance],
    alias_metadata: dict[str, dict[str, Any]],
) -> None:
    alias_by_source = {
        str(metadata.get("source_texture", "")).replace("\\", "/").lower(): alias
        for alias, metadata in alias_metadata.items()
    }
    liquid_aliases = tuple(alias_by_source[texture.lower()] for texture in MM9_BARREL_LIQUID_TEXTURES)
    instances_by_source = {
        instance.source_object_index: instance
        for instance in baked_instances
        if instance.variant_index == 0
    }
    for source in manifest.barrels:
        source.liquid_texture_aliases = liquid_aliases
        instance = instances_by_source.get(source.provenance.source_object_index)
        if instance is None or instance.bmodel_index >= len(bmodels):
            continue
        source.bmodel_index = instance.bmodel_index
        bmodel = bmodels[instance.bmodel_index]
        source.liquid_faces = tuple(
            face_index
            for face_index, is_liquid in enumerate(bmodel.source_barrel_liquid_for_face)
            if is_liquid
        )


def perception_difficulties_by_model_name(dat_world: DatWorld) -> dict[str, int]:
    difficulties: dict[str, int] = {}

    for world_object in dat_world.objects:
        if world_object.name.lower() != "perceptionbrush":
            continue

        properties = {prop.name.lower(): prop for prop in world_object.properties}
        name_property = properties.get("name")
        value_property = properties.get("perceptionvalue")

        if name_property is None or not isinstance(name_property.value, str) or value_property is None:
            continue

        # MM9 registers PerceptionValue as a LithTech PT_UINT, but the shipped DATs contain an IEEE-754 float
        # bit pattern. The original object code compares those non-negative bit patterns directly, which preserves
        # numeric ordering; values are authored as integral difficulties in the same 0-20 range as Perception.
        if len(value_property.raw_data) != 4:
            continue

        difficulty = struct.unpack("<f", value_property.raw_data)[0]

        if not math.isfinite(difficulty):
            continue

        rounded_difficulty = int(round(difficulty))

        if abs(difficulty - rounded_difficulty) > 0.001 or rounded_difficulty < 0 or rounded_difficulty > 20:
            continue

        difficulties[name_property.value.lower()] = rounded_difficulty

    return difficulties


def transcode_geometry(
    dat_world: DatWorld,
    scale: float,
    texture_sizes: dict[str, tuple[int, int, Path]],
    extracted_root: Path | None = None,
    preserve_source_ngons: bool = True,
    excluded_baked_object_indices: set[int] | None = None,
    baked_model_variant_sources: dict[int, list[tuple[str, str]]] | None = None,
) -> tuple[list[OdmBModel], dict[str, dict[str, Any]], dict[str, Any], list[BakedModelInstance]]:
    sprite_index = build_sprite_animation_index(extracted_root)
    unique_textures: set[str] = set()
    for model in dat_world.world_models:
        if is_skipped_world_model_name(model.name):
            continue
        for poly in model.polies:
            if poly.surface_index >= len(model.surfaces):
                continue
            surface = model.surfaces[poly.surface_index]
            if surface.texture_index >= len(model.textures):
                continue
            texture_name = model.textures[surface.texture_index]
            if is_rail_helper_texture(texture_name) or is_green_screen_helper_texture(texture_name):
                continue
            face_role = classify_face_role(model.name, texture_name, surface.flags)
            if should_skip_face_role(face_role):
                continue
            unique_textures.add(texture_name)
    if any(world_object.name.lower() == "barrel" for world_object in dat_world.objects):
        unique_textures.update(MM9_BARREL_LIQUID_TEXTURES)
    unique_textures = sorted(unique_textures)
    aliases = build_aliases(unique_textures)
    aliases_by_source = dict(aliases)
    used_aliases = set(aliases.values())
    alias_metadata: dict[str, dict[str, Any]] = {}
    sprite_animation_sources = 0
    sprite_animation_frames = 0
    for texture_name in unique_textures:
        width, height, physical_path = find_texture_size(texture_sizes, texture_name)
        sprite_frames = resolve_sprite_animation_frames(sprite_index, texture_sizes, texture_name)
        if sprite_frames and sprite_frames[0].get("physical_path"):
            width = int(sprite_frames[0]["width"])
            height = int(sprite_frames[0]["height"])
            physical_path = str(sprite_frames[0]["physical_path"])
        metadata = {
            "source_texture": texture_name,
            "width": width,
            "height": height,
            "physical_path": physical_path,
        }
        if physical_path:
            metadata.update(read_dtx_header_metadata(Path(physical_path)))
        if sprite_frames:
            sprite_animation_sources += 1
            sprite_animation_frames += len(sprite_frames)
            animation_frames: list[dict[str, Any]] = []
            for frame in sprite_frames:
                frame_source = str(frame["source_texture"])
                frame_alias = ensure_alias_metadata(
                    frame_source,
                    texture_sizes,
                    aliases_by_source,
                    alias_metadata,
                    used_aliases,
                )
                animation_frames.append({
                    "alias": frame_alias,
                    "source_texture": frame_source,
                    "physical_path": frame.get("physical_path", ""),
                    "width": frame.get("width", 0),
                    "height": frame.get("height", 0),
                    "frames_per_second": frame.get("frames_per_second", 0),
                })
            metadata["animation_frames"] = animation_frames
            metadata["animation_frame_count"] = len(animation_frames)
            metadata["animation_frames_per_second"] = int(
                sprite_frames[0].get("frames_per_second", 0) or 0
            )
        alias_metadata[aliases[texture_name]] = metadata

    bmodels: list[OdmBModel] = []
    perception_difficulties = perception_difficulties_by_model_name(dat_world)
    stats = {
        "source_models": len(dat_world.world_models),
        "source_polies": 0,
        "emitted_faces": 0,
        "skipped_polies": 0,
        "triangulated_polies": 0,
        "preserved_source_ngon_faces": 0,
        "skipped_degenerate_triangles": 0,
        "source_plane_orientation_flips": 0,
        "clamped_plane_distances": 0,
        "faces_world_geometry": 0,
        "faces_physics_hull": 0,
        "faces_invisible_collision": 0,
        "faces_visibility_helper": 0,
        "faces_navigation_helper": 0,
        "faces_secret_perception": 0,
        "faces_water_surface": 0,
        "faces_visual_non_collision": 0,
        "faces_ai_barrier": 0,
        "faces_non_collision_helper": 0,
        "sprite_animation_sources": sprite_animation_sources,
        "sprite_animation_frames": sprite_animation_frames,
        "skipped_helper_models": 0,
        "skipped_skybox_models": 0,
        "skipped_ai_track_models": 0,
        "skipped_ai_barrier_models": 0,
        "skipped_vis_bsp_models": 0,
        "skipped_rail_models": 0,
        "skipped_rail_polies": 0,
        "skipped_green_screen_polies": 0,
        "skipped_helper_polies": 0,
        "baked_model_instances": 0,
        "baked_model_faces": 0,
        "baked_model_skipped_actor_like": 0,
        "baked_model_missing_source": 0,
        "baked_model_empty": 0,
        "baked_model_destructible_props": 0,
        "baked_model_chests": 0,
        "baked_model_pickups": 0,
        "baked_model_excluded_semantic_item_source": 0,
        "baked_model_move_to_floor_requested": 0,
        "baked_model_move_to_floor_snapped": 0,
        "baked_model_move_to_floor_already_supported": 0,
        "baked_model_move_to_floor_no_support": 0,
        "baked_model_move_to_floor_missing_dims": 0,
        "baked_model_move_to_floor_defaulted": 0,
        "baked_model_move_to_floor_model_snapped": 0,
        "baked_model_move_to_floor_model_already_supported": 0,
        "baked_model_visual_ground_lift": 0,
        "baked_model_visual_terrain_offset": 0,
        "baked_model_visual_floor_lift": 0,
    }

    for model_index, model in enumerate(dat_world.world_models):
        compact_model_name = normalize_model_role_name(model.name)
        if is_skipped_world_model_name(model.name):
            stats["skipped_helper_models"] += 1
            if compact_model_name.startswith("aitrk"):
                stats["skipped_ai_track_models"] += 1
            elif compact_model_name.startswith("aibarrier"):
                stats["skipped_ai_barrier_models"] += 1
            elif compact_model_name.startswith("rail"):
                stats["skipped_rail_models"] += 1
            elif (
                compact_model_name.startswith("todsky")
                or compact_model_name.startswith("skybox")
                or compact_model_name == "sky"
            ):
                stats["skipped_skybox_models"] += 1
            elif compact_model_name == "visbsp":
                stats["skipped_vis_bsp_models"] += 1
            continue

        bmodel = OdmBModel(
            name=model.name or f"WorldModel{model_index}",
            source_model_index=model_index,
            source_model_name=model.name,
            source_world_translation_lt=model.world_translation,
            source_world_info_flags=model.counts.get("world_info_flags", 0),
            perception_difficulty=perception_difficulties.get(model.name.lower()),
        )
        bmodel.vertices = [lt_to_odm(point, scale) for point in model.points]

        for poly_index, poly in enumerate(model.polies):
            stats["source_polies"] += 1
            if len(poly.disk_verts) < 3:
                stats["skipped_polies"] += 1
                continue
            if poly.surface_index >= len(model.surfaces):
                stats["skipped_polies"] += 1
                continue

            surface = model.surfaces[poly.surface_index]
            if surface.texture_index >= len(model.textures):
                stats["skipped_polies"] += 1
                continue

            source_indices = [disk_vert.vertex_index for disk_vert in poly.disk_verts]
            if any(index >= len(bmodel.vertices) for index in source_indices):
                stats["skipped_polies"] += 1
                continue

            texture_name = model.textures[surface.texture_index]
            if is_rail_helper_texture(texture_name):
                stats["skipped_rail_polies"] += 1
                continue
            if is_green_screen_helper_texture(texture_name):
                stats["skipped_green_screen_polies"] += 1
                continue

            face_role = classify_face_role(bmodel.name, texture_name, surface.flags)
            if should_skip_face_role(face_role):
                stats["skipped_helper_polies"] += 1
                continue
            texture_alias = aliases[texture_name]
            texture_width = alias_metadata[texture_alias]["width"]
            texture_height = alias_metadata[texture_alias]["height"]
            source_uvs = [
                opq_to_pixel_uv(model.points[index], surface.uv_origin, surface.uv_u, surface.uv_v, texture_width, texture_height)
                for index in source_indices
            ]

            source_faces: list[tuple[list[int], list[tuple[int, int]]]]
            if (
                preserve_source_ngons
                and len(source_indices) <= MAX_BMODEL_FACE_VERTICES
                and source_polygon_can_be_preserved_as_ngon(source_indices)
            ):
                source_faces = [(source_indices, source_uvs)]
            else:
                stats["triangulated_polies"] += 1
                source_faces = triangulate_polygon_fan(source_indices, source_uvs)

            for face_indices, face_uvs in source_faces:
                # The LithTech X/Y/Z -> ODM X/Z/Y axis transform swaps handedness. Keep the same textured surface,
                # but reverse each emitted polygon so ODM plane normals point to the same side as the source DAT.
                face_indices, face_uvs = reverse_polygon_winding(face_indices, face_uvs)
                if poly.plane_index < len(model.planes):
                    source_normal = transformed_lt_plane_normal(model.planes[poly.plane_index])
                    emitted_normal = compute_unit_normal(bmodel.vertices, face_indices)
                    if (
                        source_normal is not None
                        and emitted_normal is not None
                        and vec_dot(source_normal, emitted_normal) < -0.75
                    ):
                        face_indices, face_uvs = reverse_polygon_winding(face_indices, face_uvs)
                        stats["source_plane_orientation_flips"] += 1
                append_source_face(
                    bmodel,
                    face_indices,
                    face_uvs,
                    "" if face_role.render_role == "hidden" else texture_alias,
                    0 if face_role.render_role == "hidden" else list(alias_metadata.keys()).index(texture_alias),
                    face_role,
                    poly_index,
                    poly.surface_index,
                    surface,
                    surface.texture_index,
                    stats,
                )

        if bmodel.vertices and bmodel.faces:
            bmodels.append(bmodel)

    baked_model_instances: list[BakedModelInstance] = []
    if extracted_root is not None:
        excluded_indices = excluded_baked_object_indices or set()
        model_index = build_case_insensitive_file_index(extracted_root / "MODELS" / "MODELS", ".abc")
        abc_cache: dict[Path, AbcModel] = {}
        floor_triangles = build_floor_support_triangles(dat_world)
        work_items: list[BakedModelWorkItem] = []
        properties_by_object_index: dict[int, dict[str, Any]] = {}

        for object_index, world_object in enumerate(dat_world.objects):
            properties = object_property_map(world_object)
            properties_by_object_index[object_index] = properties
            if object_index in excluded_indices:
                stats["baked_model_excluded_semantic_item_source"] += 1
                continue
            source_model = properties.get("filename")
            position = properties.get("pos")
            if not isinstance(source_model, str) or not source_model:
                continue
            if not is_model_source_path(source_model):
                continue
            if not isinstance(position, list) or len(position) != 3:
                continue

            source_class = world_object.name
            normalized_source_model = normalize_lithtech_virtual_path(source_model)
            if not should_bake_model_instance(source_class, normalized_source_model):
                stats["baked_model_skipped_actor_like"] += 1
                continue

            model_path = resolve_source_model_path(model_index, normalized_source_model)
            if model_path is None:
                stats["baked_model_missing_source"] += 1
                continue

            source_name = properties.get("name")
            if not isinstance(source_name, str) or not source_name:
                source_name = f"{world_object.name}{object_index}"
            rotation = properties.get("rotation")
            if not isinstance(rotation, list) or len(rotation) != 4:
                rotation = [0.0, 0.0, 0.0, 1.0]
            uniform_scale = properties.get("scale", 1.0)
            if not isinstance(uniform_scale, (int, float)):
                uniform_scale = 1.0
            source_skin = properties.get("skin", "")
            if not isinstance(source_skin, str):
                source_skin = ""
            source_skin = normalize_lithtech_virtual_path_list(source_skin)

            abc_model = abc_cache.get(model_path)
            if abc_model is None:
                try:
                    abc_model = read_abc(model_path)
                except Exception:
                    stats["baked_model_missing_source"] += 1
                    continue
                abc_cache[model_path] = abc_model

            placement_info = abc_static_model_placement_info(abc_model)
            raw_position = [float(position[0]), float(position[1]), float(position[2])]
            bake_position = list(raw_position)
            visual_offset_lt = [0.0, 0.0, 0.0]
            move_to_floor_property = properties.get("movetofloor")
            move_to_floor = truthy_property(move_to_floor_property, True)
            if move_to_floor_property is None:
                stats["baked_model_move_to_floor_defaulted"] += 1

            if move_to_floor and not object_skips_floor_placement(source_class, source_name):
                stats["baked_model_move_to_floor_requested"] += 1
                half_dims = placement_half_dims_lt(properties, placement_info, float(uniform_scale))
                bake_position, floor_status = move_position_to_floor_lt(raw_position, half_dims, floor_triangles)
                if floor_status == "snapped":
                    stats["baked_model_move_to_floor_snapped"] += 1
                elif floor_status == "already_supported":
                    stats["baked_model_move_to_floor_already_supported"] += 1
                elif floor_status == "no_support":
                    stats["baked_model_move_to_floor_no_support"] += 1
                elif floor_status == "missing_dims":
                    stats["baked_model_move_to_floor_missing_dims"] += 1

            plant_or_tree_source = is_plant_or_tree_prop_source(source_class, normalized_source_model)
            if (
                placement_info is not None
                and plant_or_tree_source
                and truthy_property(properties.get("visible"), True)
            ):
                model_height = max(0.0, placement_info.bounds.max[1] - placement_info.bounds.min[1])
                scale_y = abs(float(uniform_scale))
                ground_lift = max(0.0, -placement_info.bounds.min[1])
                visual_offset_y = ground_lift
                terrain_floor_y = floor_y_near_position_lt(
                    raw_position,
                    floor_triangles,
                    max(512.0, model_height * scale_y),
                )
                if terrain_floor_y is not None:
                    model_translation_lt = tuple(
                        placement_info.binding_origin[index] + (
                            visual_offset_y if index == 1 else visual_offset_lt[index]
                        )
                        for index in range(3)
                    )
                    bounds = transformed_model_aabb_lt(
                        bake_position,
                        rotation,
                        float(uniform_scale),
                        placement_info.bounds,
                        model_translation_lt,
                    )
                    terrain_delta = terrain_floor_y - bounds.min[1]
                    if abs(terrain_delta) > 0.25 and scale_y > 0.000001:
                        visual_offset_y = max(0.0, visual_offset_y + terrain_delta / scale_y)
                        stats["baked_model_visual_terrain_offset"] += 1
                    else:
                        stats["baked_model_visual_ground_lift"] += 1
                elif ground_lift > 0.0:
                    stats["baked_model_visual_ground_lift"] += 1
                visual_offset_lt[1] = visual_offset_y

            if (
                placement_info is not None
                and source_model_is_authored_floor_contact(normalized_source_model)
                and not move_to_floor
                and truthy_property(properties.get("visible"), True)
                and truthy_property(properties.get("rayhit"), False)
            ):
                floor_y = floor_y_under_position_lt(raw_position, floor_triangles, max_drop_distance=10000.0)
                if floor_y is not None:
                    model_translation_lt = tuple(
                        placement_info.binding_origin[index] + visual_offset_lt[index]
                        for index in range(3)
                    )
                    bounds = transformed_model_aabb_lt(
                        raw_position,
                        rotation,
                        float(uniform_scale),
                        placement_info.bounds,
                        model_translation_lt,
                    )
                    bottom_y = bounds.min[1]
                    scale_y = abs(float(uniform_scale))
                    if bottom_y < floor_y - 0.25 and scale_y > 0.000001:
                        visual_offset_lt[1] += (floor_y - bottom_y + 0.1) / scale_y
                        stats["baked_model_visual_floor_lift"] += 1

            work_items.append(BakedModelWorkItem(
                object_index=object_index,
                source_class=source_class,
                source_name=source_name,
                source_model=normalized_source_model,
                source_skin=source_skin,
                position_lt=bake_position,
                raw_position_lt=raw_position,
                rotation_lt=rotation,
                uniform_scale=float(uniform_scale),
                visual_offset_lt=tuple(visual_offset_lt),
                placement_kind="move_to_floor_world" if bake_position != raw_position else "",
                abc_model=abc_model,
                placement_info=placement_info,
                plant_or_tree_source=plant_or_tree_source,
                move_to_floor=move_to_floor,
                solid=truthy_property(properties.get("solid"), False),
                ray_hit=truthy_property(properties.get("rayhit"), False),
            ))

            for variant_index, (variant_model, variant_skin) in enumerate(
                (baked_model_variant_sources or {}).get(object_index, []),
                start=1,
            ):
                normalized_variant_model = normalize_lithtech_virtual_path(variant_model)
                variant_path = resolve_source_model_path(model_index, normalized_variant_model)
                if variant_path is None:
                    raise ValueError(
                        f"MM9 object {object_index} persistent model variant is missing: {variant_model}")
                variant_abc_model = abc_cache.get(variant_path)
                if variant_abc_model is None:
                    variant_abc_model = read_abc(variant_path)
                    abc_cache[variant_path] = variant_abc_model
                work_items.append(BakedModelWorkItem(
                    object_index=object_index,
                    source_class=source_class,
                    source_name=source_name,
                    source_model=normalized_variant_model,
                    source_skin=normalize_lithtech_virtual_path_list(variant_skin),
                    position_lt=list(bake_position),
                    raw_position_lt=list(raw_position),
                    rotation_lt=list(rotation),
                    uniform_scale=float(uniform_scale),
                    visual_offset_lt=tuple(visual_offset_lt),
                    placement_kind="persistent_model_variant",
                    abc_model=variant_abc_model,
                    placement_info=abc_static_model_placement_info(variant_abc_model),
                    plant_or_tree_source=False,
                    move_to_floor=False,
                    solid=truthy_property(properties.get("solid"), False),
                    ray_hit=truthy_property(properties.get("rayhit"), False),
                    variant_index=variant_index,
                ))

        apply_model_support_floor_pass(work_items, properties_by_object_index, floor_triangles)
        apply_model_support_floor_pass(work_items, properties_by_object_index, floor_triangles)

        for work_item in work_items:
            if work_item.move_to_floor and work_item.placement_info is not None:
                floor_y = floor_y_under_position_lt(work_item.position_lt, floor_triangles)
                if floor_y is not None:
                    model_translation_lt = tuple(
                        work_item.placement_info.binding_origin[index] + work_item.visual_offset_lt[index]
                        for index in range(3)
                    )
                    bounds = transformed_model_aabb_lt(
                        work_item.position_lt,
                        work_item.rotation_lt,
                        work_item.uniform_scale,
                        work_item.placement_info.bounds,
                        model_translation_lt,
                    )
                    scale_y = abs(work_item.uniform_scale)
                    if bounds.min[1] < floor_y - 0.25 and scale_y > 0.000001:
                        visual_offset = list(work_item.visual_offset_lt)
                        visual_offset[1] += (floor_y - bounds.min[1] + 0.1) / scale_y
                        work_item.visual_offset_lt = tuple(visual_offset)
                        stats["baked_model_visual_floor_lift"] += 1

            source_model_index = len(dat_world.world_models) + len(baked_model_instances)
            bmodel = bake_abc_model_instance(
                work_item.abc_model,
                work_item.object_index,
                work_item.source_class,
                work_item.source_name,
                work_item.source_model,
                work_item.source_skin,
                work_item.position_lt,
                work_item.rotation_lt,
                work_item.uniform_scale,
                scale,
                texture_sizes,
                aliases_by_source,
                alias_metadata,
                used_aliases,
                source_model_index,
                work_item.visual_offset_lt,
            )
            if work_item.variant_index > 0:
                bmodel.name += f"_variant_{work_item.variant_index}"
            if not bmodel.faces:
                stats["baked_model_empty"] += 1
                continue

            bmodels.append(bmodel)
            bmodel_index = len(bmodels) - 1
            kind = baked_model_kind(work_item.source_class, work_item.source_model)
            destructible = kind == "destructible_prop"
            baked_model_instances.append(BakedModelInstance(
                source_object_index=work_item.object_index,
                source_class=work_item.source_class,
                source_name=work_item.source_name,
                source_model=work_item.source_model,
                source_skin=work_item.source_skin,
                bmodel_index=bmodel_index,
                bmodel_name=bmodel.name,
                kind=kind,
                destructible=destructible,
                placement_kind=work_item.placement_kind,
                source_position_lt=list(work_item.raw_position_lt),
                bake_position_lt=list(work_item.position_lt),
                visual_offset_lt=list(work_item.visual_offset_lt),
                variant_index=work_item.variant_index,
            ))
            stats["baked_model_instances"] += 1
            stats["baked_model_faces"] += len(bmodel.faces)
            if work_item.placement_kind == "move_to_floor_model_snapped":
                stats["baked_model_move_to_floor_model_snapped"] += 1
            elif work_item.placement_kind == "move_to_floor_model_already_supported":
                stats["baked_model_move_to_floor_model_already_supported"] += 1
            if destructible:
                stats["baked_model_destructible_props"] += 1
            elif kind == "chest":
                stats["baked_model_chests"] += 1
            elif kind == "pickup":
                stats["baked_model_pickups"] += 1

    alias_indices = {alias: index for index, alias in enumerate(alias_metadata.keys())}
    for bmodel in bmodels:
        for face in bmodel.faces:
            face.bitmap_index = alias_indices.get(face.texture_alias, 0)

    return bmodels, alias_metadata, stats, baked_model_instances


def pack_fixed_string(text: str, length: int) -> bytes:
    raw = text.encode("ascii", errors="replace")[:length]
    return raw + b"\0" * (length - len(raw))


def append_i16(data: bytearray, value: int) -> None:
    data += struct.pack("<h", value)


def append_u16(data: bytearray, value: int) -> None:
    data += struct.pack("<H", value)


def append_i32(data: bytearray, value: int) -> None:
    data += struct.pack("<i", value)


def append_u32(data: bytearray, value: int) -> None:
    data += struct.pack("<I", value)


def bmodel_bounds(bmodel: OdmBModel) -> dict[str, int]:
    min_x = min(vertex.x for vertex in bmodel.vertices)
    min_y = min(vertex.y for vertex in bmodel.vertices)
    min_z = min(vertex.z for vertex in bmodel.vertices)
    max_x = max(vertex.x for vertex in bmodel.vertices)
    max_y = max(vertex.y for vertex in bmodel.vertices)
    max_z = max(vertex.z for vertex in bmodel.vertices)
    center_x = round((min_x + max_x) * 0.5)
    center_y = round((min_y + max_y) * 0.5)
    center_z = round((min_z + max_z) * 0.5)
    radius = 0
    for vertex in bmodel.vertices:
        dx = vertex.x - center_x
        dy = vertex.y - center_y
        dz = vertex.z - center_z
        radius = max(radius, math.ceil(math.sqrt(dx * dx + dy * dy + dz * dz)))
    return {
        "position_x": center_x,
        "position_y": center_y,
        "position_z": center_z,
        "min_x": min_x,
        "min_y": min_y,
        "min_z": min_z,
        "max_x": max_x,
        "max_y": max_y,
        "max_z": max_z,
        "center_x": center_x,
        "center_y": center_y,
        "center_z": center_z,
        "radius": radius,
    }


def write_i32_at(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 4] = struct.pack("<i", value)


def write_u8_at(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 1] = struct.pack("<B", value)


def write_u16_at(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 2] = struct.pack("<H", value)


def write_i16_at(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 2] = struct.pack("<h", value)


def write_fixed_string_at(data: bytearray, offset: int, length: int, text: str) -> None:
    data[offset:offset + length] = pack_fixed_string(text, length)


def build_odm_bytes(name: str, bmodels: list[OdmBModel], entities: list[OdmEntity] | None = None) -> bytes:
    entities = entities or []
    data = bytearray(0xB4)
    write_fixed_string_at(data, 0x00, 0x20, name)
    write_fixed_string_at(data, 0x20, 0x20, f"{name}.odm")
    write_fixed_string_at(data, 0x60, 0x20, "")
    write_fixed_string_at(data, 0x80, 0x20, "planset")

    data += b"\0" * TERRAIN_MAP_SIZE
    data += b"\0" * TERRAIN_MAP_SIZE
    data += b"\0" * TERRAIN_MAP_SIZE
    append_i32(data, 0)
    data += b"\0" * CMAP1_SIZE
    data += b"\0" * CMAP2_SIZE

    append_i32(data, len(bmodels))
    for bmodel in bmodels:
        header = bytearray(BMODEL_HEADER_SIZE)
        bounds = bmodel_bounds(bmodel)
        write_fixed_string_at(header, 0x00, 0x20, bmodel.name)
        write_fixed_string_at(header, 0x20, 0x20, bmodel.name)
        write_i32_at(header, 0x44, len(bmodel.vertices))
        write_i32_at(header, 0x4C, len(bmodel.faces))
        write_i32_at(header, 0x5C, 0)
        write_i32_at(header, 0x68, bounds["position_x"])
        write_i32_at(header, 0x6C, bounds["position_y"])
        write_i32_at(header, 0x70, bounds["position_z"])
        write_i32_at(header, 0x74, bounds["min_x"])
        write_i32_at(header, 0x78, bounds["min_y"])
        write_i32_at(header, 0x7C, bounds["min_z"])
        write_i32_at(header, 0x80, bounds["max_x"])
        write_i32_at(header, 0x84, bounds["max_y"])
        write_i32_at(header, 0x88, bounds["max_z"])
        write_i32_at(header, 0xA8, bounds["center_x"])
        write_i32_at(header, 0xAC, bounds["center_y"])
        write_i32_at(header, 0xB0, bounds["center_z"])
        write_i32_at(header, 0xB4, bounds["radius"])
        data += header

    for bmodel in bmodels:
        for vertex in bmodel.vertices:
            append_i32(data, vertex.x)
            append_i32(data, vertex.y)
            append_i32(data, vertex.z)

        for face in bmodel.faces:
            face_bytes = bytearray(BMODEL_FACE_SIZE)
            write_i32_at(face_bytes, 0x00, face.plane_normal[0])
            write_i32_at(face_bytes, 0x04, face.plane_normal[1])
            write_i32_at(face_bytes, 0x08, face.plane_normal[2])
            write_i32_at(face_bytes, 0x0C, face.plane_distance)
            write_i32_at(face_bytes, 0x1C, face.attributes)
            write_i16_at(face_bytes, 0x110, face.bitmap_index)
            write_i16_at(face_bytes, 0x112, 0)
            write_i16_at(face_bytes, 0x114, 0)
            write_u16_at(face_bytes, 0x122, 0)
            write_u16_at(face_bytes, 0x124, 0)
            write_u16_at(face_bytes, 0x126, 0)
            write_u16_at(face_bytes, 0x128, face.reserved)
            write_u8_at(face_bytes, 0x12E, len(face.vertex_indices))
            write_u8_at(face_bytes, 0x12F, face.polygon_type)
            write_u8_at(face_bytes, 0x130, 0)
            write_u8_at(face_bytes, 0x131, 31)
            for index, vertex_index in enumerate(face.vertex_indices):
                write_u16_at(face_bytes, 0x20 + index * 2, vertex_index)
                write_i16_at(face_bytes, 0x48 + index * 2, face.texture_us[index])
                write_i16_at(face_bytes, 0x70 + index * 2, face.texture_vs[index])
            data += face_bytes

        data += b"\0" * (len(bmodel.faces) * BMODEL_FACE_FLAGS_SIZE)
        for face in bmodel.faces:
            data += pack_fixed_string(face.texture_alias, BMODEL_TEXTURE_NAME_SIZE)

    append_i32(data, len(entities))
    for entity in entities:
        entity_bytes = bytearray(ODM_ENTITY_SIZE)
        write_u16_at(entity_bytes, 0x00, entity.decoration_list_id)
        write_u16_at(entity_bytes, 0x02, entity.ai_attributes)
        write_i32_at(entity_bytes, 0x04, entity.x)
        write_i32_at(entity_bytes, 0x08, entity.y)
        write_i32_at(entity_bytes, 0x0C, entity.z)
        write_i32_at(entity_bytes, 0x10, entity.facing)
        write_u16_at(entity_bytes, 0x14, entity.event_id_primary)
        write_u16_at(entity_bytes, 0x16, entity.event_id_secondary)
        write_u16_at(entity_bytes, 0x18, entity.variable_primary)
        write_u16_at(entity_bytes, 0x1A, entity.variable_secondary)
        write_u16_at(entity_bytes, 0x1C, entity.special_trigger)
        data += entity_bytes
    for entity in entities:
        data += pack_fixed_string(entity.name, ODM_ENTITY_NAME_SIZE)
    append_i32(data, 0)
    data += b"\0" * (TERRAIN_MAP_SIZE * 4)
    append_i32(data, 0)
    return bytes(data)


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    return str(value)


def object_property_map(world_object: WorldObject) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for prop in world_object.properties:
        if not prop.decoded:
            continue
        values[prop.name.lower()] = prop.value
    return values


def is_mm9_light_class(source_class: str) -> bool:
    return source_class.lower() in {"light", "dirlight", "objectlight", "staticsunlight"}


def float_property(value: Any, default: float) -> float:
    result = default
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value)
        except ValueError:
            result = default
    if not math.isfinite(result):
        return default
    return result


def color_tuple_property(value: Any, default: tuple[int, int, int]) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) < 3:
        return default
    channels: list[int] = []
    for channel in value[:3]:
        if isinstance(channel, (int, float)):
            channels.append(max(0, min(255, int(round(channel)))))
        else:
            return default
    return (channels[0], channels[1], channels[2])


def export_mm9_authored_fog(
    dat_world: DatWorld,
    coordinate_scale: float,
) -> tuple[Mm9AuthoredFogState, Mm9AuthoredFogState] | None:
    named_objects: dict[str, WorldObject] = {}
    for world_object in dat_world.objects:
        properties = object_property_map(world_object)
        source_name = properties.get("name")
        if isinstance(source_name, str) and source_name:
            named_objects[source_name.lower()] = world_object

    def fog_state(source_name: Any) -> Mm9AuthoredFogState | None:
        if not isinstance(source_name, str) or not source_name:
            return None
        fog_object = named_objects.get(source_name.lower())
        if fog_object is None or fog_object.name.lower() != "fog":
            return None
        properties = object_property_map(fog_object)
        near_distance = max(
            0,
            int(round(float_property(properties.get("fognearz"), 0.0) * coordinate_scale)),
        )
        far_distance = max(
            near_distance + 1,
            int(round(float_property(properties.get("fogfarz"), 0.0) * coordinate_scale)),
        )
        return Mm9AuthoredFogState(
            enabled=truthy_property(properties.get("fogenable"), False),
            near_distance=near_distance,
            far_distance=far_distance,
            color=color_tuple_property(properties.get("fogcolor"), (0, 0, 0)),
        )

    for world_object in dat_world.objects:
        if world_object.name.lower() != "weatherman":
            continue
        properties = object_property_map(world_object)
        if not truthy_property(properties.get("starton"), False):
            continue
        fog_on = fog_state(properties.get("fogon"))
        fog_off = fog_state(properties.get("fogoff"))
        if fog_on is None:
            continue
        if truthy_property(properties.get("turnonatnight"), False):
            return (fog_off or fog_on, fog_on)
        if truthy_property(properties.get("turnoffatnight"), False):
            return (fog_on, fog_off or fog_on)
        return (fog_on, fog_on)

    for world_object in dat_world.objects:
        if world_object.name.lower() != "fog":
            continue
        properties = object_property_map(world_object)
        if not truthy_property(properties.get("starton"), False):
            continue
        state = fog_state(properties.get("name"))
        if state is not None:
            return (state, state)

    return None


def scaled_color(color: tuple[int, int, int], scale: float) -> tuple[int, int, int]:
    if not math.isfinite(scale):
        scale = 1.0
    return tuple(max(0, min(255, int(round(channel * scale)))) for channel in color)


def int_property(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return default
    return default


def export_mm9_party_start_points(dat_world: DatWorld, coordinate_scale: float) -> tuple[list[PartyStartPoint], dict[str, int]]:
    starts: list[PartyStartPoint] = []
    skipped = 0

    for object_index, world_object in enumerate(dat_world.objects):
        if world_object.name != "StartPoint":
            continue

        properties = object_property_map(world_object)
        position_lt = properties.get("pos")
        if not isinstance(position_lt, list) or len(position_lt) < 3:
            skipped += 1
            continue

        rotation_lt = properties.get("rotation")
        if not isinstance(rotation_lt, list) or len(rotation_lt) < 4:
            rotation_lt = [0.0, 0.0, 0.0, 0.0]

        source_name = str(properties.get("name") or f"StartPoint{len(starts)}")
        starts.append(PartyStartPoint(
            start_index=len(starts),
            source_object_index=object_index,
            source_name=source_name,
            source_position_lt=[float(value) for value in position_lt[:3]],
            position=lt_vec_to_odm_tuple(position_lt, coordinate_scale),
            source_rotation_lt=[float(value) for value in rotation_lt[:4]],
            direction_yaw_units=lt_rotation_to_openyamm_yaw_units(rotation_lt),
            direction_degrees=lt_rotation_to_openyamm_yaw_degrees(rotation_lt),
            team_number=int_property(properties.get("teamnbr"), 0),
            player_number=int_property(properties.get("playernbr"), 0),
            move_player_to_floor=truthy_property(properties.get("moveplayertofloor"), True),
        ))

    return starts, {
        "party_start_points": len(starts),
        "party_start_points_skipped": skipped,
    }


def build_mm9_party_start_point_lines(starts: list[PartyStartPoint]) -> list[str]:
    if not starts:
        return ["  []"]

    lines: list[str] = []
    for start in starts:
        lines.extend([
            f"  - start_index: {start.start_index}",
            f"    source_object_index: {start.source_object_index}",
            '    source_class: "StartPoint"',
            f"    source_name: {yaml_scalar(start.source_name)}",
            "    source_position_lt: ["
            f"{start.source_position_lt[0]:.8g}, {start.source_position_lt[1]:.8g}, "
            f"{start.source_position_lt[2]:.8g}]",
            f"    position: {{x: {start.position[0]}, y: {start.position[1]}, z: {start.position[2]}}}",
            "    source_rotation_lt: ["
            f"{start.source_rotation_lt[0]:.8g}, {start.source_rotation_lt[1]:.8g}, "
            f"{start.source_rotation_lt[2]:.8g}, {start.source_rotation_lt[3]:.8g}]",
            f"    direction_yaw_units: {start.direction_yaw_units}",
            f"    direction_degrees: {start.direction_degrees:.8g}",
            f"    team_number: {start.team_number}",
            f"    player_number: {start.player_number}",
            f"    move_player_to_floor: {str(start.move_player_to_floor).lower()}",
        ])
    return lines


def default_party_start_point(starts: list[PartyStartPoint]) -> PartyStartPoint | None:
    if not starts:
        return None

    for start in starts:
        if start.source_name.lower() == "startpoint0":
            return start

    return starts[0]


def build_classic_party_start_entities(starts: list[PartyStartPoint]) -> list[OdmEntity]:
    start = default_party_start_point(starts)
    if start is None:
        return []

    return [OdmEntity(
        name="party start",
        decoration_list_id=0,
        ai_attributes=0,
        x=start.position[0],
        y=start.position[1],
        z=start.position[2],
        facing=int(round(start.direction_degrees)) % 360,
    )]


def build_odm_entity_lines(entities: list[OdmEntity]) -> list[str]:
    if not entities:
        return ["  []"]

    lines: list[str] = []
    for entity_index, entity in enumerate(entities):
        lines.extend([
            f"  - entity_index: {entity_index}",
            f"    name: {yaml_scalar(entity.name)}",
            f"    decoration_list_id: {entity.decoration_list_id}",
            f"    ai_attributes: {entity.ai_attributes}",
            f"    position: {{x: {entity.x}, y: {entity.y}, z: {entity.z}}}",
            f"    facing: {entity.facing}",
            f"    event_id_primary: {entity.event_id_primary}",
            f"    event_id_secondary: {entity.event_id_secondary}",
            f"    variable_primary: {entity.variable_primary}",
            f"    variable_secondary: {entity.variable_secondary}",
            f"    special_trigger: {entity.special_trigger}",
            f"    initial_decoration_flag: {entity.initial_decoration_flag}",
        ])
    return lines


def export_mm9_lights(dat_world: DatWorld, scale: float) -> tuple[list[ExportedLight], dict[str, int]]:
    lights: list[ExportedLight] = []
    stats = {
        "light_objects": 0,
        "light_missing_position": 0,
        "light_static_object_eligible": 0,
    }
    for object_index, world_object in enumerate(dat_world.objects):
        source_class = world_object.name
        if not is_mm9_light_class(source_class):
            continue

        stats["light_objects"] += 1
        properties = object_property_map(world_object)
        position = properties.get("pos")
        if not isinstance(position, list) or len(position) < 3:
            stats["light_missing_position"] += 1
            continue

        source_name = properties.get("name")
        if not isinstance(source_name, str) or not source_name:
            source_name = f"{source_class}{object_index}"

        source_class_lower = source_class.lower()
        global_object_light = source_class_lower == "staticsunlight"
        default_light_objects = source_class_lower in {"light", "dirlight", "staticsunlight"}
        default_fast_light_objects = source_class_lower in {"light", "dirlight", "objectlight", "staticsunlight"}
        light_objects = truthy_property(properties.get("lightobjects"), default_light_objects)
        fast_light_objects = truthy_property(properties.get("fastlightobjects"), default_fast_light_objects)
        static_object_light_eligible = light_objects and not fast_light_objects and not global_object_light
        if static_object_light_eligible:
            stats["light_static_object_eligible"] += 1

        color_property_name = (
            "innercolor" if source_class_lower in {"dirlight", "staticsunlight"} else "lightcolor"
        )
        color = color_tuple_property(properties.get(color_property_name), (255, 255, 255))
        brightness_scale = float_property(properties.get("brightscale"), 1.0)
        object_brightness_scale = float_property(properties.get("objectbrightscale"), 1.0)
        effective_color = scaled_color(color, brightness_scale * object_brightness_scale)
        radius_lt = max(0.0, float_property(properties.get("lightradius"), 300.0))
        radius = max(0, int(round(radius_lt * scale)))
        light_group = properties.get("lightgroup", "")
        if not isinstance(light_group, str):
            light_group = ""
        rotation = properties.get("rotation")
        if not isinstance(rotation, list) or len(rotation) < 4:
            rotation = [0.0, 0.0, 0.0, 0.0]

        lights.append(ExportedLight(
            source_object_index=object_index,
            source_class=source_class,
            source_name=source_name,
            source_position_lt=(float(position[0]), float(position[1]), float(position[2])),
            position=lt_vec_to_odm_tuple(position, scale),
            source_radius_lt=radius_lt,
            radius=radius,
            color=color,
            effective_color=effective_color,
            light_type="directional" if source_class_lower in {"dirlight", "staticsunlight"} else "point",
            light_objects=light_objects,
            fast_light_objects=fast_light_objects,
            static_object_light_eligible=static_object_light_eligible,
            global_object_light=global_object_light,
            light_group=light_group,
            source_rotation_lt=tuple(float(value) for value in rotation[:4]),
            fov_degrees=float_property(properties.get("fov"), 90.0),
            brightness_scale=brightness_scale,
            object_brightness_scale=object_brightness_scale,
            cast_shadows=truthy_property(properties.get("castshadows"), True),
            clip_light=truthy_property(properties.get("cliplight"), source_class_lower in {"light", "dirlight"}),
        ))
    return lights, stats


def ensure_mm9_city_sunlight(map_name: str, lights: list[ExportedLight]) -> bool:
    if not map_name.lower().endswith("city") or any(light.global_object_light for light in lights):
        return False

    lights.append(ExportedLight(
        source_object_index=0xFFFFFFFF,
        source_class="StaticSunLight",
        source_name="OpenYAMMCitySunLight",
        source_position_lt=(0.0, 0.0, 0.0),
        position=(0, 0, 0),
        source_radius_lt=0.0,
        radius=0,
        color=(255, 255, 255),
        effective_color=(179, 179, 179),
        light_type="directional",
        light_objects=True,
        fast_light_objects=True,
        static_object_light_eligible=False,
        global_object_light=True,
        light_group="",
        source_rotation_lt=(1.0471976, 1.0471976, 0.0, 0.0),
        fov_degrees=90.0,
        brightness_scale=0.7,
        object_brightness_scale=1.0,
        cast_shadows=False,
        clip_light=False,
    ))
    return True


def build_mm9_light_lines(lights: list[ExportedLight]) -> list[str]:
    lines: list[str] = []
    for light in lights:
        lines.extend([
            f"  - source_object_index: {light.source_object_index}",
            f"    source_class: {yaml_scalar(light.source_class)}",
            f"    source_name: {yaml_scalar(light.source_name)}",
            "    source_position_lt: ["
            f"{light.source_position_lt[0]:.8g}, {light.source_position_lt[1]:.8g}, "
            f"{light.source_position_lt[2]:.8g}]",
            f"    position: {{x: {light.position[0]}, y: {light.position[1]}, z: {light.position[2]}}}",
            f"    source_radius_lt: {light.source_radius_lt:.8g}",
            f"    radius: {light.radius}",
            f"    color: [{light.color[0]}, {light.color[1]}, {light.color[2]}]",
            "    effective_color: ["
            f"{light.effective_color[0]}, {light.effective_color[1]}, {light.effective_color[2]}]",
            f"    type: {yaml_scalar(light.light_type)}",
            "    source_rotation_lt: ["
            f"{light.source_rotation_lt[0]:.8g}, {light.source_rotation_lt[1]:.8g}, "
            f"{light.source_rotation_lt[2]:.8g}, {light.source_rotation_lt[3]:.8g}]",
            f"    fov_degrees: {light.fov_degrees:.8g}",
            f"    brightness_scale: {light.brightness_scale:.8g}",
            f"    object_brightness_scale: {light.object_brightness_scale:.8g}",
            f"    cast_shadows: {yaml_scalar(light.cast_shadows)}",
            f"    clip_light: {yaml_scalar(light.clip_light)}",
            f"    light_objects: {yaml_scalar(light.light_objects)}",
            f"    fast_light_objects: {yaml_scalar(light.fast_light_objects)}",
            f"    static_object_light_eligible: {yaml_scalar(light.static_object_light_eligible)}",
            f"    global_object_light: {yaml_scalar(light.global_object_light)}",
        ])
        if light.light_group:
            lines.append(f"    light_group: {yaml_scalar(light.light_group)}")
    return lines


def parse_world_ambient_color(world_info: WorldInfo) -> tuple[int, int, int]:
    match = re.search(
        r"(?:^|[;\s])AmbientLight\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)",
        world_info.properties,
        re.IGNORECASE,
    )
    if match is None:
        return (255, 255, 255)
    return tuple(max(0, min(255, int(round(float(value))))) for value in match.groups())


def normalized_tuple(value: tuple[float, float, float]) -> tuple[float, float, float] | None:
    length = math.sqrt(vec_dot(value, value))
    if length <= 0.0001:
        return None
    return (value[0] / length, value[1] / length, value[2] / length)


def lightmap_basis(normal: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    principal_normals = (
        (0.0, 1.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, -1.0),
        (1.0, 0.0, 0.0),
        (-1.0, 0.0, 0.0),
    )
    principal_v = (
        (0.0, 0.0, -1.0),
        (0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, -1.0, 0.0),
    )
    plane_index = max(range(len(principal_normals)), key=lambda index: vec_dot(principal_normals[index], normal))
    axis_u = vec_cross(normal, principal_v[plane_index])
    axis_v = vec_cross(axis_u, normal)
    return axis_u, axis_v


def add_scaled_tuple(
    value: tuple[float, float, float],
    axis: tuple[float, float, float],
    scale: float,
) -> tuple[float, float, float]:
    return (
        value[0] + axis[0] * scale,
        value[1] + axis[1] * scale,
        value[2] + axis[2] * scale,
    )


def adjusted_lightmap_origin(
    origin: tuple[float, float, float],
    axis: tuple[float, float, float],
    grid_size: float,
) -> tuple[float, float, float]:
    unit_axis = normalized_tuple(axis)
    if unit_axis is None:
        return origin
    offset = math.fmod(vec_dot(unit_axis, origin), grid_size)
    snap_distance = offset if offset >= 0.0 else grid_size + offset
    return add_scaled_tuple(origin, unit_axis, -snap_distance)


def lightmap_uvs_for_poly(
    model: WorldBsp,
    poly: Poly,
    point_indices: list[int],
    grid_size: float,
) -> list[tuple[float, float]]:
    if (
        poly.lightmap_width <= 0
        or poly.lightmap_height <= 0
        or grid_size <= 0.0001
        or len(poly.disk_verts) < 3
    ):
        return [(0.5, 0.5)] * len(point_indices)

    source_points = [model.points[vertex.vertex_index] for vertex in poly.disk_verts]
    edge_a = vec_sub_lt(source_points[1], source_points[0])
    normal: tuple[float, float, float] | None = None
    for point in source_points[2:]:
        edge_b = vec_sub_lt(point, source_points[0])
        normal = normalized_tuple(vec_cross(edge_a, edge_b))
        if normal is not None:
            break
    if normal is None:
        return [(0.5, 0.5)] * len(point_indices)

    axis_u, axis_v = lightmap_basis(normal)
    unit_u = normalized_tuple(axis_u)
    unit_v = normalized_tuple(axis_v)
    if unit_u is None or unit_v is None:
        return [(0.5, 0.5)] * len(point_indices)

    origin = source_points[0]
    for point in source_points:
        offset_u = vec_dot(unit_u, vec_sub_lt(point, origin))
        if offset_u < 0.0:
            origin = add_scaled_tuple(origin, unit_u, offset_u)
        offset_v = vec_dot(unit_v, vec_sub_lt(point, origin))
        if offset_v < 0.0:
            origin = add_scaled_tuple(origin, unit_v, offset_v)
    origin = adjusted_lightmap_origin(origin, axis_u, grid_size)
    origin = adjusted_lightmap_origin(origin, axis_v, grid_size)

    result: list[tuple[float, float]] = []
    for point_index in point_indices:
        offset = vec_sub_lt(model.points[point_index], origin)
        pixel_u = vec_dot(offset, axis_u) / grid_size + 0.5
        pixel_v = vec_dot(offset, axis_v) / grid_size + 0.5
        result.append((1.0 - pixel_u / poly.lightmap_width, pixel_v / poly.lightmap_height))
    return result


def pack_lightmap_atlases(
    lightmaps: dict[tuple[int, int], Poly],
) -> tuple[list[LightmapAtlasPage], dict[tuple[int, int], LightmapAtlasRect]]:
    page_layouts: list[dict[str, Any]] = []
    rects: dict[tuple[int, int], LightmapAtlasRect] = {}
    ordered_lightmaps = sorted(
        lightmaps.items(),
        key=lambda entry: (-(entry[1].lightmap_height + 2), -(entry[1].lightmap_width + 2), entry[0]),
    )

    for key, poly in ordered_lightmaps:
        outer_width = poly.lightmap_width + 2
        outer_height = poly.lightmap_height + 2
        if outer_width > OUTDOOR_LIGHTING_ATLAS_MAX_WIDTH or outer_height > OUTDOOR_LIGHTING_ATLAS_MAX_WIDTH:
            raise DatParseError(f"MM9 lightmap {key} does not fit an atlas page")

        placement: tuple[int, int, int] | None = None
        for page_index, page in enumerate(page_layouts):
            for shelf in page["shelves"]:
                if outer_height <= shelf["height"] and shelf["x"] + outer_width <= OUTDOOR_LIGHTING_ATLAS_MAX_WIDTH:
                    placement = (page_index, shelf["x"], shelf["y"])
                    shelf["x"] += outer_width
                    break
            if placement is not None:
                break
            next_y = page["height"]
            if next_y + outer_height <= OUTDOOR_LIGHTING_ATLAS_MAX_WIDTH:
                page["shelves"].append({"x": outer_width, "y": next_y, "height": outer_height})
                page["height"] += outer_height
                placement = (page_index, 0, next_y)
                break

        if placement is None:
            page_layouts.append({
                "shelves": [{"x": outer_width, "y": 4, "height": outer_height}],
                "height": outer_height + 4,
            })
            placement = (len(page_layouts) - 1, 0, 4)

        page_index, outer_x, outer_y = placement
        rects[key] = LightmapAtlasRect(
            page_index=page_index,
            x=outer_x + 1,
            y=outer_y + 1,
            width=poly.lightmap_width,
            height=poly.lightmap_height,
        )

    pages: list[LightmapAtlasPage] = []
    for page_index, layout in enumerate(page_layouts):
        used_width = 1
        for rect in rects.values():
            if rect.page_index == page_index:
                used_width = max(used_width, rect.x + rect.width + 1)
        width = used_width
        height = max(1, layout["height"])
        pages.append(LightmapAtlasPage(width, height, [0xFFFFFFFF] * (width * height)))

    for key, poly in lightmaps.items():
        rect = rects[key]
        page = pages[rect.page_index]
        for y in range(rect.height):
            source_offset = y * rect.width
            target_offset = (rect.y + y) * page.width + rect.x
            page.pixels_bgra[target_offset:target_offset + rect.width] = (
                poly.lightmap_pixels_bgra[source_offset:source_offset + rect.width]
            )
        for x in range(rect.width):
            page.pixels_bgra[(rect.y - 1) * page.width + rect.x + x] = (
                page.pixels_bgra[rect.y * page.width + rect.x + x]
            )
            page.pixels_bgra[(rect.y + rect.height) * page.width + rect.x + x] = (
                page.pixels_bgra[(rect.y + rect.height - 1) * page.width + rect.x + x]
            )
        for y in range(rect.height):
            page.pixels_bgra[(rect.y + y) * page.width + rect.x - 1] = (
                page.pixels_bgra[(rect.y + y) * page.width + rect.x]
            )
            page.pixels_bgra[(rect.y + y) * page.width + rect.x + rect.width] = (
                page.pixels_bgra[(rect.y + y) * page.width + rect.x + rect.width - 1]
            )
        page.pixels_bgra[(rect.y - 1) * page.width + rect.x - 1] = page.pixels_bgra[rect.y * page.width + rect.x]
        page.pixels_bgra[(rect.y - 1) * page.width + rect.x + rect.width] = (
            page.pixels_bgra[rect.y * page.width + rect.x + rect.width - 1]
        )
        page.pixels_bgra[(rect.y + rect.height) * page.width + rect.x - 1] = (
            page.pixels_bgra[(rect.y + rect.height - 1) * page.width + rect.x]
        )
        page.pixels_bgra[(rect.y + rect.height) * page.width + rect.x + rect.width] = (
            page.pixels_bgra[(rect.y + rect.height - 1) * page.width + rect.x + rect.width - 1]
        )

    return pages, rects


def abgr_color(red: float, green: float, blue: float) -> int:
    red_byte = max(0, min(255, int(round(red * 255.0))))
    green_byte = max(0, min(255, int(round(green * 255.0))))
    blue_byte = max(0, min(255, int(round(blue * 255.0))))
    return 0xFF000000 | (blue_byte << 16) | (green_byte << 8) | red_byte


def static_object_light_color(
    vertex: OdmVertex,
    ambient: tuple[int, int, int],
    lights: list[ExportedLight],
) -> int:
    color = [channel / 255.0 for channel in ambient]
    for light in lights:
        if light.global_object_light:
            for channel in range(3):
                color[channel] += light.effective_color[channel] / 255.0 * 0.7
            continue
        if not light.static_object_light_eligible or light.radius <= 0:
            continue
        dx = float(vertex.x - light.position[0])
        dy = float(vertex.y - light.position[1])
        dz = float(vertex.z - light.position[2])
        distance_squared = dx * dx + dy * dy + dz * dz
        radius_squared = float(light.radius * light.radius)
        if distance_squared >= radius_squared:
            continue
        attenuation = 1.0 - distance_squared / radius_squared
        attenuation *= attenuation
        for channel in range(3):
            color[channel] += light.effective_color[channel] / 255.0 * attenuation
    return abgr_color(min(color[0], 1.0), min(color[1], 1.0), min(color[2], 1.0))


def normalize_lithtech_virtual_path(value: str, lowercase: bool = False) -> str:
    normalized = value.replace("\\", "/").strip()
    while normalized.startswith("/"):
        normalized = normalized[1:]
    parts = [part for part in normalized.split("/") if part and part != "."]
    if len(parts) >= 2 and parts[0].lower() == parts[1].lower():
        parts = parts[1:]
    normalized = "/".join(parts)
    return normalized.lower() if lowercase else normalized


def normalize_lithtech_virtual_path_list(value: str) -> str:
    return ";".join(
        normalize_lithtech_virtual_path(part)
        for part in value.split(";")
        if normalize_lithtech_virtual_path(part)
    )


def is_model_source_path(value: str) -> bool:
    return Path(normalize_lithtech_virtual_path(value)).suffix.lower() in MODEL_SOURCE_EXTENSIONS


def model_asset_path(source_model: str) -> str:
    normalized = normalize_lithtech_virtual_path(source_model, lowercase=True)
    if "." in Path(normalized).name:
        return str(Path(normalized).with_suffix(".glb")).replace("\\", "/")
    return normalized + ".glb"


def model_instance_collision_mode(properties: dict[str, Any]) -> str:
    if properties.get("solid") == 1:
        return "solid"
    if properties.get("rayhit") == 1:
        return "rayhit"
    return "none"


def build_model_instance_lines(dat_world: DatWorld, scale: float) -> tuple[list[str], list[dict[str, Any]]]:
    lines: list[str] = []
    asset_counts: dict[str, dict[str, Any]] = {}
    map_id = dat_world.path.stem.lower()
    for object_index, world_object in enumerate(dat_world.objects):
        properties = object_property_map(world_object)
        source_model = properties.get("filename")
        position = properties.get("pos")
        if not isinstance(source_model, str) or not source_model:
            continue
        if not is_model_source_path(source_model):
            continue
        if not isinstance(position, list) or len(position) != 3:
            continue

        source_name = properties.get("name")
        if not isinstance(source_name, str) or not source_name:
            source_name = f"{world_object.name}{object_index}"
        rotation = properties.get("rotation")
        if not isinstance(rotation, list) or len(rotation) != 4:
            rotation = [0.0, 0.0, 0.0, 1.0]
        uniform_scale = properties.get("scale", 1.0)
        if not isinstance(uniform_scale, (int, float)):
            uniform_scale = 1.0
        source_skin = properties.get("skin", "")
        if not isinstance(source_skin, str):
            source_skin = ""
        source_skin = normalize_lithtech_virtual_path_list(source_skin)

        x, y, z = lt_vec_to_odm_tuple(position, scale)
        qx, qy, qz, qw = lt_rotation_to_odm_quat(rotation)
        normalized_source_model = normalize_lithtech_virtual_path(source_model)
        target_model_asset = model_asset_path(source_model)
        collision_mode = model_instance_collision_mode(properties)
        asset_entry = asset_counts.setdefault(
            target_model_asset,
            {
                "source_model": normalized_source_model,
                "model_asset": target_model_asset,
                "instance_count": 0,
                "source_object_indices": [],
            },
        )
        asset_entry["instance_count"] += 1
        asset_entry["source_object_indices"].append(object_index)
        instance_id = f"mm9:{map_id}:object:{object_index}"
        lines.extend([
            f"  - instance_id: {yaml_scalar(instance_id)}",
            f"    source_ref: {yaml_scalar(f'objects/{object_index}')}",
            '    source_kind: "mm9_dat_object"',
            f"    source_object_index: {object_index}",
            f"    source_class: {yaml_scalar(world_object.name)}",
            f"    source_name: {yaml_scalar(source_name)}",
            f"    source_model: {yaml_scalar(normalized_source_model)}",
            f"    source_skin: {yaml_scalar(source_skin)}",
            f"    model_asset: {yaml_scalar(target_model_asset)}",
            f"    position: {{x: {x}, y: {y}, z: {z}}}",
            f"    rotation_quat: {{x: {qx:.8g}, y: {qy:.8g}, z: {qz:.8g}, w: {qw:.8g}}}",
            f"    scale: {{x: {float(uniform_scale):.8g}, y: {float(uniform_scale):.8g}, z: {float(uniform_scale):.8g}}}",
            f"    collision: {yaml_scalar(collision_mode)}",
        ])
    return lines, sorted(asset_counts.values(), key=lambda entry: entry["model_asset"])


def build_baked_model_instance_lines(baked_instances: list[BakedModelInstance]) -> list[str]:
    lines: list[str] = []
    for instance in baked_instances:
        lines.extend([
            f"  - source_object_index: {instance.source_object_index}",
            f"    source_class: {yaml_scalar(instance.source_class)}",
            f"    source_name: {yaml_scalar(instance.source_name)}",
            f"    source_model: {yaml_scalar(instance.source_model)}",
            f"    source_skin: {yaml_scalar(instance.source_skin)}",
            f"    bmodel_index: {instance.bmodel_index}",
            f"    bmodel_name: {yaml_scalar(instance.bmodel_name)}",
            f"    kind: {yaml_scalar(instance.kind)}",
            f"    destructible: {yaml_scalar(instance.destructible)}",
            f"    persistent_variant_index: {instance.variant_index}",
        ])
        if instance.placement_kind:
            lines.append(f"    placement_kind: {yaml_scalar(instance.placement_kind)}")
        if instance.source_position_lt:
            lines.append(
                "    source_position_lt: ["
                + ", ".join(f"{value:.8g}" for value in instance.source_position_lt)
                + "]"
            )
        if instance.bake_position_lt:
            lines.append(
                "    bake_position_lt: ["
                + ", ".join(f"{value:.8g}" for value in instance.bake_position_lt)
                + "]"
            )
        if instance.visual_offset_lt and any(abs(value) > 0.000001 for value in instance.visual_offset_lt):
            lines.append(
                "    visual_offset_lt: ["
                + ", ".join(f"{value:.8g}" for value in instance.visual_offset_lt)
                + "]"
            )
    return lines


def mechanism_runtime_id(source_object_index: int) -> int:
    return 900000 + source_object_index


def mechanism_event_id(source_object_index: int) -> int:
    return MM9_MECHANISM_EVENT_ID_BASE + source_object_index


def property_map_cased(world_object: WorldObject) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for prop in world_object.properties:
        if prop.decoded:
            values[prop.name] = prop.value
    return values


def mm9_npc_object_class(role: str, type_picture: str, named_actor: bool = False) -> str | None:
    parts = type_picture.split()
    if len(parts) < 4 or parts[0].lower() != "peasant":
        if not named_actor:
            return None
        named_class = re.sub(r"[^A-Za-z0-9]", "", role)
        return named_class or None

    palette = parts[-1]
    if palette not in {"A", "B", "C", "D"}:
        return None

    body = parts[1:-1]
    body[-1] = re.sub(r"[A-D]$", "", body[-1])
    return role + "".join(body) + palette


def read_mm9_npc_replacements(
    actor_table_path: Path,
    replacement_table_path: Path,
    monster_descriptor_path: Path,
) -> dict[str, Mm9NpcReplacement]:
    replacement_ids: dict[int, int] = {}
    object_class_overrides: dict[int, str] = {}
    with replacement_table_path.open(newline="", encoding="utf-8") as input_file:
        for row in csv.DictReader(input_file, delimiter="\t"):
            source_number = int(row["mm9_source_number"])
            if source_number in replacement_ids:
                raise ValueError(f"duplicate MM9 NPC replacement source number {source_number}")
            replacement_ids[source_number] = int(row["legacy_actor_id"])
            object_class_override = (row.get("object_class_override") or "").strip()
            if object_class_override:
                object_class_overrides[source_number] = object_class_override

    descriptor_sizes: dict[int, tuple[int, int]] = {}
    with monster_descriptor_path.open(newline="", encoding="utf-8") as input_file:
        for row in csv.reader(input_file, delimiter="\t"):
            if not row or not row[0].strip().isdigit() or len(row) < 4:
                continue
            descriptor_sizes[int(row[0])] = (int(row[2]), int(row[3]))

    result: dict[str, Mm9NpcReplacement] = {}
    with actor_table_path.open(newline="", encoding="cp1252") as input_file:
        for row in csv.DictReader(input_file, delimiter="\t"):
            source_number_text = (row.get("Number") or "").strip()
            if not source_number_text.isdigit():
                continue
            source_number = int(source_number_text)
            legacy_actor_id = replacement_ids.get(source_number)
            if legacy_actor_id is None:
                continue

            role = (row.get("Monster Name") or "").strip()
            object_class = object_class_overrides.get(source_number, "")
            if not object_class:
                object_class = mm9_npc_object_class(
                    role,
                    (row.get("Type/Picture") or "").strip(),
                    named_actor=source_number >= 246,
                )
            if object_class is None:
                continue

            descriptor_size = descriptor_sizes.get(legacy_actor_id)
            if descriptor_size is None:
                raise ValueError(
                    f"MM9 NPC replacement {source_number} references missing legacy actor {legacy_actor_id}")

            replacement = Mm9NpcReplacement(
                source_number=source_number,
                object_class=object_class,
                role=role,
                hit_points=int((row.get("HP") or "0").strip() or "0"),
                legacy_actor_id=legacy_actor_id,
                height=descriptor_size[0],
                radius=descriptor_size[1],
            )
            existing = result.get(object_class)
            if existing is not None and existing != replacement:
                raise ValueError(f"ambiguous MM9 NPC object class {object_class}")
            result[object_class] = replacement

    return result


def read_mm9_npc_names(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    with path.open(newline="", encoding="cp1252") as input_file:
        for row in csv.reader(input_file):
            if len(row) < 2 or not row[0].strip().isdigit():
                continue
            result[int(row[0])] = row[1].strip()
    return result


def resolve_mm9_npc_replacement(
    world_object: WorldObject,
    values: dict[str, Any],
    replacements: dict[str, Mm9NpcReplacement],
) -> Mm9NpcReplacement | None:
    normalized_replacements: dict[str, Mm9NpcReplacement] = {}
    for object_class, replacement in replacements.items():
        normalized_class = normalized_binding_name(object_class)
        normalized_replacements[normalized_class] = replacement
        if "human1" in normalized_class:
            normalized_replacements.setdefault(normalized_class.replace("human1", "human"), replacement)

    replacement = normalized_replacements.get(normalized_binding_name(world_object.name))
    if replacement is not None:
        return replacement

    source_name = values.get("Name")
    if not isinstance(source_name, str) or not source_name:
        return None

    normalized_source_name = normalized_binding_name(source_name)
    matches = [
        replacement
        for object_class, replacement in replacements.items()
        if re.fullmatch(normalized_binding_name(object_class) + r"\d+", normalized_source_name)
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def mm9_npc_rude_id(values: dict[str, Any]) -> int:
    if not bool(values.get("DoRude", 0)):
        return 0

    script_name = values.get("ScriptName")
    if isinstance(script_name, str):
        match = re.search(r"(?:^|[/\\])NPC(\d+)\.scr$", script_name, re.IGNORECASE)
        if match is not None:
            return int(match.group(1))

    greeting_sound = values.get("GreetingSound")
    if isinstance(greeting_sound, str):
        match = re.search(r"(?:^|[/\\])NPC_(\d+)\.wav$", greeting_sound, re.IGNORECASE)
        if match is not None:
            return int(match.group(1))

    raw_npc_number = values.get("NPCNbr")
    if isinstance(raw_npc_number, int) and 0 <= raw_npc_number <= 0xFFFFFFFF:
        decoded = struct.unpack("<f", struct.pack("<I", raw_npc_number))[0]
        if decoded.is_integer() and 0 < decoded < 10000:
            return int(decoded)
    if isinstance(raw_npc_number, (int, float)) and 0 < raw_npc_number < 10000:
        return int(raw_npc_number)
    return 0


def build_mm9_npc_actor_lines(
    dat_world: DatWorld,
    scale: float,
    replacements: dict[str, Mm9NpcReplacement],
    npc_names: dict[int, str],
    excluded_source_object_indices: set[int] | None = None,
    emitted_source_object_indices: set[int] | None = None,
) -> list[str]:
    lines: list[str] = []
    excluded_indices = excluded_source_object_indices or set()
    for object_index, world_object in enumerate(dat_world.objects):
        if object_index in excluded_indices:
            continue
        values = property_map_cased(world_object)
        replacement = resolve_mm9_npc_replacement(world_object, values, replacements)
        if replacement is None:
            continue

        position = values.get("Pos")
        if not isinstance(position, list) or len(position) != 3:
            continue
        rotation = values.get("Rotation")
        if not isinstance(rotation, list) or len(rotation) < 2:
            rotation = [0.0, 0.0, 0.0, 0.0]

        rude_id = mm9_npc_rude_id(values)
        source_name = values.get("Name")
        if not isinstance(source_name, str) or not source_name:
            source_name = world_object.name
        display_name = npc_names.get(rude_id, source_name)
        x, y, z = lt_vec_to_odm_tuple(position, scale)
        is_guard = replacement.role.lower() == "guard"
        can_receive_damage = bool(values.get("CanDamage", 1))
        if emitted_source_object_indices is not None:
            emitted_source_object_indices.add(object_index)

        lines.extend([
            f"    - name: {yaml_scalar(display_name)}",
            "      npc_id: 0",
            f"      mm9_rude_id: {rude_id}",
            f"      mm9_source_object_index: {object_index}",
            f"      mm9_can_receive_damage: {yaml_scalar(can_receive_damage)}",
            f"      mm9_civilian: {yaml_scalar(not is_guard)}",
            f"      mm9_guard: {yaml_scalar(is_guard)}",
            f"      initial_yaw_units: {lt_rotation_to_openyamm_yaw_units(rotation)}",
            f"      immobile: {yaml_scalar(rude_id > 0)}",
            "      attributes: 0",
            f"      hp: {replacement.hit_points}",
            "      hostility_type: 0",
            "      monster_info_id: 0",
            f"      monster_id: {replacement.legacy_actor_id}",
            f"      radius: {replacement.radius}",
            f"      height: {replacement.height}",
            "      move_speed: 0",
            f"      position: {{x: {x}, y: {y}, z: {z}}}",
            "      sprite_ids: [0, 0, 0, 0]",
            "      sector_id: 0",
            "      current_action_animation: 0",
            "      carried_item_id: 0",
            "      group: 0",
            "      ally: 0",
            "      unique_name_index: 0",
        ])
    return lines


def read_numeric_tsv_rows(path: Path) -> dict[int, list[str]]:
    with path.open(newline="", encoding="utf-8") as input_file:
        return {
            int(row[0]): row
            for row in csv.reader(input_file, delimiter="\t")
            if row and row[0].strip().isdigit()
        }


def read_mm9_monster_replacements(
    source_monster_table_path: Path,
    actor_table_path: Path,
    replacement_table_path: Path,
    mm9_monster_data_path: Path,
    mm9_monster_descriptor_path: Path,
) -> dict[str, list[Mm9MonsterReplacement]]:
    replacement_ids: dict[int, int] = {}
    object_class_overrides: dict[int, str] = {}
    with replacement_table_path.open(newline="", encoding="utf-8") as input_file:
        for row in csv.DictReader(input_file, delimiter="\t"):
            source_number = int(row["mm9_source_number"])
            runtime_monster_id = MM9_MONSTER_ID_BASE + source_number
            if source_number in replacement_ids:
                raise ValueError(f"duplicate MM9 monster replacement source number {source_number}")
            replacement_ids[source_number] = runtime_monster_id
            object_class_override = (row.get("object_class_override") or "").strip()
            if object_class_override:
                object_class_overrides[source_number] = object_class_override

    monster_data_rows = read_numeric_tsv_rows(mm9_monster_data_path)
    descriptor_rows = read_numeric_tsv_rows(mm9_monster_descriptor_path)
    result: dict[str, list[Mm9MonsterReplacement]] = {}
    replacements_by_source: dict[int, Mm9MonsterReplacement] = {}

    with source_monster_table_path.open(newline="", encoding="cp1252") as input_file:
        for row in csv.DictReader(input_file, delimiter="\t"):
            source_number_text = (row.get("Number") or "").strip()
            if not source_number_text.isdigit():
                continue

            source_number = int(source_number_text)
            runtime_monster_id = replacement_ids.get(source_number)
            if runtime_monster_id is None:
                continue

            object_class = object_class_overrides.get(
                source_number,
                (row.get("Monster Name") or "").strip(),
            )
            monster_data = monster_data_rows.get(runtime_monster_id)
            descriptor = descriptor_rows.get(runtime_monster_id)
            if not object_class or monster_data is None or descriptor is None:
                raise ValueError(
                    f"MM9 monster {source_number} has no object class or generated runtime table row")
            if len(monster_data) < 14 or len(descriptor) < 4:
                raise ValueError(f"MM9 monster {source_number} has an incomplete runtime table row")

            type_picture = (row.get("Type/Picture") or "").strip()
            variant_match = re.search(r"(\d+)(?:\s+[ABC])?$", type_picture, re.IGNORECASE)
            replacement = Mm9MonsterReplacement(
                source_number=source_number,
                object_class=object_class,
                source_model=(row.get("ModelName") or "").strip(),
                source_skins=tuple(
                    value.strip()
                    for value in (
                        row.get("SkinName") or "",
                        row.get("SkinName2") or "",
                        row.get("SkinName3") or "",
                    )
                    if value.strip()
                ),
                display_name=monster_data[1].strip(),
                runtime_monster_id=runtime_monster_id,
                hit_points=int(monster_data[4]),
                hostility=int(monster_data[12]),
                move_speed=int(monster_data[13]),
                height=int(descriptor[2]),
                radius=int(descriptor[3]),
                source_rank=(
                    rank_match.group(1).upper()
                    if (rank_match := re.search(r"(?:^|\s)([ABC])$", type_picture))
                    else ""
                ),
                source_variant=variant_match.group(1) if variant_match is not None else "",
            )
            normalized_class = normalized_binding_name(object_class)
            result.setdefault(normalized_class, []).append(replacement)
            replacements_by_source[source_number] = replacement

    with actor_table_path.open(newline="", encoding="cp1252") as input_file:
        for row in csv.DictReader(input_file, delimiter="\t"):
            source_number_text = (row.get("Number") or "").strip()
            if not source_number_text.isdigit():
                continue
            replacement = replacements_by_source.get(int(source_number_text))
            object_class = (row.get("Monster Name") or "").strip()
            if replacement is None or not object_class:
                continue
            aliases = result.setdefault(normalized_binding_name(object_class), [])
            if replacement not in aliases:
                aliases.append(replacement)

    for normalized_class, aliases in list(result.items()):
        if len(aliases) <= 1:
            continue
        for replacement in aliases:
            if replacement.source_rank in {"B", "C"}:
                ranked_aliases = result.setdefault(
                    f"{normalized_class}{replacement.source_rank.lower()}", [])
                if replacement not in ranked_aliases:
                    ranked_aliases.append(replacement)
            if replacement.source_variant:
                variant_aliases = result.setdefault(
                    f"{normalized_class}{replacement.source_variant}", [])
                if replacement not in variant_aliases:
                    variant_aliases.append(replacement)

    resolved_source_numbers = {
        entry.source_number
        for entry in replacements_by_source.values()
    }
    missing_source_numbers = sorted(set(replacement_ids) - resolved_source_numbers)
    if missing_source_numbers:
        raise ValueError(f"MM9 monster mappings have no source table rows: {missing_source_numbers}")
    return result


def resolve_mm9_monster_replacement(
    world_object: WorldObject,
    replacements: dict[str, list[Mm9MonsterReplacement]],
) -> Mm9MonsterReplacement | None:
    candidates = replacements.get(normalized_binding_name(world_object.name), [])
    if len(candidates) <= 1:
        return candidates[0] if candidates else None

    values = property_map_cased(world_object)
    source_model = str(values.get("Filename", "")).replace("\\", "/").rsplit("/", 1)[-1].lower()
    source_skin = str(values.get("Skin", "")).replace("\\", "/").lower()
    skin_matching = [
        candidate
        for candidate in candidates
        if source_skin and any(skin.lower() in source_skin for skin in candidate.source_skins)
    ]
    model_matching = [
        candidate
        for candidate in candidates
        if source_model and candidate.source_model.lower() == source_model
    ]
    matching = skin_matching or model_matching or candidates
    if len(matching) == 1:
        return matching[0]

    unnumbered_candidates = [candidate for candidate in matching if not candidate.source_variant]
    if len(unnumbered_candidates) == 1:
        return unnumbered_candidates[0]

    if all(
        candidate.source_model.lower() == matching[0].source_model.lower()
        and tuple(skin.lower() for skin in candidate.source_skins)
            == tuple(skin.lower() for skin in matching[0].source_skins)
        for candidate in matching[1:]
    ):
        return min(matching, key=lambda candidate: candidate.source_number)

    rank_a_candidates = [candidate for candidate in matching if candidate.source_rank == "A"]
    if len(rank_a_candidates) == 1:
        return rank_a_candidates[0]
    raise ValueError(
        f"ambiguous MM9 monster object {world_object.name}: cannot select source row from "
        f"{[candidate.source_number for candidate in candidates]}")


def build_mm9_monster_actor_lines(
    dat_world: DatWorld,
    scale: float,
    replacements: dict[str, list[Mm9MonsterReplacement]],
    emitted_source_object_indices: set[int] | None = None,
) -> list[str]:
    lines: list[str] = []
    for object_index, world_object in enumerate(dat_world.objects):
        values = property_map_cased(world_object)
        if bool(values.get("CacheOnly", 0)):
            continue

        replacement = resolve_mm9_monster_replacement(world_object, replacements)
        if replacement is None:
            continue

        position = values.get("Pos")
        if not isinstance(position, list) or len(position) != 3:
            continue
        rotation = values.get("Rotation")
        if not isinstance(rotation, list) or len(rotation) < 2:
            rotation = [0.0, 0.0, 0.0, 0.0]

        attributes = ACTOR_ATTRIBUTE_AGGRESSOR
        if not bool(values.get("Visible", 1)):
            attributes |= ACTOR_ATTRIBUTE_INVISIBLE
        x, y, z = lt_vec_to_odm_tuple(position, scale)
        if emitted_source_object_indices is not None:
            emitted_source_object_indices.add(object_index)

        lines.extend([
            f"    - name: {yaml_scalar(replacement.display_name)}",
            "      npc_id: 0",
            f"      mm9_source_object_index: {object_index}",
            "      mm9_can_receive_damage: true",
            "      mm9_civilian: false",
            "      mm9_guard: false",
            f"      initial_yaw_units: {lt_rotation_to_openyamm_yaw_units(rotation)}",
            "      immobile: false",
            f"      attributes: {attributes}",
            f"      hp: {replacement.hit_points}",
            f"      hostility_type: {replacement.hostility}",
            f"      monster_info_id: {replacement.runtime_monster_id}",
            f"      monster_id: {replacement.runtime_monster_id}",
            f"      radius: {replacement.radius}",
            f"      height: {replacement.height}",
            f"      move_speed: {replacement.move_speed}",
            f"      position: {{x: {x}, y: {y}, z: {z}}}",
            "      sprite_ids: [0, 0, 0, 0]",
            "      sector_id: 0",
            "      current_action_animation: 0",
            "      carried_item_id: 0",
            "      group: 0",
            "      ally: 0",
            "      unique_name_index: 0",
        ])
    return lines


def mm9_monster_actor_source_object_indices(
    dat_world: DatWorld,
    replacements: dict[str, list[Mm9MonsterReplacement]],
) -> set[int]:
    result: set[int] = set()
    for object_index, world_object in enumerate(dat_world.objects):
        values = property_map_cased(world_object)
        if bool(values.get("CacheOnly", 0)):
            continue
        position = values.get("Pos")
        if not isinstance(position, list) or len(position) != 3:
            continue
        if resolve_mm9_monster_replacement(world_object, replacements) is not None:
            result.add(object_index)
    return result


def normalized_binding_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def find_bmodel_binding_for_mechanism(
    values: dict[str, Any],
    bmodels: list[OdmBModel],
) -> tuple[int, OdmBModel, str] | None:
    source_name = values.get("Name")
    if isinstance(source_name, str) and source_name:
        normalized_source_name = normalized_binding_name(source_name)
        for bmodel_index, bmodel in enumerate(bmodels):
            if normalized_binding_name(bmodel.source_model_name or bmodel.name) == normalized_source_name:
                return bmodel_index, bmodel, "exact_source_model_name"
            if normalized_binding_name(bmodel.name) == normalized_source_name:
                return bmodel_index, bmodel, "exact_bmodel_name"

    rotation_point = values.get("RotationPoint")
    if isinstance(rotation_point, list) and len(rotation_point) >= 3:
        movable_candidates: list[tuple[float, int, OdmBModel]] = []
        for bmodel_index, bmodel in enumerate(bmodels):
            if (bmodel.source_world_info_flags & (1 << 1)) == 0:
                continue
            dx = float(rotation_point[0]) - bmodel.source_world_translation_lt[0]
            dy = float(rotation_point[1]) - bmodel.source_world_translation_lt[1]
            dz = float(rotation_point[2]) - bmodel.source_world_translation_lt[2]
            movable_candidates.append((math.sqrt(dx * dx + dy * dy + dz * dz), bmodel_index, bmodel))
        if movable_candidates:
            distance, bmodel_index, bmodel = min(movable_candidates, key=lambda item: item[0])
            if distance <= 0.001:
                return bmodel_index, bmodel, "shared_rotation_point_exact_world_translation"

    return None


def mechanism_move_time_ms(values: dict[str, Any]) -> int:
    distance = abs(float(values.get("MoveDist", 0.0) or 0.0))
    rotation_angles = values.get("RotationAngles")
    if distance <= 0.0 and isinstance(rotation_angles, list):
        distance = max((abs(float(value)) for value in rotation_angles[:3]), default=0.0)
    speed = abs(float(values.get("Speed", 0.0) or 0.0))
    if distance <= 0.0 or speed <= 0.0:
        return 1000
    return max(1, int(round(distance / speed * 1000.0)))


def mechanism_motion_support(mechanism_kind: str, values: dict[str, Any]) -> tuple[bool, bool]:
    has_linear = (
        mechanism_kind in {"linear_door", "linear_button", "weighted_lift"}
        and isinstance(values.get("MoveDir"), list)
        and len(values.get("MoveDir")) >= 3
        and "MoveDist" in values
    )
    has_rotation = (
        mechanism_kind in {"rotating_door", "rotating_switch", "rotating_brush"}
        and isinstance(values.get("RotationPoint"), list)
        and isinstance(values.get("RotationAngles"), list)
    )
    return has_linear, has_rotation


def append_optional_bool_line(lines: list[str], key: str, value: Any) -> None:
    if isinstance(value, bool):
        lines.append(f"      {key}: {yaml_scalar(value)}")
    elif isinstance(value, int):
        lines.append(f"      {key}: {yaml_scalar(value != 0)}")


def normalize_mm9_sound_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("/"):
        normalized = normalized[1:]

    lower = normalized.lower()
    for prefix in ("sounds/", "source/sounds/"):
        if lower.startswith(prefix):
            normalized = normalized[len(prefix):]
            lower = normalized.lower()

    return normalized


def build_mm9_npc_greeting_lines(dat_world: DatWorld) -> list[str]:
    lines: list[str] = []

    for object_index, world_object in enumerate(dat_world.objects):
        values = property_map_cased(world_object)
        sound_name = normalize_mm9_sound_name(values.get("GreetingSound"))
        if not sound_name:
            continue

        lines.extend([
            f"  - source_object_index: {object_index}",
            f"    sound: {yaml_scalar(sound_name)}",
        ])

    return lines


def build_mechanism_lines(dat_world: DatWorld, bmodels: list[OdmBModel], scale: float) -> tuple[list[str], dict[str, Any]]:
    lines: list[str] = []
    stats = {
        "mechanisms": 0,
        "mechanisms_bound": 0,
        "mechanisms_unbound": 0,
        "mechanisms_linear": 0,
        "mechanisms_rotating": 0,
        "mechanisms_unsupported": 0,
    }

    for object_index, world_object in enumerate(dat_world.objects):
        mechanism_kind = MM9_MECHANISM_CLASS_KINDS.get(world_object.name)
        if mechanism_kind is None:
            continue

        values = property_map_cased(world_object)
        source_name = values.get("Name")
        if not isinstance(source_name, str) or not source_name:
            source_name = f"{world_object.name}{object_index}"

        binding = find_bmodel_binding_for_mechanism(values, bmodels)
        runtime_id = mechanism_runtime_id(object_index)
        has_linear, has_rotation = mechanism_motion_support(mechanism_kind, values)

        stats["mechanisms"] += 1
        if has_linear:
            stats["mechanisms_linear"] += 1
        if has_rotation:
            stats["mechanisms_rotating"] += 1
        if not has_linear and not has_rotation:
            stats["mechanisms_unsupported"] += 1
        if binding is None:
            stats["mechanisms_unbound"] += 1
        else:
            stats["mechanisms_bound"] += 1

        lines.extend([
            f"  - mechanism_id: {runtime_id}",
            f"    event_id: {mechanism_event_id(object_index)}",
            f"    source_object_index: {object_index}",
            f"    source_class: {yaml_scalar(world_object.name)}",
            f"    source_name: {yaml_scalar(source_name)}",
            f"    kind: {yaml_scalar(mechanism_kind)}",
        ])

        if binding is not None:
            bmodel_index, bmodel, confidence = binding
            lines.extend([
                "    binding:",
                '      target_kind: "odm_bmodel"',
                f"      bmodel_index: {bmodel_index}",
                f"      bmodel_name: {yaml_scalar(bmodel.name)}",
                f"      source_model_index: {bmodel.source_model_index}",
                f"      source_model_name: {yaml_scalar(bmodel.source_model_name)}",
                f"      confidence: {yaml_scalar(confidence)}",
            ])
        else:
            lines.extend([
                "    binding:",
                '      target_kind: "unresolved"',
                '      confidence: "unresolved"',
            ])

        lines.append("    motion:")
        if has_linear:
            move_dir = values["MoveDir"]
            move_dist_lt = float(values.get("MoveDist", 0.0) or 0.0)
            dx = int(round(float(move_dir[0]) * move_dist_lt * scale))
            dy = int(round(float(move_dir[2]) * move_dist_lt * scale))
            dz = int(round(float(move_dir[1]) * move_dist_lt * scale))
            lines.extend([
                "      linear:",
                f"        move_dir_lt: [{float(move_dir[0]):.8g}, {float(move_dir[1]):.8g}, {float(move_dir[2]):.8g}]",
                f"        move_dist_lt: {move_dist_lt:.8g}",
                f"        delta_openyamm: {{x: {dx}, y: {dy}, z: {dz}}}",
            ])
            if "Speed" in values:
                lines.append(f"        open_speed_lt_per_sec: {float(values['Speed']):.8g}")
            if "ClosingSpeed" in values:
                lines.append(f"        close_speed_lt_per_sec: {float(values['ClosingSpeed']):.8g}")
        if has_rotation:
            rotation_point = values["RotationPoint"]
            rotation_angles = values["RotationAngles"]
            pivot = lt_vec_to_odm_tuple(rotation_point, scale)
            lines.extend([
                "      rotation:",
                "        rotation_point_lt: ["
                f"{float(rotation_point[0]):.8g}, {float(rotation_point[1]):.8g}, {float(rotation_point[2]):.8g}]",
                f"        pivot_openyamm: {{x: {pivot[0]}, y: {pivot[1]}, z: {pivot[2]}}}",
                "        rotation_angles_deg: ["
                f"{float(rotation_angles[0]):.8g}, {float(rotation_angles[1]):.8g}, {float(rotation_angles[2]):.8g}]",
                "        rotation_angles_openyamm_deg: {"
                f"x: {float(rotation_angles[0]):.8g}, y: {float(rotation_angles[2]):.8g}, "
                f"z: {float(rotation_angles[1]):.8g}}}",
            ])
        if not has_linear and not has_rotation:
            lines.append("      unsupported: true")
        lines.extend([
            f"      move_time_ms: {mechanism_move_time_ms(values)}",
            "    activation:",
        ])
        append_optional_bool_line(lines, "start_open", values.get("StartOpen"))
        append_optional_bool_line(lines, "start_on", values.get("StartOn"))
        append_optional_bool_line(lines, "push_open", values.get("PushOpen"))
        append_optional_bool_line(lines, "touch_to_open", values.get("TouchToOpen"))
        append_optional_bool_line(lines, "locked", values.get("Locked"))
        append_optional_bool_line(lines, "open_away", values.get("OpenAway"))

        sound_fields = (
            ("open", "OpenSoundName"),
            ("close", "CloseSoundName"),
            ("open_start", "OpenStartSound"),
            ("open_busy", "OpenBusySound"),
            ("open_stop", "OpenStopSound"),
            ("close_start", "CloseStartSound"),
            ("close_busy", "CloseBusySound"),
            ("close_stop", "CloseStopSound"),
            ("jiggle", "JiggleSound"),
        )
        sounds = [
            (phase, normalize_mm9_sound_name(values.get(property_name)))
            for phase, property_name in sound_fields
        ]
        sounds = [(phase, sound_name) for phase, sound_name in sounds if sound_name]

        if sounds:
            sound_position = values.get("SoundPos")
            if not isinstance(sound_position, list) or len(sound_position) < 3 or not any(sound_position):
                sound_position = values.get("Pos")

            lines.append("    sounds:")
            if isinstance(sound_position, list) and len(sound_position) >= 3:
                position = lt_vec_to_odm_tuple(sound_position, scale)
                lines.append(
                    f"      position: {{x: {position[0]}, y: {position[1]}, z: {position[2]}}}")
            for phase, sound_name in sounds:
                lines.append(f"      {phase}: {yaml_scalar(sound_name)}")

    return lines, stats


def destructible_auxiliary_bmodel_indices(
    destructible_bmodel_index: int,
    bmodels: list[OdmBModel],
) -> list[int]:
    destructible = bmodels[destructible_bmodel_index]
    destructible_translation = destructible.source_world_translation_lt
    matches: list[int] = []
    for candidate_index, candidate in enumerate(bmodels):
        if not normalize_model_role_name(candidate.source_model_name).startswith("perceptionbrush"):
            continue
        if len(candidate.vertices) != len(destructible.vertices) or len(candidate.faces) != len(destructible.faces):
            continue

        candidate_translation = candidate.source_world_translation_lt
        squared_distance = sum(
            (candidate_translation[axis] - destructible_translation[axis]) ** 2
            for axis in range(3)
        )
        if squared_distance <= 16.0:
            matches.append(candidate_index)

    return matches


def build_destructible_and_trigger_lines(
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    scale: float,
) -> tuple[list[str], list[str], dict[str, int]]:
    destructible_lines: list[str] = []
    trigger_lines: list[str] = []
    destructible_indices: set[int] = set()
    source_index_by_name: dict[str, int] = {}
    stats = {
        "destructibles": 0,
        "destructibles_bound": 0,
        "destructibles_unbound": 0,
        "destructible_trigger_volumes": 0,
        "destructible_trigger_outputs": 0,
    }

    for object_index, world_object in enumerate(dat_world.objects):
        values = property_map_cased(world_object)
        source_name = values.get("Name")
        if isinstance(source_name, str) and source_name:
            source_index_by_name.setdefault(source_name.lower(), object_index)
        if world_object.name in MM9_DESTRUCTIBLE_CLASS_NAMES:
            destructible_indices.add(object_index)

    for object_index in sorted(destructible_indices):
        world_object = dat_world.objects[object_index]
        values = property_map_cased(world_object)
        source_name = values.get("Name")
        if not isinstance(source_name, str) or not source_name:
            source_name = f"{world_object.name}{object_index}"
        binding = find_bmodel_binding_for_mechanism(values, bmodels)
        stats["destructibles"] += 1
        if binding is None:
            stats["destructibles_unbound"] += 1
            continue

        bmodel_index, bmodel, _ = binding
        auxiliary_bmodel_indices = destructible_auxiliary_bmodel_indices(bmodel_index, bmodels)
        stats["destructibles_bound"] += 1
        initial_hp = max(1, int(round(float(values.get("HitPoints", 1.0) or 1.0))))
        destruction_sound = normalize_mm9_sound_name(values.get("CustomSound"))
        death_target_name = values.get("DeathTriggerTarget")
        death_target_index = (
            source_index_by_name.get(death_target_name.lower(), 0)
            if isinstance(death_target_name, str) and death_target_name
            else 0
        )
        death_message = values.get("DeathTriggerMessage")
        if not isinstance(death_message, str):
            death_message = ""

        destructible_lines.extend([
            f"  - source_object_index: {object_index}",
            f"    runtime_object_id: {mechanism_runtime_id(object_index)}",
            f"    source_name: {yaml_scalar(source_name)}",
            "    binding:",
            '      target_kind: "odm_bmodel"',
            f"      bmodel_index: {bmodel_index}",
            f"      bmodel_name: {yaml_scalar(bmodel.name)}",
            "      auxiliary_bmodel_indices: ["
            + ", ".join(str(index) for index in auxiliary_bmodel_indices)
            + "]",
            f"    initial_hp: {initial_hp}",
            f"    initially_damage_enabled: {yaml_scalar(bool(values.get('CanDamage', 0)))}",
            f"    trigger_destroy_only: {yaml_scalar(bool(values.get('TriggerDestroyOnly', 0)))}",
            f"    should_mini_save: {yaml_scalar(bool(values.get('ShouldMiniSave', 1)))}",
            f"    destruction_sound: {yaml_scalar(destruction_sound)}",
            f"    death_target_source_object_index: {death_target_index}",
            f"    death_message: {yaml_scalar(death_message)}",
        ])

    for object_index, world_object in enumerate(dat_world.objects):
        if world_object.name != "Trigger":
            continue
        values = property_map_cased(world_object)
        position_lt = values.get("Pos")
        dimensions_lt = values.get("Dims")
        if not isinstance(position_lt, list) or len(position_lt) < 3:
            continue
        if not isinstance(dimensions_lt, list) or len(dimensions_lt) < 3:
            continue

        outputs: list[tuple[int, str]] = []
        for slot in range(1, 11):
            target_name = values.get(f"TargetName{slot}")
            message_name = values.get(f"MessageName{slot}")
            if not isinstance(target_name, str) or not isinstance(message_name, str):
                continue
            target_index = source_index_by_name.get(target_name.lower())
            action = MM9_DESTRUCTIBLE_TRIGGER_MESSAGES.get(message_name.lower())
            if target_index not in destructible_indices or action is None:
                continue
            outputs.append((target_index, action))

        if not outputs:
            continue

        position = lt_vec_to_odm_tuple(position_lt, scale)
        half_extents = lt_vec_to_odm_tuple(dimensions_lt, scale)
        source_name = values.get("Name")
        if not isinstance(source_name, str) or not source_name:
            source_name = f"Trigger{object_index}"
        trigger_lines.extend([
            f"  - source_object_index: {object_index}",
            f"    source_name: {yaml_scalar(source_name)}",
            f"    position: {{x: {position[0]}, y: {position[1]}, z: {position[2]}}}",
            "    half_extents: {"
            f"x: {abs(half_extents[0])}, y: {abs(half_extents[1])}, z: {abs(half_extents[2])}}}",
            f"    start_on: {yaml_scalar(bool(values.get('StartOn', 1)))}",
            "    outputs:",
        ])
        for target_index, action in outputs:
            trigger_lines.extend([
                f"      - target_source_object_index: {target_index}",
                f"        action: {yaml_scalar(action)}",
            ])
        stats["destructible_trigger_volumes"] += 1
        stats["destructible_trigger_outputs"] += len(outputs)

    return destructible_lines, trigger_lines, stats


def build_destructible_receiver_lines(dat_world: DatWorld) -> list[str]:
    lines: list[str] = []
    for object_index, world_object in enumerate(dat_world.objects):
        if world_object.name != "ScriptObject":
            continue

        values = property_map_cased(world_object)
        script_name = values.get("ScriptName")
        script_params = values.get("ScriptParams")
        if not isinstance(script_name, str) or script_name.lower() != "tm_hardrock.scr":
            continue
        if not isinstance(script_params, str):
            continue

        parts = script_params.split()
        if len(parts) != 3:
            continue
        try:
            required_count, raw_quest_key, reward_experience = (int(part) for part in parts)
        except ValueError:
            continue
        if required_count <= 0 or raw_quest_key <= 0 or reward_experience < 0:
            continue

        source_name = values.get("Name")
        if not isinstance(source_name, str) or not source_name:
            source_name = f"ScriptObject{object_index}"
        lines.extend([
            f"  - source_object_index: {object_index}",
            f"    source_name: {yaml_scalar(source_name)}",
            f"    required_destruction_count: {required_count}",
            f"    reward_raw_quest_key: {raw_quest_key}",
            f"    reward_experience: {reward_experience}",
        ])

    return lines


def build_outdoor_mechanism_interactive_face_lines(
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    item_source_manifest: Mm9ItemSourceManifest | None = None,
    baked_instances: list[BakedModelInstance] | None = None,
) -> tuple[list[str], dict[str, int]]:
    lines: list[str] = []
    stats = {
        "mechanism_event_faces": 0,
        "mechanism_event_face_mechanisms": 0,
        "mechanism_event_face_unbound": 0,
    }
    seen_faces: set[tuple[int, int]] = set()
    semantic_source_indices = set()
    if item_source_manifest is not None:
        semantic_source_indices.update(
            source.provenance.source_object_index
            for source in item_source_manifest.loot_containers
            if source.kind == "chest"
        )
        semantic_source_indices.update(
            source.provenance.source_object_index
            for source in item_source_manifest.searchable_loot_props
        )
        semantic_source_indices.update(
            source.provenance.source_object_index
            for source in item_source_manifest.spawned_loot_containers
        )
        semantic_source_indices.update(
            source.provenance.source_object_index
            for source in item_source_manifest.persistent_item_mechanisms
        )
        semantic_source_indices.update(
            source.provenance.source_object_index
            for source in getattr(item_source_manifest, "barrels", [])
        )

    for object_index, world_object in enumerate(dat_world.objects):
        mechanism_kind = MM9_MECHANISM_CLASS_KINDS.get(world_object.name)
        if mechanism_kind not in MM9_INTERACTIVE_MECHANISM_KINDS and object_index not in semantic_source_indices:
            continue

        event_id = mechanism_event_id(object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue

        binding = None
        if object_index in semantic_source_indices and baked_instances is not None:
            instance = next(
                (
                    candidate
                    for candidate in baked_instances
                    if candidate.source_object_index == object_index and candidate.variant_index == 0
                ),
                None,
            )
            if instance is not None and instance.bmodel_index < len(bmodels):
                binding = (instance.bmodel_index, bmodels[instance.bmodel_index], 0.0)
        if binding is None:
            binding = find_bmodel_binding_for_mechanism(property_map_cased(world_object), bmodels)
        if binding is None:
            stats["mechanism_event_face_unbound"] += 1
            continue

        bmodel_index, bmodel, _ = binding
        wrote_for_mechanism = False
        for face_index, face in enumerate(bmodel.faces):
            key = (bmodel_index, face_index)
            if key in seen_faces:
                continue

            seen_faces.add(key)
            legacy_attributes = (
                face.attributes
                | FACE_ATTRIBUTE_CLICKABLE
            ) & ~FACE_ATTRIBUTE_HAS_HINT & ~FACE_ATTRIBUTE_INVISIBLE
            lines.extend([
                f"  - bmodel_index: {bmodel_index}",
                f"    face_index: {face_index}",
                f"    legacy_attributes: {legacy_attributes}",
                f"    cog_number: {event_id}",
                f"    cog_triggered_number: {event_id}",
                "    cog_trigger: 0",
            ])
            stats["mechanism_event_faces"] += 1
            wrote_for_mechanism = True

        if wrote_for_mechanism:
            stats["mechanism_event_face_mechanisms"] += 1

    for instance in baked_instances or []:
        if instance.variant_index <= 0 or instance.source_object_index not in semantic_source_indices:
            continue
        base_event_id = mechanism_event_id(instance.source_object_index)
        state_cog_number = 60000 + instance.source_object_index + instance.variant_index - 1
        if base_event_id <= 0 or base_event_id > 0xffff or state_cog_number > 0xffff:
            continue
        bmodel = bmodels[instance.bmodel_index]
        wrote_for_variant = False
        for face_index, face in enumerate(bmodel.faces):
            key = (instance.bmodel_index, face_index)
            if key in seen_faces:
                continue
            seen_faces.add(key)
            legacy_attributes = (
                face.attributes
                | FACE_ATTRIBUTE_CLICKABLE
                | FACE_ATTRIBUTE_INVISIBLE
                | FACE_ATTRIBUTE_UNTOUCHABLE
            ) & ~FACE_ATTRIBUTE_HAS_HINT
            lines.extend([
                f"  - bmodel_index: {instance.bmodel_index}",
                f"    face_index: {face_index}",
                f"    legacy_attributes: {legacy_attributes}",
                f"    cog_number: {state_cog_number}",
                f"    cog_triggered_number: {base_event_id}",
                "    cog_trigger: 0",
            ])
            stats["mechanism_event_faces"] += 1
            wrote_for_variant = True
        if wrote_for_variant:
            stats["mechanism_event_face_mechanisms"] += 1

    return lines, stats


def build_perception_face_lines(bmodels: list[OdmBModel]) -> list[str]:
    lines: list[str] = []

    for bmodel_index, bmodel in enumerate(bmodels):
        if bmodel.perception_difficulty is None:
            continue

        for face_index, face in enumerate(bmodel.faces):
            if not face.texture_alias or (face.attributes & FACE_ATTRIBUTE_SECRET) == 0:
                continue

            lines.extend([
                f"    - bmodel_index: {bmodel_index}",
                f"      face_index: {face_index}",
                f"      difficulty: {bmodel.perception_difficulty}",
            ])

    return lines


def write_scene_yml(
    path: Path,
    odm_name: str,
    source_metadata_name: str,
    model_instance_lines: list[str],
    mechanism_lines: list[str],
    interactive_face_lines: list[str],
    light_lines: list[str],
    party_start_point_lines: list[str],
    entity_lines: list[str],
    surface_animation_lines: list[str] | None = None,
    baked_model_instance_lines: list[str] | None = None,
    location_type: str = "exterior",
    mm9_npc_greeting_lines: list[str] | None = None,
    mm9_npc_actor_lines: list[str] | None = None,
    mm9_monster_actor_lines: list[str] | None = None,
    authored_fog: tuple[Mm9AuthoredFogState, Mm9AuthoredFogState] | None = None,
    perception_face_lines: list[str] | None = None,
    item_source_manifest: Mm9ItemSourceManifest | None = None,
    destructible_lines: list[str] | None = None,
    destructible_receiver_lines: list[str] | None = None,
    trigger_volume_lines: list[str] | None = None,
) -> None:
    map_name = Path(odm_name).stem.lower()
    is_city = map_name.endswith("city")
    effective_location_type = "exterior" if is_city else location_type
    sky_texture = "plansky3" if is_city else ""
    view_distance_scale = 0.4 if is_city or effective_location_type == "enclosed" else 1.0
    if is_city:
        authored_fog = None
    zeros_map = ", ".join(["0"] * 75)
    zeros_decor = ", ".join(["0"] * 125)
    model_instances = "\n".join(model_instance_lines) if model_instance_lines else "  []"
    mechanisms = "\n".join(mechanism_lines) if mechanism_lines else "  []"
    destructibles = "\n".join(destructible_lines) if destructible_lines else "  []"
    destructible_receivers = (
        "\n".join(destructible_receiver_lines)
        if destructible_receiver_lines
        else "  []"
    )
    trigger_volumes = "\n".join(trigger_volume_lines) if trigger_volume_lines else "  []"
    mm9_npc_greetings = "\n".join(mm9_npc_greeting_lines) if mm9_npc_greeting_lines else "  []"
    mm9_actor_lines = (mm9_npc_actor_lines or []) + (mm9_monster_actor_lines or [])
    mm9_actors = "\n".join(mm9_actor_lines) if mm9_actor_lines else "    []"
    interactive_faces = "\n".join(interactive_face_lines) if interactive_face_lines else "    []"
    perception_faces = "\n".join(perception_face_lines) if perception_face_lines else "    []"
    lights = "\n".join(light_lines) if light_lines else "  []"
    party_start_points = "\n".join(party_start_point_lines) if party_start_point_lines else "  []"
    entities = "\n".join(entity_lines) if entity_lines else "  []"
    surface_animations = "\n".join(surface_animation_lines) if surface_animation_lines else "  []"
    baked_model_instances = (
        "\n".join(baked_model_instance_lines)
        if baked_model_instance_lines
        else "  []"
    )
    item_source_sections = yaml.safe_dump(
        item_source_manifest.scene_data() if item_source_manifest is not None else {
            "world_items": [],
            "loot_containers": [],
            "searchable_loot_props": [],
            "actor_loot_overrides": [],
            "spawned_loot_containers": [],
            "persistent_item_mechanisms": [],
        },
        sort_keys=False,
        width=120,
    ).rstrip()
    foggy = authored_fog is not None and authored_fog[0].enabled
    fog_near_distance = authored_fog[0].near_distance if authored_fog is not None else 8192
    fog_far_distance = authored_fog[0].far_distance if authored_fog is not None else 16384
    if authored_fog is not None:
        day_fog, night_fog = authored_fog
        weather_block = "\n".join([
            '    fog_mode: "authored_day_night"',
            '    precipitation: "none"',
            "    authored_fog:",
            "      day:",
            f"        enabled: {yaml_scalar(day_fog.enabled)}",
            f"        near_distance: {day_fog.near_distance}",
            f"        far_distance: {day_fog.far_distance}",
            f"        color_rgb: [{day_fog.color[0]}, {day_fog.color[1]}, {day_fog.color[2]}]",
            "      night:",
            f"        enabled: {yaml_scalar(night_fog.enabled)}",
            f"        near_distance: {night_fog.near_distance}",
            f"        far_distance: {night_fog.far_distance}",
            f"        color_rgb: [{night_fog.color[0]}, {night_fog.color[1]}, {night_fog.color[2]}]",
        ])
    else:
        weather_block = """    fog_mode: "static"
    precipitation: "none"
    daily_fog:
      small_chance: 0
      average_chance: 0
      dense_chance: 0
      small:
        weak_distance: 8192
        strong_distance: 16384
      average:
        weak_distance: 8192
        strong_distance: 16384
      dense:
        weak_distance: 8192
        strong_distance: 16384"""
    path.write_text(
        f"""format_version: 1
kind: "outdoor_scene"
scene_profile: "bmodel_world"
source:
  geometry_file: "{odm_name}"
  source_metadata_file: "{source_metadata_name}"
lighting:
  lightmap_brightness_scale: 1.25
rendering:
  view_distance_scale: {view_distance_scale:.1f}
runtime_restrictions:
  allow_save_game: false
  allow_lloyds_beacon: false
  allow_rest: true
  arena: false
environment:
  location_type: "{effective_location_type}"
  sky_texture: "{sky_texture}"
  ground_tileset_name: "planset"
  master_tile: 0
  tile_set_lookup_indices: [0, 0, 0, 0]
  day_bits_raw: 0
  map_extra_bits_raw: 8
  flags:
    foggy: {yaml_scalar(foggy)}
    raining: false
    snowing: false
    underwater: false
    no_terrain: true
    always_dark: false
    always_light: false
    always_foggy: false
    red_fog: false
  fog:
    weak_distance: {fog_near_distance}
    strong_distance: {fog_far_distance}
  weather:
{weather_block}
  ceiling: 32767
terrain:
  attribute_overrides: []
  footstep_sound_overrides: []
surface_animations:
{surface_animations}
bmodel_faces:
  interactive_faces:
{interactive_faces}
  perception_faces:
{perception_faces}
mechanisms:
{mechanisms}
destructibles:
{destructibles}
destructible_receivers:
{destructible_receivers}
trigger_volumes:
{trigger_volumes}
mm9_npc_greetings:
{mm9_npc_greetings}
baked_model_instances:
{baked_model_instances}
entities:
{entities}
lights:
{lights}
spawns: []
party_start_points:
{party_start_points}
model_instances:
{model_instances}
{item_source_sections}
initial_state:
  location:
    respawn_count: 0
    last_respawn_day: 0
    reputation: 0
    alert_status: 0
  face_attribute_overrides: []
  actors:
{mm9_actors}
  sprite_objects: []
  chests: []
  variables:
    map: [{zeros_map}]
    decor: [{zeros_decor}]
""",
        encoding="utf-8",
    )


def build_surface_animation_lines(alias_metadata: dict[str, dict[str, Any]]) -> list[str]:
    lines: list[str] = []

    for alias, metadata in sorted(alias_metadata.items()):
        animation_frames = metadata.get("animation_frames", [])
        frames_per_second = int(metadata.get("animation_frames_per_second", 0) or 0)
        if len(animation_frames) < 2 or frames_per_second <= 0:
            continue

        lines.extend([
            f"  - texture: {yaml_scalar(alias)}",
            f"    frames_per_second: {frames_per_second}",
            "    frames:",
        ])
        for frame in animation_frames:
            lines.append(f"      - {yaml_scalar(str(frame.get('alias', '')))}")

    return lines


def write_material_aliases(
    path: Path,
    source_dat: Path,
    alias_metadata: dict[str, dict[str, Any]],
    stats: dict[str, Any],
    bitmap_modes: dict[str, str],
    bitmap_directory_name: str = "",
) -> None:
    lines = [
        "format_version: 1",
        'kind: "mm9_material_aliases"',
        f"source_dat: {yaml_scalar(str(source_dat))}",
        "notes:",
        '  - "ODM face texture names are limited to 10 bytes; aliases preserve editor compatibility."',
        "stats:",
    ]
    for key, value in stats.items():
        lines.append(f"  {key}: {value}")
    lines.append("textures:")
    for alias, metadata in sorted(alias_metadata.items()):
        lines.append(f"  - alias: {yaml_scalar(alias)}")
        lines.append(f"    source_texture: {yaml_scalar(metadata['source_texture'])}")
        lines.append(f"    width: {metadata['width']}")
        lines.append(f"    height: {metadata['height']}")
        lines.append(f"    physical_path: {yaml_scalar(metadata['physical_path'])}")
        emitted_bitmap = f"{bitmap_directory_name}/{alias}.bmp" if bitmap_directory_name else f"{alias}.bmp"
        lines.append(f"    emitted_bitmap: {yaml_scalar(emitted_bitmap)}")
        lines.append(f"    emitted_bitmap_mode: {yaml_scalar(bitmap_modes.get(alias, 'not_emitted'))}")
        animation_frames = metadata.get("animation_frames", [])
        if animation_frames:
            lines.append(f"    animation_frame_count: {len(animation_frames)}")
            lines.append(
                "    animation_frames_per_second: "
                f"{int(metadata.get('animation_frames_per_second', 0) or 0)}"
            )
            lines.append("    animation_frames:")
            for frame in animation_frames:
                frame_alias = str(frame.get("alias", ""))
                frame_bitmap = (
                    f"{bitmap_directory_name}/{frame_alias}.bmp"
                    if bitmap_directory_name
                    else f"{frame_alias}.bmp"
                )
                lines.append(f"      - alias: {yaml_scalar(frame_alias)}")
                lines.append(f"        source_texture: {yaml_scalar(frame.get('source_texture', ''))}")
                lines.append(f"        physical_path: {yaml_scalar(frame.get('physical_path', ''))}")
                lines.append(f"        emitted_bitmap: {yaml_scalar(frame_bitmap)}")
                lines.append(
                    f"        frames_per_second: {int(frame.get('frames_per_second', 0) or 0)}"
                )
        for key in [
            "dtx_surface_flag",
            "dtx_texture_group",
            "dtx_bpp",
            "dtx_mipmap_count",
            "dtx_mipmaps_used",
            "dtx_flags",
            "dtx_detail_scale",
            "dtx_detail_angle",
            "dtx_command_string",
        ]:
            if key in metadata:
                lines.append(f"    {key}: {yaml_scalar(metadata[key])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fnv1a64(data: bytes) -> int:
    value = 14695981039346656037
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & 0xffffffffffffffff
    return value


def encode_bgra_rle(pixels: list[int]) -> bytes:
    output = bytearray()
    index = 0
    while index < len(pixels):
        run = 1
        while run < 128 and index + run < len(pixels) and pixels[index + run] == pixels[index]:
            run += 1
        if run >= 2:
            output.append(0x80 | (run - 1))
            output.extend(struct.pack("<I", pixels[index]))
            index += run
            continue

        start = index
        index += 1
        while index - start < 128 and index < len(pixels):
            if index + 1 < len(pixels) and pixels[index] == pixels[index + 1]:
                break
            index += 1
        output.append(index - start - 1)
        output.extend(struct.pack(f"<{index - start}I", *pixels[start:index]))
    return bytes(output)


def navigation_mechanisms_by_bmodel(dat_world: DatWorld, bmodels: list[OdmBModel]) -> dict[int, int]:
    result: dict[int, int] = {}
    for object_index, world_object in enumerate(dat_world.objects):
        mechanism_kind = MM9_MECHANISM_CLASS_KINDS.get(world_object.name)
        is_destructible = world_object.name in MM9_DESTRUCTIBLE_CLASS_NAMES
        if mechanism_kind is None and not is_destructible:
            continue
        values = property_map_cased(world_object)
        if not is_destructible and not any(mechanism_motion_support(mechanism_kind, values)):
            continue
        binding = find_bmodel_binding_for_mechanism(values, bmodels)
        if binding is None:
            continue
        bmodel_index, _, _ = binding
        runtime_id = mechanism_runtime_id(object_index)
        result.setdefault(bmodel_index, runtime_id)
        if is_destructible:
            for auxiliary_bmodel_index in destructible_auxiliary_bmodel_indices(bmodel_index, bmodels):
                result.setdefault(auxiliary_bmodel_index, runtime_id)
    return result


def navigation_face_geometry_key(
    bmodel: OdmBModel,
    face: OdmFace,
    kind: int,
    mechanism_id: int,
) -> tuple[Any, ...]:
    vertices = sorted(
        (bmodel.vertices[index].x, bmodel.vertices[index].y, bmodel.vertices[index].z)
        for index in face.vertex_indices
    )
    return (kind, mechanism_id, tuple(vertices))


def navigation_floor_component_counts(
    records: list[tuple[int, int, int, int, int, int, int]],
    bmodels: list[OdmBModel],
) -> tuple[int, int]:
    floor_records = [record for record in records if record[4] == OUTDOOR_NAVIGATION_KIND_FLOOR]
    if not floor_records:
        return 0, 0

    parents = list(range(len(floor_records)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    edge_owners: dict[tuple[tuple[int, int, int], tuple[int, int, int]], int] = {}
    for record_index, record in enumerate(floor_records):
        _, bmodel_index, face_index, _, _, _, _ = record
        bmodel = bmodels[bmodel_index]
        face = bmodel.faces[face_index]
        vertices = [
            (bmodel.vertices[index].x, bmodel.vertices[index].y, bmodel.vertices[index].z)
            for index in face.vertex_indices
        ]
        for vertex_index, vertex in enumerate(vertices):
            next_vertex = vertices[(vertex_index + 1) % len(vertices)]
            edge = tuple(sorted((vertex, next_vertex)))
            owner = edge_owners.get(edge)
            if owner is None:
                edge_owners[edge] = record_index
            else:
                union(record_index, owner)

    component_sizes: dict[int, int] = {}
    for index in range(len(floor_records)):
        root = find(index)
        component_sizes[root] = component_sizes.get(root, 0) + 1
    return len(component_sizes), sum(1 for size in component_sizes.values() if size == 1)


def mark_navigation_coplanar_triangle_pairs(
    records: list[tuple[int, int, int, int, int, int]],
    bmodels: list[OdmBModel],
) -> tuple[list[tuple[int, int, int, int, int, int, int]], int]:
    edge_owners: dict[tuple[Any, ...], int] = {}
    paired_records: set[int] = set()
    merge_offsets = [0] * len(records)
    merge_count = 0

    for record_index, record in enumerate(records):
        _, bmodel_index, face_index, mechanism_id, kind, _ = record
        face = bmodels[bmodel_index].faces[face_index]
        if mechanism_id != 0 or kind != OUTDOOR_NAVIGATION_KIND_FLOOR or len(face.vertex_indices) != 3:
            continue

        vertices = [
            (
                bmodels[bmodel_index].vertices[index].x,
                bmodels[bmodel_index].vertices[index].y,
                bmodels[bmodel_index].vertices[index].z,
            )
            for index in face.vertex_indices
        ]
        plane = (*face.plane_normal, face.plane_distance)
        for vertex_index, vertex in enumerate(vertices):
            next_vertex = vertices[(vertex_index + 1) % len(vertices)]
            edge_key = (plane, *sorted((vertex, next_vertex)))
            owner_index = edge_owners.get(edge_key)
            if owner_index is None:
                edge_owners[edge_key] = record_index
                continue
            if owner_index in paired_records or record_index in paired_records:
                continue
            owner = records[owner_index]
            owner_face = bmodels[owner[1]].faces[owner[2]]
            owner_vertices = {
                (
                    bmodels[owner[1]].vertices[index].x,
                    bmodels[owner[1]].vertices[index].y,
                    bmodels[owner[1]].vertices[index].z,
                )
                for index in owner_face.vertex_indices
            }
            current_vertices = set(vertices)
            shared_vertices = owner_vertices & current_vertices
            owner_only = owner_vertices - shared_vertices
            current_only = current_vertices - shared_vertices
            if (
                len(owner_vertices | current_vertices) != 4
                or len(shared_vertices) != 2
                or len(owner_only) != 1
                or len(current_only) != 1
                or record_index - owner_index > 0xffff
            ):
                continue
            edge_start, edge_end = tuple(shared_vertices)
            owner_point = next(iter(owner_only))
            current_point = next(iter(current_only))
            edge_x = edge_end[0] - edge_start[0]
            edge_y = edge_end[1] - edge_start[1]
            owner_side = edge_x * (owner_point[1] - edge_start[1]) - edge_y * (owner_point[0] - edge_start[0])
            current_side = (
                edge_x * (current_point[1] - edge_start[1])
                - edge_y * (current_point[0] - edge_start[0])
            )
            if owner_side == 0 or current_side == 0 or owner_side * current_side >= 0:
                continue
            merge_offsets[record_index] = record_index - owner_index
            paired_records.add(owner_index)
            paired_records.add(record_index)
            merge_count += 1
            break

    return [record + (merge_offsets[index],) for index, record in enumerate(records)], merge_count


def build_navigation_records(
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    mechanisms_by_bmodel: dict[int, int] | None = None,
) -> tuple[list[tuple[int, int, int, int, int, int, int]], dict[str, Any]]:
    if mechanisms_by_bmodel is None:
        mechanisms_by_bmodel = navigation_mechanisms_by_bmodel(dat_world, bmodels)
    records: list[tuple[int, int, int, int, int, int]] = []
    geometry_keys: set[tuple[Any, ...]] = set()
    stats: dict[str, Any] = {
        "navigation_source_faces": sum(len(bmodel.faces) for bmodel in bmodels),
        "navigation_floor_facets": 0,
        "navigation_barrier_facets": 0,
        "navigation_dynamic_facets": 0,
        "navigation_duplicate_facets_removed": 0,
        "navigation_decorative_faces_excluded": 0,
        "navigation_ceiling_faces_excluded": 0,
        "navigation_steep_faces_excluded": 0,
        "navigation_other_faces_excluded": 0,
        "navigation_max_slope_degrees": 0.0,
    }
    collision_roles = {"world_geometry", "physics_hull", "invisible_collision"}

    for bmodel_index, bmodel in enumerate(bmodels):
        decorative = bmodel.name.lower().startswith(
            ("mm9_static_prop_", "mm9_destructible_prop_", "mm9_chest_", "mm9_pickup_")
        )
        mechanism_id = mechanisms_by_bmodel.get(bmodel_index, 0)

        for face_index, face in enumerate(bmodel.faces):
            role = bmodel.source_collision_role_for_face[face_index]
            if decorative:
                stats["navigation_decorative_faces_excluded"] += 1
                continue

            kind = 0
            flags = 0
            normal_z = face.plane_normal[2] / OUTDOOR_FACE_PLANE_SCALE
            if role == "ai_barrier":
                kind = OUTDOOR_NAVIGATION_KIND_BARRIER
                flags = OUTDOOR_NAVIGATION_FLAG_BLOCKING
            elif (
                role in collision_roles
                and face.reserved & ODM_FACE_RESERVED_NOT_A_STEP == 0
                and face.polygon_type
                in {OUTDOOR_POLYGON_FLOOR, OUTDOOR_POLYGON_IN_BETWEEN_FLOOR_AND_WALL}
                and normal_z >= OUTDOOR_NAVIGATION_MIN_WALKABLE_NORMAL_Z
            ):
                kind = OUTDOOR_NAVIGATION_KIND_FLOOR
                flags = OUTDOOR_NAVIGATION_FLAG_WALKABLE
                slope_degrees = math.degrees(math.acos(min(1.0, normal_z)))
                stats["navigation_max_slope_degrees"] = max(
                    stats["navigation_max_slope_degrees"], slope_degrees
                )
            elif role in collision_roles and face.polygon_type in {
                OUTDOOR_POLYGON_VERTICAL_WALL,
                OUTDOOR_POLYGON_IN_BETWEEN_FLOOR_AND_WALL,
            }:
                kind = OUTDOOR_NAVIGATION_KIND_BARRIER
                flags = OUTDOOR_NAVIGATION_FLAG_BLOCKING
                if face.polygon_type == OUTDOOR_POLYGON_IN_BETWEEN_FLOOR_AND_WALL:
                    stats["navigation_steep_faces_excluded"] += 1
            elif face.polygon_type in {
                OUTDOOR_POLYGON_CEILING,
                OUTDOOR_POLYGON_IN_BETWEEN_CEILING_AND_WALL,
            }:
                stats["navigation_ceiling_faces_excluded"] += 1
                continue
            else:
                stats["navigation_other_faces_excluded"] += 1
                continue

            geometry_key = navigation_face_geometry_key(bmodel, face, kind, mechanism_id)
            if geometry_key in geometry_keys:
                stats["navigation_duplicate_facets_removed"] += 1
                continue
            geometry_keys.add(geometry_key)

            if mechanism_id != 0:
                flags |= OUTDOOR_NAVIGATION_FLAG_DYNAMIC
                stats["navigation_dynamic_facets"] += 1
            if kind == OUTDOOR_NAVIGATION_KIND_FLOOR:
                stats["navigation_floor_facets"] += 1
            else:
                stats["navigation_barrier_facets"] += 1

            source_key = (bmodel_index << 32) | face_index
            records.append((source_key, bmodel_index, face_index, mechanism_id, kind, flags))

    merged_records, merged_pair_count = mark_navigation_coplanar_triangle_pairs(records, bmodels)
    component_count, isolated_component_count = navigation_floor_component_counts(merged_records, bmodels)
    stats["navigation_floor_components"] = component_count
    stats["navigation_isolated_floor_components"] = isolated_component_count
    stats["navigation_cooked_facets"] = len(records)
    stats["navigation_coplanar_triangle_pairs_merged"] = merged_pair_count
    stats["navigation_max_slope_degrees"] = round(stats["navigation_max_slope_degrees"], 4)
    return merged_records, stats


def build_navigation_bytes(
    odm_bytes: bytes,
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    mechanisms_by_bmodel: dict[int, int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    records, stats = build_navigation_records(dat_world, bmodels, mechanisms_by_bmodel)
    source_face_count = sum(len(bmodel.faces) for bmodel in bmodels)
    geometry_hash = fnv1a64(odm_bytes)
    stats["navigation_geometry_fnv1a64"] = geometry_hash
    data = bytearray(struct.pack(
        "<8sIIIIQIIII",
        OUTDOOR_NAVIGATION_MAGIC,
        OUTDOOR_NAVIGATION_VERSION,
        OUTDOOR_NAVIGATION_HEADER_SIZE,
        OUTDOOR_NAVIGATION_RECORD_SIZE,
        0,
        geometry_hash,
        len(bmodels),
        source_face_count,
        len(records),
        0,
    ))
    for source_key, bmodel_index, face_index, mechanism_id, kind, flags, merge_leader_offset in records:
        data.extend(struct.pack(
            "<QIIIBBH",
            source_key,
            bmodel_index,
            face_index,
            mechanism_id,
            kind,
            flags,
            merge_leader_offset,
        ))
    return bytes(data), stats


def write_navigation_metadata(
    path: Path,
    geometry_name: str,
    navigation_name: str,
    geometry_hash: int,
    stats: dict[str, Any],
) -> None:
    lines = [
        "format_version: 1",
        'kind: "outdoor_navigation_metadata"',
        "source:",
        f"  geometry_file: {yaml_scalar(geometry_name)}",
        f"  navigation_file: {yaml_scalar(navigation_name)}",
        f"  geometry_fnv1a64: {geometry_hash}",
        "settings:",
        f"  minimum_walkable_normal_z: {OUTDOOR_NAVIGATION_MIN_WALKABLE_NORMAL_Z}",
        "stats:",
    ]
    for key, value in stats.items():
        lines.append(f"  {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_render_data_bytes(
    odm_bytes: bytes,
    bmodels: list[OdmBModel],
    mechanisms_by_bmodel: dict[int, int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    mechanisms_by_bmodel = mechanisms_by_bmodel or {}
    records: list[tuple[int, int, int, int, int, int]] = []
    cells: set[tuple[int, int]] = set()
    static_faces = 0
    dynamic_faces = 0
    translucent_faces = 0
    invisible_faces = 0
    untextured_faces = 0

    for bmodel_index, bmodel in enumerate(bmodels):
        dynamic = bmodel_index in mechanisms_by_bmodel
        for face_index, face in enumerate(bmodel.faces):
            if face.attributes & FACE_ATTRIBUTE_INVISIBLE:
                invisible_faces += 1
                continue
            if len(face.vertex_indices) < 3 or not face.texture_alias:
                untextured_faces += 1
                continue

            vertices = [bmodel.vertices[index] for index in face.vertex_indices]
            centroid_x = sum(vertex.x for vertex in vertices) / len(vertices)
            centroid_y = sum(vertex.y for vertex in vertices) / len(vertices)
            cell_x = math.floor(centroid_x / OUTDOOR_RENDER_CELL_SIZE)
            cell_y = math.floor(centroid_y / OUTDOOR_RENDER_CELL_SIZE)
            if not -32768 <= cell_x <= 32767 or not -32768 <= cell_y <= 32767:
                raise ValueError("render chunk cell coordinate does not fit the sidecar format")

            flags = OUTDOOR_RENDER_FLAG_DYNAMIC if dynamic else 0
            source_surface_flags = (
                bmodel.source_surface_flags_for_face[face_index]
                if face_index < len(bmodel.source_surface_flags_for_face)
                else 0
            )
            if source_surface_flags & LT_SURFACE_FLAG_TRANSPARENT:
                flags |= OUTDOOR_RENDER_FLAG_TRANSLUCENT
                translucent_faces += 1
            source_key = (bmodel_index << 32) | face_index
            records.append((source_key, bmodel_index, face_index, cell_x, cell_y, flags))
            if dynamic:
                dynamic_faces += 1
            else:
                static_faces += 1
                cells.add((cell_x, cell_y))

    geometry_hash = fnv1a64(odm_bytes)
    data = bytearray(struct.pack(
        "<8sIIIIQIIII",
        OUTDOOR_RENDER_MAGIC,
        OUTDOOR_RENDER_VERSION,
        OUTDOOR_RENDER_HEADER_SIZE,
        OUTDOOR_RENDER_RECORD_SIZE,
        OUTDOOR_RENDER_CELL_SIZE,
        geometry_hash,
        len(bmodels),
        sum(len(bmodel.faces) for bmodel in bmodels),
        len(records),
        0,
    ))
    for record in records:
        data.extend(struct.pack("<QIIhhI", *record))

    return bytes(data), {
        "render_geometry_fnv1a64": geometry_hash,
        "render_cell_size": OUTDOOR_RENDER_CELL_SIZE,
        "render_source_faces": sum(len(bmodel.faces) for bmodel in bmodels),
        "render_cooked_faces": len(records),
        "render_static_faces": static_faces,
        "render_dynamic_faces": dynamic_faces,
        "render_translucent_faces": translucent_faces,
        "render_static_cells": len(cells),
        "render_invisible_faces_excluded": invisible_faces,
        "render_untextured_faces_excluded": untextured_faces,
    }


def build_outdoor_lighting_bytes(
    odm_bytes: bytes,
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    lights: list[ExportedLight],
) -> tuple[bytes, dict[str, int]]:
    emitted_lightmaps: dict[tuple[int, int], Poly] = {}
    for bmodel in bmodels:
        if bmodel.source_model_index >= len(dat_world.world_models):
            continue
        source_model = dat_world.world_models[bmodel.source_model_index]
        for poly_index in bmodel.source_poly_for_face:
            if poly_index < 0 or poly_index >= len(source_model.polies):
                continue
            poly = source_model.polies[poly_index]
            if poly.lightmap_pixels_bgra:
                emitted_lightmaps[(bmodel.source_model_index, poly_index)] = poly

    pages, atlas_rects = pack_lightmap_atlases(emitted_lightmaps)
    ambient = parse_world_ambient_color(dat_world.world_info)
    lighting_faces: list[OutdoorLightingFace] = []
    for bmodel_index, bmodel in enumerate(bmodels):
        source_model = (
            dat_world.world_models[bmodel.source_model_index]
            if bmodel.source_model_index < len(dat_world.world_models)
            else None
        )
        for face_index, face in enumerate(bmodel.faces):
            source_poly_index = bmodel.source_poly_for_face[face_index]
            key = (bmodel.source_model_index, source_poly_index)
            rect = atlas_rects.get(key)
            local_uvs: list[tuple[float, float]] = []
            if rect is not None and source_model is not None:
                source_poly = source_model.polies[source_poly_index]
                local_uvs = lightmap_uvs_for_poly(
                    source_model,
                    source_poly,
                    list(face.vertex_indices),
                    dat_world.world_info.light_map_grid_size,
                )
                page = pages[rect.page_index]
                vertex_uvs = [
                    (
                        (rect.x + uv[0] * rect.width) / page.width,
                        (rect.y + uv[1] * rect.height) / page.height,
                    )
                    for uv in local_uvs
                ]
                vertex_colors = [0xFFFFFFFF] * len(face.vertex_indices)
                page_index = rect.page_index
            else:
                vertex_uvs = (
                    [(0.5 / pages[0].width, 0.5 / pages[0].height)] * len(face.vertex_indices)
                    if pages
                    else [(0.5, 0.5)] * len(face.vertex_indices)
                )
                vertex_colors = [
                    static_object_light_color(bmodel.vertices[vertex_index], ambient, lights)
                    for vertex_index in face.vertex_indices
                ]
                page_index = 0 if pages else 0xFFFF
            lighting_faces.append(OutdoorLightingFace(
                bmodel_index=bmodel_index,
                face_index=face_index,
                page_index=page_index,
                has_lightmap=rect is not None,
                vertex_uvs=vertex_uvs,
                vertex_colors_abgr=vertex_colors,
            ))

    page_records_offset = OUTDOOR_LIGHTING_HEADER_SIZE
    face_records_offset = page_records_offset + len(pages) * OUTDOOR_LIGHTING_PAGE_RECORD_SIZE
    vertex_count = sum(len(face.vertex_uvs) for face in lighting_faces)
    vertex_records_offset = face_records_offset + len(lighting_faces) * OUTDOOR_LIGHTING_FACE_RECORD_SIZE
    light_records_offset = vertex_records_offset + vertex_count * OUTDOOR_LIGHTING_VERTEX_RECORD_SIZE
    pixel_data_offset = light_records_offset + len(lights) * OUTDOOR_LIGHTING_LIGHT_RECORD_SIZE
    page_payloads = [encode_bgra_rle(page.pixels_bgra) for page in pages]
    pixel_bytes = sum(len(payload) for payload in page_payloads)
    file_size = pixel_data_offset + pixel_bytes
    data = bytearray(file_size)
    ambient_abgr = abgr_color(ambient[0] / 255.0, ambient[1] / 255.0, ambient[2] / 255.0)
    data[0:8] = OUTDOOR_LIGHTING_MAGIC
    struct.pack_into("<IIQ", data, 8, OUTDOOR_LIGHTING_VERSION, OUTDOOR_LIGHTING_HEADER_SIZE, fnv1a64(odm_bytes))
    struct.pack_into(
        "<IIIIIIIIIIIII",
        data,
        24,
        len(bmodels),
        sum(len(bmodel.faces) for bmodel in bmodels),
        len(pages),
        len(lighting_faces),
        vertex_count,
        len(lights),
        page_records_offset,
        face_records_offset,
        vertex_records_offset,
        light_records_offset,
        pixel_data_offset,
        file_size,
        ambient_abgr,
    )

    current_pixel_offset = pixel_data_offset
    for page_index, (page, payload) in enumerate(zip(pages, page_payloads)):
        page_pixel_bytes = len(payload)
        struct.pack_into(
            "<IIII",
            data,
            page_records_offset + page_index * OUTDOOR_LIGHTING_PAGE_RECORD_SIZE,
            page.width,
            page.height,
            current_pixel_offset,
            page_pixel_bytes,
        )
        data[current_pixel_offset:current_pixel_offset + page_pixel_bytes] = payload
        current_pixel_offset += page_pixel_bytes

    current_vertex_index = 0
    for face_record_index, face in enumerate(lighting_faces):
        flags = OUTDOOR_LIGHTING_FACE_HAS_LIGHTMAP if face.has_lightmap else 0
        source_key = (face.bmodel_index << 32) | face.face_index
        struct.pack_into(
            "<QIIHHI",
            data,
            face_records_offset + face_record_index * OUTDOOR_LIGHTING_FACE_RECORD_SIZE,
            source_key,
            face.bmodel_index,
            face.face_index,
            face.page_index,
            flags,
            current_vertex_index,
        )
        for vertex_index, uv in enumerate(face.vertex_uvs):
            struct.pack_into(
                "<ffI",
                data,
                vertex_records_offset + current_vertex_index * OUTDOOR_LIGHTING_VERTEX_RECORD_SIZE,
                uv[0],
                uv[1],
                face.vertex_colors_abgr[vertex_index],
            )
            current_vertex_index += 1

    for light_index, light in enumerate(lights):
        flags = 0
        if light.light_objects:
            flags |= OUTDOOR_LIGHTING_LIGHT_OBJECTS
        if light.fast_light_objects:
            flags |= OUTDOOR_LIGHTING_LIGHT_FAST_OBJECTS
        if light.static_object_light_eligible:
            flags |= OUTDOOR_LIGHTING_LIGHT_STATIC_OBJECT_ELIGIBLE
        if light.cast_shadows:
            flags |= 0x08
        if light.clip_light:
            flags |= 0x10
        if light.global_object_light:
            flags |= OUTDOOR_LIGHTING_LIGHT_GLOBAL_OBJECT
        light_type = (
            OUTDOOR_LIGHTING_LIGHT_DIRECTIONAL
            if light.light_type == "directional"
            else OUTDOOR_LIGHTING_LIGHT_POINT
        )
        record_offset = light_records_offset + light_index * OUTDOOR_LIGHTING_LIGHT_RECORD_SIZE
        struct.pack_into(
            "<II4fII4f3f5I",
            data,
            record_offset,
            light.source_object_index,
            light_type,
            float(light.position[0]),
            float(light.position[1]),
            float(light.position[2]),
            float(light.radius),
            abgr_color(*(channel / 255.0 for channel in light.effective_color)),
            flags,
            *light.source_rotation_lt,
            light.fov_degrees,
            light.brightness_scale,
            light.object_brightness_scale,
            abgr_color(*(channel / 255.0 for channel in light.color)),
            zlib.crc32(light.light_group.encode("utf-8")),
            0,
            0,
            0,
        )

    return bytes(data), {
        "lighting_geometry_fnv1a64": fnv1a64(odm_bytes),
        "lighting_atlas_pages": len(pages),
        "lighting_atlas_texels": sum(page.width * page.height for page in pages),
        "lighting_lightmapped_source_polies": len(emitted_lightmaps),
        "lighting_faces": len(lighting_faces),
        "lighting_lightmapped_faces": sum(1 for face in lighting_faces if face.has_lightmap),
        "lighting_vertex_records": vertex_count,
        "lighting_authored_lights": len(lights),
        **dat_world.lightmap_stats,
    }


def write_render_data_metadata(
    path: Path,
    geometry_name: str,
    render_name: str,
    stats: dict[str, Any],
) -> None:
    lines = [
        "format_version: 1",
        'kind: "outdoor_render_data_metadata"',
        "source:",
        f"  geometry_file: {yaml_scalar(geometry_name)}",
        f"  render_file: {yaml_scalar(render_name)}",
        f"  geometry_fnv1a64: {stats['render_geometry_fnv1a64']}",
        "settings:",
        f"  cell_size: {stats['render_cell_size']}",
        "stats:",
    ]
    for key, value in stats.items():
        lines.append(f"  {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_source_metadata(
    path: Path,
    source_dat: Path,
    odm_name: str,
    material_aliases_name: str,
    model_assets_name: str,
    raw_objects_name: str,
    coordinate_scale: float,
    bmodels: list[OdmBModel],
    stats: dict[str, Any],
) -> None:
    lines = [
        "format_version: 1",
        'kind: "outdoor_source_metadata"',
        "source:",
        f"  geometry_file: {yaml_scalar(odm_name)}",
        '  source_kind: "mm9_dat"',
        f"  source_dat: {yaml_scalar(str(source_dat))}",
        f"  coordinate_scale: {coordinate_scale:.8g}",
        "related_files:",
        f"  navigation: {yaml_scalar(str(Path(odm_name).with_suffix('.nav')))}",
        f"  render_data: {yaml_scalar(str(Path(odm_name).with_suffix('.render')))}",
        f"  lighting: {yaml_scalar(str(Path(odm_name).with_suffix('.lighting')))}",
        f"  material_aliases: {yaml_scalar(material_aliases_name)}",
        f"  model_assets: {yaml_scalar(model_assets_name)}",
        f"  raw_objects: {yaml_scalar(raw_objects_name)}",
        "stats:",
    ]
    for key, value in stats.items():
        lines.append(f"  {key}: {value}")
    lines.append("bmodels:")
    for bmodel_index, bmodel in enumerate(bmodels):
        lines.append(f"  - bmodel_index: {bmodel_index}")
        lines.append(f"    name: {yaml_scalar(bmodel.name)}")
        lines.append(f"    source_model_index: {bmodel.source_model_index}")
        lines.append(f"    source_model_name: {yaml_scalar(bmodel.source_model_name)}")
        lines.append(f"    world_info_flags: {bmodel.source_world_info_flags}")
        lines.append(
            "    world_translation_lt: ["
            + ", ".join(f"{value:.8g}" for value in bmodel.source_world_translation_lt)
            + "]"
        )
        lines.append("    roles:")
        compact_name = normalize_model_role_name(bmodel.source_model_name or bmodel.name)
        lines.append(f"      physics_bsp: {yaml_scalar(compact_name == 'physicsbsp')}")
        lines.append(f"      vis_bsp: {yaml_scalar(compact_name == 'visbsp')}")
        lines.append(f"      movable: {yaml_scalar((bmodel.source_world_info_flags & (1 << 1)) != 0)}")
        lines.append(f"    vertex_count: {len(bmodel.vertices)}")
        lines.append(f"    face_count: {len(bmodel.faces)}")
    lines.append("bmodel_faces:")
    lines.append("  source_faces:")
    for bmodel_index, bmodel in enumerate(bmodels):
        for face_index, poly_index in enumerate(bmodel.source_poly_for_face):
            lines.append(f"    - bmodel_index: {bmodel_index}")
            lines.append(f"      face_index: {face_index}")
            lines.append('      source_kind: "mm9_dat"')
            lines.append(f"      source_model_index: {bmodel.source_model_index}")
            lines.append(f"      source_model_name: {yaml_scalar(bmodel.source_model_name or bmodel.name)}")
            lines.append(f"      source_poly_index: {poly_index}")
            lines.append(f"      source_surface_index: {bmodel.source_surface_for_face[face_index]}")
            lines.append(f"      source_surface_flags: {bmodel.source_surface_flags_for_face[face_index]}")
            lines.append(f"      source_texture_index: {bmodel.source_texture_index_for_face[face_index]}")
            lines.append(f"      barrel_liquid: {yaml_scalar(bmodel.source_barrel_liquid_for_face[face_index])}")
            lines.append(f"      source_texture_flags: {bmodel.source_texture_flags_for_face[face_index]}")
            lines.append(f"      texture_alias: {yaml_scalar(bmodel.faces[face_index].texture_alias)}")
            lines.append(f"      attributes: {bmodel.faces[face_index].attributes}")
            lines.append(f"      collision_role: {yaml_scalar(bmodel.source_collision_role_for_face[face_index])}")
            lines.append(f"      render_role: {yaml_scalar(bmodel.source_render_role_for_face[face_index])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_model_assets(path: Path, source_dat: Path, model_assets: list[dict[str, Any]]) -> None:
    lines = [
        "format_version: 1",
        'kind: "mm9_model_assets"',
        f"source_dat: {yaml_scalar(str(source_dat))}",
        f"unique_model_count: {len(model_assets)}",
        "models:",
    ]
    for asset in model_assets:
        lines.append(f"  - source_model: {yaml_scalar(asset['source_model'])}")
        lines.append(f"    model_asset: {yaml_scalar(asset['model_asset'])}")
        lines.append(f"    instance_count: {asset['instance_count']}")
        lines.append("    source_object_indices:")
        for object_index in asset["source_object_indices"]:
            lines.append(f"      - {object_index}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def property_to_plain(prop: ObjectProperty) -> dict[str, Any]:
    return {
        "name": prop.name,
        "code": prop.code,
        "flags": prop.flags,
        "declared_data_length": prop.declared_data_length,
        "raw_hex": prop.raw_data.hex(),
        "decoded": prop.decoded,
        "decode_error": prop.decode_error,
        "value": prop.value,
    }


def write_raw_objects(path: Path, dat_world: DatWorld) -> None:
    unknown_properties = [
        prop
        for obj in dat_world.objects
        for prop in obj.properties
        if not prop.decoded
    ]
    unknown_codes = sorted({prop.code for prop in unknown_properties})
    lines = [
        "format_version: 1",
        'kind: "mm9_raw_world_objects"',
        f"source_dat: {yaml_scalar(str(dat_world.path))}",
        f"object_count: {len(dat_world.objects)}",
        f"unknown_property_count: {len(unknown_properties)}",
        "unknown_property_codes: [" + ", ".join(str(code) for code in unknown_codes) + "]",
        "objects:",
    ]
    for index, obj in enumerate(dat_world.objects):
        lines.append(f"  - object_index: {index}")
        lines.append(f"    name: {yaml_scalar(obj.name)}")
        lines.append(f"    property_count: {len(obj.properties)}")
        lines.append(f"    data_length: {obj.data_length}")
        lines.append(f"    trailing_hex: {yaml_scalar(obj.trailing_data.hex())}")
        lines.append("    properties:")
        for prop in obj.properties:
            lines.append(f"      - name: {yaml_scalar(prop.name)}")
            lines.append(f"        code: {prop.code}")
            lines.append(f"        flags: {prop.flags}")
            lines.append(f"        declared_data_length: {prop.declared_data_length}")
            lines.append(f"        consumed_data_length: {len(prop.raw_data)}")
            lines.append(f"        decoded: {yaml_scalar(prop.decoded)}")
            if prop.decode_error:
                lines.append(f"        decode_error: {yaml_scalar(prop.decode_error)}")
            lines.append(f"        raw_hex: {yaml_scalar(prop.raw_data.hex())}")
            lines.append(f"        value_json: {yaml_scalar(json.dumps(prop.value))}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat", required=True, type=Path, help="Path to an extracted MM9 DAT v66 world")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write ODM and sidecars")
    parser.add_argument("--name", default=None, help="Output basename, defaults to DAT stem lowercased")
    parser.add_argument(
        "--scale",
        default=MM9_TO_OPENYAMM_COORDINATE_SCALE,
        type=float,
        help="Coordinate scale from LithTech units to OpenYAMM units",
    )
    parser.add_argument(
        "--extracted-root",
        default=Path("mm9/extracted"),
        type=Path,
        help="Root of extracted MM9 REZ files, used for DTX size lookup",
    )
    parser.add_argument(
        "--actor-table",
        default=Path("mm9/extracted/DATA/DATA/ACTOR.txt"),
        type=Path,
        help="MM9 actor archetype table",
    )
    parser.add_argument(
        "--npc-replacements",
        default=Path("tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv"),
        type=Path,
        help="Authoritative MM9 NPC to legacy actor mapping",
    )
    parser.add_argument(
        "--npc-names",
        default=Path("mm9/extracted/RUDE/RUDE/NPCNAME.rude"),
        type=Path,
        help="MM9 RUDE NPC name table",
    )
    parser.add_argument(
        "--monster-replacements",
        default=Path("tools/mm9_import_discovery/mm9_monster_legacy_replacements.tsv"),
        type=Path,
        help="Authoritative MM9 monster to legacy billboard-family mapping",
    )
    parser.add_argument(
        "--source-monsters",
        default=Path("mm9/extracted/DATA/DATA/MONSTERS.txt"),
        type=Path,
        help="Authoritative MM9 monster archetype table",
    )
    parser.add_argument(
        "--mm9-monster-data",
        default=Path("assets_dev/worlds/mm9/data_tables/monster_data.txt"),
        type=Path,
        help="World-owned MM9 monster gameplay table",
    )
    parser.add_argument(
        "--mm9-monster-descriptors",
        default=Path("assets_dev/worlds/mm9/data_tables/monster_descriptors.txt"),
        type=Path,
        help="World-owned MM9 monster billboard descriptor table",
    )
    parser.add_argument(
        "--monster-descriptors",
        default=Path("assets_dev/engine/data_tables/monster_descriptors.txt"),
        type=Path,
        help="Merged legacy actor descriptor table",
    )
    parser.add_argument(
        "--bitmap-dir",
        type=Path,
        help="Optional shared directory for emitted BMP aliases; defaults to a map-local .bitmaps directory",
    )
    parser.add_argument(
        "--location-type",
        choices=("exterior", "enclosed"),
        default="exterior",
        help="Gameplay environment semantics for the generated BModel world",
    )
    parser.add_argument(
        "--item-id-map",
        default=Path("assets_dev/worlds/mm9/state/item_ids.yml"),
        type=Path,
        help="Canonical MM9 raw-to-runtime item id map",
    )
    args = parser.parse_args()

    output_name = args.name or args.dat.stem.lower()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dat_world = read_dat_world(args.dat)
    item_source_manifest = build_mm9_item_source_manifest(
        output_name,
        dat_world.objects,
        Mm9ItemIdMap.load(args.item_id_map),
        args.scale,
    )
    item_source_manifest.require_resolved_item_references()
    texture_sizes = build_texture_size_index(args.extracted_root)
    bmodels, alias_metadata, stats, baked_instances = transcode_geometry(
        dat_world,
        args.scale,
        texture_sizes,
        args.extracted_root,
        excluded_baked_object_indices=item_source_manifest.excluded_baked_object_indices(),
        baked_model_variant_sources={
            source.provenance.source_object_index: list(zip(source.model_variants, source.model_variant_skins))
            for source in item_source_manifest.persistent_item_mechanisms
            if source.model_variants
        },
    )
    bind_mm9_barrel_geometry(item_source_manifest, bmodels, baked_instances, alias_metadata)
    model_instance_lines: list[str] = []
    model_assets: list[dict[str, Any]] = []
    baked_model_instance_lines = build_baked_model_instance_lines(baked_instances)
    mechanism_lines, mechanism_stats = build_mechanism_lines(dat_world, bmodels, args.scale)
    destructible_lines, trigger_volume_lines, destructible_stats = build_destructible_and_trigger_lines(
        dat_world,
        bmodels,
        args.scale,
    )
    destructible_receiver_lines = build_destructible_receiver_lines(dat_world)
    mm9_npc_greeting_lines = build_mm9_npc_greeting_lines(dat_world)
    mm9_monster_replacements = read_mm9_monster_replacements(
        args.source_monsters,
        args.actor_table,
        args.monster_replacements,
        args.mm9_monster_data,
        args.mm9_monster_descriptors,
    )
    mm9_monster_source_indices = mm9_monster_actor_source_object_indices(
        dat_world,
        mm9_monster_replacements,
    )
    mm9_npc_replacements = read_mm9_npc_replacements(
        args.actor_table,
        args.npc_replacements,
        args.monster_descriptors,
    )
    emitted_actor_source_object_indices: set[int] = set()
    mm9_npc_actor_lines = build_mm9_npc_actor_lines(
        dat_world,
        args.scale,
        mm9_npc_replacements,
        read_mm9_npc_names(args.npc_names),
        mm9_monster_source_indices,
        emitted_actor_source_object_indices,
    )
    mm9_monster_actor_lines = build_mm9_monster_actor_lines(
        dat_world,
        args.scale,
        mm9_monster_replacements,
        emitted_actor_source_object_indices,
    )
    item_source_manifest.actor_loot_overrides = [
        source
        for source in item_source_manifest.actor_loot_overrides
        if source.source_object_index in emitted_actor_source_object_indices
    ]
    interactive_face_lines, interactive_face_stats = build_outdoor_mechanism_interactive_face_lines(
        dat_world,
        bmodels,
        item_source_manifest,
        baked_instances,
    )
    perception_face_lines = build_perception_face_lines(bmodels)
    lights, light_stats = export_mm9_lights(dat_world, args.scale)
    light_stats["synthetic_city_sunlight"] = int(ensure_mm9_city_sunlight(output_name, lights))
    light_lines = build_mm9_light_lines(lights)
    party_start_points, party_start_stats = export_mm9_party_start_points(dat_world, args.scale)
    party_start_point_lines = build_mm9_party_start_point_lines(party_start_points)
    entities = build_classic_party_start_entities(party_start_points)
    entity_lines = build_odm_entity_lines(entities)
    authored_fog = export_mm9_authored_fog(dat_world, args.scale)
    stats["model_instances"] = 0
    stats["unique_model_assets"] = 0
    stats["classic_party_start_entities"] = len(entities)
    stats["mm9_npc_actors"] = sum(line.startswith("    - name:") for line in mm9_npc_actor_lines)
    stats["mm9_monster_actors"] = sum(
        line.startswith("    - name:") for line in mm9_monster_actor_lines)
    stats.update(mechanism_stats)
    stats.update(destructible_stats)
    stats.update(interactive_face_stats)
    stats.update(light_stats)
    stats.update(party_start_stats)

    odm_path = args.output_dir / f"{output_name}.odm"
    navigation_path = args.output_dir / f"{output_name}.nav"
    navigation_metadata_path = args.output_dir / f"{output_name}.nav.yml"
    render_data_path = args.output_dir / f"{output_name}.render"
    render_data_metadata_path = args.output_dir / f"{output_name}.render.yml"
    lighting_path = args.output_dir / f"{output_name}.lighting"
    scene_path = args.output_dir / f"{output_name}.scene.yml"
    source_metadata_path = args.output_dir / f"{output_name}.mm9.yml"
    aliases_path = args.output_dir / f"{output_name}.material_aliases.yml"
    model_assets_path = args.output_dir / f"{output_name}.model_assets.yml"
    raw_objects_path = args.output_dir / f"{output_name}.raw_objects.yml"
    default_bitmap_directory_name = f"{output_name}.bitmaps"
    bitmap_dir = args.bitmap_dir or (args.output_dir / default_bitmap_directory_name)
    bitmap_directory_name = os.path.relpath(bitmap_dir, args.output_dir).replace("\\", "/")

    odm_bytes = build_odm_bytes(output_name, bmodels, entities)
    mechanisms_by_bmodel = navigation_mechanisms_by_bmodel(dat_world, bmodels)
    navigation_bytes, navigation_stats = build_navigation_bytes(
        odm_bytes,
        dat_world,
        bmodels,
        mechanisms_by_bmodel,
    )
    render_data_bytes, render_data_stats = build_render_data_bytes(
        odm_bytes,
        bmodels,
        mechanisms_by_bmodel,
    )
    lighting_bytes, lighting_stats = build_outdoor_lighting_bytes(
        odm_bytes,
        dat_world,
        bmodels,
        lights,
    )
    stats.update(navigation_stats)
    stats.update(render_data_stats)
    stats.update(lighting_stats)
    odm_path.write_bytes(odm_bytes)
    navigation_path.write_bytes(navigation_bytes)
    render_data_path.write_bytes(render_data_bytes)
    lighting_path.write_bytes(lighting_bytes)
    write_navigation_metadata(
        navigation_metadata_path,
        odm_path.name,
        navigation_path.name,
        navigation_stats["navigation_geometry_fnv1a64"],
        navigation_stats,
    )
    write_render_data_metadata(
        render_data_metadata_path,
        odm_path.name,
        render_data_path.name,
        render_data_stats,
    )
    bitmap_modes = write_alias_bitmaps(bitmap_dir, alias_metadata)
    surface_animation_lines = build_surface_animation_lines(alias_metadata)
    write_scene_yml(
        scene_path,
        odm_path.name,
        source_metadata_path.name,
        model_instance_lines,
        mechanism_lines,
        interactive_face_lines,
        light_lines,
        party_start_point_lines,
        entity_lines,
        surface_animation_lines,
        baked_model_instance_lines,
        args.location_type,
        mm9_npc_greeting_lines=mm9_npc_greeting_lines,
        mm9_npc_actor_lines=mm9_npc_actor_lines,
        mm9_monster_actor_lines=mm9_monster_actor_lines,
        authored_fog=authored_fog,
        perception_face_lines=perception_face_lines,
        item_source_manifest=item_source_manifest,
        destructible_lines=destructible_lines,
        destructible_receiver_lines=destructible_receiver_lines,
        trigger_volume_lines=trigger_volume_lines,
    )
    write_material_aliases(aliases_path, args.dat, alias_metadata, stats, bitmap_modes, bitmap_directory_name)
    write_source_metadata(
        source_metadata_path,
        args.dat,
        odm_path.name,
        aliases_path.name,
        model_assets_path.name,
        raw_objects_path.name,
        args.scale,
        bmodels,
        stats)
    write_model_assets(model_assets_path, args.dat, model_assets)
    write_raw_objects(raw_objects_path, dat_world)

    print(f"wrote {odm_path} ({odm_path.stat().st_size} bytes)")
    print(f"wrote {navigation_path} ({navigation_path.stat().st_size} bytes)")
    print(f"wrote {navigation_metadata_path}")
    print(f"wrote {render_data_path} ({render_data_path.stat().st_size} bytes)")
    print(f"wrote {render_data_metadata_path}")
    print(f"wrote {lighting_path} ({lighting_path.stat().st_size} bytes)")
    print(f"wrote {scene_path}")
    print(f"wrote {source_metadata_path}")
    print(f"wrote {aliases_path}")
    print(f"wrote {model_assets_path}")
    print(f"wrote {raw_objects_path}")
    print(f"wrote {len(bitmap_modes)} bitmap aliases under {bitmap_dir}")
    print(
        "models={models} source_polies={source_polies} emitted_faces={emitted_faces} "
        "triangulated_polies={triangulated_polies} skipped_polies={skipped_polies} "
        "skipped_degenerate_triangles={skipped_degenerate_triangles} "
        "source_plane_orientation_flips={source_plane_orientation_flips}".format(
            models=len(bmodels),
            **stats,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
