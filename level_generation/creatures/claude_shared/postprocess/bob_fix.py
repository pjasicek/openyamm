#!/usr/bin/env python3
"""Reshapes the body bob of a biped's walk or run clip, written into a copy of the GLB (only animation samplers
change: new accessors are appended, meshes, skins, materials and variants are kept byte for byte).

    bob_fix.py <in.glb> <out.glb> --clip CLIP TARGET [--clip CLIP TARGET ...] [--keep-uneven]

The bob is the vertical travel of the pelvis (the head follows it within a few per cent on every installed biped).
For each clip the pelvis height y(t) over the loop is split into its even part, (y(t) + y(t + T/2)) / 2 (the two steps
alike), and the rest (one step higher than the other: a limp). The new height is

    mean + gain * (even part - mean)          (+ the uneven rest with --keep-uneven)

with the gain chosen so the head's peak-to-peak travel becomes TARGET per cent of the head's standing height (Standing
at 0 s), but at least GAIN_MIN: where the spine's own nod carries the head, the target is not reached. TARGET 0 keeps
the even part as authored and only removes the limp.

A TARGET with a shape suffix replaces the authored bob with a synthetic one timed by the legs, for a clip whose own
bob is too faint or out of step to scale up: `3:walk` (an inverted pendulum: the pelvis is highest over the planted
foot, lowest when the feet are spread) and `4:run` (a grounded run: the pelvis is lowest over the planted foot). The
planted foot is the lower one; the shape is -d^2 or +d^2 of its horizontal distance d from the pelvis, evened over the
two steps.

The root joints move by the difference (the whole skeleton, as floor_fix.py does), then each leg is solved again so
its foot joint keeps its original world position and rotation: the planted feet, the stride and the floor contact are
unchanged. The knee stays in its
original bend plane. A leg is never stretched further than the clip already stretches it: where the new height needs
more, the pelvis is lowered to reach and the curve is smoothed around it.

Legs are found by name: the leaf-most foot joint (FOOT names, as in stride_audit.py), its parent (calf) and that
joint's parent (thigh). Prints the head bob before and after and the worst foot drift (should be ~0).
"""
import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "floor"))
import floor_fix  # noqa: E402
import glb_pose  # noqa: E402

UP = np.array([0.0, 1.0, 0.0])
FOOT = ("foot", "toe", "ankle", "hoof", "paw", "tarsus")
# Share of the clip's own longest hip-to-ankle reach the new pose may use.
REACH = 1.0
# Least share of the authored even bob a damped clip keeps: below it the hips glide while a nodding spine still bobs
# the head (the rest of the head's travel is then the upper body's, reported as is).
GAIN_MIN = 0.2
SMOOTH_PASSES = 4


def find_joint(model, *patterns):
    nodes = model.glb.json["nodes"]
    for pattern in patterns:
        for joint in model.joints:
            name = nodes[joint].get("name", "").lower()
            if pattern in name and "socket" not in name and "end" not in name:
                return joint
    raise SystemExit(f"no joint named like {patterns}")


def legs(model):
    """[(thigh, calf, foot)] per leg: foot is the joint that ends the two-bone chain (it keeps its world transform)."""
    nodes = model.glb.json["nodes"]
    is_foot = [any(part in node.get("name", "").lower() for part in FOOT) for node in nodes]
    leaves = [joint for joint in model.joints
              if is_foot[joint] and not any(is_foot[child] for child in nodes[joint].get("children", []))]
    chains = []
    for leaf in leaves:
        foot = leaf
        # A toe under the foot: the chain ends at the topmost foot-named joint (the ankle).
        while is_foot[model.parent[foot]]:
            foot = model.parent[foot]
        calf = model.parent[foot]
        thigh = model.parent[calf]
        chains.append((thigh, calf, foot))
    if len(chains) != 2:
        raise SystemExit(f"expected two legs, found {len(chains)}")
    return chains


def rotation_of(matrix):
    return floor_fix.unit_columns(matrix[:3, :3])


def frame(direction, normal):
    first = direction / np.linalg.norm(direction)
    second = normal - np.dot(normal, first) * first
    second /= np.linalg.norm(second)
    return np.stack([first, second, np.cross(first, second)], axis=1)


def periodic(times, values, duration):
    """values at times, as a function over one loop (linear, wrapping)."""
    def at(query):
        return np.interp(np.mod(query, duration), times, values)
    return at


def smooth(values, width):
    """Periodic box smoothing over width samples (odd)."""
    if width < 3:
        return values
    kernel = np.ones(width) / width
    padded = np.concatenate([values[-width:], values, values[:width]])
    return np.convolve(padded, kernel, mode="same")[width:-width]


def bob_percent(model, clip, head, height):
    times = np.linspace(0.0, model.clip_times(clip)[-1], 241)
    ys = [model.world(model.sample(clip, time))[head][1, 3] for time in times]
    return float(np.ptp(ys) / height * 100.0)


