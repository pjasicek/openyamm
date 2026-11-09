#!/usr/bin/env python3
"""Replace one GLB clip with an exact copy of another (own key data, so either can be retimed later).

    copy_clip.py <in.glb> <out.glb> --source Attack --target Cast

The target keeps its name and position; its old key data is dropped and the binary chunk is compacted.
"""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from build_actor_lods import read_glb, write_glb  # noqa: E402


def viewBytes(document, binary, index):
    view = document["bufferViews"][index]
    start = view.get("byteOffset", 0)
    return binary[start:start + view["byteLength"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("write to a new file")

    document, binary = read_glb(args.input)
    if len(document["buffers"]) != 1:
        raise SystemExit("expected one buffer")
    animations = {animation.get("name"): animation for animation in document["animations"]}
    source = animations[args.source]
    target = animations[args.target]

    # Copy the source's accessors (each on its own new buffer view) and point a copy of its samplers at them.
    accessors = document["accessors"]
    views = document["bufferViews"]
    extra = bytearray()
    base = len(binary) + (-len(binary) % 4)
    copied = {}
    copiedViews = {}
    for sampler in source["samplers"]:
        for key in ("input", "output"):
            index = sampler[key]
            if index in copied:
                continue
            accessor = copy.deepcopy(accessors[index])
            if accessor["bufferView"] not in copiedViews:
                view = copy.deepcopy(views[accessor["bufferView"]])
                data = viewBytes(document, binary, accessor["bufferView"])
                extra += b"\0" * (-len(extra) % 4)
                view["byteOffset"] = base + len(extra)
                extra += data
                views.append(view)
                copiedViews[accessor["bufferView"]] = len(views) - 1
            accessor["bufferView"] = copiedViews[accessor["bufferView"]]
            accessors.append(accessor)
            copied[index] = len(accessors) - 1
    removed = {sampler[key] for sampler in target["samplers"] for key in ("input", "output")}
    target["channels"] = copy.deepcopy(source["channels"])
    target["samplers"] = [dict(sampler, input=copied[sampler["input"]], output=copied[sampler["output"]])
                          for sampler in source["samplers"]]
    binary = bytes(binary) + b"\0" * (base - len(binary)) + bytes(extra)

    # Drop accessors nobody references any more, then buffer views, and rebuild the binary chunk.
    def accessorRefs():
        for mesh in document.get("meshes", []):
            for primitive in mesh["primitives"]:
                for attributes in [primitive["attributes"], *primitive.get("targets", [])]:
                    for name in attributes:
                        yield attributes, name
                if "indices" in primitive:
                    yield primitive, "indices"
        for skin in document.get("skins", []):
            if "inverseBindMatrices" in skin:
                yield skin, "inverseBindMatrices"
        for animation in document["animations"]:
            for sampler in animation["samplers"]:
                yield sampler, "input"
                yield sampler, "output"

    used = {holder[key] for holder, key in accessorRefs()}
    shared = len(used & removed)
    keep = [index for index in range(len(accessors)) if index in used]
    accessorMap = {old: new for new, old in enumerate(keep)}
    for holder, key in list(accessorRefs()):
        holder[key] = accessorMap[holder[key]]
    document["accessors"] = [accessors[index] for index in keep]

    viewUsers = [accessor for accessor in document["accessors"] if "bufferView" in accessor]
    viewUsers += [image for image in document.get("images", []) if "bufferView" in image]
    usedViews = sorted({holder["bufferView"] for holder in viewUsers})
    compact = bytearray()
    viewMap = {}
    for old in usedViews:
        compact += b"\0" * (-len(compact) % 4)
        data = viewBytes(document, binary, old)
        view = dict(views[old], byteOffset=len(compact))
        compact += data
        viewMap[old] = len(viewMap)
        views[old] = view
    document["bufferViews"] = [views[old] for old in usedViews]
    for holder in viewUsers:
        holder["bufferView"] = viewMap[holder["bufferView"]]
    write_glb(args.output, document, bytes(compact))
    print(f"{args.target} <- {args.source}: {len(accessors) - len(keep)} accessors dropped, "
          f"{shared} still used by other clips, {len(binary)} -> {len(compact)} bytes")


if __name__ == "__main__":
    main()
