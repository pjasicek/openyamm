#!/usr/bin/env python3
"""MM9's held items (AttachProp models, Ercc's cup) as static GLBs for actor attachments.

Each item is MM9's own mesh with its skin x4 (plain Lanczos, the MM9 props rule), posed at the first frame of its own
animation, in the frame our creature models use: MM9's x mirrored (triangles turned to keep their front) at
heldlib.ITEM_SCALE, origin at its model origin (LithTech attaches that at the socket). A piece cut from a creature's
model (Ercc's cup) keeps its frame relative to the node it is weighted to; the socket made for it there is that node.

    python3 level_generation/props/mm9_held_items_claude/scripts/build_items.py   # writes export/*.glb
"""
from __future__ import annotations

import io
import struct
from pathlib import Path

import numpy as np
from PIL import Image

import heldlib
from heldlib import abc

PROJECT = Path(__file__).resolve().parents[1]
# name: (ABC, its skin, the piece (None: all), the node whose frame it keeps (None: the model origin))
ITEMS = {
    "mm9_item_monkhoe": ("MODELPROPS/MONKHOE.abc", "MODELPROPS/MONKHOE.dtx", None, None),
    "mm9_item_monkbroom": ("MODELPROPS/MONKBROOM.abc", "MODELPROPS/MONKBROOM.dtx", None, None),
    "mm9_item_monkcloth": ("MODELPROPS/MONKCLOTH.abc", "MODELPROPS/MONKCLOTH.dtx", None, None),
    "mm9_item_monkhammer": ("MODELPROPS/MONKHAMMER.abc", "MODELPROPS/MONKHAMMER.dtx", None, None),
    "mm9_item_dwarfaxe": ("MODELPROPS/DWARFAXE.abc", "MODELPROPS/DWARFAXE.dtx", None, None),
    "mm9_item_hammer": ("MODELPROPS/HAMMER.abc", "MODELPROPS/HAMMER.dtx", None, None),
    "mm9_item_kirasword": ("MODELPROPS/KIRASWORD.abc", "MODELPROPS/KIRASWORD.dtx", None, None),
    "mm9_item_honkpamphlet": ("MODELPROPS/HONKPAMPHLET.abc", "MODELPROPS/PAMPHLET.dtx", None, None),
    "mm9_item_erccup": ("PROPS/ERCC.abc", "PROPS/CUP1.dtx", "Cup1", "piece"),
}

# Items whose mesh lies away from its origin: DWARFAXE.abc's pick is modelled about 23 MM9 units to the side of its
# origin (in both its animations), so attached at the origin it floats a pick's length off the miner's fist. Moved
# across so its handle runs through the origin like every other item's (the height along the handle is kept).
GRIP_ON_HANDLE = {"mm9_item_dwarfaxe"}


def handle_on_origin(positions: np.ndarray) -> np.ndarray:
    """The item moved across (x, z) so the lower third of its handle (along y) centres on the origin."""
    y = positions[:, 1]
    lower = positions[y < y.min() + (y.max() - y.min()) / 3.0]
    offset = np.array([lower[:, 0].mean(), 0.0, lower[:, 2].mean()])
    return positions - offset


def piece_node(model, piece) -> int:
    """The node a rigid piece is weighted to (the heaviest)."""
    totals: dict[int, float] = {}
    for vertex in piece.lods[0].vertices:
        for weight in vertex.weights:
            totals[weight.node_index] = totals.get(weight.node_index, 0.0) + weight.bias
    return max(totals, key=totals.get)


