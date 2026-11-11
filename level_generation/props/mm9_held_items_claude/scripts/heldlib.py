"""Shared helpers of the MM9 held items project: GLB reading and writing, ABC and GLB poses, and the frame of our
MM9 creature models against their ABC (MM9's skeleton mirrored on x at about 1/40, fitted per model)."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
import convert_abc_model as abc  # noqa: E402

MODELS = ROOT / "mm9/extracted/MODELS/MODELS"
SKINS = ROOT / "mm9/extracted/SKINS/SKINS"
# Our creature models are MM9's skeleton mirrored on x (true handedness, mirror_glb.py) at about this scale; each
# model's own scale is fitted (frame_fit), and an item exported at this one is scaled to it by its socket node.
ITEM_SCALE = 1.0 / 40.0
MIRROR = np.diag([-1.0, 1.0, 1.0])

COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
DTYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}


def abc_file(name: str) -> Path:
    files = {path.relative_to(MODELS).as_posix().lower(): path for path in MODELS.rglob("*.abc")}
    return files[name.lower()]


def read_glb(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    json_length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + json_length])
    offset = 20 + json_length
    blob = b""
    if offset < len(raw):
        blob_length = struct.unpack_from("<I", raw, offset)[0]
        blob = raw[offset + 8:offset + 8 + blob_length]
    return document, blob


def write_glb(path: Path, document: dict, blob: bytes) -> None:
    encoded = json.dumps(document, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    blob += b"\0" * (-len(blob) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(encoded), 0x4E4F534A)
                     + encoded + struct.pack("<II", len(blob), 0x004E4942) + blob)


def accessor(document: dict, blob: bytes, index: int) -> np.ndarray:
    item = document["accessors"][index]
    view = document["bufferViews"][item["bufferView"]]
    count, width = item["count"], COMPONENTS[item["type"]]
    dtype = np.dtype(DTYPES[item["componentType"]])
    start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    stride = view.get("byteStride", 0) or dtype.itemsize * width
    rows = [np.frombuffer(blob, dtype, width, start + row * stride) for row in range(count)]
    return np.array(rows, dtype=np.float64).reshape(count, width)


def quat_matrix(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def matrix_quat(m: np.ndarray) -> list[float]:
    return list(abc.quaternion_from_matrix(np.block([[m, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]])))


def trs(translation, rotation, scale) -> np.ndarray:
    matrix = np.eye(4)
    matrix[:3, :3] = quat_matrix(rotation) * np.array(scale)
    matrix[:3, 3] = translation
    return matrix


def glb_parents(document: dict) -> list[int | None]:
    parents: list[int | None] = [None] * len(document["nodes"])
    for index, node in enumerate(document["nodes"]):
        for child in node.get("children", []):
            parents[child] = index
    return parents


def glb_clip(document: dict, name: str) -> dict:
    for animation in document.get("animations", []):
        if animation.get("name") == name:
            return animation
    raise KeyError(f"no clip {name}")


def glb_clip_seconds(document: dict, blob: bytes, clip: dict) -> float:
    return max(float(accessor(document, blob, sampler["input"]).max()) for sampler in clip["samplers"])


def sample(times: np.ndarray, values: np.ndarray, at: float, rotation: bool) -> np.ndarray:
    return abc.sample_values(times.reshape(-1), values, at, rotation)


def glb_pose(document: dict, blob: bytes, clip: dict | None, at: float) -> list[np.ndarray]:
    """World matrices of every node at a time of the clip (its rest pose without one)."""
    local = []
    for node in document["nodes"]:
        local.append([list(node.get("translation", [0, 0, 0])), list(node.get("rotation", [0, 0, 0, 1])),
                      list(node.get("scale", [1, 1, 1]))])
    for channel in (clip or {}).get("channels", []):
        sampler = clip["samplers"][channel["sampler"]]
        times = accessor(document, blob, sampler["input"])
        values = accessor(document, blob, sampler["output"])
        path = channel["target"]["path"]
        slot = {"translation": 0, "rotation": 1, "scale": 2}[path]
        local[channel["target"]["node"]][slot] = list(sample(times, values, at, path == "rotation"))
    parents = glb_parents(document)
    world: list[np.ndarray | None] = [None] * len(local)

    def evaluate(index: int) -> np.ndarray:
        if world[index] is None:
            matrix = trs(*local[index])
            world[index] = matrix if parents[index] is None else evaluate(parents[index]) @ matrix
        return world[index]

    return [evaluate(index) for index in range(len(local))]


def abc_pose(model, animation, at: float) -> list[np.ndarray]:
    """World matrices of the ABC's nodes at a time of one of its animations (its bind pose without one)."""
    if animation is None:
        return [np.array(node.bind_matrix, dtype=np.float64) for node in model.nodes]
    pose = abc.source_animation_pose(model, animation, at)
    parents = [node.parent_index for node in model.nodes]
    return [np.array(matrix, dtype=np.float64) for matrix in abc.global_pose_matrices(pose, parents)]


def abc_animation(model, name: str):
    for animation in model.animations:
        if animation.name.lower() == name.lower():
            return animation
    raise KeyError(f"{model.name}: no animation {name}")


def rotation_of(matrix: np.ndarray) -> np.ndarray:
    rotation = matrix[:3, :3].copy()
    return rotation / np.linalg.norm(rotation, axis=0)


def frame_scale(document: dict, model) -> float:
    """Our model's scale against its ABC: our rest pose's bones fitted to theirs in MM9's bind pose."""
    ours = {node.get("name"): matrix[:3, 3] for node, matrix in zip(document["nodes"], glb_pose(document, b"", None, 0))}
    theirs = {node.name: np.array(node.bind_matrix)[:3, 3] for node in model.nodes}
    common = [name for name in theirs if name in ours and name.startswith("Bip01")]
    a = np.array([theirs[name] for name in common])
    b = np.array([ours[name] for name in common])
    a -= a.mean(0)
    b -= b.mean(0)
    # The best rigid fit's scale (Procrustes): steadier than the spreads' ratio where the poses differ.
    singular = np.linalg.svd(b.T @ a, compute_uv=False)
    return float(singular.sum() / (a ** 2).sum())
