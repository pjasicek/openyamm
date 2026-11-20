#!/usr/bin/env python3
"""Derive a slower, heavier walk from an installed creature's own walk clip, written as a new clip into a copy of the
GLB (only animations are added: meshes, skins, materials, variants and every existing clip are kept byte for byte).

    derive_walk.py <in.glb> <out.glb> <config.json> [clip names...]

The engine plays a walk by distance, one loop per stride, so a slower gait needs a shorter stride per loop, not a
retime. Per derived clip (config "clips"):

  stride_scale  the planted feet's travel per loop against the source walk's (the ankle paths' forward component
                about each foot's mean, as run_fit.py scales a run); the stance foot then slides back at that share of
                the source speed
  speed         the authored speed (model units per second) the clip is made for; the clip length is the measured
                source stride x stride_scale / speed, rounded to whole frames at the source frame rate. The source
                cycle is stretched uniformly over it (a giant's legs swing slower: a pendulum's period grows with the
                square root of its length)
  widen         metres added to each ankle's distance from the body's mid-line (a heavier, wider track)
  lift          share of the swing foot's lift above its planted height that is kept
  foot_pitch    share of the foot's rotation away from its flat planted rotation that is kept (heel strike, toe-off)
  pelvis        {"bob", "sway", "surge", "turn"}: shares of the pelvis's vertical, lateral and fore-aft motion about
                its cycle mean, and of its rotation about its mean rotation; "drop": metres the pelvis sits lower
                (bent knees); "settle": metres of extra dip after each heel strike (weight landing on the leg)
  lean          degrees of forward lean spread over the spine joints; the neck and head take it back, so the gaze stays
  arm_swing     share of each arm joint's rotation about its cycle mean that is kept (per side: "arm_swing_left",
                "arm_swing_right" override it)
  arm_out       degrees the upper arms turn away from the body about the forward axis (a bulky body's arms hang
                clear of the swaying hips and thighs)

The legs are re-solved by two-bone IK (hip from the new pelvis, knee in the source knee's direction, foot at its new
rotation); a leg that cannot reach lowers the pelvis for that frame (smoothed over the cycle). Each foot's lowest
vertex is then put back where the source has it relative to the floor (planted at the floor, the swing scaled by
lift), so the stride measurement and the floor rules see a planted foot. Model axes: glTF +Y up, the actor faces +Z.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "claude_shared" / "floor"))
sys.path.insert(0, str(HERE.parents[2] / "claude_shared" / "postprocess"))
import glb_pose  # noqa: E402
import stride_audit  # noqa: E402

UP = np.array([0.0, 1.0, 0.0])
CONTACT = 0.012  # a foot's lowest vertex within this many model units of its planted height is on the floor


def quat_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def quat_inv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])


def quat_axis(axis, degrees):
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / np.linalg.norm(axis)
    half = np.radians(degrees) / 2
    return np.concatenate([axis * np.sin(half), [np.cos(half)]])


def quat_between(a, b):
    """Smallest rotation taking direction a to direction b."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    cross = np.cross(a, b)
    dot = float(np.dot(a, b))
    if dot < -0.999999:
        raise ValueError("opposite directions")
    q = np.concatenate([cross, [1.0 + dot]])
    return q / np.linalg.norm(q)


def mean_quat(quats):
    reference = quats[0]
    total = np.zeros(4)
    for q in quats:
        total += q if np.dot(q, reference) >= 0 else -q
    return total / np.linalg.norm(total)


def rotate(q, v):
    return glb_pose.quaternion_matrix(q) @ v


def circular_smooth(values, radius):
    if radius <= 0:
        return values
    kernel = np.hanning(2 * radius + 3)[1:-1]
    kernel /= kernel.sum()
    padded = np.concatenate([values[-radius:], values, values[:radius]])
    return np.convolve(padded, kernel, mode="valid")


