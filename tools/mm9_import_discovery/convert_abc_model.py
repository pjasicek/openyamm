#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import shutil
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml
from PIL import Image as PillowImage
from pygltflib import (
    ARRAY_BUFFER,
    ELEMENT_ARRAY_BUFFER,
    FLOAT,
    LINEAR,
    REPEAT,
    UNSIGNED_INT,
    UNSIGNED_SHORT,
    Accessor,
    Animation,
    AnimationChannel,
    AnimationChannelTarget,
    AnimationSampler,
    Asset,
    Buffer,
    BufferView,
    GLTF2,
    Image,
    Material,
    Mesh,
    Node,
    PbrMetallicRoughness,
    Primitive,
    Sampler,
    Scene,
    Skin,
    Texture,
)

from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


DTX_RESOURCE_TYPE = 0
DTX_BPP_8P = 0
DTX_BPP_32 = 3
DTX_BPP_DXT1 = 4
DTX_BPP_DXT3 = 5
DTX_BPP_DXT5 = 6
GL_TRIANGLES = 4


@dataclass
class Weight:
    node_index: int
    bias: float


@dataclass
class Vertex:
    position: tuple[float, float, float]
    normal: tuple[float, float, float]
    weights: list[Weight]


@dataclass
class FaceVertex:
    uv: tuple[float, float]
    vertex_index: int


@dataclass
class Face:
    vertices: list[FaceVertex]


@dataclass
class Lod:
    faces: list[Face]
    vertices: list[Vertex]


@dataclass
class Piece:
    name: str
    material_index: int
    specular_power: float
    specular_scale: float
    lod_weight: float
    lods: list[Lod]


@dataclass
class NodeInfo:
    name: str
    index: int
    flags: int
    child_count: int
    bind_matrix: np.ndarray
    parent_index: int | None = None
    children: list[int] = field(default_factory=list)


@dataclass
class Keyframe:
    time_ms: int
    event: str


@dataclass
class Transform:
    translation: tuple[float, float, float]
    rotation: tuple[float, float, float, float]


@dataclass
class ModelAnimation:
    name: str
    interpolation_time_ms: int
    keyframes: list[Keyframe]
    node_transforms: list[list[Transform]]


@dataclass
class SocketInfo:
    name: str
    node_index: int
    rotation: tuple[float, float, float, float]
    translation: tuple[float, float, float]


@dataclass
class AnimBinding:
    name: str
    extents: tuple[float, float, float]
    origin: tuple[float, float, float]


@dataclass
class AbcModel:
    name: str
    version: int
    command_string: str
    internal_radius: float
    lod_distances: list[float]
    pieces: list[Piece]
    nodes: list[NodeInfo]
    animations: list[ModelAnimation]
    sockets: list[SocketInfo]
    anim_bindings: list[AnimBinding]


@dataclass
class TextureInput:
    material_index: int
    source: Path
    texture_id: str


@dataclass
class MaterialOutput:
    material_index: int
    texture_id: str
    texture_path: Path
    texture_uri: str
    model_texture_path: str
    runtime_texture_path: str
    preview_texture_path: str
    source_texture: Path
    has_transparency: bool = False


class BinaryReader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def seek(self, offset: int) -> None:
        self.offset = offset

    def read_struct(self, fmt: str):
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, self.data, self.offset)
        self.offset += size
        return value

    def read_u16(self) -> int:
        return self.read_struct("<H")[0]

    def read_i32(self) -> int:
        return self.read_struct("<i")[0]

    def read_u32(self) -> int:
        return self.read_struct("<I")[0]

    def read_i8(self) -> int:
        return self.read_struct("<b")[0]

    def read_f32(self) -> float:
        return self.read_struct("<f")[0]

    def read_vec3(self) -> tuple[float, float, float]:
        return self.read_struct("<3f")

    def read_quat(self) -> tuple[float, float, float, float]:
        return self.read_struct("<4f")

    def read_string(self) -> str:
        length = self.read_u16()
        raw = self.data[self.offset : self.offset + length]
        self.offset += length
        return raw.decode("ascii", errors="replace").rstrip("\x00")

    def skip(self, size: int) -> None:
        self.offset += size


def read_sections(reader: BinaryReader) -> dict[str, int]:
    sections: dict[str, int] = {}
    next_offset = 0
    while next_offset != -1:
        reader.seek(next_offset)
        section_name = reader.read_string()
        next_offset = reader.read_i32()
        sections[section_name] = reader.offset
    return sections


def build_node_hierarchy(nodes: list[NodeInfo]) -> None:
    def visit(index: int, parent_index: int | None) -> int:
        nodes[index].parent_index = parent_index
        next_index = index + 1
        for _ in range(nodes[index].child_count):
            child_index = next_index
            nodes[index].children.append(child_index)
            next_index = visit(child_index, index)
        return next_index

    if nodes:
        visit(0, None)


def read_weight(reader: BinaryReader) -> Weight:
    node_index = reader.read_u32()
    reader.skip(12)
    return Weight(node_index=node_index, bias=reader.read_f32())


def read_vertex(reader: BinaryReader) -> Vertex:
    weight_count = reader.read_u16()
    reader.skip(2)
    weights = [read_weight(reader) for _ in range(weight_count)]
    position = reader.read_vec3()
    normal = reader.read_vec3()
    return Vertex(position=position, normal=normal, weights=weights)


def read_face(reader: BinaryReader) -> Face:
    vertices = []
    for _ in range(3):
        uv = reader.read_struct("<2f")
        vertex_index = reader.read_u16()
        vertices.append(FaceVertex(uv=uv, vertex_index=vertex_index))
    return Face(vertices=vertices)


