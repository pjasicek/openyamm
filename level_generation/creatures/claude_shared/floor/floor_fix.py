#!/usr/bin/env python3
"""Floor fixes on a creature GLB's clips, written into a copy of the GLB (only animation samplers change: new accessors
are appended, meshes, skins, materials and variants are kept byte for byte).

    floor_fix.py <in.glb> <out.glb> [operations...]

  --ground-loop CLIP     per key, move the root joints so the lowest visible point meets the floor (a walk or idle
                         keeps a foot on it: a hop's all-feet-off lift is removed and sunk feet are raised)
  --raise CLIP           per key, raise the root joints by any depth of the lowest visible point under the floor,
                         keeping authored lifts (attacks, hits and casts that hop or lunge)
  --raise-uniform CLIP   raise every key of the clip by ONE amount: the depth under the floor of its lowest visible
                         point over the whole clip (0 when it never goes under). For a flier's loop whose wings beat
                         below the body: a per-key --raise follows the wing tips and bobs the body with the stroke,
                         while this keeps the clip's own vertical motion plus one constant hover offset
  --ground-death DEATH DEAD
                         per key of DEAD, move the root joints so the corpse's lowest point meets the floor; per key
                         of DEATH, raise any part below the floor onto it and lower a lift toward the corpse's own
                         (never further), so the fall settles into the grounded corpse without a jump
  --lift-joints CLIP...  per key of the clips, lift the strips (unbranched joint chains: skirt strips, a tail) whose
                         skinned vertices go below the floor, bending from the strip's top joint by the smallest angle
                         (at most 35 degrees per joint) and further down the strip only where needed; root joints
                         never bend. For a corpse whose cloth, not its body, goes under the floor.
  --lift-only PATTERNS   with --lift-joints, bend only joints whose names match one of the comma-separated globs
                         (cloth: 'Cloak*,Shroud*,Dress*'). Bending limbs reads badly (a 35 degree clavicle to save
                         3 cm): leave their penetration to --ground-death or --raise, or accept it under the cloth.
  --hover METRES DEATH DEAD
                         the flier/hoverer rule: every clip but DEATH and DEAD moves up by METRES (negative: down),
                         so the lowest point over the living clips meets the floor (floor_audit.py prints the amount);
                         DEATH eases the move out (smoothstep over the clip) without taking any key lower than the
                         floor or its authored depth, so the corpse in DEAD stays where it was authored
  --swim METRES DEATH DEAD
                         the swimmer rule (MM9's AISwimFly rows, README.md): every clip but DEATH and DEAD moves up by
                         METRES (MM9's origin to the centre of its body box: half the descriptor height in model
                         units), DEAD's corpse is put on the floor, and DEATH eases from the lift to the corpse's
                         (smoothstep) with no floor clamp: the death starts in the water, where raising its keys onto
                         the floor would pop the body up, and the corpse then sinks to the bed
  --smooth CLIP SECONDS  low-pass the root offsets of --ground-loop, --raise or --ground-death on CLIP instead of
                         solving each key alone (a per-key offset shakes the body where the lowest point changes
                         fast): running maximum of +/- SECONDS x --smooth-hold (default 1; 0 lets the lowest point dip
                         briefly instead of hovering), then a Gaussian of SECONDS, eased back to the original offsets
                         at a one-shot's first and last keys. --smooth-median N first takes the median of N keys (default 1: off), for one-key
                         spikes of a flung hem or hand. --smooth-loop wraps around the clip end. Repeatable.
  --seat-like REF CLIP   move every key of CLIP by ONE amount: the offset that grounds REF's first key (a seated loop).
                         For seated scene clips that start from and return to the seat (mm9_bjarni's Argument clips):
                         a per-key --ground-loop drops the sitter whenever a foot lifts off the floor (crossed legs,
                         feet stretched forward) and shakes the body; the seat height stays the seated loop's. Repeatable;
                         runs before --ground-loop, on the input clips.
  --tolerance METRES     floor tolerance in model units (default 0.001)

Operations run in a fixed order, each on the result of the previous one: --lift-joints, --ground-loop, --raise,
--raise-uniform, --hover, --swim, then --ground-death. The root joints are the skeleton joints whose parent is not a joint; their translation keys are moved
in their parent's space. A channel whose keys do not cover the clip's key times (a two-key STEP hold) is first
resampled onto them, as LINEAR keys of the same motion. See README.md.
"""
import argparse
import fnmatch
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_pose  # noqa: E402

