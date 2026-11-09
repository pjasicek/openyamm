"""Dress shape fix (user review 2026-11-01: "really inflated and doesn't copy her hips/body at all from the stomach
down"). Animation only: mesh, UVs, weights and LODs stay, so every LOD and shadow mesh follows.

Cause (measured on the installed GLB): the rest mesh is close to the HD master's A-line (skirt 0.39 m wide at 0.85 m
height against the master's 0.37 m, flaring to 0.68 m at 0.3 m). The idle clips balloon it to 0.56 m right under the
belt: in Standing (and Fidget and Hit, which start from it) the hands hang at x = +-0.21 m, on the rest skirt surface,
and the production cloth sim (mm7_m342_claude/scripts/robe_sim.py) pushes every chain point out of the forearm and hand
capsules (radius 0.045 + margin 0.012) along the chain's outward direction, so the side chains stand 8 cm out. The walk
was retargeted with the arms abducted 6 deg (hands at +-0.24 m) and keeps the rest width.

Fix, per clip in CLIPS, at every key of its rotation channels:
1. Arms: both upper arms abducted by ARM_DEG about the chest's forward axis (the walk retarget's ARM_ABDUCT_DEG), so
   the hands hang outside the slim skirt.
2. Chains: each chain point (the four joints below the root and the last bone's tail) is pulled back toward the rest
   bell hung from its posed root in the pelvis's heading (the sim's own target) wherever it stands more than E_ALLOW
   outside it along the chain's outward direction. The leg capsules of the sim (LEG_R 1.3, same radius rule) still
   apply: a point that would enter one keeps as much of its push as it needs. Segments stay rigid (bone lengths), and
   each bone takes the minimal rotation that aims it at its corrected joint.
Translation, scale, every other bone and every other clip are untouched.

Usage: dress_fix.py <in glb> <out glb> [arm deg 6] -> also prints per clip the largest pull and the skirt widths."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glb_pose as G  # noqa: E402
from glb import Glb  # noqa: E402

CLIPS = ('Standing', 'Fidget', 'Hit')
ARM_DEG = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
E_ALLOW = 0.01
LEG_R, LEG_FLOOR, MARGIN = 1.3, 0.06, 0.012
CAPS = [('B_L_Thigh', 'B_L_Calf', 0.065), ('B_R_Thigh', 'B_R_Calf', 0.065), ('B_L_Calf', 'B_L_Foot', 0.05),
        ('B_R_Calf', 'B_R_Foot', 0.05), ('B_L_Thigh', 'B_R_Thigh', 0.07), ('B_L_Foot', 'B_L_Toe0', 0.05),
        ('B_R_Foot', 'B_R_Toe0', 0.05)]


def rot_axis(axis, angle):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K


def rot_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    s, c = np.linalg.norm(v), float(a @ b)
    if s < 1e-12:
        return np.eye(3)
    return rot_axis(v, np.arctan2(s, c))


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t * ab))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    g = G.Glb(src)
    m = G.Model(g)
    nodes = g.json['nodes']
    idx = {n.get('name'): i for i, n in enumerate(nodes)}
    joint_index = {n: k for k, n in enumerate(nodes[j]['name'] for j in m.joints)}
    rest_world = {nodes[j]['name']: np.linalg.inv(m.inverse_binds[k]) for k, j in enumerate(m.joints)}
    chains = sorted({n[:7] for n in idx if n.startswith('Robe_')})
    bones = {c: [f'{c}_{k}' for k in range(4)] for c in chains}
    seg = {c: [float(np.linalg.norm(nodes[idx[b]]['translation'])) for b in bones[c][1:]] for c in chains}
    for c in chains:
        seg[c].append(seg[c][-1])                                     # last bone: as long as the one above it
    pel0 = rest_world['B_Pelvis'][:3, 3]
    rest_pts = {}
    out_dir = {}
    for c in chains:
        heads = [rest_world[b][:3, 3] for b in bones[c]]
        tail = (rest_world[bones[c][3]] @ np.array([0, seg[c][3], 0, 1.0]))[:3]
        rest_pts[c] = np.array(heads + [tail])
        o = heads[0] - pel0
        o[1] = 0
        out_dir[c] = o / np.linalg.norm(o)
    rest_caps = [(rest_world[a][:3, 3], rest_world[b][:3, 3]) for a, b, _ in CAPS]
    allrest = np.vstack([rest_pts[c][1:] for c in chains])
    radii = []
    for (a, b), (_, _, r) in zip(rest_caps, CAPS):
        d = min(seg_dist(p, a, b) for p in allrest)
        radii.append(min(r * LEG_R, max(LEG_FLOOR, d - MARGIN - 0.004)))

    out = Glb(src)
    doc = out.doc
    report = {'arm_deg': ARM_DEG, 'e_allow_m': E_ALLOW, 'leg_capsule_radii': [round(r, 3) for r in radii]}
    for clip in CLIPS:
        anim = doc['animations'][m.clips[clip]]
        rot_ch = {nodes[c['target']['node']]['name']: c for c in anim['channels'] if c['target']['path'] == 'rotation'}
        names = ['B_L_UpperArm', 'B_R_UpperArm'] + [b for c in chains for b in bones[c]]
        inputs = {anim['samplers'][rot_ch[n]['sampler']]['input'] for n in names}
        assert len(inputs) == 1, f'{clip}: rotation channels on different inputs'
        times = out.accessor(inputs.pop())
        new_q = {n: out.accessor(anim['samplers'][rot_ch[n]['sampler']]['output']).astype(np.float64) for n in names}
        pull_max, leg_kept = 0.0, 0
        for ti, t in enumerate(times):
            local = m.sample(clip, float(t))
            world = m.world(local)
            # 1. arms
            spine = world[idx['B_Spine2']][:3, :3] @ rest_world['B_Spine2'][:3, :3].T
            forward = spine @ np.array([0.0, 0.0, 1.0])
            for name, sign in (('B_L_UpperArm', 1.0), ('B_R_UpperArm', -1.0)):
                i = idx[name]
                R = rot_axis(forward, sign * np.radians(ARM_DEG)) @ world[i][:3, :3]
                lr = world[m.parent[i]][:3, :3].T @ R
                q = G.matrix_quaternion(np.block([[lr, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]))
                local[i][1] = np.asarray(q, np.float64)
                new_q[name][ti] = local[i][1]
            world = m.world(local)
            # 2. chains
            pel = world[idx['B_Pelvis']][:3, :3] @ rest_world['B_Pelvis'][:3, :3].T
            f = pel @ np.array([0.0, 0.0, 1.0])
            Ry = rot_axis(np.array([0.0, 1.0, 0.0]), np.arctan2(f[0], f[2]))
            caps = [(world[idx[a]][:3, 3], world[idx[b]][:3, 3]) for a, b, _ in CAPS]
            for c in chains:
                W = [world[idx[b]].copy() for b in bones[c]]
                pts = [w[:3, 3] for w in W] + [(W[3] @ np.array([0, seg[c][3], 0, 1.0]))[:3]]
                u0 = Ry @ out_dir[c]
                target = pts[0] + (rest_pts[c] - rest_pts[c][0]) @ Ry.T
                fixed = [pts[0]]
                for k in range(1, 5):
                    x = pts[k].copy()
                    e = float((x - target[k]) @ u0)
                    if e > E_ALLOW:
                        pull = e - E_ALLOW
                        x = x - u0 * pull
                        for step in np.arange(0.0, pull + 1e-9, 0.002):   # the legs keep the push they need
                            y = x + u0 * step
                            if all(seg_dist(y, a, b) >= r + MARGIN for (a, b), r in zip(caps, radii)):
                                if step > 0:
                                    leg_kept += 1
                                x = y
                                break
                        else:
                            x = pts[k]
                        pull_max = max(pull_max, float(np.linalg.norm(x - pts[k])))
                    d = x - fixed[-1]
                    fixed.append(fixed[-1] + d / np.linalg.norm(d) * seg[c][k - 1 if k < 4 else 3])
                # re-aim the bones
                parent_R = world[idx['B_Pelvis']][:3, :3]
                for k, b in enumerate(bones[c]):
                    i = idx[b]
                    Rk = parent_R @ G.quaternion_matrix(local[i][1])[:3, :3]
                    head = fixed[k]
                    R = rot_between(Rk[:, 1], fixed[k + 1] - head) @ Rk
                    lr = parent_R.T @ R
                    q = G.matrix_quaternion(np.block([[lr, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]))
                    q = np.asarray(q, np.float64)
                    if q @ new_q[b][ti] < 0:
                        q = -q
                    new_q[b][ti] = q
                    parent_R = R
        for n in names:
            out.set_accessor(anim['samplers'][rot_ch[n]['sampler']]['output'], new_q[n].astype(np.float32))
        report[clip] = {'keys': int(len(times)), 'largest_pull_m': round(pull_max, 3), 'leg_push_kept_points': leg_kept}
    out.save(dst)
    print('DRESS_FIX', json.dumps(report))


if __name__ == '__main__':
    main()