def read_lod(reader: BinaryReader) -> Lod:
    face_count = reader.read_u32()
    faces = [read_face(reader) for _ in range(face_count)]
    vertex_count = reader.read_u32()
    vertices = [read_vertex(reader) for _ in range(vertex_count)]
    return Lod(faces=faces, vertices=vertices)


def read_piece(reader: BinaryReader, version: int, lod_count: int) -> Piece:
    material_index = reader.read_u16()
    specular_power = reader.read_f32()
    specular_scale = reader.read_f32()
    lod_weight = reader.read_f32() if version > 9 else 1.0
    reader.skip(2)
    name = reader.read_string()
    lods = [read_lod(reader) for _ in range(lod_count)]
    return Piece(
        name=name,
        material_index=material_index,
        specular_power=specular_power,
        specular_scale=specular_scale,
        lod_weight=lod_weight,
        lods=lods,
    )


def read_node(reader: BinaryReader) -> NodeInfo:
    name = reader.read_string()
    index = reader.read_u16()
    flags = reader.read_i8()
    matrix_values = reader.read_struct("<16f")
    bind_matrix = np.array(matrix_values, dtype=np.float32).reshape((4, 4))
    child_count = reader.read_u32()
    return NodeInfo(name=name, index=index, flags=flags, child_count=child_count, bind_matrix=bind_matrix)


def read_animation(reader: BinaryReader, version: int, node_count: int) -> ModelAnimation:
    reader.skip(12)
    name = reader.read_string()
    reader.skip(4)
    interpolation_time_ms = reader.read_u32() if version >= 12 else 200
    keyframe_count = reader.read_u32()
    keyframes = []
    for _ in range(keyframe_count):
        keyframes.append(Keyframe(time_ms=reader.read_u32(), event=reader.read_string()))

    node_transforms = []
    for _ in range(node_count):
        if version == 13:
            reader.skip(4)
        transforms = []
        for _ in range(keyframe_count):
            translation = reader.read_vec3()
            rotation = reader.read_quat()
            if version == 13:
                reader.skip(8)
            transforms.append(Transform(translation=translation, rotation=rotation))
        node_transforms.append(transforms)

    return ModelAnimation(
        name=name,
        interpolation_time_ms=interpolation_time_ms,
        keyframes=keyframes,
        node_transforms=node_transforms,
    )


def read_socket(reader: BinaryReader) -> SocketInfo:
    node_index = reader.read_u32()
    name = reader.read_string()
    rotation = reader.read_quat()
    translation = reader.read_vec3()
    return SocketInfo(name=name, node_index=node_index, rotation=rotation, translation=translation)


def read_anim_binding(reader: BinaryReader) -> AnimBinding:
    name = reader.read_string()
    extents = reader.read_vec3()
    origin = reader.read_vec3()
    return AnimBinding(name=name, extents=extents, origin=origin)


def read_abc(path: Path) -> AbcModel:
    data = path.read_bytes()
    reader = BinaryReader(data)
    sections = read_sections(reader)

    reader.seek(sections["Header"])
    version = reader.read_u32()
    if version not in (9, 10, 11, 12, 13):
        raise ValueError(f"{path} has unsupported ABC version {version}")

    reader.skip(8)
    node_count = reader.read_u32()
    reader.skip(20)
    lod_count = reader.read_u32()
    reader.skip(4)
    reader.skip(4)
    reader.skip(8)
    if version >= 13:
        reader.skip(4)
    command_string = reader.read_string()
    internal_radius = reader.read_f32()
    reader.skip(64)
    lod_distances = [reader.read_f32() for _ in range(lod_count)]

    reader.seek(sections["Pieces"])
    reader.skip(4)
    piece_count = reader.read_u32()
    pieces = [read_piece(reader, version, lod_count) for _ in range(piece_count)]

    nodes: list[NodeInfo] = []
    animations: list[ModelAnimation] = []
    sockets: list[SocketInfo] = []
    anim_bindings: list[AnimBinding] = []

    if "Nodes" in sections:
        reader.seek(sections["Nodes"])
        nodes = [read_node(reader) for _ in range(node_count)]
        build_node_hierarchy(nodes)

    if "Animation" in sections:
        reader.seek(sections["Animation"])
        animation_count = reader.read_u32()
        animations = [read_animation(reader, version, node_count) for _ in range(animation_count)]

    if "Sockets" in sections:
        reader.seek(sections["Sockets"])
        socket_count = reader.read_u32()
        sockets = [read_socket(reader) for _ in range(socket_count)]

    if "AnimBindings" in sections:
        reader.seek(sections["AnimBindings"])
        binding_count = reader.read_u32()
        anim_bindings = [read_anim_binding(reader) for _ in range(binding_count)]

    return AbcModel(
        name=path.stem,
        version=version,
        command_string=command_string,
        internal_radius=internal_radius,
        lod_distances=lod_distances,
        pieces=pieces,
        nodes=nodes,
        animations=animations,
        sockets=sockets,
        anim_bindings=anim_bindings,
    )


def rgb565_to_rgb(value: int) -> tuple[int, int, int]:
    red = (value >> 11) & 0x1f
    green = (value >> 5) & 0x3f
    blue = value & 0x1f
    return (
        (red << 3) | (red >> 2),
        (green << 2) | (green >> 4),
        (blue << 3) | (blue >> 2),
    )


