#!/usr/bin/env python3
"""
Transcode a LithTech 2.x/MM9 DAT v66 world into an OpenYAMM outdoor ODM shell.

This is a discovery/import tool. It intentionally writes the existing OpenYAMM
ODM layout so the editor can load the result without a runtime format fork, and
puts MM9-specific source metadata into sidecars.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from convert_abc_model import AbcModel, read_abc
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


DAT_VERSION_LT2 = 66

TERRAIN_MAP_SIZE = 0x4000
CMAP1_SIZE = 0x20000
CMAP2_SIZE = 0x10000
BMODEL_HEADER_SIZE = 0xBC
BMODEL_FACE_SIZE = 0x134
BMODEL_FACE_FLAGS_SIZE = 2
BMODEL_TEXTURE_NAME_SIZE = 10
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
MM9_MECHANISM_EVENT_ID_BASE = 30000
MM9_SPR_HEADER_SIZE = 20
LT_SURFACE_FLAG_INVISIBLE = 0x00000004
MM9_MECHANISM_CLASS_KINDS = {
    "Door": "linear_door",
    "RotatingDoor": "rotating_door",
    "WeightedLift": "weighted_lift",
    "RotatingBrush": "rotating_brush",
    "InvisibleBrush": "collision_volume",
}
MM9_INTERACTIVE_MECHANISM_KINDS = {
    "linear_door",
    "weighted_lift",
    "rotating_door",
    "rotating_brush",
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
    light_group: str


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


@dataclass
class OdmBModel:
    name: str
    source_model_index: int = 0
    source_model_name: str = ""
    source_world_translation_lt: tuple[float, float, float] = (0.0, 0.0, 0.0)
    source_world_info_flags: int = 0
    vertices: list[OdmVertex] = field(default_factory=list)
    faces: list[OdmFace] = field(default_factory=list)
    source_poly_for_face: list[int] = field(default_factory=list)
    source_surface_for_face: list[int] = field(default_factory=list)
    source_surface_flags_for_face: list[int] = field(default_factory=list)
    source_texture_index_for_face: list[int] = field(default_factory=list)
    source_texture_flags_for_face: list[int] = field(default_factory=list)
    source_collision_role_for_face: list[str] = field(default_factory=list)
    source_render_role_for_face: list[str] = field(default_factory=list)


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


@dataclass(frozen=True)
class FaceRole:
    attributes: int
    collision_role: str
    render_role: str


@dataclass(frozen=True)
class LtFloorTriangle:
    vertices: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


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

    return DatWorld(
        path=path,
        version=version,
        object_data_pos=object_data_pos,
        render_data_pos=render_data_pos,
        world_model_pos=world_model_pos,
        world_info=world_info,
        world_models=world_models,
        objects=objects,
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

    frame_count, frame_ticks = struct.unpack_from("<II", data, 0)
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
    return frame_ticks, frames


def build_sprite_animation_index(extracted_root: Path | None) -> dict[str, dict[str, Any]]:
    if extracted_root is None:
        return {}
    sprite_root = extracted_root / "SPRITES" / "SPRITES"
    if not sprite_root.exists():
        return {}

    result: dict[str, dict[str, Any]] = {}
    for path in sorted(sprite_root.rglob("*.spr")):
        if not path.is_file():
            continue
        frame_ticks, frames = parse_spr_frame_paths(path)
        if not frames:
            continue
        rel = path.relative_to(sprite_root).as_posix()
        rel_no_ext = str(Path(rel).with_suffix("")).replace("\\", "/")
        entry = {
            "frame_ticks": frame_ticks,
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
        or compact_model.startswith("aibarrier")
        or compact_model.startswith("todsky")
        or compact_model.startswith("skybox")
        or compact_model == "sky"
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
    frame_ticks = int(entry.get("frame_ticks", 0) or 0)
    for frame_source in entry.get("frames", []):
        width, height, physical_path = find_texture_size(texture_sizes, str(frame_source))
        frames.append({
            "source_texture": str(frame_source),
            "width": width,
            "height": height,
            "physical_path": physical_path,
            "frame_ticks": frame_ticks,
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

    if compact_model.startswith("perceptionbrush"):
        return FaceRole(
            FACE_ATTRIBUTE_SECRET | FACE_ATTRIBUTE_INVISIBLE,
            "secret_perception",
            "hidden",
        )

    if compact_model == "visbsp":
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "visibility_helper",
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

    if compact_model == "physicsbsp":
        if explicit_invisible or invisible_texture:
            return FaceRole(FACE_ATTRIBUTE_INVISIBLE, "physics_hull", "hidden")
        return FaceRole(0, "physics_hull", "visible")

    if explicit_invisible:
        return FaceRole(FACE_ATTRIBUTE_INVISIBLE, "invisible_collision", "hidden")

    if normalized_model.startswith("bluewater") or texture_stem.startswith("water"):
        return FaceRole(
            FACE_ATTRIBUTE_INVISIBLE | FACE_ATTRIBUTE_UNTOUCHABLE,
            "water_helper",
            "hidden",
        )

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
    if not abc_model.anim_bindings:
        return (0.0, 0.0, 0.0)
    return tuple(float(value) for value in abc_model.anim_bindings[0].origin)


def abc_static_model_half_dims_lt(abc_model: AbcModel) -> tuple[float, float, float] | None:
    if not abc_model.anim_bindings:
        return None
    return tuple(max(0.0, float(value)) for value in abc_model.anim_bindings[0].extents)


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
        attributes=0,
        plane_normal=plane_normal,
        plane_distance=clamp_i32(plane_distance),
    )
    bmodel.faces.append(face)
    bmodel.source_poly_for_face.append(source_poly_index)
    bmodel.source_surface_for_face.append(-1)
    bmodel.source_surface_flags_for_face.append(0)
    bmodel.source_texture_index_for_face.append(-1)
    bmodel.source_texture_flags_for_face.append(0)
    bmodel.source_collision_role_for_face.append("baked_model_instance")
    bmodel.source_render_role_for_face.append("visible")
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
    )
    bmodel.faces.append(face)
    bmodel.source_poly_for_face.append(poly_index)
    bmodel.source_surface_for_face.append(source_surface_index)
    bmodel.source_surface_flags_for_face.append(surface.flags)
    bmodel.source_texture_index_for_face.append(source_texture_index)
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
    model_translation_lt = abc_static_model_translation_lt(abc_model)
    for piece in abc_model.pieces:
        if not piece.lods:
            continue
        skin = source_skin_for_material(source_skin, piece.material_index)
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
            )
            source_poly_index += 1

    return bmodel


def transcode_geometry(
    dat_world: DatWorld,
    scale: float,
    texture_sizes: dict[str, tuple[int, int, Path]],
    extracted_root: Path | None = None,
    preserve_source_ngons: bool = True,
) -> tuple[list[OdmBModel], dict[str, dict[str, Any]], dict[str, Any], list[BakedModelInstance]]:
    sprite_index = build_sprite_animation_index(extracted_root)
    unique_textures = sorted({
        texture
        for model in dat_world.world_models
        if not is_skipped_world_model_name(model.name)
        for texture in model.textures
        if not is_rail_helper_texture(texture)
        if not is_green_screen_helper_texture(texture)
    })
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
                    "frame_ticks": frame.get("frame_ticks", 0),
                })
            metadata["animation_frames"] = animation_frames
            metadata["animation_frame_count"] = len(animation_frames)
            metadata["animation_frame_ticks"] = int(sprite_frames[0].get("frame_ticks", 0) or 0)
        alias_metadata[aliases[texture_name]] = metadata

    bmodels: list[OdmBModel] = []
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
        "faces_non_collision_helper": 0,
        "sprite_animation_sources": sprite_animation_sources,
        "sprite_animation_frames": sprite_animation_frames,
        "skipped_helper_models": 0,
        "skipped_skybox_models": 0,
        "skipped_ai_track_models": 0,
        "skipped_ai_barrier_models": 0,
        "skipped_rail_polies": 0,
        "skipped_green_screen_polies": 0,
        "baked_model_instances": 0,
        "baked_model_faces": 0,
        "baked_model_skipped_actor_like": 0,
        "baked_model_missing_source": 0,
        "baked_model_empty": 0,
        "baked_model_destructible_props": 0,
        "baked_model_chests": 0,
        "baked_model_pickups": 0,
        "baked_model_move_to_floor_requested": 0,
        "baked_model_move_to_floor_snapped": 0,
        "baked_model_move_to_floor_already_supported": 0,
        "baked_model_move_to_floor_no_support": 0,
        "baked_model_move_to_floor_missing_dims": 0,
    }

    for model_index, model in enumerate(dat_world.world_models):
        compact_model_name = normalize_model_role_name(model.name)
        if is_skipped_world_model_name(model.name):
            stats["skipped_helper_models"] += 1
            if compact_model_name.startswith("aitrk"):
                stats["skipped_ai_track_models"] += 1
            elif compact_model_name.startswith("aibarrier"):
                stats["skipped_ai_barrier_models"] += 1
            elif (
                compact_model_name.startswith("todsky")
                or compact_model_name.startswith("skybox")
                or compact_model_name == "sky"
            ):
                stats["skipped_skybox_models"] += 1
            continue

        bmodel = OdmBModel(
            name=model.name or f"WorldModel{model_index}",
            source_model_index=model_index,
            source_model_name=model.name,
            source_world_translation_lt=model.world_translation,
            source_world_info_flags=model.counts.get("world_info_flags", 0),
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

            texture_alias = aliases[texture_name]
            texture_width = alias_metadata[texture_alias]["width"]
            texture_height = alias_metadata[texture_alias]["height"]
            face_role = classify_face_role(bmodel.name, texture_name, surface.flags)
            source_uvs = [
                opq_to_pixel_uv(model.points[index], surface.uv_origin, surface.uv_u, surface.uv_v, texture_width, texture_height)
                for index in source_indices
            ]

            source_faces: list[tuple[list[int], list[tuple[int, int]]]]
            if preserve_source_ngons and len(source_indices) <= MAX_BMODEL_FACE_VERTICES:
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
                    texture_alias,
                    list(alias_metadata.keys()).index(texture_alias),
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
        model_index = build_case_insensitive_file_index(extracted_root / "MODELS" / "MODELS", ".abc")
        abc_cache: dict[Path, AbcModel] = {}
        floor_triangles = build_floor_support_triangles(dat_world)

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

            bake_position = position
            if truthy_property(properties.get("movetofloor"), False):
                stats["baked_model_move_to_floor_requested"] += 1
                half_dims = abc_static_model_half_dims_lt(abc_model)
                if half_dims is not None:
                    half_dims = (
                        half_dims[0] * float(uniform_scale),
                        half_dims[1] * float(uniform_scale),
                        half_dims[2] * float(uniform_scale),
                    )
                bake_position, floor_status = move_position_to_floor_lt(position, half_dims, floor_triangles)
                if floor_status == "snapped":
                    stats["baked_model_move_to_floor_snapped"] += 1
                elif floor_status == "already_supported":
                    stats["baked_model_move_to_floor_already_supported"] += 1
                elif floor_status == "no_support":
                    stats["baked_model_move_to_floor_no_support"] += 1
                elif floor_status == "missing_dims":
                    stats["baked_model_move_to_floor_missing_dims"] += 1

            source_model_index = len(dat_world.world_models) + len(baked_model_instances)
            bmodel = bake_abc_model_instance(
                abc_model,
                object_index,
                source_class,
                source_name,
                normalized_source_model,
                source_skin,
                bake_position,
                rotation,
                float(uniform_scale),
                scale,
                texture_sizes,
                aliases_by_source,
                alias_metadata,
                used_aliases,
                source_model_index,
            )
            if not bmodel.faces:
                stats["baked_model_empty"] += 1
                continue

            bmodels.append(bmodel)
            bmodel_index = len(bmodels) - 1
            kind = baked_model_kind(source_class, normalized_source_model)
            destructible = kind == "destructible_prop"
            baked_model_instances.append(BakedModelInstance(
                source_object_index=object_index,
                source_class=source_class,
                source_name=source_name,
                source_model=normalized_source_model,
                source_skin=source_skin,
                bmodel_index=bmodel_index,
                bmodel_name=bmodel.name,
                kind=kind,
                destructible=destructible,
            ))
            stats["baked_model_instances"] += 1
            stats["baked_model_faces"] += len(bmodel.faces)
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


def build_odm_bytes(name: str, bmodels: list[OdmBModel]) -> bytes:
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
            write_u16_at(face_bytes, 0x128, 0)
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

    append_i32(data, 0)
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
    return source_class.lower() in {"light", "dirlight", "objectlight"}


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
        default_light_objects = source_class_lower in {"light", "dirlight"}
        default_fast_light_objects = source_class_lower in {"light", "dirlight", "objectlight"}
        light_objects = truthy_property(properties.get("lightobjects"), default_light_objects)
        fast_light_objects = truthy_property(properties.get("fastlightobjects"), default_fast_light_objects)
        static_object_light_eligible = light_objects and not fast_light_objects
        if static_object_light_eligible:
            stats["light_static_object_eligible"] += 1

        color_property_name = "innercolor" if source_class_lower == "dirlight" else "lightcolor"
        color = color_tuple_property(properties.get(color_property_name), (255, 255, 255))
        brightness_scale = float_property(properties.get("brightscale"), 1.0)
        object_brightness_scale = float_property(properties.get("objectbrightscale"), 1.0)
        effective_color = scaled_color(color, brightness_scale * object_brightness_scale)
        radius_lt = max(0.0, float_property(properties.get("lightradius"), 300.0))
        radius = max(0, int(round(radius_lt * scale)))
        light_group = properties.get("lightgroup", "")
        if not isinstance(light_group, str):
            light_group = ""

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
            light_type="directional" if source_class_lower == "dirlight" else "point",
            light_objects=light_objects,
            fast_light_objects=fast_light_objects,
            static_object_light_eligible=static_object_light_eligible,
            light_group=light_group,
        ))
    return lights, stats


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
            f"    light_objects: {yaml_scalar(light.light_objects)}",
            f"    fast_light_objects: {yaml_scalar(light.fast_light_objects)}",
            f"    static_object_light_eligible: {yaml_scalar(light.static_object_light_eligible)}",
        ])
        if light.light_group:
            lines.append(f"    light_group: {yaml_scalar(light.light_group)}")
    return lines


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
        ])
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


def append_optional_bool_line(lines: list[str], key: str, value: Any) -> None:
    if isinstance(value, bool):
        lines.append(f"      {key}: {yaml_scalar(value)}")
    elif isinstance(value, int):
        lines.append(f"      {key}: {yaml_scalar(value != 0)}")


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
        has_linear = (
            mechanism_kind in {"linear_door", "weighted_lift"}
            and isinstance(values.get("MoveDir"), list)
            and len(values.get("MoveDir")) >= 3
            and "MoveDist" in values
        )
        has_rotation = (
            mechanism_kind in {"rotating_door", "rotating_brush"}
            and isinstance(values.get("RotationPoint"), list)
            and isinstance(values.get("RotationAngles"), list)
        )

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

    return lines, stats


def build_outdoor_mechanism_interactive_face_lines(
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
) -> tuple[list[str], dict[str, int]]:
    lines: list[str] = []
    stats = {
        "mechanism_event_faces": 0,
        "mechanism_event_face_mechanisms": 0,
        "mechanism_event_face_unbound": 0,
    }
    seen_faces: set[tuple[int, int]] = set()

    for object_index, world_object in enumerate(dat_world.objects):
        mechanism_kind = MM9_MECHANISM_CLASS_KINDS.get(world_object.name)
        if mechanism_kind not in MM9_INTERACTIVE_MECHANISM_KINDS:
            continue

        event_id = mechanism_event_id(object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue

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

    return lines, stats


def write_scene_yml(
    path: Path,
    odm_name: str,
    source_metadata_name: str,
    model_instance_lines: list[str],
    mechanism_lines: list[str],
    interactive_face_lines: list[str],
    light_lines: list[str],
    party_start_point_lines: list[str],
    baked_model_instance_lines: list[str] | None = None,
) -> None:
    zeros_map = ", ".join(["0"] * 75)
    zeros_decor = ", ".join(["0"] * 125)
    model_instances = "\n".join(model_instance_lines) if model_instance_lines else "  []"
    mechanisms = "\n".join(mechanism_lines) if mechanism_lines else "  []"
    interactive_faces = "\n".join(interactive_face_lines) if interactive_face_lines else "    []"
    lights = "\n".join(light_lines) if light_lines else "  []"
    party_start_points = "\n".join(party_start_point_lines) if party_start_point_lines else "  []"
    baked_model_instances = (
        "\n".join(baked_model_instance_lines)
        if baked_model_instance_lines
        else "  []"
    )
    path.write_text(
        f"""format_version: 1
