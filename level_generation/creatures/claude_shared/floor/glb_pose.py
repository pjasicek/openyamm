"""Pose evaluation of an installed or exported creature GLB, without Blender: node hierarchy, LINEAR/STEP animation
samplers, linear-blend skinning and the lowest visible point of a pose, plus appending accessors and writing the GLB.

Coordinates are the GLB's own: glTF +Y is up and the actor's floor is y = 0 (the engine maps glTF +Y to world +Z and
puts model-space 0 on the actor's floor, game/fx/WorldFxSystem.cpp). Hidden parts (nodes or bones scaled to zero, so
their triangles collapse) are left out of the lowest point, as are the coarser LOD meshes (names with LOD1..LOD3).
"""
import json
from pathlib import Path
import re
import struct

import numpy as np

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
COMPONENTS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NORMALIZED_DIVISORS = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
# A triangle whose doubled area (model units squared) is below this is collapsed: a part hidden by a zero or tiny scale
# (the centaur's parked arrow is 0.9 mm long, its triangles about 3e-9).
COLLAPSED_AREA = 1e-8


class Glb:
    def __init__(self, path):
        data = Path(path).read_bytes()
        magic, version, length = struct.unpack_from("<III", data, 0)
        if magic != GLB_MAGIC or version != 2 or length != len(data):
            raise ValueError(f"{path}: not a glTF 2.0 binary")
        offset, self.json, self.bin = 12, None, b""
        while offset < length:
            size, kind = struct.unpack_from("<II", data, offset)
            chunk = data[offset + 8:offset + 8 + size]
            if kind == CHUNK_JSON:
                self.json = json.loads(chunk)
            elif kind == CHUNK_BIN:
                self.bin = bytearray(chunk)
            offset += 8 + size
        if not isinstance(self.bin, bytearray):
            self.bin = bytearray(self.bin)

    def accessor(self, index):
        """Accessor data as float32 (count, width); normalized integers are scaled to [0, 1] or [-1, 1]."""
        accessor = self.json["accessors"][index]
        if "sparse" in accessor:
            raise ValueError("sparse accessors are not supported")
        dtype = np.dtype(COMPONENTS[accessor["componentType"]])
        width = WIDTHS[accessor["type"]]
        count = accessor["count"]
        view = self.json["bufferViews"][accessor["bufferView"]]
        start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 0) or dtype.itemsize * width
        raw = np.ndarray((count, width), dtype=dtype, buffer=self.bin, offset=start,
                         strides=(stride, dtype.itemsize))
        values = raw.astype(np.float32)
        if accessor.get("normalized") and accessor["componentType"] in NORMALIZED_DIVISORS:
            values = np.maximum(values / NORMALIZED_DIVISORS[accessor["componentType"]], -1.0)
        return values

    def append_accessor(self, values, kind):
        """Appends float32 values (count, width) as a new tightly packed accessor; returns its index."""
        values = np.ascontiguousarray(values, dtype=np.float32).reshape(len(values), WIDTHS[kind])
        self.bin += b"\0" * (-len(self.bin) % 4)
        views = self.json.setdefault("bufferViews", [])
        views.append({"buffer": 0, "byteOffset": len(self.bin), "byteLength": values.nbytes})
        self.bin += values.tobytes()
        accessors = self.json.setdefault("accessors", [])
        accessors.append({"bufferView": len(views) - 1, "componentType": 5126, "count": len(values), "type": kind,
                          "min": values.min(axis=0).tolist(), "max": values.max(axis=0).tolist()})
        self.json["buffers"][0]["byteLength"] = len(self.bin)
        return len(accessors) - 1

    def write(self, path):
        text = json.dumps(self.json, separators=(",", ":")).encode()
        text += b" " * (-len(text) % 4)
        binary = bytes(self.bin) + b"\0" * (-len(self.bin) % 4)
        length = 12 + 8 + len(text) + 8 + len(binary)
        Path(path).write_bytes(struct.pack("<III", GLB_MAGIC, 2, length) + struct.pack("<II", len(text), CHUNK_JSON)
                               + text + struct.pack("<II", len(binary), CHUNK_BIN) + binary)


