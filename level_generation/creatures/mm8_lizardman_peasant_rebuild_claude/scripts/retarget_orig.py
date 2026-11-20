#!/usr/bin/env python3
"""Replace the lizardman peasant's clips by world-rotation retargets of other rigs' clips (follow-up 2, 2026-11-12).

    retarget_orig.py <target.glb> <out.glb> <config.json>

The target is the installed GLB (MM9 LIZARDORC skeleton, `Bip01 *`). Sources are GLBs on other rigs: the model before
the 2026-11-11 rebuild (Meshy auto-rig: Hips, Spine02, LeftArm ...) and the humanoid set (`B_*`). Per mapped bone the
target's bind frame is first swung so its bone direction (to a child joint, or the mean of several) matches the
source's bind direction; the fixed offset O = S_bind^-1 @ swing @ T_bind then gives T(f) = S(f) @ O, so every bone
points where the source bone points and keeps the source twist (mm6_ttn1_claude/scripts/retarget_fbx.py, in numpy on
the GLB). Bones without a direction (pelvis, head, feet) copy the source's world rotation change from its bind.
The pelvis moves by the source hips' displacement from bind, scaled by the ratio of the pelvis heights above the floor.
Joints the source does not drive (fingers, MM9's jaw, tongue, tail and cutlass bones) keep the local rotation of one
reference pose: a clip of the target GLB at a time (`hold_from`), the MM9 mitten curl the 2026-11-11 build gave the
four-digit hands. Optional leg IK (`ik_feet`) places the ankles at the source ankles' displacement from bind, scaled,
with the knee in the FK leg plane, so planted feet stay planted on the different leg proportions.

Only the `animations` change (new accessors are appended); meshes, skins, materials and variants are kept as they
are. Every clip is written with a translation and a rotation channel for every joint, LINEAR, sign-continuous.
"""
import fnmatch
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "claude_shared" / "floor"))
from glb_pose import Glb, Model, matrix_quaternion, quaternion_matrix, slerp, trs_matrix  # noqa: E402

SIDES = (("L", "Left", "L"), ("R", "Right", "R"))


def meshy_map():
    """Target joint -> (source joint, [target direction children], [source direction children]
    [, (target roll from, to), (source roll from, to)]). With a roll pair (the hands: across the knuckles, little
    finger to index finger) the bind frames are matched on both axes, so the source's palm facing carries over too, not
    only the bone direction. The thumb is no roll reference: the rebuild's left thumb lies almost along the hand."""
    result = {
        "Bip01 Pelvis": ("Hips", [], []),
        "Bip01 Spine": ("Hips", [], []),
        "Bip01 Spine1": ("Spine02", ["Bip01 Spine2"], ["Spine01"]),
        "Bip01 Spine2": ("Spine01", ["Bip01 Spine3"], ["Spine"]),
        "Bip01 Spine3": ("Spine", ["Bip01 Neck"], ["neck"]),
        "Bip01 Neck": ("neck", ["Bip01 Head"], ["Head"]),
        "Bip01 Head": ("Head", [], []),
    }
    for t, s, _ in SIDES:
        b = f"Bip01 {t} "
        result.update({
            b + "Clavicle": (s + "Shoulder", [b + "UpperArm"], [s + "Arm"]),
            b + "UpperArm": (s + "Arm", [b + "Forearm"], [s + "ForeArm"]),
            b + "Forearm": (s + "ForeArm", [b + "Hand"], [s + "Hand"]),
            b + "Hand": (s + "Hand", [b + "Finger1", b + "Finger2", b + "Finger3"],
                         [s + "Digit1", s + "Digit2", s + "Digit3"], (b + "Finger3", b + "Finger1"),
                         (s + "Digit2", s + "Digit1")),
            b + "Thigh": (s + "UpLeg", [b + "Calf"], [s + "Leg"]),
            b + "Calf": (s + "Leg", [b + "Foot"], [s + "Foot"]),
            b + "Foot": (s + "Foot", [], []),
        })
    return result