kind: "outdoor_scene"
source:
  geometry_file: "{odm_name}"
  source_metadata_file: "{source_metadata_name}"
runtime_restrictions:
  allow_save_game: false
  allow_lloyds_beacon: false
  arena: false
environment:
  sky_texture: ""
  ground_tileset_name: "planset"
  master_tile: 0
  tile_set_lookup_indices: [0, 0, 0, 0]
  day_bits_raw: 0
  map_extra_bits_raw: 8
  flags:
    foggy: false
    raining: false
    snowing: false
    underwater: false
    no_terrain: true
    always_dark: false
    always_light: false
    always_foggy: false
    red_fog: false
  fog:
    weak_distance: 8192
    strong_distance: 16384
  weather:
    fog_mode: "static"
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
        strong_distance: 16384
  ceiling: 32767
terrain:
  attribute_overrides: []
  footstep_sound_overrides: []
bmodel_faces:
  interactive_faces:
{interactive_faces}
mechanisms:
{mechanisms}
baked_model_instances:
{baked_model_instances}
entities: []
lights:
{lights}
spawns: []
party_start_points:
{party_start_points}
model_instances:
{model_instances}
initial_state:
  location:
    respawn_count: 0
    last_respawn_day: 0
    reputation: 0
    alert_status: 0
  face_attribute_overrides: []
  actors: []
  sprite_objects: []
  chests: []
  variables:
    map: [{zeros_map}]
    decor: [{zeros_decor}]