class Rig:
    def __init__(self, model, names):
        self.model = model
        self.nodes = model.glb.json["nodes"]
        self.index = {node.get("name"): i for i, node in enumerate(self.nodes)}
        self.names = names

    def node(self, name):
        return self.index[name]


def world_from_local(model, local):
    """World rotations (quaternions) and positions of every node."""
    matrices = model.world(local)
    rotations = [glb_pose.matrix_quaternion(matrix[:3, :3]) for matrix in matrices]
    return matrices, rotations


def foot_vertex_sets(model, rig, side):
    """Per LOD0 primitive: vertex indices dominated by this side's foot or toe joint."""
    joints = {rig.node(rig.names[side]["foot"]), rig.node(rig.names[side]["toe"])}
    sets = []
    for primitive in model.primitives:
        if not primitive["skinned"]:
            sets.append(np.zeros(0, dtype=np.int64))
            continue
        dominant = primitive["joints"][np.arange(len(primitive["positions"])), np.argmax(primitive["weights"], axis=1)]
        nodes = np.array([model.joints[j] for j in dominant])
        sets.append(np.nonzero(np.isin(nodes, list(joints)))[0])
    return sets


def foot_lows(model, local, vertex_sets):
    world = model.world(local)
    posed = model.skinned_positions(world)
    result = {}
    for side, sets in vertex_sets.items():
        lows = [points[indices, 1].min() for (points, _), indices in zip(posed, sets) if len(indices)]
        result[side] = float(min(lows))
    return result


def set_world_rotation(model, local, rotations_world, node, q_world):
    parent = model.parent[node]
    parent_q = rotations_world[parent]
    local[node][1] = quat_mul(quat_inv(parent_q), q_world)