def hs_map():
    """The humanoid set's B_* rig (three spine joints, no neck chain split)."""
    result = {
        "Bip01 Pelvis": ("B_Pelvis", [], []),
        "Bip01 Spine": ("B_Pelvis", [], []),
        "Bip01 Spine1": ("B_Spine", ["Bip01 Spine2"], ["B_Spine1"]),
        "Bip01 Spine2": ("B_Spine1", ["Bip01 Spine3"], ["B_Spine2"]),
        "Bip01 Spine3": ("B_Spine2", ["Bip01 Neck"], ["B_Neck"]),
        "Bip01 Neck": ("B_Neck", ["Bip01 Head"], ["B_Head"]),
        "Bip01 Head": ("B_Head", [], []),
    }
    for t, _, s in SIDES:
        b, c = f"Bip01 {t} ", f"B_{s}_"
        result.update({
            b + "Clavicle": (c + "Clavicle", [b + "UpperArm"], [c + "UpperArm"]),
            b + "UpperArm": (c + "UpperArm", [b + "Forearm"], [c + "Forearm"]),
            b + "Forearm": (c + "Forearm", [b + "Hand"], [c + "Hand"]),
            b + "Hand": (c + "Hand", [b + "Finger1", b + "Finger2", b + "Finger3"],
                         [c + "Finger1", c + "Finger2", c + "Finger3"], (b + "Finger3", b + "Finger1"),
                         (c + "Finger4", c + "Finger1")),
            b + "Thigh": (c + "Thigh", [b + "Calf"], [c + "Calf"]),
            b + "Calf": (c + "Calf", [b + "Foot"], [c + "Foot"]),
            b + "Foot": (c + "Foot", [], []),
        })
    return result


MAPS = {"meshy": meshy_map, "hs": hs_map}


def rotation(matrix):
    """Rotation part of a world matrix with any uniform or per-axis scale."""
    r = matrix[:3, :3] / np.linalg.norm(matrix[:3, :3], axis=0)[None, :]
    u, _, vt = np.linalg.svd(r)
    return u @ vt


def swing(a, b):
    """Smallest rotation matrix taking direction a onto direction b."""
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    axis = np.cross(a, b)
    s, c = np.linalg.norm(axis), float(np.dot(a, b))
    if s < 1e-9:
        return np.eye(3)
    k = axis / s
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    angle = np.arctan2(s, c)
    return np.eye(3) + np.sin(angle) * kx + (1 - np.cos(angle)) * kx @ kx


def frame(primary, secondary):
    """Orthonormal frame (columns) from a primary direction and a secondary one projected off it."""
    x = primary / np.linalg.norm(primary)
    y = secondary - np.dot(secondary, x) * x
    y /= np.linalg.norm(y)
    return np.stack([x, y, np.cross(x, y)], axis=1)


def yaw_matrix(degrees):
    a = np.radians(degrees)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


def lowest_bind(model):
    posed = model.skinned_positions(model.world({}))
    return min(float(points[:, 1].min()) for points, _ in posed)


class Source:
    def __init__(self, spec):
        self.glb = Glb(spec["glb"])
        self.model = Model(self.glb)
        self.names = {node.get("name"): i for i, node in enumerate(self.glb.json["nodes"])}
        self.map = MAPS[spec["map"]]()
        self.frame = yaw_matrix(spec.get("yaw", 0.0))
        self.bind = self.model.world({})
        self.floor = spec.get("floor")
        if self.floor is None:
            self.floor = lowest_bind(self.model) if self.model.primitives else 0.0

    def world(self, clip, time):
        return self.model.world(self.model.sample(clip, time))

    def duration(self, clip):
        return self.model.clip_times(clip)[-1]


def two_bone_ik(hip, knee, ankle, goal):
    """New knee and ankle positions for a hip-knee-ankle chain reaching for goal, knee kept in the FK plane."""
    a, b = np.linalg.norm(knee - hip), np.linalg.norm(ankle - knee)
    d_vec = goal - hip
    d = np.clip(np.linalg.norm(d_vec), abs(a - b) + 1e-4, a + b - 1e-4)
    axis = d_vec / np.linalg.norm(d_vec)
    pole = knee - hip
    pole = pole - np.dot(pole, axis) * axis
    if np.linalg.norm(pole) < 1e-6:
        pole = np.cross(axis, [1.0, 0.0, 0.0])
    pole /= np.linalg.norm(pole)
    x = (a * a - b * b + d * d) / (2 * d)
    h = np.sqrt(max(a * a - x * x, 0.0))
    new_knee = hip + axis * x + pole * h
    return new_knee, hip + axis * d


