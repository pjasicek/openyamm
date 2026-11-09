#!/usr/bin/env python3
"""Lift the Ratman's head in the clips: pitch B_Neck up and give B_Head the opposite pitch, so the head keeps its
orientation and rides on the shoulders instead of hanging in front of the chest.

The ready pose shared by Standing, Attack, Hit, Fidget and the start of Death points the neck 15 degrees below
horizontal (rest: 24 above), which puts the head joint 10 cm below the shoulder joints; Running drops it to -22.
Per key, the neck's world pitch is found by forward kinematics and the lift is TARGET minus that pitch, clamped to
0..MAX (so the ready pose gets the full lift, Walking a little and Fidget's look-up none). Every B_Neck / B_Head
rotation key is right-multiplied by a local pitch about the bone's lateral axis (the rig's X axis in the bone's rest
frame). Death fades the lift out while the body falls (DEATH_FADE seconds), so the corpse and Dead are unchanged.
Rest pose, geometry and weights are untouched. Usage: lift_neck_clips.py <in.glb> <out.glb> [target max]"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

TARGET, MAX = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (30.0, 45.0)
SKIP = {'Dead'}
DEATH_FADE = (0.12, 0.45)
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
N = doc['nodes']; idx = {n.get('name'): i for i, n in enumerate(N)}
parent = {c: i for i, n in enumerate(N) for c in n.get('children', [])}


def read(i):
    a = doc['accessors'][i]
    n = {'SCALAR': 1, 'VEC4': 4}[a['type']]
    return np.frombuffer(accessor_bytes(doc, binary, i), np.float32).reshape(a['count'], n).astype(np.float64)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def world_rot(i):
    m = quat_mat(N[i].get('rotation', [0, 0, 0, 1]))
    while i in parent:
        i = parent[i]; m = quat_mat(N[i].get('rotation', [0, 0, 0, 1])) @ m
    return m


def axis_quat(axis, angle):
    axis = axis / np.linalg.norm(axis); s = math.sin(angle / 2)
    return np.concatenate([axis * s, [math.cos(angle / 2)]])


def qmul(a, b):
    ax, ay, az, aw = a.T; bx, by, bz, bw = b.T
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], -1)


def smooth(x, a, b):
    s = np.clip((x - a) / (b - a), 0, 1); return s * s * (3 - 2 * s)


neck, head = idx['B_Neck'], idx['B_Head']
lat = np.array([1.0, 0, 0])
ax_n, ax_h = world_rot(neck).T @ lat, world_rot(head).T @ lat
# sign: a positive lift must raise the head joint (glTF Y up) in the rest pose
off = world_rot(neck) @ np.array(N[head]['translation'])
sign = 1 if (world_rot(neck) @ quat_mat(axis_quat(ax_n, 0.3)) @ np.array(N[head]['translation']))[1] > off[1] else -1


def slerp(a, b, f):
    if a @ b < 0:
        b = -b
    th = math.acos(min(1.0, a @ b))
    return a if th < 1e-6 else (math.sin((1 - f) * th) * a + math.sin(f * th) * b) / math.sin(th)


def sample(sampler, t):
    """local rotation of a channel at time t"""
    ts = read(sampler['input'])[:, 0]; qs = read(sampler['output'])
    k = int(np.searchsorted(ts, t, side='right')) - 1
    if k < 0 or k >= len(ts) - 1 or sampler.get('interpolation') == 'STEP':
        return qs[max(0, min(k, len(ts) - 1))]
    return slerp(qs[k], qs[k + 1], (t - ts[k]) / (ts[k + 1] - ts[k]))


def neck_pitch(rot_ch, t):
    """world pitch of the B_Neck bone (degrees above horizontal; glTF Y up, the Ratman faces +Z) at time t"""
    m = np.eye(3); i = neck
    chain = [i]
    while i in parent:
        i = parent[i]; chain.append(i)
    for j in reversed(chain):
        q = sample(rot_ch[j], t) if j in rot_ch else np.array(N[j].get('rotation', [0, 0, 0, 1.0]))
        m = m @ quat_mat(q)
    d = m @ np.array([0, 1.0, 0])
    return math.degrees(math.atan2(d[1], d[2]))


for a in doc['animations']:
    if a['name'] in SKIP:
        continue
    rot_ch = {c['target']['node']: a['samplers'][c['sampler']] for c in a['channels'] if c['target']['path'] == 'rotation'}
    if neck not in rot_ch:
        continue
    tn = read(rot_ch[neck]['input'])[:, 0]
    lift = np.array([min(MAX, max(0.0, TARGET - neck_pitch(rot_ch, t))) for t in tn])
    if a['name'] == 'Death':
        lift *= 1 - smooth(tn, *DEATH_FADE)
    for c in a['channels']:
        j = c['target']['node']
        if c['target']['path'] != 'rotation' or j not in (neck, head):
            continue
        a['samplers'].append(dict(a['samplers'][c['sampler']])); c['sampler'] = len(a['samplers']) - 1
        s = a['samplers'][c['sampler']]
        t = read(s['input'])[:, 0]; q = read(s['output'])
        ang = sign * np.radians(np.interp(t, tn, lift)) * (1 if j == neck else -1)
        p = np.stack([axis_quat(ax_n if j == neck else ax_h, x) for x in ang])
        s['output'] = append_accessor(doc, binary, doc['accessors'][s['output']], qmul(q, p).astype(np.float32).tobytes())
    print('LIFT', a['name'], f'{lift.min():.0f}..{lift.max():.0f} deg')
write_glb(dst, doc, bytes(binary))
