#!/usr/bin/env python3
"""Remove clips from an exported GLB without Blender, keeping everything else as it is: the clips' animations go, and
the accessors and buffer views only they used are dropped and the binary chunk compacted.

    drop_clips.py <in.glb> <out.glb> --clip Attack [--clip Other ...]

Accessors are referenced from mesh primitives (attributes, indices, morph targets), skins and animation samplers;
buffer views from accessors and images. Accessors referenced from none of these are orphans (left by earlier key
edits) and are dropped too. A file with sparse accessors or required (compression) extensions is refused.
"""
import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "floor"))
import glb_pose  # noqa: E402


def accessor_refs(document):
    """Every place an accessor index is stored: (container, key) pairs to read and remap."""
    refs = []
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            refs += [(primitive["attributes"], key) for key in primitive["attributes"]]
            if "indices" in primitive:
                refs.append((primitive, "indices"))
            for target in primitive.get("targets", []):
                refs += [(target, key) for key in target]
    for skin in document.get("skins", []):
        if "inverseBindMatrices" in skin:
            refs.append((skin, "inverseBindMatrices"))
    for animation in document.get("animations", []):
        for sampler in animation["samplers"]:
            refs += [(sampler, "input"), (sampler, "output")]
    return refs


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--clip", action="append", required=True)
    args = parser.parse_args()
    glb = glb_pose.Glb(args.source)
    document = glb.json
    if any("sparse" in accessor for accessor in document["accessors"]) or document.get("extensionsRequired"):
        sys.exit("sparse accessors or required extensions: not supported")
    names = [animation.get("name") for animation in document.get("animations", [])]
    missing = [clip for clip in args.clip if clip not in names]
    if missing:
        sys.exit(f"no such clips: {missing} (have {names})")
    orphans = len(document["accessors"]) - len({ref[0][ref[1]] for ref in accessor_refs(document)})
    document["animations"] = [animation for animation in document["animations"] if animation.get("name") not in args.clip]
    if not document["animations"]:
        del document["animations"]

    refs = accessor_refs(document)
    kept_accessors = sorted({container[key] for container, key in refs})
    accessor_map = {old: new for new, old in enumerate(kept_accessors)}
    for container, key in refs:
        container[key] = accessor_map[container[key]]
    document["accessors"] = [document["accessors"][old] for old in kept_accessors]

    view_users = [accessor for accessor in document["accessors"] if "bufferView" in accessor]
    view_users += [image for image in document.get("images", []) if "bufferView" in image]
    kept_views = sorted({user["bufferView"] for user in view_users})
    view_map = {old: new for new, old in enumerate(kept_views)}
    binary = bytearray()
    views = []
    for old in kept_views:
        view = dict(document["bufferViews"][old])
        if view.get("buffer", 0) != 0:
            sys.exit("more than one buffer: not supported")
        start = view.get("byteOffset", 0)
        data = glb.bin[start:start + view["byteLength"]]
        binary += b"\0" * (-len(binary) % 4)
        view["byteOffset"] = len(binary)
        binary += data
        views.append(view)
    for user in view_users:
        user["bufferView"] = view_map[user["bufferView"]]
    document["bufferViews"] = views
    binary += b"\0" * (-len(binary) % 4)
    document["buffers"][0]["byteLength"] = len(binary)
    glb.bin = binary
    glb.write(args.out)

    check = glb_pose.Model(glb_pose.Glb(args.out))
    before = glb_pose.Model(glb_pose.Glb(args.source))
    for clip in check.clips:
        for time in np.linspace(0.0, before.clip_times(clip)[-1], 7):
            difference = np.abs(check.world(check.sample(clip, time)) - before.world(before.sample(clip, time))).max()
            assert difference < 1e-6, (clip, time, difference)
    print(f"{args.out}: dropped {args.clip} and {orphans} orphan accessors; clips {sorted(check.clips)}; "
          f"{args.source.stat().st_size} -> {args.out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