def retarget(spec, src, target, tnames, order, tbind, tfloor, pelvis, root, held_local):
    """Frames (local TRS per joint) of one source clip retargeted onto the target."""
    clip = spec["clip"]
    start, end = spec.get("trim", [0.0, src.duration(clip)])
    rate = spec.get("rate", 1.0)
    fps = spec.get("fps", 60)
    duration = (end - start) / rate
    count = max(2, int(round(duration * fps)) + 1)
    times = np.linspace(0.0, duration, count)
    R = src.frame
    # Offsets per mapped target joint, from the two bind poses.
    offsets = {}
    for tj, (sj, tchildren, schildren, *roll) in src.map.items():
        if tj not in tnames or sj not in src.names:
            continue
        ti, si = tnames[tj], src.names[sj]
        rs = R @ rotation(src.bind[si])
        rt = rotation(tbind[ti])
        sw = np.eye(3)
        if tchildren and not all(c in src.names for c in schildren):
            # A source without finger joints (Meshy library rigs): the hand continues its forearm in both binds.
            tp, sp = target.parent[ti], src.model.parent[si]
            tdir = tbind[ti][:3, 3] - tbind[tp][:3, 3]
            sdir = R @ (src.bind[si][:3, 3] - src.bind[sp][:3, 3])
            sw = swing(tdir, sdir)
        elif tchildren and spec.get("swing", True):
            tdir = np.mean([tbind[tnames[c]][:3, 3] for c in tchildren], axis=0) - tbind[ti][:3, 3]
            sdir = R @ (np.mean([src.bind[src.names[c]][:3, 3] for c in schildren], axis=0)
                        - src.bind[si][:3, 3])
            sw = swing(tdir, sdir)
            if roll and spec.get("roll", True):
                (ta, tb), (sa, sb) = roll
                tsec = tbind[tnames[tb]][:3, 3] - tbind[tnames[ta]][:3, 3]
                ssec = R @ (src.bind[src.names[sb]][:3, 3] - src.bind[src.names[sa]][:3, 3])
                sw = frame(sdir, ssec) @ frame(tdir, tsec).T
        offsets[ti] = (si, rs.T @ sw @ rt)
    s_hips = src.names[src.map["Bip01 Pelvis"][0]]
    s_hip_h = src.bind[s_hips][1, 3] - src.floor
    t_hip_h = tbind[pelvis][1, 3] - tfloor
    k = spec.get("height_scale", t_hip_h / s_hip_h)
    travel = np.array(spec.get("travel", [1.0, 1.0, 1.0]))
    frames_local = []
    for time in times:
        st = start + time * rate
        sw_world = src.world(clip, st)
        world = {}
        local = {}
        for j in order:
            parent = target.parent[j]
            pworld = world[parent] if parent in world else (
                tbind[parent] if parent >= 0 else np.eye(4))
            if j in offsets:
                si, offset = offsets[j]
                rot = R @ rotation(sw_world[si]) @ offset
                if j == pelvis:
                    disp = R @ (sw_world[s_hips][:3, 3] - src.bind[s_hips][:3, 3]) * k * travel
                    pos = tbind[pelvis][:3, 3] + disp
                    pos[1] += -tfloor - spec.get("floor_shift", 0.0)
                else:
                    pos = (pworld @ np.append(target.rest[j][0], 1.0))[:3]
                m = np.eye(4)
                m[:3, :3] = rot
                m[:3, 3] = pos
                lm = np.linalg.inv(pworld) @ m
                q = matrix_quaternion(rotation(lm))
                t_local = target.rest[j][0] if j != pelvis else lm[:3, 3]
                local[j] = (np.array(t_local), q, target.rest[j][2])
            elif j == root:
                local[j] = (np.zeros(3), target.rest[j][1], target.rest[j][2])
            else:
                local[j] = tuple(np.array(v) for v in held_local[j])
            world[j] = pworld @ trs_matrix(*local[j])
        if spec.get("ik_feet"):
            for t, _, _ in SIDES:
                hip_i, knee_i, ankle_i = (tnames[f"Bip01 {t} {n}"] for n in ("Thigh", "Calf", "Foot"))
                s_ankle = src.names[src.map[f"Bip01 {t} Foot"][0]]
                goal = tbind[ankle_i][:3, 3] + R @ (sw_world[s_ankle][:3, 3] - src.bind[s_ankle][:3, 3]) * k * travel
                goal[1] += -tfloor - spec.get("floor_shift", 0.0)
                hip, knee, ankle = (world[i][:3, 3] for i in (hip_i, knee_i, ankle_i))
                new_knee, new_ankle = two_bone_ik(hip, knee, ankle, goal)
                foot_world = world[ankle_i].copy()
                for chain_i, child_i, child_new in ((hip_i, knee_i, new_knee), (knee_i, ankle_i, new_ankle)):
                    cur = world[chain_i]
                    child_now = world[child_i][:3, 3]
                    m = cur.copy()
                    m[:3, :3] = swing(child_now - cur[:3, 3], child_new - cur[:3, 3]) @ rotation(cur)
                    pw = world[target.parent[chain_i]]
                    q = matrix_quaternion(rotation(np.linalg.inv(pw) @ m))
                    local[chain_i] = (local[chain_i][0], q, local[chain_i][2])
                    world[chain_i] = pw @ trs_matrix(*local[chain_i])
                    world[child_i] = world[chain_i] @ trs_matrix(*local[child_i])
                # The foot keeps its FK world rotation.
                q = matrix_quaternion(rotation(np.linalg.inv(world[knee_i]) @ foot_world))
                local[ankle_i] = (local[ankle_i][0], q, local[ankle_i][2])
                world[ankle_i] = world[knee_i] @ trs_matrix(*local[ankle_i])
        frames_local.append(local)
    line = (f"{spec['src']}:{clip} {start:.3f}-{end:.3f}s x{rate} -> {duration:.4f}s, {count} keys, k={k:.3f}")
    return times, frames_local, line