UP = np.array([0.0, 1.0, 0.0])


def channel(model, clip, node, path):
    animation = model.glb.json["animations"][model.clips[clip]]
    for entry in animation["channels"]:
        if entry["target"]["node"] == node and entry["target"]["path"] == path:
            return animation["samplers"][entry["sampler"]]
    return None


def keys_covering(model, sampler, times, path):
    """The sampler's (inputs, outputs); resampled onto its keys and times (LINEAR) when its keys miss some of times."""
    inputs = model.glb.accessor(sampler["input"])[:, 0].astype(np.float64)
    outputs = model.glb.accessor(sampler["output"]).astype(np.float64)
    missing = [time for time in times if np.min(np.abs(inputs - time)) > 1e-6]
    if not missing and sampler.get("interpolation", "LINEAR") == "LINEAR":
        return inputs, outputs
    merged = np.array(sorted(set(np.round(inputs, 7)) | set(np.round(times, 7))))
    step = sampler.get("interpolation", "LINEAR") == "STEP"
    values = []
    for time in merged:
        key = int(np.searchsorted(inputs, time + 1e-7, side="right")) - 1
        if key < 0:
            values.append(outputs[0])
        elif key >= len(inputs) - 1 or step:
            values.append(outputs[min(key, len(inputs) - 1)])
        else:
            fraction = (time - inputs[key]) / max(inputs[key + 1] - inputs[key], 1e-12)
            values.append(glb_pose.slerp(outputs[key], outputs[key + 1], fraction) if path == "rotation"
                          else outputs[key] + fraction * (outputs[key + 1] - outputs[key]))
    sampler["input"] = model.glb.append_accessor(merged[:, None], "SCALAR")
    sampler["interpolation"] = "LINEAR"
    return merged, np.array(values)


def shift_roots(model, clip, times, offsets):
    """Moves every root joint's translation keys in a clip by offsets (model units, up) given at times."""
    rest_world = model.world({})
    for root in model.root_joints:
        sampler = channel(model, clip, root, "translation")
        if sampler is None:
            # A root the clip leaves at rest (a static helper joint) gets its own keys, holding its rest translation.
            animation = model.glb.json["animations"][model.clips[clip]]
            animation["samplers"].append({"input": model.glb.append_accessor(np.array(times)[:, None], "SCALAR"),
                                          "output": model.glb.append_accessor(np.tile(model.rest[root][0], (len(times), 1)),
                                                                              "VEC3"),
                                          "interpolation": "LINEAR"})
            animation["channels"].append({"sampler": len(animation["samplers"]) - 1,
                                          "target": {"node": root, "path": "translation"}})
            sampler = animation["samplers"][-1]
        parent = model.parent[root]
        linear = rest_world[parent][:3, :3] if parent >= 0 else np.eye(3)
        local_up = np.linalg.solve(linear, UP)
        inputs, outputs = keys_covering(model, sampler, times, "translation")
        delta = np.interp(inputs, times, offsets)
        sampler["output"] = model.glb.append_accessor(outputs + delta[:, None] * local_up[None, :], "VEC3")


def lowest_series(model, clip):
    times = model.clip_times(clip)
    lows = [model.lowest(clip, time) for time in times]
    if any(low is None for low in lows):
        raise SystemExit(f"{clip}: a key shows no visible geometry")
    return np.array(times), np.array(lows)


SMOOTH = {}
HOLD = [1.0]
MEDIAN = [1]


def smoothed(clip, times, offsets):
    """The offsets of a clip after --smooth or --smooth-loop (see the module help), or unchanged."""
    sigma, loop = SMOOTH.get(clip, (0.0, False))
    if not sigma or len(times) < 3:
        return offsets
    step = float(np.median(np.diff(times)))
    body = offsets[:-1] if loop else offsets
    if MEDIAN[0] > 1:                      # one-key spikes (a flung hem or hand chased by the whole body)
        half = MEDIAN[0] // 2
        wide = np.pad(body, half, mode="wrap" if loop else "edge")
        body = np.array([np.median(wide[i:i + MEDIAN[0]]) for i in range(len(body))])
    reach = int(round(HOLD[0] * sigma / step))
    radius = int(np.ceil(3 * sigma / step))
    padded = np.pad(body, radius + reach, mode="wrap" if loop else "edge")
    held = np.array([padded[i - reach:i + reach + 1].max() for i in range(reach, len(padded) - reach)])
    kernel = np.exp(-0.5 * (np.arange(-radius, radius + 1) * step / sigma) ** 2)
    out = np.convolve(held, kernel / kernel.sum(), mode="valid")
    if loop:
        return np.r_[out, out[0]]
    # a one-shot starts and ends on its own offsets (no pop against the clips around it): a smooth tail at each end
    tail = np.clip(1.0 - (times - times[0]) / (4 * sigma), 0.0, 1.0)
    out = out + (offsets[0] - out[0]) * tail * tail * (3 - 2 * tail)
    tail = np.clip(1.0 - (times[-1] - times) / (4 * sigma), 0.0, 1.0)
    return out + (offsets[-1] - out[-1]) * tail * tail * (3 - 2 * tail)