def quaternion_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def matrix_quaternion(m):
    """Unit quaternion (x, y, z, w) of a rotation matrix."""
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0:
        s = 2.0 * np.sqrt(trace + 1.0)
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def slerp(a, b, t):
    dot = float(np.dot(a, b))
    if dot < 0.0:
        b, dot = -b, -dot
    if dot > 0.9995:
        result = a + t * (b - a)
    else:
        angle = np.arccos(dot)
        result = (np.sin((1 - t) * angle) * a + np.sin(t * angle) * b) / np.sin(angle)
    return result / np.linalg.norm(result)


def trs_matrix(translation, rotation, scale):
    matrix = np.eye(4)
    matrix[:3, :3] = quaternion_matrix(rotation) * np.asarray(scale)[None, :]
    matrix[:3, 3] = translation
    return matrix


class Model:
    """A GLB's hierarchy, clips and LOD0 meshes, posed at clip times."""

    def __init__(self, glb):
        self.glb = glb
        document = glb.json
        nodes = document["nodes"]
        self.parent = [-1] * len(nodes)
        for index, node in enumerate(nodes):
            for child in node.get("children", []):
                self.parent[child] = index
        self.order = []
        scene = document["scenes"][document.get("scene", 0)]
        stack = list(reversed(scene["nodes"]))
        while stack:
            index = stack.pop()
            self.order.append(index)
            stack.extend(reversed(nodes[index].get("children", [])))
        self.rest = []
        for node in nodes:
            if "matrix" in node:
                raise ValueError(f"node {node.get('name')} uses a matrix; only TRS nodes are supported")
            self.rest.append((np.array(node.get("translation", [0.0, 0.0, 0.0])),
                              np.array(node.get("rotation", [0.0, 0.0, 0.0, 1.0])),
                              np.array(node.get("scale", [1.0, 1.0, 1.0]))))
        self.clips = {animation.get("name", str(index)): index
                      for index, animation in enumerate(document.get("animations", []))}
        skins = document.get("skins", [])
        self.joints = skins[0]["joints"] if skins else []
        self.inverse_binds = glb.accessor(skins[0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1) \
            if skins and "inverseBindMatrices" in skins[0] else None
        joint_set = set(self.joints)
        # Joints whose parent is not a joint: moving all of them moves the whole skeleton.
        self.root_joints = [joint for joint in self.joints if self.parent[joint] not in joint_set]
        self.primitives = []
        for index in self.order:
            node = nodes[index]
            if "mesh" not in node:
                continue
            mesh = document["meshes"][node["mesh"]]
            found = re.search(r"LOD(\d)", mesh.get("name") or node.get("name") or "", re.I)
            if found and found.group(1) != "0":
                continue
            for primitive in mesh["primitives"]:
                if primitive.get("mode", 4) != 4:
                    continue
                attributes = primitive["attributes"]
                positions = glb.accessor(attributes["POSITION"]).astype(np.float64)
                triangles = glb.accessor(primitive["indices"]).astype(np.int64).reshape(-1, 3) \
                    if "indices" in primitive else np.arange(len(positions)).reshape(-1, 3)
                skinned = "skin" in node and "JOINTS_0" in attributes
                entry = {"node": index, "positions": positions, "triangles": triangles, "skinned": skinned}
                if skinned:
                    entry["joints"] = glb.accessor(attributes["JOINTS_0"]).astype(np.int64)
                    weights = glb.accessor(attributes["WEIGHTS_0"]).astype(np.float64)
                    entry["weights"] = weights / np.maximum(weights.sum(axis=1, keepdims=True), 1e-12)
                self.primitives.append(entry)

    def clip_times(self, clip):
        """Every key time of a clip, sorted."""
        animation = self.glb.json["animations"][self.clips[clip]]
        times = set()
        for sampler in animation["samplers"]:
            times.update(float(value) for value in self.glb.accessor(sampler["input"])[:, 0])
        return sorted(times)

    def sample(self, clip, time):
        """Node TRS overrides {node: [translation, rotation, scale]} of a clip at a time."""
        animation = self.glb.json["animations"][self.clips[clip]]
        local = {}
        for channel in animation["channels"]:
            path = channel["target"]["path"]
            if path == "weights":
                continue
            sampler = animation["samplers"][channel["sampler"]]
            interpolation = sampler.get("interpolation", "LINEAR")
            if interpolation not in ("LINEAR", "STEP"):
                raise ValueError(f"{clip}: {interpolation} samplers are not supported")
            inputs = self.glb.accessor(sampler["input"])[:, 0]
            outputs = self.glb.accessor(sampler["output"]).astype(np.float64)
            key = int(np.searchsorted(inputs, time, side="right")) - 1
            if key < 0:
                value = outputs[0]
            elif key >= len(inputs) - 1 or interpolation == "STEP":
                value = outputs[min(key, len(inputs) - 1)]
            else:
                fraction = (time - inputs[key]) / max(inputs[key + 1] - inputs[key], 1e-12)
                value = slerp(outputs[key], outputs[key + 1], fraction) if path == "rotation" \
                    else outputs[key] + fraction * (outputs[key + 1] - outputs[key])
            if path == "rotation":
                # Keys may be stored rounded (not unit length); the engine normalises them too.
                value = value / max(np.linalg.norm(value), 1e-12)
            node = channel["target"]["node"]
            trs = local.setdefault(node, [part.copy() for part in self.rest[node]])
            trs[{"translation": 0, "rotation": 1, "scale": 2}[path]] = np.asarray(value, dtype=np.float64)
        return local

    def world(self, local):
        """World matrices (nodes, 4, 4) of a pose from sample(); nodes the clip does not animate keep their rest TRS."""
        result = np.zeros((len(self.rest), 4, 4))
        for index in self.order:
            matrix = trs_matrix(*local.get(index, self.rest[index]))
            parent = self.parent[index]
            result[index] = matrix if parent < 0 else result[parent] @ matrix
        return result

    def skinned_positions(self, world):
        """Per LOD0 primitive: its posed vertex positions (n, 3) and its triangles."""
        palette = None
        if self.joints:
            palette = world[self.joints] @ self.inverse_binds if self.inverse_binds is not None \
                else world[self.joints]
        posed = []
        for primitive in self.primitives:
            positions = primitive["positions"]
            homogeneous = np.concatenate([positions, np.ones((len(positions), 1))], axis=1)
            if primitive["skinned"]:
                blended = np.einsum("vk,vkij->vij", primitive["weights"], palette[primitive["joints"]])
                points = np.einsum("vij,vj->vi", blended, homogeneous)[:, :3]
            else:
                points = homogeneous @ world[primitive["node"]].T
                points = points[:, :3]
            posed.append((points, primitive["triangles"]))
        return posed

    def visible_vertices(self, posed):
        """Indices of each primitive's vertices on a triangle that has not collapsed (a visible part)."""
        result = []
        for points, triangles in posed:
            a, b, c = (points[triangles[:, corner]] for corner in range(3))
            area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
            result.append(np.unique(triangles[area > COLLAPSED_AREA]))
        return result

    def lowest(self, clip, time):
        """Lowest visible point (glTF y, model units) of a clip at a time; None when nothing is visible."""
        return self._extreme(clip, time, min)

    def highest(self, clip, time):
        """Highest visible point (glTF y, model units) of a clip at a time; None when nothing is visible."""
        return self._extreme(clip, time, max)

    def _extreme(self, clip, time, pick):
        posed = self.skinned_positions(self.world(self.sample(clip, time)))
        values = [pick(points[visible, 1]) for (points, _), visible in zip(posed, self.visible_vertices(posed))
                  if len(visible)]
        return float(pick(values)) if values else None
