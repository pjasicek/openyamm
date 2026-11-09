"""Applause clap spread (mm9_sven, 2026-11-02): MM9's seated clap brings its thin hands together; our thicker MPFB hands
and the bracers then overlap 2.2 cm (arm and hand gate). arm_clear.py's per-key turns cleared it but jittered 5.8 deg/f
over MM9. Here each upper arm gets one constant horizontal abduction about the vertical axis through the shoulder, in
world space through the parent's frame (so MM9's own motion is untouched apart from the offset), eased in and out over
EASE seconds at the clip's ends (seamless to Sit). Env SPREAD_AXIS=z turns about the forward axis instead (a hanging hand
moves out from the hip: Talk), SPREAD_SIDES=L|R limits the sides. Args: <in glb> <out glb> <clip> <degrees> [ease 0.4]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
src, dst, clip, deg = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
EASE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.4
glb = Glb(Path(src)); model = Model(glb)
names = [n.get('name') for n in glb.json['nodes']]
anim = glb.json['animations'][model.clips[clip]]
times_all = model.clip_times(clip); T = max(times_all)
import os
AXIS = os.environ.get('SPREAD_AXIS', 'y')
rep = {}
for tok in os.environ.get('SPREAD_SIDES', 'LR'):
    ua = names.index(f'Bip01 {tok} UpperArm'); hand = names.index(f'Bip01 {tok} Hand')
    ch = next(c for c in anim['channels'] if c['target']['node'] == ua and c['target']['path'] == 'rotation')
    smp = anim['samplers'][ch['sampler']]
    tin = glb.accessor(smp['input'])[:, 0]; qout = glb.accessor(smp['output']).astype(np.float64)
    par = model.parent[ua]
    # sign: the abduction moves the hand toward its own shoulder's side at mid-clip
    W = model.world(model.sample(clip, T / 2))
    sh, hd = W[ua][:3, 3], W[hand][:3, 3]
    def Ry(a):
        c, s = np.cos(a), np.sin(a)
        if AXIS == 'z':
            return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    test = Ry(np.radians(deg)) @ (hd - sh) + sh
    sign = 1.0 if (test[0] - hd[0]) * sh[0] > 0 else -1.0     # toward the shoulder's side (the clapping hands cross x = 0)
    new = []
    for t, q in zip(tin, qout):
        e = min(1.0, t / EASE, (T - t) / EASE) if EASE > 0 else 1.0
        e = 0.5 - 0.5 * np.cos(np.pi * max(e, 0.0))
        W = model.world(model.sample(clip, float(t)))
        P = W[par][:3, :3]; P = P / np.linalg.norm(P, axis=0)
        R = P.T @ Ry(sign * np.radians(deg) * e) @ P @ quaternion_matrix(q / np.linalg.norm(q))[:3, :3]
        qn = matrix_quaternion(R)
        if np.dot(qn, q) < 0:
            qn = -qn
        new.append(qn)
    smp['output'] = glb.append_accessor(np.array(new, np.float32), 'VEC4')
    rep[tok] = {'keys': len(tin), 'sign': sign}
glb.write(Path(dst))
print('CLAP_SPREAD', clip, deg, rep)
