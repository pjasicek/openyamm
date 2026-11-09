"""Seat the blade and the grip in the crossguard (user review 2026-10-19: a gap between the guard and the blade).

`make_sword.py` built the guard as a thin recurved bar whose centre lies at y 0.100-0.115 m and whose tips rise to
0.145 m, but started the blade at the tips' height (0.149 m) and ended the grip at 0.093 m: the centreline showed a
4 cm hole above the guard and a 7 mm one below it. In every LOD this moves the blade's root row down to BLADE_ROOT,
inside the guard bar, and the grip's top row up to GRIP_TOP, against the bar's underside (the grip gates select the grip
below 0.1 m, gates.json). UVs and normals stay; the edit is made in the GLB.

Usage: close_sword_guard.py <in.glb> <out.glb>
"""
import json
import struct
import sys

import numpy as np

BLADE_ROOT = 0.108
GRIP_TOP = 0.0995


def components(indices, positions):
    parent = list(range(len(positions)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in indices:
        parent[find(a)] = find(b)
        parent[find(b)] = find(c)
    seen = {}
    for i, key in enumerate(map(tuple, np.round(positions, 5))):
        if key in seen:
            parent[find(i)] = find(seen[key])
        else:
            seen[key] = i
    groups = {}
    for i in range(len(positions)):
        groups.setdefault(find(i), []).append(i)
    return [np.array(group) for group in groups.values()]


def main():
    data = bytearray(open(sys.argv[1], "rb").read())
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + length])
    binaryStart = 20 + length + 8

    def array(index, dtype, components):
        accessor = gltf["accessors"][index]
        bufferView = gltf["bufferViews"][accessor["bufferView"]]
        offset = binaryStart + bufferView.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        return offset, np.frombuffer(data, dtype, accessor["count"] * components, offset).reshape(-1, components)

    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            offset, positions = array(primitive["attributes"]["POSITION"], "<f4", 3)
            indexType = {5123: "<u2", 5125: "<u4"}[gltf["accessors"][primitive["indices"]]["componentType"]]
            _, indices = array(primitive["indices"], indexType, 1)
            positions = positions.copy()
            moved = []
            for group in components(indices.reshape(-1, 3), positions):
                y = positions[group, 1]
                if y.max() > 0.5:
                    rows = group[y < y.min() + 0.002]
                    positions[rows, 1] = BLADE_ROOT
                    moved.append(f"blade root {y.min():.3f} -> {BLADE_ROOT}")
                elif -0.075 < y.min() < 0 and 0.05 < y.max() < 0.1:
                    rows = group[y > y.max() - 0.002]
                    positions[rows, 1] = GRIP_TOP
                    moved.append(f"grip top {y.max():.3f} -> {GRIP_TOP}")
            assert len(moved) == 2, (mesh["name"], moved)
            data[offset:offset + positions.nbytes] = positions.astype("<f4").tobytes()
            accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
            accessor["min"] = positions.min(axis=0).tolist()
            accessor["max"] = positions.max(axis=0).tolist()
            print(mesh["name"], "; ".join(moved))
    # The accessor bounds changed (the same length when re-encoded, padded with spaces to keep the chunk size).
    encoded = json.dumps(gltf, separators=(",", ":")).encode()
    assert len(encoded) <= length, "JSON grew; re-encode the GLB"
    data[20:20 + length] = encoded + b" " * (length - len(encoded))
    open(sys.argv[2], "wb").write(data)


if __name__ == "__main__":
    main()