def ground_loop(model, clip, tolerance):
    times, lows = lowest_series(model, clip)
    offsets = smoothed(clip, times, -np.where(np.abs(lows) > tolerance, lows, 0.0))
    shift_roots(model, clip, times, offsets)
    print(f"{clip}: grounded at {int(np.count_nonzero(offsets))} of {len(times)} keys (lowest {lows.min():+.4f}, "
          f"highest {lows.max():+.4f})")


def seat_like(model, ref, clip, tolerance):
    low = model.lowest(ref, model.clip_times(ref)[0])
    offset = -low if abs(low) > tolerance else 0.0
    times = np.array(model.clip_times(clip))
    shift_roots(model, clip, times, np.full(len(times), offset))
    print(f"{clip}: seated like {ref}, every key moved by {offset:+.4f}")


def raise_clip(model, clip, tolerance):
    times, lows = lowest_series(model, clip)
    offsets = smoothed(clip, times, np.where(lows < -tolerance, -lows, 0.0))
    shift_roots(model, clip, times, offsets)
    print(f"{clip}: raised at {int(np.count_nonzero(offsets))} of {len(times)} keys (lowest {lows.min():+.4f})")


def raise_uniform(model, clip, tolerance):
    times, lows = lowest_series(model, clip)
    amount = -lows.min() if lows.min() < -tolerance else 0.0
    shift_roots(model, clip, times, np.full(len(times), amount))
    print(f"{clip}: raised uniformly by {amount:+.4f} at all {len(times)} keys (lowest {lows.min():+.4f} at "
          f"{times[int(np.argmin(lows))]:.3f} s)")


def ground_death(model, death, dead, tolerance):
    dead_times, dead_lows = lowest_series(model, dead)
    shift_roots(model, dead, dead_times, -dead_lows)
    corpse = float(dead_lows[-1])
    times, lows = lowest_series(model, death)
    offsets = smoothed(death, times, np.where(lows < -tolerance, -lows, -np.clip(lows, 0.0, max(corpse, 0.0))))
    shift_roots(model, death, times, offsets)
    print(f"{dead}: corpse moved by {-corpse:+.4f}; {death}: {int(np.count_nonzero(lows < -tolerance))} keys raised "
          f"(lowest {lows.min():+.4f}), settling toward the corpse")


def hover(model, amount, death, dead):
    for clip in model.clips:
        if clip not in (death, dead):
            times = model.clip_times(clip)
            shift_roots(model, clip, times, np.full(len(times), amount))
    times = np.array(model.clip_times(death))
    # A key with nothing visible (a body dissolved before its end) has no floor to keep.
    lows = np.array([np.inf if low is None else low for low in (model.lowest(death, time) for time in times)])
    progress = np.clip(times / times[-1], 0.0, 1.0) if times[-1] > 0 else np.ones(len(times))
    eased = amount * (1.0 - progress * progress * (3.0 - 2.0 * progress))
    offsets = np.maximum(eased, -np.maximum(lows, 0.0))
    shift_roots(model, death, times, offsets)
    living = sorted(clip for clip in model.clips if clip not in (death, dead))
    print(f"hover {amount:+.6f} on {', '.join(living)}; {death} eased out, "
          f"{int(np.count_nonzero(offsets > eased + 1e-9))} keys held at the floor")


def swim(model, amount, death, dead):
    dead_times, dead_lows = lowest_series(model, dead)
    shift_roots(model, dead, dead_times, -dead_lows)
    for clip in model.clips:
        if clip not in (death, dead):
            times = model.clip_times(clip)
            shift_roots(model, clip, times, np.full(len(times), amount))
    times = np.array(model.clip_times(death))
    progress = np.clip(times / times[-1], 0.0, 1.0) if times[-1] > 0 else np.ones(len(times))
    eased = progress * progress * (3.0 - 2.0 * progress)
    corpse = -float(dead_lows[0])
    shift_roots(model, death, times, amount * (1.0 - eased) + corpse * eased)
    living = sorted(clip for clip in model.clips if clip not in (death, dead))
    print(f"swim lift {amount:+.6f} on {', '.join(living)}; {dead} corpse moved by {corpse:+.4f}; {death} eased "
          f"from the lift to it")


