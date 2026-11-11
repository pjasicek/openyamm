"""Where a held item sits against the hand, from the GLBs alone (node and animation maths, as the engine composes them).

python3 socket_check.py <creature.glb> <Socket_node> <item.glb> [--clips A,B] [--samples 5] [--hand "Bip01 R Hand"]

For each clip and sample time, as fractions of the skeleton's height (H): the socket's distance from the hand node
(default: the socket's parent), the item's nearest point to it (a held item: about 0.05-0.13 H; DWARFAXE before its
fix: 0.6 H) and the item's size.
"""
import argparse
import json
import struct

import numpy as np


def read_glb(path):
    data = open(path, "rb").read()
    length = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + length])
    offset = 20 + length
    binary = b""
    if offset < len(data):
        chunk_length = struct.unpack_from("<I", data, offset)[0]
        binary = data[offset + 8:offset + 8 + chunk_length]
    return doc, binary


COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
DTYPES = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}


def accessor(doc, binary, index):
    acc = doc["accessors"][index]
    view = doc["bufferViews"][acc["bufferView"]]
    count = acc["count"]
    width = COMPONENTS[acc["type"]]
    dtype = DTYPES[acc["componentType"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", 0)
    item = np.dtype(dtype).itemsize * width
    if stride and stride != item:
        rows = [np.frombuffer(binary, dtype, width, start + i * stride) for i in range(count)]
        return np.array(rows)
    return np.frombuffer(binary, dtype, count * width, start).reshape(count, width)


def quat_matrix(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def trs(t, r, s):
    m = np.eye(4)
    m[:3, :3] = quat_matrix(r) * np.array(s)
    m[:3, 3] = t
    return m


def node_local(node, override=None):
    if "matrix" in node:
        return np.array(node["matrix"]).reshape(4, 4).T
    values = {"translation": node.get("translation", [0, 0, 0]), "rotation": node.get("rotation", [0, 0, 0, 1]),
              "scale": node.get("scale", [1, 1, 1])}
    if override:
        values.update(override)
    return trs(values["translation"], values["rotation"], values["scale"])


def sample(doc, binary, animation, t):
    poses = {}
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        times = accessor(doc, binary, sampler["input"])[:, 0]
        values = accessor(doc, binary, sampler["output"]).astype(float)
        path = channel["target"]["path"]
        if path == "weights":
            continue
        i = int(np.searchsorted(times, t, side="right") - 1)
        i = max(0, min(i, len(times) - 1))
        if i + 1 < len(times) and times[i + 1] > times[i]:
            f = (t - times[i]) / (times[i + 1] - times[i])
            a, b = values[i], values[i + 1]
            if path == "rotation":
                if np.dot(a, b) < 0:
                    b = -b
                v = a * (1 - f) + b * f
                v = v / np.linalg.norm(v)
            else:
                v = a * (1 - f) + b * f
        else:
            v = values[i]
        poses.setdefault(channel["target"]["node"], {})[path] = list(v)
    return poses


def world_matrices(doc, poses):
    parents = {}
    for i, node in enumerate(doc["nodes"]):
        for child in node.get("children", []):
            parents[child] = i
    cache = {}

    def world(i):
        if i not in cache:
            local = node_local(doc["nodes"][i], poses.get(i))
            cache[i] = world(parents[i]) @ local if i in parents else local
        return cache[i]

    return world, parents


def item_points(path, steps: int = 8):
    """Points over the item's triangles (a barycentric grid of `steps` per edge): a long handle has vertices only at
    its ends, so its vertices alone would miss the hand."""
    doc, binary = read_glb(path)
    world, _ = world_matrices(doc, {})
    grid = np.array([(a, b) for a in range(steps + 1) for b in range(steps + 1 - a)], dtype=float) / steps
    points = []
    for i, node in enumerate(doc["nodes"]):
        if "mesh" not in node:
            continue
        for primitive in doc["meshes"][node["mesh"]]["primitives"]:
            p = accessor(doc, binary, primitive["attributes"]["POSITION"]).astype(float)
            m = world(i)
            p = p @ m[:3, :3].T + m[:3, 3]
            if "indices" in primitive:
                triangles = accessor(doc, binary, primitive["indices"]).astype(int).reshape(-1, 3)
            else:
                triangles = np.arange(len(p)).reshape(-1, 3)
            a, b, c = p[triangles[:, 0]], p[triangles[:, 1]], p[triangles[:, 2]]
            samples = (a[:, None] + grid[None, :, :1] * (b - a)[:, None] + grid[None, :, 1:] * (c - a)[:, None])
            points.append(samples.reshape(-1, 3))
    return np.concatenate(points)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("socket")
    parser.add_argument("item")
    parser.add_argument("--clips", default="")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--hand", default="")
    args = parser.parse_args()
    doc, binary = read_glb(args.model)
    names = {n.get("name"): i for i, n in enumerate(doc["nodes"])}
    socket = names[args.socket]
    item = item_points(args.item)
    _, parents = world_matrices(doc, {})
    hand = names[args.hand] if args.hand else parents[socket]
    print(f"socket {args.socket} on {doc['nodes'][parents[socket]]['name']}; hand {doc['nodes'][hand]['name']}")
    print("item extent (item units):", np.round(item.max(0) - item.min(0), 4))
    animations = {a["name"]: a for a in doc.get("animations", [])}
    clips = [c for c in args.clips.split(",") if c] or list(animations)
    for clip in clips:
        animation = animations[clip]
        end = max(accessor(doc, binary, s["input"])[:, 0].max() for s in animation["samplers"])
        for k in range(args.samples):
            t = end * k / max(1, args.samples - 1)
            world, _ = world_matrices(doc, sample(doc, binary, animation, t))
            joints = doc["skins"][0]["joints"]
            joint_positions = np.array([world(j)[:3, 3] for j in joints])
            height = joint_positions[:, 1].max() - joint_positions[:, 1].min()
            m = world(socket)
            placed = item @ m[:3, :3].T + m[:3, 3]
            hand_pos = world(hand)[:3, 3]
            grip = np.linalg.norm(placed - hand_pos, axis=1).min()
            print(f"{clip:12s} t={t:5.2f} socket-hand {np.linalg.norm(m[:3, 3] - hand_pos) / height:6.3f}H"
                  f"  item-nearest-to-hand {grip / height:6.3f}H  item size {np.ptp(placed, 0).max() / height:5.2f}H"
                  f"  hand y {(hand_pos[1] - joint_positions[:, 1].min()) / height:5.2f}H")


if __name__ == "__main__":
    main()
