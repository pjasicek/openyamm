"""Spread the waist over the spine chain so the cuirass rim stays on the belt when the torso twists.

The installed skin has the cuirass rigid on B_Spine2 down to 1.04 m (its joint is at 1.27 m) and the belt on
B_Pelvis below 0.96 m: in Attack the spine twists about 45 degrees and bends about 55 degrees over the pelvis, so the
rim swings off the belt and the dark underlayer shows. Vertices weighted only to the spine chain (torso shell, belt,
underlayer; not arms or legs) between LOW and HIGH metres get weights blended by height along the chain
B_Pelvis -> B_Spine -> B_Spine1 -> B_Spine2 (smoothstep), in every colour and shadow LOD. Above HIGH (the shoulder
repair, the upper cuirass) and below LOW nothing changes.

Usage: waist_weights.py <in.glb> <out.glb> [LOW HIGH]
"""
import json
import struct
import sys

import numpy as np

CHAIN = ["B_Pelvis", "B_Spine", "B_Spine1", "B_Spine2"]


def main():
    source, target = sys.argv[1], sys.argv[2]
    low, high = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.96, 1.12)
    data = bytearray(open(source, "rb").read())
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + length])
    binaryStart = 20 + length + 8
    joints = [gltf["nodes"][j]["name"] for j in gltf["skins"][0]["joints"]]
    chain = [joints.index(name) for name in CHAIN]

    def view(index, dtype, components):
        accessor = gltf["accessors"][index]
        bufferView = gltf["bufferViews"][accessor["bufferView"]]
        assert "byteStride" not in bufferView or bufferView["byteStride"] == np.dtype(dtype).itemsize * components
        offset = binaryStart + bufferView.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        return np.frombuffer(data, dtype, accessor["count"] * components, offset).reshape(-1, components)

    changed = 0
    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            attributes = primitive["attributes"]
            assert gltf["accessors"][attributes["WEIGHTS_0"]]["componentType"] == 5126
            assert gltf["accessors"][attributes["JOINTS_0"]]["componentType"] == 5121
            positions = view(attributes["POSITION"], "<f4", 3)
            weights = view(attributes["WEIGHTS_0"], "<f4", 4).copy()
            boneIds = view(attributes["JOINTS_0"], "u1", 4).copy()
            for i, (x, height, z) in enumerate(positions):
                if not low < height < high:
                    continue
                used = {int(bone) for bone, weight in zip(boneIds[i], weights[i]) if weight > 1e-4}
                if not used or not used <= set(chain):
                    continue
                t = (height - low) / (high - low)
                c = t * t * (3 - 2 * t) * (len(chain) - 1)
                k = min(int(c), len(chain) - 2)
                f = c - k
                boneIds[i] = [chain[k], chain[k + 1], 0, 0]
                weights[i] = [1 - f, f, 0, 0]
                changed += 1
            for index, values in ((attributes["WEIGHTS_0"], weights), (attributes["JOINTS_0"], boneIds)):
                accessor = gltf["accessors"][index]
                bufferView = gltf["bufferViews"][accessor["bufferView"]]
                offset = binaryStart + bufferView.get("byteOffset", 0) + accessor.get("byteOffset", 0)
                raw = values.tobytes()
                data[offset:offset + len(raw)] = raw
    open(target, "wb").write(data)
    print(f"{changed} vertices reweighted over {low}-{high} m")


if __name__ == "__main__":
    main()
