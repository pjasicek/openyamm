#!/usr/bin/env python3
"""Re-aim one arm of a clip through authored direction keys (follow-up 2, 2026-11-12: Cleric Sun's Attack, whose
right upper arm pointed straight forward under the sun mantle while the forearm went out sideways from the chest).

    arm_aim.py <in.glb> <out.glb> <job.json>

Job: {"clip": "Attack", "side": "R", "rate": 60,
      "weight": [t0, t1, t2, t3],             blend from the clip (0) to the keys (1): eased in t0..t1, out t2..t3
      "keys": [{"t": .., "ua": [x, y, z], "fa": [x, y, z], "fingers": [x, y, z], "palm": [x, y, z]}, ...]}
Directions are in the chest frame (B_Spine2 at Standing frame 0; the bodies face +Z, left +X, up +Y): ua the upper
arm (shoulder -> elbow), fa the forearm (elbow -> wrist). Between keys the directions are slerped with smoothstep.
`fingers` and `palm` (optional, chest frame): the hand's finger direction and palm normal, blended in with the
weight; the forearm takes the hand's roll (its target keeps Standing's wrist relation, turned onto `fa`) and the
forearm twist bone blends to its Standing local, so the wrist does not twist. Each bone takes the least rotation from its clip direction to the blended target (its roll is
the clip's); the hand, twist bones and fingers keep their local transforms. Only the upper arm, forearm and hand
rotation channels of the clip are rewritten (keyed at `rate`); everything else stays byte for byte.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402


def unit(v):
    return v / max(float(np.linalg.norm(v)), 1e-12)


def ortho(m):
    u, _, vt = np.linalg.svd(m)
    return u @ vt


def rot_between(a, b):
    a, b = unit(a), unit(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def axis_angle(axis, deg):
    axis = unit(axis)
    a = np.radians(deg)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def frac_rot(R, w):
    q = glb_pose.matrix_quaternion(R)
    return glb_pose.quaternion_matrix(glb_pose.slerp(np.array([0, 0, 0, 1.0]), q, w))


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def vslerp(a, b, f):
    a, b = unit(np.asarray(a, float)), unit(np.asarray(b, float))
    ang = np.arccos(np.clip(np.dot(a, b), -1, 1))
    if ang < 1e-6:
        return a
    return unit((np.sin((1 - f) * ang) * a + np.sin(f * ang) * b) / np.sin(ang))


def key_at(keys, t, name):
    ks = [k for k in keys if name in k]
    if t <= ks[0]['t']:
        return np.asarray(ks[0][name], float)
    for k0, k1 in zip(ks[:-1], ks[1:]):
        if t <= k1['t']:
            f = smooth((t - k0['t']) / max(k1['t'] - k0['t'], 1e-9))
            if name == 'wrist':
                return (1 - f) * np.asarray(k0[name], float) + f * np.asarray(k1[name], float)
            return vslerp(k0[name], k1[name], f)
    return np.asarray(ks[-1][name], float)


def weight(w, t):
    t0, t1, t2, t3 = w
    if t <= t0 or t >= t3:
        return 0.0
    if t < t1:
        return smooth((t - t0) / (t1 - t0))
    if t > t2:
        return smooth((t3 - t) / (t3 - t2))
    return 1.0


def main():
    src, out, job_path = sys.argv[1:4]
    job = json.loads(Path(job_path).read_text())
    g = glb_pose.Glb(src)
    m = glb_pose.Model(g)
    names = [n['name'] for n in g.json['nodes']]
    I = {n: i for i, n in enumerate(names)}
    s = job.get('side', 'R')
    clip = job.get('clip', 'Attack')
    ua_n, fa_n, hand_n = I[f'B_{s}_UpperArm'], I[f'B_{s}_Forearm'], I[f'B_{s}_Hand']
    chest = I['B_Spine2']
    T = m.clip_times(clip)[-1]
    rate = float(job.get('rate', 60))
    N = int(round(T * rate))
    times = np.linspace(0, T, N + 1)
    C0 = ortho(m.world(m.sample('Standing', 0.0))[chest][:3, :3])
    tw_n = I.get(f'B_{s}_ForearmTwist')
    out_rot = {ua_n: [], fa_n: [], hand_n: []}
    if tw_n is not None and any('fingers' in k for k in job['keys']):
        out_rot[tw_n] = []
    report = []
    W0 = m.world(m.sample('Standing', 0.0))
    F0, H0 = ortho(W0[fa_n][:3, :3]), ortho(W0[hand_n][:3, :3])
    rel0 = F0.T @ H0                                     # Standing's wrist: hand in the forearm frame
    axis0 = F0.T @ unit(W0[hand_n][:3, 3] - W0[fa_n][:3, 3])   # forearm axis, forearm local
    tw0 = glb_pose.matrix_quaternion(F0.T @ ortho(W0[tw_n][:3, :3])) if tw_n is not None else None
    for t in times:
        local = m.sample(clip, float(t))
        W = m.world(local)
        w = weight(job['weight'], t)
        Rc = ortho(W[chest][:3, :3]) @ C0.T                 # chest change since Standing
        # upper arm
        sh, el, wr = W[ua_n][:3, 3], W[fa_n][:3, 3], W[hand_n][:3, 3]
        Rua = ortho(W[ua_n][:3, :3])
        Rfa = ortho(W[fa_n][:3, :3])
        Rh = ortho(W[hand_n][:3, :3])
        Rp = ortho(W[m.parent[ua_n]][:3, :3])
        new_ua = Rua
        new_fa = Rfa
        new_h = Rh
        if w > 0:
            tgt = Rc @ key_at(job['keys'], t, 'ua')
            cur = unit(el - sh)
            dR = frac_rot(rot_between(cur, tgt), w)
            new_ua = dR @ Rua
            # the forearm and hand ride with the upper arm, then the forearm is aimed
            Rfa1 = dR @ Rfa
            Rh1 = dR @ Rh
            cur_fa = dR @ unit(wr - el)
            tgt_fa = Rc @ key_at(job['keys'], t, 'fa')
            dF = frac_rot(rot_between(cur_fa, tgt_fa), w)
            new_fa = dF @ Rfa1
            new_h = dF @ Rh1
            if any('fingers' in k for k in job['keys']):
                # the hand set absolutely in the chest frame (local +Y along the fingers, +Z the palm normal on these
                # B_* hands). The forearm takes the hand's roll: its target is the hand target with Standing's wrist
                # relation (no wrist twist), turned onto the forearm direction; both blended in with the weight, and
                # the forearm twist bone blends to its Standing local (the hand's roll against the forearm is ~0)
                fing = Rc @ key_at(job['keys'], t, 'fingers')
                palm = Rc @ key_at(job['keys'], t, 'palm')
                palm = unit(palm - fing * (palm @ fing))
                Ht = np.stack([np.cross(fing, palm), fing, palm], axis=1)
                Fc = Ht @ rel0.T
                Ff = rot_between(Fc @ axis0, tgt_fa) @ Fc
                new_fa = glb_pose.quaternion_matrix(glb_pose.slerp(glb_pose.matrix_quaternion(new_fa),
                                                                   glb_pose.matrix_quaternion(Ff), w))
                new_h = glb_pose.quaternion_matrix(glb_pose.slerp(glb_pose.matrix_quaternion(new_h),
                                                                  glb_pose.matrix_quaternion(Ht), w))
        out_rot[ua_n].append(glb_pose.matrix_quaternion(Rp.T @ new_ua))
        out_rot[fa_n].append(glb_pose.matrix_quaternion(new_ua.T @ new_fa))
        out_rot[hand_n].append(glb_pose.matrix_quaternion(new_fa.T @ new_h))
        if tw_n in out_rot:
            q_clip = glb_pose.matrix_quaternion(Rfa.T @ ortho(W[tw_n][:3, :3]))
            out_rot[tw_n].append(glb_pose.slerp(q_clip, tw0, w))
        report.append((round(float(t), 3), round(w, 2)))
    animation = g.json['animations'][m.clips[clip]]
    t_acc = g.append_accessor(times.reshape(-1, 1), 'SCALAR')
    for node, qs in out_rot.items():
        q = np.array(qs)
        for i in range(1, len(q)):
            if np.dot(q[i], q[i - 1]) < 0:
                q[i] = -q[i]
        acc = g.append_accessor(q, 'VEC4')
        ch = [c for c in animation['channels'] if c['target']['node'] == node and c['target']['path'] == 'rotation']
        if ch:
            # a new sampler (another channel might share the old one)
            animation['samplers'].append({'input': t_acc, 'output': acc, 'interpolation': 'LINEAR'})
            ch[0]['sampler'] = len(animation['samplers']) - 1
        else:
            animation['samplers'].append({'input': t_acc, 'output': acc, 'interpolation': 'LINEAR'})
            animation['channels'].append({'sampler': len(animation['samplers']) - 1,
                                          'target': {'node': node, 'path': 'rotation'}})
    used = sorted({c['sampler'] for c in animation['channels']})
    remap = {old: new for new, old in enumerate(used)}
    animation['samplers'] = [animation['samplers'][i] for i in used]
    for c in animation['channels']:
        c['sampler'] = remap[c['sampler']]
    g.write(out)
    print(f'ARM_AIM {clip} {s}: {N + 1} keys; weight {job["weight"]}')


if __name__ == '__main__':
    main()
