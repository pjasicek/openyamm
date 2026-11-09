#!/usr/bin/env python3
"""Fall corrections on a Honk GLB's clips, written into a copy (only rotation samplers change). Smooth by construction: one
constant local rotation with a smoothstep weight, or one constant blend towards the Standing pose, never a per-key solve.
  --foot DEG T0 T1 [CLIP DEATH DEAD]  turn both feet DEG towards the line of the leg: 0 at T0 of Death, all of it from T1 and in Dead.
      In the corpse the toes point up (as in MM9), and our boot is longer than the hem ring's flattened opening: the toe and heel
      came through the robe. A relaxed foot lies along the leg, inside the ring.
  --damp GLOB FACTOR CLIP[,CLIP]      blend matching joints towards their first Standing key by FACTOR through the clips: the female's
      braids are longer than MM9's on the same local rotations, and flew out like tentacles in Death.
Usage: clip_relax.py <in.glb> <out.glb> [--foot ...] [--damp ...] [--lift CLIP T SIGMA METRES]"""
import fnmatch, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, slerp, matrix_quaternion

a = sys.argv[1:]
src, dst = a[:2]
g = Glb(src)
m = Model(g)
doc = g.json
nodes = doc['nodes']
nd = [n.get('name', '') for n in nodes]


def chan(clip, node):
    an = doc['animations'][m.clips[clip]]
    for c in an['channels']:
        if c['target']['node'] == node and c['target']['path'] == 'rotation':
            return an['samplers'][c['sampler']]
    return None


def qmul(p, q):
    x1, y1, z1, w1 = p
    x2, y2, z2, w2 = q
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def write(sampler, out):
    out = out / np.linalg.norm(out, axis=1, keepdims=True)
    sampler['output'] = g.append_accessor(out, 'VEC4')


rest_world = m.world({})
i = 2
foot_jobs = []
damp_jobs = []
lift_jobs = []
while i < len(a):
    if a[i] == '--foot':
        foot_jobs.append((float(a[i + 1]), float(a[i + 2]), float(a[i + 3])))
        i += 4
    elif a[i] == '--lift':
        lift_jobs.append((a[i + 1], float(a[i + 2]), float(a[i + 3]), float(a[i + 4])))
        i += 5
    elif a[i] == '--damp':
        damp_jobs.append((a[i + 1], float(a[i + 2]), a[i + 3].split(',')))
        i += 4
    else:
        raise SystemExit('unknown ' + a[i])
for deg, t0, t1 in foot_jobs:
    for s in 'LR':
        foot, calf, toe = (nd.index(f'Bip01 {s} {b}') for b in ('Foot', 'Calf', 'Toe0'))
        ankle = rest_world[foot][:3, 3]
        leg = ankle - rest_world[calf][:3, 3]
        leg /= np.linalg.norm(leg)
        tip = np.array([0.0, 0.0, 1.0])          # the toes point along the nose in the rest pose
        axis = np.cross(tip, leg)
        axis /= np.linalg.norm(axis)
        local = rest_world[foot][:3, :3].T @ axis
        local /= np.linalg.norm(local)
        for clip in ('Death', 'Dead'):
            sm = chan(clip, foot)
            T = g.accessor(sm['input'])[:, 0].astype(np.float64)
            Q = g.accessor(sm['output']).astype(np.float64)
            out = []
            for tt, q in zip(T, Q):
                x = 1.0 if clip == 'Dead' else float(np.clip((tt - t0) / (t1 - t0), 0, 1))
                w = x * x * (3 - 2 * x)
                ang = np.radians(deg) * w
                dq = np.r_[local * np.sin(ang / 2), np.cos(ang / 2)]
                out.append(qmul(q, dq))
            write(sm, np.array(out))
for glob, f, clips in damp_jobs:
    ids = [i_ for i_, n in enumerate(nd) if fnmatch.fnmatch(n, glob)]
    done = 0
    for n in ids:
        base = chan('Standing', n)
        q0 = g.accessor(base['output'])[0].astype(np.float64) if base else np.array(m.rest[n][1])
        for clip in clips:
            sm = chan(clip, n)
            if sm is None:
                continue
            Q = g.accessor(sm['output']).astype(np.float64)
            write(sm, np.array([slerp(q / np.linalg.norm(q), q0 / np.linalg.norm(q0), f) for q in Q]))
            done += 1
    print('DAMP', glob, 'joints', len(ids), 'channels', done)
# --lift CLIP T SIGMA METRES: the whole body up by a Gaussian bump (the root's y keys): a floor overshoot of a millimetre or two in the fall, where tighter
# floor smoothing shakes the shoulders
for clip, t0, sg, h in lift_jobs:
    an = doc['animations'][m.clips[clip]]
    root = nd.index('Scene Root')
    ch = next((c for c in an['channels'] if c['target']['node'] == root and c['target']['path'] == 'translation'), None)
    sm = an['samplers'][ch['sampler']]
    T = g.accessor(sm['input'])[:, 0].astype(np.float64)
    V = g.accessor(sm['output']).astype(np.float64).copy()
    V[:, 1] += h * np.exp(-0.5 * ((T - t0) / sg) ** 2)
    sm['output'] = g.append_accessor(V, 'VEC3')
g.write(dst)
print('RELAX', dst)