def derive(model, rig, source, settings, fps, source_stride):
    names = rig.names
    source_times = model.clip_times(source)
    source_length = source_times[-1]
    stride_scale = settings["stride_scale"]
    length = source_stride * stride_scale / settings["speed"]
    frames = max(int(round(length * fps)), 8)
    length = frames / fps
    phases = np.arange(frames + 1) / frames
    samples = [model.sample(source, phase * source_length) for phase in phases[:-1]]
    sides = ("left", "right")
    pelvis = rig.node(names["pelvis"])
    pelvis_parent = model.parent[pelvis]

    # Source world data over the cycle.
    src_world, src_rot = zip(*(world_from_local(model, sample) for sample in samples))
    leg = {side: {key: rig.node(names[side][key]) for key in ("thigh", "calf", "foot", "toe")} for side in sides}
    vertex_sets = {side: foot_vertex_sets(model, rig, side) for side in sides}
    src_lows = [foot_lows(model, sample, vertex_sets) for sample in samples]
    planted_height = {side: min(lows[side] for lows in src_lows) for side in sides}
    pelvis_pos = np.array([world[pelvis][:3, 3] for world in src_world])
    pelvis_mean = pelvis_pos.mean(axis=0)
    pelvis_quat_mean = mean_quat([rotations[pelvis] for rotations in src_rot])
    ankles = {side: np.array([world[leg[side]["foot"]][:3, 3] for world in src_world]) for side in sides}
    ankle_mean = {side: ankles[side].mean(axis=0) for side in sides}
    mid_line = (ankle_mean["left"][0] + ankle_mean["right"][0]) / 2
    ankle_planted = {side: ankles[side][:, 1].min() for side in sides}
    # Flat foot: the source rotation at the middle of the planted phase (lowest ankle).
    flat = {}
    for side in sides:
        # The lowest ankle of the cycle: mid-stance, the foot flat on the floor (toe-off keeps the toes on the floor
        # with the ankle raised, so contact alone does not find it).
        middle = int(np.argmin(ankles[side][:, 1]))
        flat[side] = src_rot[middle][leg[side]["foot"]]
    arm_nodes = {side: [rig.node(name) for name in names[side]["arm"]] for side in sides}
    arm_mean = {node: mean_quat([sample[node][1] for sample in samples]) for side in sides for node in arm_nodes[side]}
    pelvis_cfg = settings.get("pelvis", {})
    bob, sway, surge = (pelvis_cfg.get(key, 1.0) for key in ("bob", "sway", "surge"))
    turn = pelvis_cfg.get("turn", 1.0)
    drop = pelvis_cfg.get("drop", 0.0)
    settle = pelvis_cfg.get("settle", 0.0)
    count = len(samples)

    # Heel strikes per foot (first planted frame after a swing): an extra settle dip of the pelvis follows each.
    settle_curve = np.zeros(count)
    if settle:
        for side in sides:
            planted = np.array([lows[side] - planted_height[side] < CONTACT for lows in src_lows])
            for i in range(count):
                if planted[i] and not planted[i - 1]:
                    span = max(int(round(0.35 * count / 2)), 2)
                    for j in range(span + 1):
                        settle_curve[(i + j) % count] += np.sin(np.pi * j / span) * settle
    lowering = np.zeros(count)

    def build(frame, extra_drop, ankle_dy):
        sample = {node: [part.copy() for part in trs] for node, trs in samples[frame].items()}
        world, rotations = src_world[frame], src_rot[frame]
        # Pelvis position and rotation.
        position = pelvis_pos[frame]
        offset = position - pelvis_mean
        new_position = pelvis_mean + np.array([sway * offset[0], bob * offset[1], surge * offset[2]])
        new_position[1] -= drop + settle_curve[frame] + extra_drop
        new_rotation = glb_pose.slerp(pelvis_quat_mean, rotations[pelvis], turn)
        parent_matrix = model.world({})[pelvis_parent] if pelvis_parent >= 0 else np.eye(4)
        parent_inverse = np.linalg.inv(parent_matrix)
        sample[pelvis][0] = (parent_inverse @ np.append(new_position, 1.0))[:3]
        parent_q = glb_pose.matrix_quaternion(parent_matrix[:3, :3] / np.linalg.norm(parent_matrix[:3, 0]))
        sample[pelvis][1] = quat_mul(quat_inv(parent_q), new_rotation)
        # Arms: swing about the cycle mean.
        for side in sides:
            share = settings.get(f"arm_swing_{side}", settings.get("arm_swing", 1.0))
            for node in arm_nodes[side]:
                sample[node][1] = glb_pose.slerp(arm_mean[node], sample[node][1], share)
            outward = settings.get("arm_out", 0.0)
            if outward:
                # The upper arm (second arm joint, after the clavicle) turned away from the body about the
                # forward axis: the hand clears the hip and thigh it would otherwise brush.
                upper_arm = arm_nodes[side][1]
                _, current = world_from_local(model, sample)
                sign = 1.0 if ankle_mean[side][0] > mid_line else -1.0
                world_q = quat_mul(quat_axis([0.0, 0.0, 1.0], sign * outward), current[upper_arm])
                sample[upper_arm][1] = quat_mul(quat_inv(current[model.parent[upper_arm]]), world_q)
        # Lean over the spine, taken back at the neck and head.
        lean = settings.get("lean", 0.0)
        if lean:
            spine = [rig.node(name) for name in names["spine"]]
            back = [rig.node(name) for name in names["neck_head"]]
            for nodes, total in ((spine, lean), (back, -lean)):
                for node in nodes:
                    _, current = world_from_local(model, sample)
                    parent_q = current[model.parent[node]]
                    delta = quat_axis([1.0, 0.0, 0.0], total / len(nodes))
                    world_q = quat_mul(delta, current[node])
                    sample[node][1] = quat_mul(quat_inv(parent_q), world_q)
        # Legs.
        new_world, new_rot = world_from_local(model, sample)
        reach_deficit = 0.0
        for side in sides:
            ids = leg[side]
            hip_src = world[ids["thigh"]][:3, 3]
            knee_src = world[ids["calf"]][:3, 3]
            ankle_src = world[ids["foot"]][:3, 3]
            hip = new_world[ids["thigh"]][:3, 3]
            target = ankle_src.copy()
            sign = 1.0 if ankle_mean[side][0] > mid_line else -1.0
            target[0] += sign * settings.get("widen", 0.0)
            target[2] = ankle_mean[side][2] + stride_scale * (ankle_src[2] - ankle_mean[side][2])
            target[1] = ankle_planted[side] + settings.get("lift", 1.0) * (ankle_src[1] - ankle_planted[side])
            target[1] += ankle_dy[side]
            upper = np.linalg.norm(knee_src - hip_src)
            lower = np.linalg.norm(ankle_src - knee_src)
            to_target = target - hip
            distance = np.linalg.norm(to_target)
            limit = 0.998 * (upper + lower)
            if distance > limit:
                # Lowering needed so this ankle is reachable (the vertical gap shrinks).
                horizontal = np.hypot(to_target[0], to_target[2])
                needed = np.sqrt(max(limit ** 2 - horizontal ** 2, 0.0))
                reach_deficit = max(reach_deficit, -to_target[1] - needed)
                target = hip + to_target / distance * limit
                to_target = target - hip
                distance = limit
            direction = to_target / distance
            cos_hip = np.clip((upper ** 2 + distance ** 2 - lower ** 2) / (2 * upper * distance), -1.0, 1.0)
            # Knee direction: the source knee's offset from its own hip-ankle line, carried onto the new line, with a
            # forward bias that takes over as the source leg straightens (its offset then has no stable direction).
            source_line = (ankle_src - hip_src) / np.linalg.norm(ankle_src - hip_src)
            pole = (knee_src - hip_src) - np.dot(knee_src - hip_src, source_line) * source_line
            pole = rotate(quat_between(source_line, direction), pole)
            facing = rotate(new_rotation, rotate(quat_inv(pelvis_quat_mean), np.array([0.0, 0.0, 1.0])))
            pole = pole + 0.02 * facing
            pole -= np.dot(pole, direction) * direction
            pole /= np.linalg.norm(pole)
            knee = hip + upper * (cos_hip * direction + np.sqrt(1 - cos_hip ** 2) * pole)
            # Thigh: the parent change already moved it (new_rot), then the smallest swing to the new knee.
            thigh_q = new_rot[ids["thigh"]]
            thigh_now = rotate(quat_mul(thigh_q, quat_inv(rotations[ids["thigh"]])), knee_src - hip_src)
            thigh_new = quat_mul(quat_between(thigh_now, knee - hip), thigh_q)
            calf_q = quat_mul(quat_mul(thigh_new, quat_inv(rotations[ids["thigh"]])), rotations[ids["calf"]])
            calf_now = rotate(quat_mul(calf_q, quat_inv(rotations[ids["calf"]])), ankle_src - knee_src)
            calf_new = quat_mul(quat_between(calf_now, target - knee), calf_q)
            foot_new = glb_pose.slerp(flat[side], rotations[ids["foot"]], settings.get("foot_pitch", 1.0))
            set_world_rotation(model, sample, new_rot, ids["thigh"], thigh_new)
            local_calf = quat_mul(quat_inv(thigh_new), calf_new)
            sample[ids["calf"]][1] = local_calf
            sample[ids["foot"]][1] = quat_mul(quat_inv(calf_new), foot_new)
        return sample, reach_deficit

    zero = {side: 0.0 for side in sides}
    # Pass 1: how much each frame must lower the pelvis for the legs to reach.
    deficits = np.array([build(frame, 0.0, zero)[1] for frame in range(count)])
    lowering = circular_smooth(np.maximum.reduce([np.roll(deficits, shift) for shift in (-2, -1, 0, 1, 2)]), 3)
    lowering = np.maximum(lowering, deficits)
    # Pass 2-4: each foot's lowest vertex back to the source's height above the floor (swing scaled by lift).
    ankle_dy = [dict(zero) for _ in range(count)]
    for _ in range(3):
        for frame in range(count):
            sample, _ = build(frame, lowering[frame], ankle_dy[frame])
            lows = foot_lows(model, sample, vertex_sets)
            for side in sides:
                source_above = src_lows[frame][side] - planted_height[side]
                wanted = planted_height[side] + settings.get("lift", 1.0) * source_above
                if source_above < CONTACT:
                    wanted = src_lows[frame][side]
                ankle_dy[frame][side] += wanted - lows[side]
    poses = []
    for frame in range(count):
        sample, deficit = build(frame, lowering[frame], ankle_dy[frame])
        poses.append(sample)
    poses.append(poses[0])
    info = {"frames": frames, "length": length, "max_lowering": float(lowering.max()),
            "max_ankle_correction": float(max(abs(v) for dy in ankle_dy for v in dy.values()))}
    return phases * length, poses, info