def layer(spec, produced, target, order, pelvis):
    """A clip of the target GLB layered over the first frame of an already produced role, with gains: per joint the
    clip's rotation change from its own first key, taken in the parent's space, is applied at `gain` to the base pose
    (L = slerp(I, D, gain) @ L_base, D = L(t) @ L(0)^-1); the pelvis translation change is applied at its gain too.
    Joints matching no gain pattern keep the base pose. For the attack: MM9's claw rake on the upright stance."""
    clip = spec["clip"]
    base = produced[spec["base"]][0]
    keys = target.clip_times(clip)
    duration = keys[-1]
    count = max(2, int(round(duration * spec.get("fps", 60))) + 1)
    times = np.linspace(0.0, duration, count)
    first = target.sample(clip, 0.0)

    def gain(name):
        for pattern, value in spec["gains"]:
            if fnmatch.fnmatch(name, pattern):
                return value
        return 0.0

    names = {j: target.glb.json["nodes"][j].get("name", "") for j in order}
    frames_local = []
    for time in times:
        pose = target.sample(clip, time)
        local = {}
        for j in order:
            t_base, q_base, s_base = base[j]
            g = gain(names[j])
            if g == 0.0:
                local[j] = (np.array(t_base), np.array(q_base), np.array(s_base))
                continue
            q0 = first.get(j, target.rest[j])[1]
            q1 = pose.get(j, target.rest[j])[1]
            d = quaternion_matrix(q1) @ quaternion_matrix(q0).T
            dq = matrix_quaternion(d)
            dq = slerp(np.array([0.0, 0.0, 0.0, 1.0]), dq, g)
            q = matrix_quaternion(quaternion_matrix(dq) @ quaternion_matrix(q_base))
            t = np.array(t_base)
            if j == pelvis:
                t = t + g * (pose.get(j, target.rest[j])[0] - first.get(j, target.rest[j])[0]) \
                    * spec.get("translation_gain", 1.0)
            local[j] = (t, q, np.array(s_base))
        frames_local.append(local)
    return times, frames_local, f"layer {clip} over {spec['base']} -> {duration:.4f}s, {count} keys"


def main():
    target_path, out_path, config_path = sys.argv[1:4]
    config = json.loads(Path(config_path).read_text())
    glb = Glb(target_path)
    target = Model(glb)
    nodes = glb.json["nodes"]
    tnames = {node.get("name"): i for i, node in enumerate(nodes)}
    joints = list(target.joints)
    joint_set = set(joints)
    order = [i for i in target.order if i in joint_set]
    tbind = target.world({})
    tfloor = lowest_bind(target)
    pelvis = tnames["Bip01 Pelvis"]
    root = tnames["Scene Root"]
    sources = {key: Source(spec) for key, spec in config["sources"].items()}

    hold = target.sample(*config["hold_from"]) if config.get("hold_from") else {}
    held_local = {j: hold.get(j, target.rest[j]) for j in joints}

    animations, report, produced = [], [], {}
    for role, spec in config["roles"].items():
        if spec["src"] == "layer":
            times, frames_local, line = layer(spec, produced, target, order, pelvis)
        else:
            times, frames_local, line = retarget(spec, sources[spec["src"]], target, tnames, order, tbind, tfloor,
                                                 pelvis, root, held_local)
        produced[role] = frames_local
        # Build channels.
        animation = {"name": role, "samplers": [], "channels": []}
        time_accessor = glb.append_accessor(times.reshape(-1, 1).astype(np.float32), "SCALAR")
        for j in order:
            trans = np.array([f[j][0] for f in frames_local])
            rots = np.array([f[j][1] for f in frames_local])
            for i in range(1, len(rots)):
                if np.dot(rots[i], rots[i - 1]) < 0:
                    rots[i] = -rots[i]
            for path, values, kind in (("translation", trans, "VEC3"), ("rotation", rots, "VEC4")):
                animation["samplers"].append({"input": time_accessor, "output": glb.append_accessor(values, kind),
                                              "interpolation": "LINEAR"})
                animation["channels"].append({"sampler": len(animation["samplers"]) - 1,
                                              "target": {"node": j, "path": path}})
        animations.append(animation)
        report.append(f"{role}: {line}")
    glb.json["animations"] = animations
    glb.write(out_path)
    for line in report:
        print("RETARGET", line)


if __name__ == "__main__":
    main()