""",
        encoding="utf-8",
    )


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
            lines.append(f"    animation_frame_ticks: {int(metadata.get('animation_frame_ticks', 0) or 0)}")
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
                lines.append(f"        frame_ticks: {int(frame.get('frame_ticks', 0) or 0)}")
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
        "--bitmap-dir",
        type=Path,
        help="Optional shared directory for emitted BMP aliases; defaults to a map-local .bitmaps directory",
    )
    args = parser.parse_args()

    output_name = args.name or args.dat.stem.lower()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dat_world = read_dat_world(args.dat)
    texture_sizes = build_texture_size_index(args.extracted_root)
    bmodels, alias_metadata, stats, baked_instances = transcode_geometry(
        dat_world,
        args.scale,
        texture_sizes,
        args.extracted_root,
    )
    model_instance_lines: list[str] = []
    model_assets: list[dict[str, Any]] = []
    baked_model_instance_lines = build_baked_model_instance_lines(baked_instances)
    mechanism_lines, mechanism_stats = build_mechanism_lines(dat_world, bmodels, args.scale)
    interactive_face_lines, interactive_face_stats = build_outdoor_mechanism_interactive_face_lines(dat_world, bmodels)
    lights, light_stats = export_mm9_lights(dat_world, args.scale)
    light_lines = build_mm9_light_lines(lights)
    party_start_points, party_start_stats = export_mm9_party_start_points(dat_world, args.scale)
    party_start_point_lines = build_mm9_party_start_point_lines(party_start_points)
    stats["model_instances"] = 0
    stats["unique_model_assets"] = 0
    stats.update(mechanism_stats)
    stats.update(interactive_face_stats)
    stats.update(light_stats)
    stats.update(party_start_stats)

    odm_path = args.output_dir / f"{output_name}.odm"
    scene_path = args.output_dir / f"{output_name}.scene.yml"
    source_metadata_path = args.output_dir / f"{output_name}.mm9.yml"
    aliases_path = args.output_dir / f"{output_name}.material_aliases.yml"
    model_assets_path = args.output_dir / f"{output_name}.model_assets.yml"
    raw_objects_path = args.output_dir / f"{output_name}.raw_objects.yml"
    default_bitmap_directory_name = f"{output_name}.bitmaps"
    bitmap_dir = args.bitmap_dir or (args.output_dir / default_bitmap_directory_name)
    bitmap_directory_name = os.path.relpath(bitmap_dir, args.output_dir).replace("\\", "/")

    odm_path.write_bytes(build_odm_bytes(output_name, bmodels))
    bitmap_modes = write_alias_bitmaps(bitmap_dir, alias_metadata)
    write_scene_yml(
        scene_path,
        odm_path.name,
        source_metadata_path.name,
        model_instance_lines,
        mechanism_lines,
        interactive_face_lines,
        light_lines,
        party_start_point_lines,
        baked_model_instance_lines,
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