def dxt_color_table(color0: int, color1: int, allow_transparent: bool) -> list[tuple[int, int, int, int]]:
    red0, green0, blue0 = rgb565_to_rgb(color0)
    red1, green1, blue1 = rgb565_to_rgb(color1)
    colors = [
        (red0, green0, blue0, 255),
        (red1, green1, blue1, 255),
    ]
    if color0 > color1 or not allow_transparent:
        colors.append(((2 * red0 + red1) // 3, (2 * green0 + green1) // 3, (2 * blue0 + blue1) // 3, 255))
        colors.append(((red0 + 2 * red1) // 3, (green0 + 2 * green1) // 3, (blue0 + 2 * blue1) // 3, 255))
    else:
        colors.append(((red0 + red1) // 2, (green0 + green1) // 2, (blue0 + blue1) // 2, 255))
        colors.append((0, 0, 0, 0))
    return colors


def decode_dxt1(data: bytes, offset: int, width: int, height: int) -> np.ndarray:
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    cursor = offset
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    for block_y in range(blocks_y):
        for block_x in range(blocks_x):
            color0, color1, codes = struct.unpack_from("<HHI", data, cursor)
            cursor += 8
            colors = dxt_color_table(color0, color1, True)
            for y in range(4):
                for x in range(4):
                    px = block_x * 4 + x
                    py = block_y * 4 + y
                    if px >= width or py >= height:
                        continue
                    index = (codes >> (2 * (4 * y + x))) & 0x03
                    pixels[py, px] = colors[index]
    return pixels


def decode_dxt3(data: bytes, offset: int, width: int, height: int) -> np.ndarray:
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    cursor = offset
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    for block_y in range(blocks_y):
        for block_x in range(blocks_x):
            alpha_bytes = data[cursor : cursor + 8]
            cursor += 8
            color0, color1, codes = struct.unpack_from("<HHI", data, cursor)
            cursor += 8
            colors = dxt_color_table(color0, color1, False)
            for y in range(4):
                for x in range(4):
                    px = block_x * 4 + x
                    py = block_y * 4 + y
                    if px >= width or py >= height:
                        continue
                    color_index = (codes >> (2 * (4 * y + x))) & 0x03
                    alpha_byte = alpha_bytes[(4 * y + x) // 2]
                    alpha_nibble = (alpha_byte >> 4) if (x % 2) else (alpha_byte & 0x0f)
                    red, green, blue, _alpha = colors[color_index]
                    pixels[py, px] = (red, green, blue, (alpha_nibble << 4) | alpha_nibble)
    return pixels


def decode_dxt5(data: bytes, offset: int, width: int, height: int) -> np.ndarray:
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    cursor = offset
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    for block_y in range(blocks_y):
        for block_x in range(blocks_x):
            alpha0 = data[cursor]
            alpha1 = data[cursor + 1]
            alpha_bits = int.from_bytes(data[cursor + 2 : cursor + 8], "little")
            cursor += 8
            alpha_table = [alpha0, alpha1]
            if alpha0 > alpha1:
                alpha_table.extend(
                    [
                        (6 * alpha0 + alpha1) // 7,
                        (5 * alpha0 + 2 * alpha1) // 7,
                        (4 * alpha0 + 3 * alpha1) // 7,
                        (3 * alpha0 + 4 * alpha1) // 7,
                        (2 * alpha0 + 5 * alpha1) // 7,
                        (alpha0 + 6 * alpha1) // 7,
                    ]
                )
            else:
                alpha_table.extend(
                    [
                        (4 * alpha0 + alpha1) // 5,
                        (3 * alpha0 + 2 * alpha1) // 5,
                        (2 * alpha0 + 3 * alpha1) // 5,
                        (alpha0 + 4 * alpha1) // 5,
                        0,
                        255,
                    ]
                )

            color0, color1, codes = struct.unpack_from("<HHI", data, cursor)
            cursor += 8
            colors = dxt_color_table(color0, color1, False)
            for y in range(4):
                for x in range(4):
                    px = block_x * 4 + x
                    py = block_y * 4 + y
                    if px >= width or py >= height:
                        continue
                    pixel_index = 4 * y + x
                    color_index = (codes >> (2 * pixel_index)) & 0x03
                    alpha_index = (alpha_bits >> (3 * pixel_index)) & 0x07
                    red, green, blue, _alpha = colors[color_index]
                    pixels[py, px] = (red, green, blue, alpha_table[alpha_index])
    return pixels


def decode_dtx(path: Path) -> PillowImage.Image:
    data = path.read_bytes()
    resource_type = struct.unpack_from("<I", data, 0)[0]
    if resource_type != DTX_RESOURCE_TYPE:
        raise ValueError(f"{path} is not a resource-wrapped DTX texture")

    version, height, width = struct.unpack_from("<iHH", data, 4)
    if version != -5:
        raise ValueError(f"{path} has unsupported DTX version {version}")

    bpp_identifier = struct.unpack_from("<12B", data, 24)[2]
    pixel_offset = 36 + 128

    if bpp_identifier in (DTX_BPP_8P, DTX_BPP_32):
        pixel_count = width * height
        pixel_bytes = data[pixel_offset : pixel_offset + pixel_count * 4]
        if len(pixel_bytes) != pixel_count * 4:
            raise ValueError(f"{path} is truncated: expected {pixel_count * 4} pixel bytes")
        bgra = np.frombuffer(pixel_bytes, dtype=np.uint8).reshape((height, width, 4)).copy()
        rgba = bgra[:, :, [2, 1, 0, 3]]
        if bpp_identifier == DTX_BPP_8P or (bpp_identifier == DTX_BPP_32 and not np.any(rgba[:, :, 3])):
            rgba[:, :, 3] = 255
    elif bpp_identifier == DTX_BPP_DXT1:
        rgba = decode_dxt1(data, pixel_offset, width, height)
    elif bpp_identifier == DTX_BPP_DXT3:
        rgba = decode_dxt3(data, pixel_offset, width, height)
    elif bpp_identifier == DTX_BPP_DXT5:
        rgba = decode_dxt5(data, pixel_offset, width, height)
    else:
        raise ValueError(f"{path} has unsupported DTX bpp {bpp_identifier}")
    return PillowImage.fromarray(rgba, "RGBA")


def decode_dtx_v5_bpp32(path: Path) -> PillowImage.Image:
    return decode_dtx(path)


def image_has_transparency(image: PillowImage.Image) -> bool:
    rgba = image if image.mode == "RGBA" else image.convert("RGBA")
    alpha_min, _alpha_max = rgba.getchannel("A").getextrema()
    return alpha_min < 255


def align_blob(blob: bytearray, alignment: int = 4) -> None:
    while len(blob) % alignment != 0:
        blob.append(0)


class GltfBuilder:
    def __init__(self):
        self.gltf = GLTF2(asset=Asset(version="2.0", generator="OpenYAMM MM9 ABC converter"))
        self.gltf.scenes = [Scene(nodes=[])]
        self.gltf.scene = 0
        self.gltf.nodes = []
        self.gltf.meshes = []
        self.gltf.materials = []
        self.gltf.textures = []
        self.gltf.images = []
        self.gltf.samplers = []
        self.gltf.skins = []
        self.gltf.animations = []
        self.gltf.accessors = []
        self.gltf.bufferViews = []
        self.gltf.buffers = []
        self.blob = bytearray()

    def add_accessor(
        self,
        values: np.ndarray,
        component_type: int,
        accessor_type: str,
        target: int | None = None,
        include_min_max: bool = True,
    ) -> int:
        if np.issubdtype(values.dtype, np.floating):
            values = np.nan_to_num(values, nan=0.0, posinf=1.0e30, neginf=-1.0e30)

        align_blob(self.blob)
        byte_offset = len(self.blob)
        raw = values.tobytes()
        self.blob.extend(raw)
        buffer_view_index = len(self.gltf.bufferViews)
        self.gltf.bufferViews.append(
            BufferView(buffer=0, byteOffset=byte_offset, byteLength=len(raw), target=target)
        )

        accessor = Accessor(
            bufferView=buffer_view_index,
            byteOffset=0,
            componentType=component_type,
            count=len(values),
            type=accessor_type,
        )
        if include_min_max and len(values) > 0:
            if accessor_type == "SCALAR":
                accessor.min = [float(values.min())]
                accessor.max = [float(values.max())]
            else:
                flattened = values.reshape((len(values), -1))
                accessor.min = [float(value) for value in flattened.min(axis=0)]
                accessor.max = [float(value) for value in flattened.max(axis=0)]

        accessor_index = len(self.gltf.accessors)
        self.gltf.accessors.append(accessor)
        return accessor_index


def normalized_joint_weight_data(weights: list[Weight]) -> tuple[list[int], list[float]]:
    ordered = sorted(weights, key=lambda value: abs(value.bias), reverse=True)[:4]
    joints = [weight.node_index for weight in ordered]
    biases = [max(0.0, weight.bias) for weight in ordered]
    while len(joints) < 4:
        joints.append(0)
        biases.append(0.0)

    total = sum(biases)
    if total <= 0.0:
        biases = [1.0, 0.0, 0.0, 0.0]
    else:
        biases = [bias / total for bias in biases]
    return joints, biases


def mesh_arrays_for_piece(piece: Piece, lod_index: int) -> dict[str, np.ndarray]:
    lod = piece.lods[lod_index]
    positions = []
    normals = []
    texcoords = []
    joints = []
    weights = []
    indices = []

    for face in lod.faces:
        for face_vertex in face.vertices:
            source_vertex = lod.vertices[face_vertex.vertex_index]
            positions.append(source_vertex.position)
            normals.append(source_vertex.normal)
            texcoords.append(face_vertex.uv)
            joint_values, weight_values = normalized_joint_weight_data(source_vertex.weights)
            joints.append(joint_values)
            weights.append(weight_values)
            indices.append(len(indices))

    return {
        "positions": np.array(positions, dtype=np.float32),
        "normals": np.array(normals, dtype=np.float32),
        "texcoords": np.array(texcoords, dtype=np.float32),
        "joints": np.array(joints, dtype=np.uint16),
        "weights": np.array(weights, dtype=np.float32),
        "indices": np.array(indices, dtype=np.uint32),
    }


def matrix_from_transform(transform: Transform) -> np.ndarray:
    x, y, z, w = transform.rotation
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 0] = 1.0 - 2.0 * (yy + zz)
    matrix[0, 1] = 2.0 * (xy - wz)
    matrix[0, 2] = 2.0 * (xz + wy)
    matrix[1, 0] = 2.0 * (xy + wz)
    matrix[1, 1] = 1.0 - 2.0 * (xx + zz)
    matrix[1, 2] = 2.0 * (yz - wx)
    matrix[2, 0] = 2.0 * (xz - wy)
    matrix[2, 1] = 2.0 * (yz + wx)
    matrix[2, 2] = 1.0 - 2.0 * (xx + yy)
    matrix[:3, 3] = np.array(transform.translation, dtype=np.float32)
    return matrix


def global_bind_matrices(model: AbcModel) -> list[np.ndarray]:
    return [node.bind_matrix for node in model.nodes]


def quaternion_from_matrix(matrix: np.ndarray) -> tuple[float, float, float, float]:
    trace = float(matrix[0, 0] + matrix[1, 1] + matrix[2, 2])
    if trace > 0.0:
        value = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * value
        x = (matrix[2, 1] - matrix[1, 2]) / value
        y = (matrix[0, 2] - matrix[2, 0]) / value
        z = (matrix[1, 0] - matrix[0, 1]) / value
    elif matrix[0, 0] > matrix[1, 1] and matrix[0, 0] > matrix[2, 2]:
        value = math.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) * 2.0
        w = (matrix[2, 1] - matrix[1, 2]) / value
        x = 0.25 * value
        y = (matrix[0, 1] + matrix[1, 0]) / value
        z = (matrix[0, 2] + matrix[2, 0]) / value
    elif matrix[1, 1] > matrix[2, 2]:
        value = math.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) * 2.0
        w = (matrix[0, 2] - matrix[2, 0]) / value
        x = (matrix[0, 1] + matrix[1, 0]) / value
        y = 0.25 * value
        z = (matrix[1, 2] + matrix[2, 1]) / value
    else:
        value = math.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) * 2.0
        w = (matrix[1, 0] - matrix[0, 1]) / value
        x = (matrix[0, 2] + matrix[2, 0]) / value
        y = (matrix[1, 2] + matrix[2, 1]) / value
        z = 0.25 * value

    length = math.sqrt(x * x + y * y + z * z + w * w)
    if length <= 0.0:
        return (0.0, 0.0, 0.0, 1.0)
    return (float(x / length), float(y / length), float(z / length), float(w / length))


def transform_from_matrix(matrix: np.ndarray) -> Transform:
    translation = tuple(float(value) for value in matrix[:3, 3])
    rotation_matrix = matrix[:3, :3].astype(np.float32).copy()
    for column in range(3):
        scale = np.linalg.norm(rotation_matrix[:, column])
        if scale > 0.0:
            rotation_matrix[:, column] /= scale
    return Transform(translation=translation, rotation=quaternion_from_matrix(rotation_matrix))


def bind_local_transform(model: AbcModel, node_index: int) -> Transform:
    node = model.nodes[node_index]
    if node.parent_index is None:
        local_matrix = node.bind_matrix
    else:
        parent_inverse = np.linalg.inv(model.nodes[node.parent_index].bind_matrix)
        local_matrix = parent_inverse @ node.bind_matrix
    return transform_from_matrix(local_matrix)


def matrix_to_gltf_values(matrix: np.ndarray) -> list[float]:
    return [float(value) for value in matrix.T.reshape(16)]


def scaled_vec3(value: tuple[float, float, float], scale: float) -> tuple[float, float, float]:
    return (value[0] * scale, value[1] * scale, value[2] * scale)


def scale_abc_model(model: AbcModel, scale: float) -> None:
    if scale == 1.0:
        return

    model.internal_radius *= scale
    model.lod_distances = [distance * scale for distance in model.lod_distances]

    for piece in model.pieces:
        for lod in piece.lods:
            for vertex in lod.vertices:
                vertex.position = scaled_vec3(vertex.position, scale)

    for node in model.nodes:
        node.bind_matrix[:3, 3] *= scale

    for animation in model.animations:
        for transforms in animation.node_transforms:
            for transform in transforms:
                transform.translation = scaled_vec3(transform.translation, scale)

    for socket in model.sockets:
        socket.translation = scaled_vec3(socket.translation, scale)

    for binding in model.anim_bindings:
        binding.extents = scaled_vec3(binding.extents, scale)
        binding.origin = scaled_vec3(binding.origin, scale)


def initial_node_transform(model: AbcModel, node_index: int) -> Transform:
    return bind_local_transform(model, node_index)


def add_material(
    builder: GltfBuilder,
    material_name: str,
    texture_uri: str | None,
    alpha_cutout: bool = False,
) -> int:
    material = Material(name=material_name)
    material.pbrMetallicRoughness = PbrMetallicRoughness(baseColorFactor=[1.0, 1.0, 1.0, 1.0])
    material.pbrMetallicRoughness.metallicFactor = 0.0
    material.pbrMetallicRoughness.roughnessFactor = 0.8
    if alpha_cutout:
        material.alphaMode = "MASK"
        material.alphaCutoff = 0.5
        material.doubleSided = True

    if texture_uri is not None:
        sampler_index = len(builder.gltf.samplers)
        builder.gltf.samplers.append(Sampler(magFilter=LINEAR, minFilter=LINEAR, wrapS=REPEAT, wrapT=REPEAT))
        image_index = len(builder.gltf.images)
        builder.gltf.images.append(Image(uri=texture_uri))
        texture_index = len(builder.gltf.textures)
        builder.gltf.textures.append(Texture(sampler=sampler_index, source=image_index))
        material.pbrMetallicRoughness.baseColorTexture = {"index": texture_index}

    material_index = len(builder.gltf.materials)
    builder.gltf.materials.append(material)
    return material_index


def add_gltf_nodes(builder: GltfBuilder, model: AbcModel) -> list[int]:
    node_indices = []
    for index, node in enumerate(model.nodes):
        transform = initial_node_transform(model, index)
        gltf_node = Node(
            name=node.name,
            translation=[float(value) for value in transform.translation],
            rotation=[float(value) for value in transform.rotation],
            children=[],
        )
        node_indices.append(len(builder.gltf.nodes))
        builder.gltf.nodes.append(gltf_node)

    for index, node in enumerate(model.nodes):
        builder.gltf.nodes[node_indices[index]].children = [node_indices[child] for child in node.children]

    if node_indices:
        builder.gltf.scenes[0].nodes.append(node_indices[0])
    return node_indices


def add_skin(builder: GltfBuilder, model: AbcModel, node_indices: list[int]) -> int | None:
    if not node_indices:
        return None

    bind_matrices = global_bind_matrices(model)
    inverse_bind_matrices = np.array([np.linalg.inv(matrix).T.reshape(16) for matrix in bind_matrices], dtype=np.float32)
    accessor = builder.add_accessor(inverse_bind_matrices, FLOAT, "MAT4", include_min_max=False)
    skin_index = len(builder.gltf.skins)
    builder.gltf.skins.append(Skin(inverseBindMatrices=accessor, joints=node_indices, skeleton=node_indices[0]))
    return skin_index


def add_meshes(
    builder: GltfBuilder,
    model: AbcModel,
    material_indices: dict[int, int],
    skin_index: int | None,
    lod_index: int,
) -> None:
    for piece in model.pieces:
        if not piece.lods:
            continue

        arrays = mesh_arrays_for_piece(piece, lod_index)
        if len(arrays["positions"]) == 0:
            continue

        position_accessor = builder.add_accessor(arrays["positions"], FLOAT, "VEC3", ARRAY_BUFFER)
        normal_accessor = builder.add_accessor(arrays["normals"], FLOAT, "VEC3", ARRAY_BUFFER)
        texcoord_accessor = builder.add_accessor(arrays["texcoords"], FLOAT, "VEC2", ARRAY_BUFFER)
        joints_accessor = builder.add_accessor(arrays["joints"], UNSIGNED_SHORT, "VEC4", ARRAY_BUFFER)
        weights_accessor = builder.add_accessor(arrays["weights"], FLOAT, "VEC4", ARRAY_BUFFER)
        index_accessor = builder.add_accessor(arrays["indices"], UNSIGNED_INT, "SCALAR", ELEMENT_ARRAY_BUFFER)

        primitive = Primitive(
            attributes={
                "POSITION": position_accessor,
                "NORMAL": normal_accessor,
                "TEXCOORD_0": texcoord_accessor,
                "JOINTS_0": joints_accessor,
                "WEIGHTS_0": weights_accessor,
            },
            indices=index_accessor,
            material=material_indices.get(piece.material_index, material_indices[0]),
            mode=GL_TRIANGLES,
        )
        mesh_index = len(builder.gltf.meshes)
        builder.gltf.meshes.append(Mesh(name=piece.name, primitives=[primitive]))

        mesh_node = Node(name=f"{piece.name}.mesh", mesh=mesh_index, skin=skin_index)
        mesh_node_index = len(builder.gltf.nodes)
        builder.gltf.nodes.append(mesh_node)
        builder.gltf.scenes[0].nodes.append(mesh_node_index)


def add_animations(builder: GltfBuilder, model: AbcModel, node_indices: list[int]) -> None:
    for animation in model.animations:
        gltf_animation = Animation(name=animation.name, samplers=[], channels=[])
        times = np.array([key.time_ms / 1000.0 for key in animation.keyframes], dtype=np.float32)
        time_accessor = builder.add_accessor(times, FLOAT, "SCALAR")

        for node_index, transforms in enumerate(animation.node_transforms):
            translations = np.array([transform.translation for transform in transforms], dtype=np.float32)
            rotations = np.array([transform.rotation for transform in transforms], dtype=np.float32)

            translation_accessor = builder.add_accessor(translations, FLOAT, "VEC3")
            translation_sampler = len(gltf_animation.samplers)
            gltf_animation.samplers.append(
                AnimationSampler(input=time_accessor, output=translation_accessor, interpolation="LINEAR")
            )
            gltf_animation.channels.append(
                AnimationChannel(
                    sampler=translation_sampler,
                    target=AnimationChannelTarget(node=node_indices[node_index], path="translation"),
                )
            )

            rotation_accessor = builder.add_accessor(rotations, FLOAT, "VEC4", include_min_max=False)
            rotation_sampler = len(gltf_animation.samplers)
            gltf_animation.samplers.append(
                AnimationSampler(input=time_accessor, output=rotation_accessor, interpolation="LINEAR")
            )
            gltf_animation.channels.append(
                AnimationChannel(
                    sampler=rotation_sampler,
                    target=AnimationChannelTarget(node=node_indices[node_index], path="rotation"),
                )
            )

        builder.gltf.animations.append(gltf_animation)


def write_glb(model: AbcModel, output_path: Path, texture_uri: str | None, lod_index: int) -> None:
    builder = GltfBuilder()
    material_index = add_material(builder, model.name, texture_uri)
    node_indices = add_gltf_nodes(builder, model)
    skin_index = add_skin(builder, model, node_indices)
    add_meshes(builder, model, {0: material_index}, skin_index, lod_index)
    add_animations(builder, model, node_indices)

    align_blob(builder.blob)
    builder.gltf.buffers = [Buffer(byteLength=len(builder.blob))]
    builder.gltf.set_binary_blob(bytes(builder.blob))
    builder.gltf.save_binary(str(output_path))


def write_glb_with_materials(
    model: AbcModel,
    output_path: Path,
    material_texture_uris: dict[int, str | None],
    material_alpha_cutouts: dict[int, bool],
    lod_index: int,
) -> None:
    builder = GltfBuilder()
    used_material_indices = sorted({piece.material_index for piece in model.pieces})
    if 0 not in used_material_indices:
        used_material_indices.insert(0, 0)

    gltf_material_indices = {}
    for material_index in used_material_indices:
        texture_uri = material_texture_uris.get(material_index)
        gltf_material_indices[material_index] = add_material(
            builder,
            f"{model.name}.{material_index}",
            texture_uri,
            material_alpha_cutouts.get(material_index, False),
        )

    node_indices = add_gltf_nodes(builder, model)
    skin_index = add_skin(builder, model, node_indices)
    add_meshes(builder, model, gltf_material_indices, skin_index, lod_index)
    add_animations(builder, model, node_indices)

    align_blob(builder.blob)
    builder.gltf.buffers = [Buffer(byteLength=len(builder.blob))]
    builder.gltf.set_binary_blob(bytes(builder.blob))
    builder.gltf.save_binary(str(output_path))


def sidecar_animation(animation: ModelAnimation) -> dict:
    events = []
    for keyframe in animation.keyframes:
        if keyframe.event:
            events.append({"timeMs": keyframe.time_ms, "event": keyframe.event})
    return {
        "name": animation.name,
        "durationMs": animation.keyframes[-1].time_ms if animation.keyframes else 0,
        "keyframes": len(animation.keyframes),
        "interpolationTimeMs": animation.interpolation_time_ms,
        "events": events,
    }


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def write_sidecars(
    model: AbcModel,
    model_path: Path,
    source_model: Path,
    material_outputs: list[MaterialOutput],
    lod_index: int,
    coordinate_scale: float,
) -> None:
    model_sidecar = {
        "schema": "openyamm.model3d.v1",
        "id": model_path.stem,
        "model": model_path.name,
        "source": {
            "format": "LithTech ABC",
            "version": model.version,
            "path": str(source_model),
            "commandString": model.command_string,
            "internalRadius": model.internal_radius,
            "coordinateScale": coordinate_scale,
            "coordinateTransform": "LithTech ABC local axes preserved; scene placement converts Y-up to OpenYAMM Z-up",
            "uvConvention": "LithTech ABC UVs preserved",
        },
        "lod": {
            "exportedIndex": lod_index,
            "distances": model.lod_distances,
        },
        "pieces": [
            {
                "name": piece.name,
                "materialIndex": piece.material_index,
                "lods": [
                    {"faces": len(lod.faces), "vertices": len(lod.vertices)}
                    for lod in piece.lods
                ],
            }
            for piece in model.pieces
        ],
        "materials": [
            {
                "index": output.material_index,
                "texture": output.model_texture_path,
                "runtime_texture": output.runtime_texture_path,
                "preview_texture": output.preview_texture_path,
                "source": str(output.source_texture),
                **(
                    {
                        "alphaMode": "MASK",
                        "alphaCutoff": 0.5,
                        "doubleSided": True,
                    }
                    if output.has_transparency
                    else {}
                ),
            }
            for output in material_outputs
        ],
        "skeleton": {
            "nodes": [
                {
                    "index": index,
                    "name": node.name,
                    "parent": node.parent_index,
                    "flags": node.flags,
                    "children": node.children,
                }
                for index, node in enumerate(model.nodes)
            ],
        },
        "sockets": [
            {
                "name": socket.name,
                "node": socket.node_index,
                "translation": list(socket.translation),
                "rotation": list(socket.rotation),
            }
            for socket in model.sockets
        ],
        "animations": [sidecar_animation(animation) for animation in model.animations],
        "animationBindings": [
            {
                "name": binding.name,
                "extents": list(binding.extents),
                "origin": list(binding.origin),
            }
            for binding in model.anim_bindings
        ],
    }
    write_yaml(model_path.with_suffix(".model.yml"), model_sidecar)

    import_dir = model_path.parent / "import"
    import_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(
        import_dir / "source.yml",
        {
            "model": str(source_model),
            "textures": [
                {
                    "materialIndex": output.material_index,
                    "source": str(output.source_texture),
                    "runtimeTexture": output.runtime_texture_path,
                    "previewTexture": output.preview_texture_path,
                    **({"hasTransparency": True} if output.has_transparency else {}),
                }
                for output in material_outputs
            ],
            "converter": "tools/mm9_import_discovery/convert_abc_model.py",
            "coordinateScale": coordinate_scale,
            "coordinateTransform": "LithTech ABC local axes preserved; scene placement converts Y-up to OpenYAMM Z-up",
        },
    )
    write_yaml(
        import_dir / "report.yml",
        {
            "abcVersion": model.version,
            "pieces": len(model.pieces),
            "nodes": len(model.nodes),
            "animations": len(model.animations),
            "sockets": len(model.sockets),
            "exportedLod": lod_index,
            "coordinateScale": coordinate_scale,
            "coordinateTransform": "LithTech ABC local axes preserved; scene placement converts Y-up to OpenYAMM Z-up",
            "warnings": [],
        },
    )


def convert_model(
    source_model: Path,
    output_dir: Path,
    model_id: str,
    textures: list[TextureInput],
    lod_index: int,
    shared_skins_dir: Path | None = None,
    preview_skins_dir: Path | None = None,
    source_skins_root: Path | None = None,
    coordinate_scale: float = MM9_TO_OPENYAMM_COORDINATE_SCALE,
) -> None:
    model = read_abc(source_model)
    scale_abc_model(model, coordinate_scale)
    if lod_index < 0 or any(lod_index >= len(piece.lods) for piece in model.pieces if piece.lods):
        raise ValueError(f"LOD index {lod_index} is not present in every non-empty piece")

    output_dir.mkdir(parents=True, exist_ok=True)
    material_outputs = []
    material_texture_uris = {}
    material_alpha_cutouts = {}
    for texture in textures:
        if shared_skins_dir is None:
            skins_dir = output_dir / "skins"
            runtime_texture_path = skins_dir / f"{texture.texture_id}.dtx"
            preview_texture_path = skins_dir / f"{texture.texture_id}.png"
            model_runtime_texture_path = f"skins/{runtime_texture_path.name}"
            model_preview_texture_path = f"skins/{preview_texture_path.name}"
        else:
            runtime_texture_path = shared_skin_path(
                texture.source,
                shared_skins_dir,
                source_skins_root,
                texture.texture_id,
                ".dtx",
            )
            world_root = shared_skins_dir.parent
            model_runtime_texture_path = runtime_texture_path.relative_to(world_root).as_posix()
            if preview_skins_dir is None:
                preview_skins_dir = world_root / "skins_preview"
            preview_texture_path = shared_skin_path(
                texture.source,
                preview_skins_dir,
                source_skins_root,
                texture.texture_id,
                ".png",
            )
            model_preview_texture_path = preview_texture_path.relative_to(world_root).as_posix()

        runtime_texture_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(texture.source, runtime_texture_path)
        preview_texture_path.parent.mkdir(parents=True, exist_ok=True)
        image = decode_dtx(texture.source)
        has_transparency = image_has_transparency(image)
        image.save(preview_texture_path)

        texture_uri = Path(os.path.relpath(preview_texture_path, output_dir)).as_posix()
        material_texture_uris[texture.material_index] = texture_uri
        material_alpha_cutouts[texture.material_index] = has_transparency
        material_outputs.append(
            MaterialOutput(
                material_index=texture.material_index,
                texture_id=texture.texture_id,
                texture_path=preview_texture_path,
                texture_uri=texture_uri,
                model_texture_path=model_preview_texture_path,
                runtime_texture_path=model_runtime_texture_path,
                preview_texture_path=model_preview_texture_path,
                source_texture=texture.source,
                has_transparency=has_transparency,
            )
        )

    model_path = output_dir / f"{model_id}.glb"
    write_glb_with_materials(model, model_path, material_texture_uris, material_alpha_cutouts, lod_index)
    write_sidecars(model, model_path, source_model, material_outputs, lod_index, coordinate_scale)


def parse_indexed_value(raw: str, default_index: int) -> tuple[int, str]:
    if "=" not in raw:
        return default_index, raw
    index, value = raw.split("=", 1)
    return int(index), value


def shared_skin_path(
    source: Path,
    output_skins_root: Path,
    source_skins_root: Path | None,
    texture_id: str,
    suffix: str,
) -> Path:
    if source_skins_root is not None:
        try:
            relative = source.resolve().relative_to(source_skins_root.resolve())
            return output_skins_root / Path(*[part.lower() for part in relative.with_suffix(suffix).parts])
        except ValueError:
            pass
    return output_skins_root / f"{texture_id}{suffix}"


def parse_texture_inputs(
    texture_args: list[str] | None,
    texture_id_args: list[str] | None,
    model_id: str,
) -> list[TextureInput]:
    texture_args = texture_args or []
    texture_id_args = texture_id_args or []
    ids = {}
    for sequential_index, raw in enumerate(texture_id_args):
        material_index, value = parse_indexed_value(raw, sequential_index)
        ids[material_index] = value

    textures = []
    for sequential_index, raw in enumerate(texture_args):
        material_index, value = parse_indexed_value(raw, sequential_index)
        texture_id = ids.get(material_index)
        if texture_id is None:
            suffix = "" if material_index == 0 else str(material_index)
            texture_id = f"{model_id}{suffix}"
        textures.append(TextureInput(material_index=material_index, source=Path(value), texture_id=texture_id))
    return textures


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert an MM9 LithTech ABC model to GLB and OpenYAMM sidecars.")
    parser.add_argument("source_model", type=Path, help="Input .abc model")
    parser.add_argument("output_dir", type=Path, help="Output model folder")
    parser.add_argument("--id", required=True, help="Output model id and file stem")
    parser.add_argument(
        "--texture",
        action="append",
        help="Optional source .dtx texture. Use INDEX=PATH to bind a texture to an ABC material index.",
    )
    parser.add_argument(
        "--texture-id",
        action="append",
        help="Optional output texture id. Use INDEX=ID when --texture uses material indices.",
    )
    parser.add_argument("--lod", type=int, default=0, help="LOD index to export")
    parser.add_argument(
        "--scale",
        type=float,
        default=MM9_TO_OPENYAMM_COORDINATE_SCALE,
        help="Coordinate scale from LithTech units to OpenYAMM units",
    )
    parser.add_argument(
        "--shared-skins-dir",
        type=Path,
        help="Optional world-level runtime DTX skins directory.",
    )
    parser.add_argument(
        "--preview-skins-dir",
        type=Path,
        help="Optional world-level PNG preview skins directory. Defaults to sibling skins_preview.",
    )
    parser.add_argument(
        "--source-skins-root",
        type=Path,
        default=Path("mm9/extracted/SKINS/SKINS"),
        help="Source DTX root used to preserve relative skin paths under --shared-skins-dir.",
    )
    args = parser.parse_args()

    convert_model(
        source_model=args.source_model,
        output_dir=args.output_dir,
        model_id=args.id,
        textures=parse_texture_inputs(args.texture, args.texture_id, args.id),
        lod_index=args.lod,
        shared_skins_dir=args.shared_skins_dir,
        preview_skins_dir=args.preview_skins_dir,
        source_skins_root=args.source_skins_root,
        coordinate_scale=args.scale,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
