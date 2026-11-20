#!/usr/bin/env python3
"""The club joint `Club` (child of the robe column Robe_03_0 at the right hip, rest = hanging there, work/club_place.json `belt`) keyed in the Attack: from the belt
into the right fist and back, with the fist's weight (finger_keys_mer.py: in over EASE_IN s, out over EASE_OUT s). In the fist the club sits
where finish_mer.py solved the grip (club_place.json G/U/A in the un-turned rest hand; the wrist turn `hand_offset` is in the Hand keys):
Club_world(t) = Hand_world(t) inv(Hand_bind) T_grip inv(T_belt) Club_bind. Other clips keep the rest (at the belt).
Args: <in glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT = sys.argv[1:3]
EASE_IN, EASE_OUT = 0.12, 0.16
BULGE = 0.14
pl = json.load(open(HERE / 'work' / 'club_place.json'))
g = Glb(Path(IN)); m = Model(g); doc = g.json
names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]
Bind = {jn[i]: np.linalg.inv(m.inverse_binds[i]) for i in range(len(jn))}
C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)              # Blender -> glTF
lift = Bind['Club'][1, 3] - pl['belt']['G'][2]


def rigid(G, U, A):
    U = C @ np.array(U); A = C @ np.array(A); A = A - U * (A @ U); A /= np.linalg.norm(A)
    T = np.eye(4); T[:3, :3] = np.c_[A, U, np.cross(A, U)]; T[:3, 3] = C @ np.array(G) + [0, lift, 0] - U * pl['tc']
    return T


Tg = rigid(pl['G'], pl['U'], pl['A']); Tb = rigid(pl['belt']['G'], pl['belt']['U'], pl['belt']['A'])
K = np.linalg.inv(Bind['Bip01 R Hand']) @ Tg @ np.linalg.inv(Tb) @ Bind['Club']
PAR = names[next(i for i, n in enumerate(doc['nodes']) if ix['Club'] in (n.get('children') or []))]
rest_local = np.linalg.inv(Bind[PAR]) @ Bind['Club']


def sstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def slerp(a, b, t):
    if a @ b < 0: b = -b
    q = a * (1 - t) + b * t; return q / np.linalg.norm(q)


an = next(a for a in doc['animations'] if a['name'] == 'Attack')
T = np.array(sorted(m.clip_times('Attack'))); dur = float(T[-1])
T = np.linspace(0, dur, int(round(dur * 60)) + 1)
qb = np.array(matrix_quaternion(rest_local[:3, :3])); tb = rest_local[:3, 3]
Q, P = [], []
for t in T:
    W = m.world(m.sample('Attack', float(t)))
    Wp = W[ix[PAR]]; Wh = W[ix['Bip01 R Hand']] @ K; Wb = W[ix['Club']]          # the belt pose as robe_keys.py keyed it
    c = float(sstep(t / EASE_IN) * sstep((dur - t) / EASE_OUT))
    # between the belt and the fist the club swings out round the hip (a straight path crossed the thigh): BULGE x sin(pi c) away from
    # the pelvis axis, horizontally
    p = Wb[:3, 3] * (1 - c) + Wh[:3, 3] * c
    rd = p - W[ix['Bip01 Pelvis']][:3, 3]; rd[1] = 0; rd /= max(np.linalg.norm(rd), 1e-6)
    p = p + rd * BULGE * np.sin(np.pi * c)
    q = slerp(np.array(matrix_quaternion(Wb[:3, :3])), np.array(matrix_quaternion(Wh[:3, :3])), c)
    x, y, z, w = q
    Rw = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                   [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    Mw = np.eye(4); Mw[:3, :3] = Rw; Mw[:3, 3] = p
    loc = np.linalg.inv(Wp) @ Mw
    Q.append(np.array(matrix_quaternion(loc[:3, :3]))); P.append(loc[:3, 3])
Q = np.array(Q)
for k in range(1, len(Q)):
    if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
ci = ix['Club']
an['channels'] = [c for c in an['channels'] if c['target']['node'] != ci]
ta = g.append_accessor(T.astype(np.float32), 'SCALAR'); doc['accessors'][ta]['min'] = [0.0]; doc['accessors'][ta]['max'] = [dur]
for path, val in (('rotation', Q), ('translation', np.array(P))):
    va = g.append_accessor(val.astype(np.float32), 'VEC4' if path == 'rotation' else 'VEC3')
    an['samplers'].append(dict(input=ta, output=va, interpolation='LINEAR'))
    an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=ci, path=path)))
g.write(Path(OUT))
print('CLUB keyed Attack', len(T), 'keys; parent', PAR, 'rest local', tb.round(3))
