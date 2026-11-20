#!/usr/bin/env python3
"""Speed up the start of one GLB clip: the first `end` seconds play `speed` times faster, easing back to the clip's
own speed over the last `ramp` seconds of that span so the following motion does not hitch; the rest keeps its timing
and moves earlier. The same warp is previewed by the timing review (review.js warpTime).

    retime_clip.py <in.glb> <out.glb> --clip Attack --end 0.4 --speed 3 [--ramp 0.1] [--time 0.78 ...]

Every sampler input of the clip is remapped (accessor min/max too); an input shared with another clip is copied first.
Prints the new length and each --time (e.g. impact markers) on the new clock. Retime the accepted project export, never
an installed copy, then install it with tools/install_model.py and move the clip's markers to the printed times.
"""
import argparse
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from build_actor_lods import read_glb, write_glb  # noqa: E402


def warpTime(time, end, speed, ramp):
    """Clip time after the warp for original clip time `time`."""
    if speed == 1.0 or end <= 0.0:
        return time
    ramp = min(max(ramp, 0.0), end)
    rampStart = end - ramp
    if time <= rampStart:
        return time / speed
    warped = rampStart / speed
    # Over the ramp the speed falls linearly from `speed` to 1: the time is the integral of 1 / speed.
    slope = (1.0 - speed) / ramp
    span = min(time, end) - rampStart
    warped += math.log((speed + slope * span) / speed) / slope
    return warped + max(0.0, time - end)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--end", type=float, required=True, help="original seconds sped up from the clip's start")
    parser.add_argument("--speed", type=float, required=True, help="playback speed of that span (> 1 is faster)")
    parser.add_argument("--ramp", type=float, default=0.1, help="seconds at its end easing back to 1x")
    parser.add_argument("--time", type=float, action="append", default=[], help="clip time to report after the warp")
    args = parser.parse_args()
    if args.speed <= 0.0 or args.end < 0.0:
        raise SystemExit("speed must be positive and end non-negative")
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("write to a new file")

    document, binary = read_glb(args.input)
    binary = bytearray(binary)
    users = {}
    for animation in document.get("animations", []):
        for sampler in animation["samplers"]:
            users.setdefault(sampler["input"], set()).add(animation.get("name"))
    animation = next((a for a in document.get("animations", []) if a.get("name") == args.clip), None)
    if animation is None:
        raise SystemExit(f"clip {args.clip} not found")
    # Key times shared with another clip are copied first, so only this clip is warped.
    copies = {}
    for sampler in animation["samplers"]:
        index = sampler["input"]
        if users[index] == {args.clip}:
            continue
        if index not in copies:
            accessor = dict(document["accessors"][index])
            view = document["bufferViews"][accessor["bufferView"]]
            start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            data = binary[start:start + accessor["count"] * 4]
            binary += b"\0" * (-len(binary) % 4)
            document["bufferViews"].append({"buffer": view["buffer"], "byteOffset": len(binary), "byteLength": len(data)})
            binary += data
            accessor["bufferView"] = len(document["bufferViews"]) - 1
            accessor.pop("byteOffset", None)
            document["accessors"].append(accessor)
            copies[index] = len(document["accessors"]) - 1
        sampler["input"] = copies[index]
    if copies:
        print(f"{args.clip}: {len(copies)} key time lists shared with other clips copied")
    end = 0.0
    for index in sorted({sampler["input"] for sampler in animation["samplers"]}):
        accessor = document["accessors"][index]
        view = document["bufferViews"][accessor["bufferView"]]
        if accessor["componentType"] != 5126 or accessor["type"] != "SCALAR" or view.get("byteStride", 4) != 4:
            raise SystemExit("unsupported key time accessor")
        start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        times = struct.unpack_from(f"<{accessor['count']}f", binary, start)
        warped = [warpTime(t, args.end, args.speed, args.ramp) for t in times]
        struct.pack_into(f"<{accessor['count']}f", binary, start, *warped)
        accessor["min"] = [min(warped)]
        accessor["max"] = [max(warped)]
        end = max(end, max(warped))
    write_glb(args.output, document, bytes(binary))
    print(f"{args.clip}: {args.end} s at {args.speed}x (ramp {args.ramp} s) -> length {end:.4f} s")
    for time in args.time:
        print(f"  {time:.4f} s -> {warpTime(time, args.end, args.speed, args.ramp):.4f} s")


if __name__ == "__main__":
    main()
