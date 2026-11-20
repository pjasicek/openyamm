#!/usr/bin/env python3
"""Add clips from one GLB to another GLB of the same skeleton, without Blender: new procedural gaits made on a
project's editable rig, grafted onto the installed (reduced, floor-fixed) export so its meshes, LODs, variants and
existing clips stay byte-for-byte.

    graft_clips.py <target.glb> <clips.glb> <out.glb> --clip Walk2 [--clip Run2 ...] [--replace]

Channels are matched to target nodes by name. Every animated node must exist in the target with the same rest
translation, rotation and scale (within 1e-4); otherwise nothing is written, because the keys would pose a different
skeleton. A clip whose name the target already has is refused unless --replace (which drops the old one).
"""
import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "floor"))
import glb_pose  # noqa: E402

REST_TOLERANCE = 1e-4
DEFAULTS = {"translation": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0, 1.0], "scale": [1.0, 1.0, 1.0]}
KINDS = {"translation": "VEC3", "rotation": "VEC4", "scale": "VEC3"}


def rest_difference(a, b):
    worst = 0.0
    for key, default in DEFAULTS.items():
        x, y = np.array(a.get(key, default)), np.array(b.get(key, default))
        if key == "rotation" and np.dot(x, y) < 0:
            y = -y
        worst = max(worst, float(np.abs(x - y).max()))
    return worst


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("clips", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--clip", action="append", required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    target, source = glb_pose.Glb(args.target), glb_pose.Glb(args.clips)
    by_name = {}
    for index, node in enumerate(target.json["nodes"]):
        by_name.setdefault(node.get("name"), index)
    animations = target.json.setdefault("animations", [])
    for name in args.clip:
        clip = next((a for a in source.json.get("animations", []) if a["name"] == name), None)
        if clip is None:
            sys.exit(f"{args.clips}: no clip {name}")
        existing = [a for a in animations if a["name"] == name]
        if existing and not args.replace:
            sys.exit(f"{args.target}: already has a clip {name} (pass --replace)")
        animations[:] = [a for a in animations if a["name"] != name]
        samplers, channels, copied = [], [], {}
        for channel in clip["channels"]:
            node = source.json["nodes"][channel["target"]["node"]]
            index = by_name.get(node.get("name"))
            if index is None:
                sys.exit(f"{name}: node {node.get('name')} is not in the target")
            difference = rest_difference(node, target.json["nodes"][index])
            if difference > REST_TOLERANCE:
                sys.exit(f"{name}: node {node.get('name')} rests differently in the target ({difference:.6f})")
            sampler = clip["samplers"][channel["sampler"]]
            path = channel["target"]["path"]
            if sampler["input"] not in copied:
                copied[sampler["input"]] = target.append_accessor(source.accessor(sampler["input"]), "SCALAR")
            samplers.append({"input": copied[sampler["input"]],
                             "output": target.append_accessor(source.accessor(sampler["output"]), KINDS[path]),
                             "interpolation": sampler.get("interpolation", "LINEAR")})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": index, "path": path}})
        animations.append({"name": name, "channels": channels, "samplers": samplers})
        length = max(float(source.accessor(s["input"])[-1, 0]) for s in clip["samplers"])
        print(f"grafted {name}: {len(channels)} channels, {length:.4f} s")
    target.write(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