def item_mesh(abc_name: str, piece_name: str | None, frame: str | None):
    """Positions, normals, uvs and triangles in our frame; the node name the frame belongs to (None: model origin)."""
    model = abc.read_abc(heldlib.abc_file(abc_name))
    animation = model.animations[0] if model.animations else None
    bind = heldlib.abc_pose(model, None, 0.0)
    pose = heldlib.abc_pose(model, animation, 0.0) if frame is None else bind
    pieces = [piece for piece in model.pieces if piece_name is None or piece.name == piece_name]
    origin = np.eye(4)
    frame_node = None
    if frame == "piece":
        index = piece_node(model, pieces[0])
        origin = np.linalg.inv(bind[index])
        frame_node = model.nodes[index].name
    positions, normals, uvs = [], [], []
    for piece in pieces:
        lod = piece.lods[0]
        for face in lod.faces:
            # Mirrored on x: the triangle's corners in reverse keep its front outward.
            for corner in reversed(face.vertices):
                vertex = lod.vertices[corner.vertex_index]
                point = np.array([*vertex.position, 1.0])
                normal = np.array(vertex.normal, dtype=np.float64)
                matrix = np.zeros((4, 4))
                for weight in vertex.weights:
                    matrix += weight.bias * (pose[weight.node_index] @ np.linalg.inv(bind[weight.node_index]))
                if not vertex.weights:
                    matrix = np.eye(4)
                matrix = origin @ matrix
                point = matrix @ point
                normal = heldlib.rotation_of(matrix) @ normal
                positions.append(heldlib.ITEM_SCALE * (heldlib.MIRROR @ point[:3]))
                normals.append(heldlib.MIRROR @ (normal / max(np.linalg.norm(normal), 1e-9)))
                uvs.append(corner.uv)
    return np.array(positions), np.array(normals), np.array(uvs), frame_node


def skin_png(dtx: str) -> tuple[bytes, bool]:
    image = abc.decode_dtx(heldlib.SKINS / dtx).convert("RGBA")
    image = image.resize((image.width * 4, image.height * 4), Image.LANCZOS)
    cutout = bool(np.asarray(image)[:, :, 3].min() < 128)
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue(), cutout


def write_item(name: str, positions, normals, uvs, png: bytes, cutout: bool) -> None:
    blob = bytearray()
    views, accessors = [], []

    def add(data: np.ndarray, kind: str, target: int | None, component: int = 5126) -> int:
        while len(blob) % 4:
            blob.append(0)
        raw = data.astype(np.float32 if component == 5126 else np.uint32).tobytes()
        view = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(raw)}
        if target is not None:
            view["target"] = target
        views.append(view)
        blob.extend(raw)
        item = {"bufferView": len(views) - 1, "componentType": component, "count": len(data), "type": kind}
        if kind == "VEC3" and component == 5126:
            item["min"] = data.min(0).tolist()
            item["max"] = data.max(0).tolist()
        accessors.append(item)
        return len(accessors) - 1

    position = add(positions, "VEC3", 34962)
    normal = add(normals, "VEC3", 34962)
    uv = add(uvs, "VEC2", 34962)
    indices = add(np.arange(len(positions)), "SCALAR", 34963, 5125)
    while len(blob) % 4:
        blob.append(0)
    views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(png)})
    blob.extend(png)
    material = {"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0,
                                                      "roughnessFactor": 0.8}}
    if cutout:
        material.update({"alphaMode": "MASK", "alphaCutoff": 0.5, "doubleSided": True})
    document = {
        "asset": {"version": "2.0", "generator": "mm9_held_items_claude/build_items.py"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0}],
        "meshes": [{"name": name, "primitives": [{"attributes": {"POSITION": position, "NORMAL": normal,
                                                                 "TEXCOORD_0": uv},
                                                  "indices": indices, "material": 0}]}],
        "materials": [material],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "images": [{"bufferView": len(views) - 1, "mimeType": "image/png"}],
        "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": len(blob)}],
    }
    heldlib.write_glb(PROJECT / "export" / f"{name}.glb", document, bytes(blob))


def main() -> int:
    for name, (abc_name, dtx, piece, frame) in ITEMS.items():
        positions, normals, uvs, frame_node = item_mesh(abc_name, piece, frame)
        if name in GRIP_ON_HANDLE:
            positions = handle_on_origin(positions)
        png, cutout = skin_png(dtx)
        write_item(name, positions, normals, uvs, png, cutout)
        size = positions.max(0) - positions.min(0)
        print(f"{name}: {len(positions) // 3} triangles, size {np.round(size, 3).tolist()}, cut-out {cutout}"
              + (f", frame of {frame_node}" if frame_node else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
