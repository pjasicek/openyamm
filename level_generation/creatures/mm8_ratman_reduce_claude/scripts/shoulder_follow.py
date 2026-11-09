#!/usr/bin/env python3
"""Let the clavicles follow the arms in every clip (shoulder rhythm), so a raised arm no longer bends at a fixed
shoulder cap.

The shoulder caps are weighted 0.7-0.9 to the clavicles and the clavicles barely move in the clips, so the sword arm
held forward in the ready pose (about 60 degrees of swing) bends at a boxy corner where the cap stays put. For every
rotation key, the upper arm's swing away from its rest direction (measured in the clavicle's parent frame) is shared:
the clavicle turns by SHARE of it (at most MAX_DEG), and the upper arm is counter-rotated so its world orientation,
and so the arm's direction, stays exactly as authored; only the shoulder point moves with the clavicle (a few cm).
Both arms, all clips (Dead keeps matching the last Death frame since the share is per key). Rest pose, geometry and
weights are untouched. Usage: shoulder_follow.py <in.glb> <out.glb> [share, default 0.3]"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

SHARE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
MAX_DEG = 20.0
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
N = doc['nodes']; idx = {n.get('name'): i for i, n in enumerate(N)}


def read(i):
    a = doc['accessors'][i]; n = {'SCALAR': 1, 'VEC4': 4}[a['type']]
    return np.frombuffer(accessor_bytes(doc, binary, i), np.float32).reshape(a['count'], n).astype(np.float64)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def mat_quat(m):
    w = math.sqrt(max(0.0, 1 + m[0, 0] + m[1, 1] + m[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0.0, 1 + m[0, 0] - m[1, 1] - m[2, 2])) / 2, m[2, 1] - m[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1 - m[0, 0] + m[1, 1] - m[2, 2])) / 2, m[0, 2] - m[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1 - m[0, 0] - m[1, 1] + m[2, 2])) / 2, m[1, 0] - m[0, 1])
    q = np.array([x, y, z, w]); return q / np.linalg.norm(q)


def arc(a, b, frac):
    """rotation taking direction a towards b by frac of the angle (capped at MAX_DEG)"""
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b); axis = np.cross(a, b); s = np.linalg.norm(axis)
    if s < 1e-8:
        return np.eye(3), 0.0
    ang = min(math.atan2(s, a @ b) * frac, math.radians(MAX_DEG)); axis /= s
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K, math.degrees(ang)


def slerp(a, b, f):
    if a @ b < 0:
        b = -b
    d = min(1.0, a @ b); th = math.acos(d)
    if th < 1e-6:
        return a
    return (math.sin((1 - f) * th) * a + math.sin(f * th) * b) / math.sin(th)


def sample(t, q, interp, T):
    out = []
    for x in T:
        k = int(np.searchsorted(t, x, side='right')) - 1
        if k < 0 or interp == 'STEP' or k >= len(t) - 1:
            out.append(q[max(0, min(k, len(t) - 1))]); continue
        out.append(slerp(q[k], q[k + 1], (x - t[k]) / (t[k + 1] - t[k])))
    return np.array(out)


Y = np.array([0, 1.0, 0])   # glTF bone axis
for side in 'RL':
    C, U = idx[f'B_{side}_Clavicle'], idx[f'B_{side}_UpperArm']
    RU0 = quat_mat(N[U]['rotation'])
    for a in doc['animations']:
        chans = {(c['target']['node'], c['target']['path']): c for c in a['channels']}
        if (C, 'rotation') not in chans or (U, 'rotation') not in chans:
            continue
        # own copies of the two samplers: the exporter shares one sampler between bones with identical keys
        for key in ((C, 'rotation'), (U, 'rotation')):
            a['samplers'].append(dict(a['samplers'][chans[key]['sampler']])); chans[key]['sampler'] = len(a['samplers']) - 1
        sc, su = a['samplers'][chans[(C, 'rotation')]['sampler']], a['samplers'][chans[(U, 'rotation')]['sampler']]
        tc, tu = read(sc['input'])[:, 0], read(su['input'])[:, 0]
        qc, qu = read(sc['output']), read(su['output'])
        if len(tc) != len(tu) or not np.allclose(tc, tu):  # resample both on the union of their key times
            T = np.union1d(tc, tu)
            qc, qu = sample(tc, qc, sc.get('interpolation', 'LINEAR'), T), sample(tu, qu, su.get('interpolation', 'LINEAR'), T)
            acc = dict(doc['accessors'][sc['input']], count=len(T), min=[float(T[0])], max=[float(T[-1])])
            sc['input'] = su['input'] = append_accessor(doc, binary, acc, T.astype(np.float32).tobytes())
            sc['interpolation'] = su['interpolation'] = 'LINEAR'
        nc, nu, angles = [], [], []
        for q1, q2 in zip(qc, qu):
            RC, RU = quat_mat(q1), quat_mat(q2)
            S, deg = arc(RC @ RU0 @ Y, RC @ RU @ Y, SHARE)    # swing in the clavicle's parent frame
            RC2 = S @ RC; RU2 = RC2.T @ RC @ RU               # upper arm keeps its world orientation
            nc.append(mat_quat(RC2)); nu.append(mat_quat(RU2)); angles.append(deg)
        nc, nu = np.array(nc), np.array(nu)
        for arr in (nc, nu):  # keep quaternion signs continuous for LINEAR interpolation
            for k in range(1, len(arr)):
                if arr[k] @ arr[k - 1] < 0:
                    arr[k] = -arr[k]
        sc['output'] = append_accessor(doc, binary, dict(doc['accessors'][sc['output']], count=len(nc)), nc.astype(np.float32).tobytes())
        su['output'] = append_accessor(doc, binary, dict(doc['accessors'][su['output']], count=len(nu)), nu.astype(np.float32).tobytes())
        print('FOLLOW', side, a['name'], f'clavicle turn max {max(angles):.1f} deg')
write_glb(dst, doc, bytes(binary))