def write_clip(glb, model, source, name, times, poses):
    document = glb.json
    source_animation = document["animations"][model.clips[source]]
    time_accessor = glb.append_accessor(np.asarray(times)[:, None], "SCALAR")
    hold_accessor = glb.append_accessor(np.array([[0.0], [times[-1]]]), "SCALAR")
    channels, samplers = [], []
    for channel in source_animation["channels"]:
        node, path = channel["target"]["node"], channel["target"]["path"]
        sampler = source_animation["samplers"][channel["sampler"]]
        slot = {"translation": 0, "rotation": 1, "scale": 2}[path]
        kind = "VEC4" if path == "rotation" else "VEC3"
        if sampler.get("interpolation") == "STEP":
            values = glb.accessor(sampler["output"])
            entry = {"input": hold_accessor, "interpolation": "STEP",
                     "output": glb.append_accessor(values[[0, -1]], kind)}
        else:
            values = np.array([pose[node][slot] if node in pose else model.rest[node][slot] for pose in poses])
            if path == "rotation":
                for i in range(1, len(values)):
                    if np.dot(values[i], values[i - 1]) < 0:
                        values[i] = -values[i]
                values /= np.linalg.norm(values, axis=1, keepdims=True)
            entry = {"input": time_accessor, "interpolation": "LINEAR", "output": glb.append_accessor(values, kind)}
        samplers.append(entry)
        channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
    document["animations"] = [animation for animation in document["animations"] if animation.get("name") != name]
    document["animations"].append({"name": name, "channels": channels, "samplers": samplers})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("clips", nargs="*")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    glb = glb_pose.Glb(args.input)
    model = glb_pose.Model(glb)
    rig = Rig(model, config["joints"])
    for name, settings in config["clips"].items():
        if args.clips and name not in args.clips:
            continue
        source = settings.get("source", config.get("source", "Walking"))
        fps = settings.get("fps", config.get("fps", 30))
        source_model = glb_pose.Model(glb_pose.Glb(args.input))
        source_stride, _ = stride_audit.measure(source_model, source)
        times, poses, info = derive(model, Rig(source_model, config["joints"]), source, settings, fps, source_stride)
        write_clip(glb, model, source, name, times, poses)
        print(f"{name}: from {source} (stride {source_stride:.3f}) x{settings['stride_scale']}, {info['frames']} frames "
              f"= {info['length']:.3f} s for {settings['speed']} u/s; pelvis lowered up to {info['max_lowering']:.3f}, "
              f"ankle corrections up to {info['max_ankle_correction']:.3f}")
    glb.write(args.output)
    check = glb_pose.Model(glb_pose.Glb(args.output))
    for name in config["clips"]:
        if name in check.clips and (not args.clips or name in args.clips):
            measured, share = stride_audit.measure(check, name)
            feet = stride_audit.measure_feet(check, name)
            length = check.clip_times(name)[-1]
            print(f"  {name}: measured stride {measured:.4f} (feet {feet:.4f}, contact {share:.0%}), length "
                  f"{length:.4f} s, authored speed {measured / length:.3f}")
    print(f"written {args.output}")


if __name__ == "__main__":
    main()