def leg_shape(model, clip, chains, root, times, kind):
    """The synthetic bob shape at times: -d^2 (walk) or +d^2 (run) of the lower foot's horizontal distance d."""
    values = []
    for time in times:
        pose = model.world(model.sample(clip, time))
        foot = min((pose[foot][:3, 3] for _, _, foot in chains), key=lambda point: point[1])
        distance = float(np.sum((foot - pose[root][:3, 3])[[0, 2]] ** 2))
        values.append(-distance if kind == "walk" else distance)
    return np.array(values)



def reshape(glb, clip, target, keep_uneven, shape=None):
    model = glb_pose.Model(glb)
    head = find_joint(model, "head")
    chains = legs(model)
    stand = "Standing" if "Standing" in model.clips else clip
    height = float(model.world(model.sample(stand, 0.0))[head][1, 3])
    before = bob_percent(model, clip, head, height)
    times = np.array(model.clip_times(clip))
    duration = float(times[-1])
    poses = [model.world(model.sample(clip, time)) for time in times]
    root = model.root_joints[0]
    pelvis = np.array([pose[root][1, 3] for pose in poses])
    # The loop's seam key repeats the first: the curve is periodic over [0, duration).
    curve = periodic(times[:-1], pelvis[:-1], duration) if np.isclose(pelvis[0], pelvis[-1], atol=1e-4) \
        else periodic(times, pelvis, duration)
    uniform = np.linspace(0.0, duration, 480, endpoint=False)
    mean = float(np.mean(curve(uniform)))
    even = 0.5 * (curve(times) + curve(times + 0.5 * duration))
    rest = pelvis - even
    even_uniform = 0.5 * (curve(uniform) + curve(uniform + 0.5 * duration))
    if shape:
        raw = periodic(uniform, leg_shape(model, clip, chains, root, uniform, shape), duration)
        synthetic = 0.5 * (raw(times) + raw(times + 0.5 * duration))
        synthetic_uniform = 0.5 * (raw(uniform) + raw(uniform + 0.5 * duration))
        # Unit-height synthetic bob around the authored mean, then scaled by the gain like an authored one.
        scale = 0.01 * height / max(np.ptp(synthetic_uniform), 1e-9)
        even = mean + (synthetic - synthetic_uniform.mean()) * scale
        even_uniform = mean + (synthetic_uniform - synthetic_uniform.mean()) * scale
    # Head travel follows the pelvis; the gain is refined below against the measured head.
    gain = 1.0 if target <= 0 else target / max(np.ptp(even_uniform) / height * 100.0, 1e-6)

    reach = {}
    for thigh, calf, foot in chains:
        reach[foot] = REACH * max(np.linalg.norm(pose[thigh][:3, 3] - pose[foot][:3, 3]) for pose in poses)

    def offsets_for(gain_value):
        wanted = mean + gain_value * (even - mean) + (rest if keep_uneven else 0.0)
        offsets = wanted - pelvis
        for _ in range(SMOOTH_PASSES):
            limit = np.full(len(times), np.inf)
            for index, pose in enumerate(poses):
                for thigh, calf, foot in chains:
                    v = pose[thigh][:3, 3] - pose[foot][:3, 3]
                    discriminant = v[1] ** 2 - v @ v + reach[foot] ** 2
                    if discriminant >= 0:
                        limit[index] = min(limit[index], -v[1] + np.sqrt(discriminant))
            clamped = np.minimum(offsets, limit)
            if np.allclose(clamped, offsets):
                break
            # Smooth the clamped curve (keys are close to evenly spaced) and clamp again: only ever lowers.
            offsets = np.minimum(smooth(clamped, max(3, (len(times) // 12) | 1)), clamped)
        if np.isclose(pelvis[0], pelvis[-1], atol=1e-4):
            offsets[-1] = offsets[0]
        return offsets

    offsets = offsets_for(gain)
    solved = solve(glb, clip, times, poses, chains, offsets)
    if target > 0:
        # Refinements: the head is not exactly the pelvis, and reach clamps cut peaks.
        for _ in range(4):
            after = bob_percent(glb_pose.Model(solved), clip, head, height)
            if abs(after - target) < 0.15:
                break
            gain = max(gain * target / max(after, 1e-6), 0.0 if shape else GAIN_MIN)
            offsets = offsets_for(gain)
            solved = solve(glb, clip, times, poses, chains, offsets)
    fixed = glb_pose.Model(solved)
    after = bob_percent(fixed, clip, head, height)
    drift = max(np.linalg.norm(fixed.world(fixed.sample(clip, time))[foot][:3, 3] - pose[foot][:3, 3])
                for time, pose in zip(times, poses) for _, _, foot in chains)
    print(f"{clip}: head bob {before:.1f}% -> {after:.1f}% of head height (gain {gain:.2f}, "
          f"{'uneven kept' if keep_uneven else 'steps evened'}{f', {shape} shape' if shape else ''}); foot drift {drift:.2e}; "
          f"pelvis moved {offsets.min():+.4f}..{offsets.max():+.4f}")
    return solved


def solve(glb, clip, times, poses, chains, offsets):
    """A copy of glb whose clip has the root joints moved by offsets and the legs solved to the original feet."""
    work = glb_pose.Glb.__new__(glb_pose.Glb)
    work.json = __import__("copy").deepcopy(glb.json)
    work.bin = bytearray(glb.bin)
    model = glb_pose.Model(work)
    floor_fix.shift_roots(model, clip, list(times), list(offsets))
    rotations = {joint: [] for chain in chains for joint in chain}
    for pose, offset in zip(poses, offsets):
        for thigh, calf, foot in chains:
            hip_old, knee_old, ankle = (pose[joint][:3, 3] for joint in (thigh, calf, foot))
            hip = hip_old + offset * UP
            upper = np.linalg.norm(knee_old - hip_old)
            lower = np.linalg.norm(ankle - knee_old)
            span_old = ankle - hip_old
            axis_old = span_old / np.linalg.norm(span_old)
            bend = knee_old - hip_old - np.dot(knee_old - hip_old, axis_old) * axis_old
            if np.linalg.norm(bend) < 1e-7:
                bend = rotation_of(pose[calf])[:, 1]
            bend /= np.linalg.norm(bend)
            span = ankle - hip
            distance = min(np.linalg.norm(span), (upper + lower) * 0.99999)
            axis = span / np.linalg.norm(span)
            bend_new = bend - np.dot(bend, axis) * axis
            bend_new /= np.linalg.norm(bend_new)
            along = (upper ** 2 - lower ** 2 + distance ** 2) / (2.0 * distance)
            knee = hip + along * axis + np.sqrt(max(upper ** 2 - along ** 2, 0.0)) * bend_new
            normal_old = np.cross(axis_old, bend)
            normal = np.cross(axis, bend_new)
            thigh_turn = frame(knee - hip, normal) @ frame(knee_old - hip_old, normal_old).T
            calf_turn = frame(ankle - knee, normal) @ frame(ankle - knee_old, normal_old).T
            thigh_world = thigh_turn @ rotation_of(pose[thigh])
            calf_world = calf_turn @ rotation_of(pose[calf])
            parent_world = rotation_of(pose[model.parent[thigh]])
            rotations[thigh].append(parent_world.T @ thigh_world)
            rotations[calf].append(thigh_world.T @ calf_world)
            rotations[foot].append(calf_world.T @ rotation_of(pose[foot]))
    for joint, matrices in rotations.items():
        quaternions = [glb_pose.matrix_quaternion(matrix) for matrix in matrices]
        for index in range(1, len(quaternions)):
            if np.dot(quaternions[index], quaternions[index - 1]) < 0:
                quaternions[index] = -quaternions[index]
        set_rotation(model, clip, joint, times, np.array(quaternions))
    return work


def set_rotation(model, clip, joint, times, quaternions):
    animation = model.glb.json["animations"][model.clips[clip]]
    sampler = {"input": model.glb.append_accessor(np.asarray(times)[:, None], "SCALAR"),
               "output": model.glb.append_accessor(quaternions, "VEC4"), "interpolation": "LINEAR"}
    animation["samplers"].append(sampler)
    index = len(animation["samplers"]) - 1
    for entry in animation["channels"]:
        if entry["target"]["node"] == joint and entry["target"]["path"] == "rotation":
            entry["sampler"] = index
            break
    else:
        animation["channels"].append({"sampler": index, "target": {"node": joint, "path": "rotation"}})


def prune_samplers(glb):
    """Drops samplers no channel uses (their accessors stay in the buffer)."""
    for animation in glb.json.get("animations", []):
        used = sorted({entry["sampler"] for entry in animation["channels"]})
        remap = {old: new for new, old in enumerate(used)}
        animation["samplers"] = [animation["samplers"][old] for old in used]
        for entry in animation["channels"]:
            entry["sampler"] = remap[entry["sampler"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--clip", nargs=2, action="append", required=True, metavar=("CLIP", "TARGET"))
    parser.add_argument("--keep-uneven", action="store_true")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("write the fixed GLB to a new path")
    glb = glb_pose.Glb(args.input)
    for clip, target in args.clip:
        value, _, shape = target.partition(":")
        if shape not in ("", "walk", "run"):
            raise SystemExit(f"{clip}: unknown shape {shape}")
        glb = reshape(glb, clip, float(value), args.keep_uneven, shape or None)
    prune_samplers(glb)
    glb.write(args.output)
    print(f"written {args.output}")


if __name__ == "__main__":
    main()