def rotation_about(axis, angle):
    axis = axis / np.linalg.norm(axis)
    x, y, z = axis
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def unit_columns(matrix):
    return matrix / np.linalg.norm(matrix, axis=0, keepdims=True)


def below_by_joint(model, local, tolerance):
    """{joint node: indices per primitive} of visible vertices below the floor, grouped by their dominant joint."""
    posed = model.skinned_positions(model.world(local))
    groups = {}
    for primitive_index, ((points, _), visible, primitive) in enumerate(
            zip(posed, model.visible_vertices(posed), model.primitives)):
        if not primitive["skinned"]:
            continue
        below = visible[points[visible, 1] < -tolerance]
        for vertex in below:
            joint = model.joints[primitive["joints"][vertex][np.argmax(primitive["weights"][vertex])]]
            groups.setdefault(joint, {}).setdefault(primitive_index, []).append(vertex)
    return groups, posed


def lowest_of(model, local, members):
    posed = model.skinned_positions(model.world(local))
    return min(posed[index][0][vertices, 1].min() for index, vertices in members.items())


def bend(model, local, joint, members, tolerance, limit):
    """Sets joint's local rotation in local to the smallest bend about its head, toward up, that lifts members'
    vertices onto the floor, or to limit (radians) when that is not enough; returns the angle used."""
    world = model.world(local)
    head = world[joint][:3, 3]
    posed = model.skinned_positions(world)
    centroid = np.mean(np.concatenate([posed[index][0][vertices] for index, vertices in members.items()]), axis=0)
    axis = np.cross(centroid - head, UP)
    if np.linalg.norm(axis) < 1e-9:
        return 0.0
    parent = model.parent[joint]
    parent_rotation = unit_columns(world[parent][:3, :3]) if parent >= 0 else np.eye(3)
    current = local.get(joint, model.rest[joint])
    original_matrix = glb_pose.quaternion_matrix(current[1])

    def rotated(angle):
        return glb_pose.matrix_quaternion(parent_rotation.T @ rotation_about(axis, angle) @ parent_rotation
                                          @ original_matrix)

    def lifted(angle):
        trial = dict(local)
        trial[joint] = [current[0], rotated(angle), current[2]]
        return lowest_of(model, trial, members) >= -tolerance * 0.5

    angle = limit
    if lifted(limit):
        low, angle = 0.0, limit
        for _ in range(24):
            middle = 0.5 * (low + angle)
            low, angle = (low, middle) if lifted(middle) else (middle, angle)
    local[joint] = [current[0].copy(), rotated(angle), current[2].copy()]
    return angle


def merge(groups):
    merged = {}
    for members in groups:
        for index, vertices in members.items():
            merged.setdefault(index, []).extend(vertices)
    return merged


def lift_joints(model, clips, tolerance, patterns=None):
    """Lifts each penetrating strip from its top: per key, the strip's first joint below a branching joint (a skirt
    strip's top under the pelvis) bends by the smallest angle, at most 35 degrees, that brings every penetrating vertex
    of the strip onto the floor; what is still below moves the bend one joint down the strip. The same rule at every
    key of every clip keeps the motion continuous; root joints never bend."""
    root_set = set(model.root_joints)
    nodes = model.glb.json["nodes"]
    allowed = {joint for joint in model.joints if not patterns
               or any(fnmatch.fnmatch(nodes[joint].get("name", ""), pattern) for pattern in patterns)}
    joint_set = set(model.joints)
    children = {joint: [child for child in model.glb.json["nodes"][joint].get("children", []) if child in joint_set]
                for joint in model.joints}

    def path(joint):
        """Joints from the strip's top down to joint."""
        chain = [joint]
        while model.parent[chain[0]] in allowed and model.parent[chain[0]] not in root_set \
                and len(children[model.parent[chain[0]]]) == 1:
            chain.insert(0, model.parent[chain[0]])
        return chain

    limit = np.radians(35.0)
    corrected, bent = {}, set()
    for clip in clips:
        for time in model.clip_times(clip):
            local = model.sample(clip, time)
            before = {joint: local[joint][1].copy() for joint in local}
            for level in range(6):
                groups, _ = below_by_joint(model, local, tolerance)
                strips = {}
                for joint, members in groups.items():
                    if joint not in root_set and joint in allowed:
                        chain = path(joint)
                        strips.setdefault(chain[0], []).append((chain, members))
                if not strips:
                    break
                for top, parts in strips.items():
                    deepest = max((chain for chain, _ in parts), key=len)
                    joint = deepest[min(level, len(deepest) - 1)]
                    bend(model, local, joint, merge(members for _, members in parts), tolerance, limit)
                    bent.add(joint)
            for joint, trs in local.items():
                if joint in before and not np.allclose(before[joint], trs[1]):
                    corrected.setdefault((clip, joint), {})[time] = trs[1]
    for (clip, joint), keys in corrected.items():
        sampler = channel(model, clip, joint, "rotation")
        if sampler is None:
            raise SystemExit(f"{clip}: joint {model.glb.json['nodes'][joint].get('name')} has no rotation keys")
        inputs, outputs = keys_covering(model, sampler, model.clip_times(clip), "rotation")
        for index, time in enumerate(inputs):
            match = min(keys, key=lambda key: abs(key - time))
            if abs(match - time) < 1e-6:
                outputs[index] = keys[match]
        sampler["output"] = model.glb.append_accessor(outputs, "VEC4")
    names = sorted({model.glb.json["nodes"][joint].get("name", str(joint)) for joint in bent})
    print(f"{' + '.join(clips)}: bent {', '.join(names)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ground-loop", action="append", default=[], metavar="CLIP")
    parser.add_argument("--ground-death", nargs=2, metavar=("DEATH", "DEAD"))
    parser.add_argument("--lift-joints", nargs="+", default=[], metavar="CLIP")
    parser.add_argument("--raise", dest="raise_clips", action="append", default=[], metavar="CLIP")
    parser.add_argument("--raise-uniform", dest="raise_uniform_clips", action="append", default=[], metavar="CLIP")
    parser.add_argument("--lift-only", help="comma-separated joint name globs for --lift-joints")
    parser.add_argument("--hover", nargs=3, metavar=("METRES", "DEATH", "DEAD"))
    parser.add_argument("--swim", nargs=3, metavar=("METRES", "DEATH", "DEAD"))
    parser.add_argument("--smooth", nargs=2, action="append", default=[], metavar=("CLIP", "SECONDS"))
    parser.add_argument("--smooth-loop", nargs=2, action="append", default=[], metavar=("CLIP", "SECONDS"))
    parser.add_argument("--smooth-hold", type=float, default=1.0)
    parser.add_argument("--smooth-median", type=int, default=1)
    parser.add_argument("--seat-like", nargs=2, action="append", default=[], metavar=("REF", "CLIP"))
    parser.add_argument("--tolerance", type=float, default=0.001)
    args = parser.parse_args()
    HOLD[0] = args.smooth_hold
    MEDIAN[0] = args.smooth_median
    SMOOTH.update({clip: (float(seconds), False) for clip, seconds in args.smooth})
    SMOOTH.update({clip: (float(seconds), True) for clip, seconds in args.smooth_loop})
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("write the fixed GLB to a new path")
    glb = glb_pose.Glb(args.input)
    # The operations run in a fixed order: bent joints first, then the whole-body moves that depend on them.
    if args.lift_joints:
        lift_joints(glb_pose.Model(glb), args.lift_joints, args.tolerance,
                    args.lift_only.split(",") if args.lift_only else None)
    for ref, clip in args.seat_like:      # before --ground-loop, so REF is measured on the input clips
        seat_like(glb_pose.Model(glb), ref, clip, args.tolerance)
    for clip in args.ground_loop:
        ground_loop(glb_pose.Model(glb), clip, args.tolerance)
    for clip in args.raise_clips:
        raise_clip(glb_pose.Model(glb), clip, args.tolerance)
    for clip in args.raise_uniform_clips:
        raise_uniform(glb_pose.Model(glb), clip, args.tolerance)
    if args.hover:
        hover(glb_pose.Model(glb), float(args.hover[0]), args.hover[1], args.hover[2])
    if args.swim:
        swim(glb_pose.Model(glb), float(args.swim[0]), args.swim[1], args.swim[2])
    if args.ground_death:
        ground_death(glb_pose.Model(glb), *args.ground_death, args.tolerance)
    glb.write(args.output)
    print(f"written {args.output}")


if __name__ == "__main__":
    main()
