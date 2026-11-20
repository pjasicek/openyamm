#!/usr/bin/env python3
"""MM9 gives Yanmir no death that ends lying down: his trap death is startdie (the floor breaks) -> fall (loops in the air) -> the
pit, and `Die` ends standing (the game then removes him). The engine needs a body on the floor, so Death and Dead come from MM9's
own Giant (GIANT.abc die1: falls forward on his face; die2: sinks to his knees and back), the same studio's biped of the same size,
retargeted onto YANMIR.abc's bind by world orientation: every Yanmir bone points where the Giant's bone points (R_y(t) = R_g(t)
R_g0^-1 L R_y0, L the least rotation from Yanmir's bind limb direction onto the Giant's), the pelvis moves by the Giant's pelvis
offset scaled by pelvis height. Giant Spine2/Spine3 drive Yanmir Spine1/Spine2; fingers, the staff bones and Ponytail1 keep
Yanmir's bind (the staff stays in the hand). Writes source/true/yanmir_plus.glb = yanmir_true.glb + clips giant_die1, giant_die2
in MM9's own raw frame, which clips_mm9.py then puts on our rig like any MM9 clip. Args: <yanmir true glb> <giant true glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion, trs_matrix
YG, GG, OUT = sys.argv[1:4]
FPS = 30
y = Model(Glb(YG)); g = Model(Glb(GG))
yn = [n.get('name') for n in y.glb.json['nodes']]; gn = [n.get('name') for n in g.glb.json['nodes']]
B = 'Bip01 '
MAP = {B + 'Spine1': B + 'Spine2', B + 'Spine2': B + 'Spine3'}
# bone -> child used for its direction (both rigs); None = no turn (centre chain, head)
CHILD = {}
for s in 'LR':
    S = B + s + ' '
    CHILD.update({S + 'Clavicle': S + 'UpperArm', S + 'UpperArm': S + 'Forearm', S + 'Forearm': S + 'Hand', S + 'Hand': S + 'Finger1',
                  S + 'Thigh': S + 'Calf', S + 'Calf': S + 'Foot', S + 'Foot': S + 'Toe0', S + 'Toe0': S + 'Toe01'})
KEEP = {n for n in yn if n and ('Finger' in n or n.startswith('Ystaff') or 'Ponytail' in n)}
Y0 = y.world({}); G0 = g.world({})
parent = y.parent


def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)


L = {}
for b, c in CHILD.items():
    gb, gc = MAP.get(b, b), MAP.get(c, c)
    L[b] = rot_between(Y0[yn.index(c)][:3, 3] - Y0[yn.index(b)][:3, 3], G0[gn.index(gc)][:3, 3] - G0[gn.index(gb)][:3, 3])
floor_y, floor_g = -1.449, min(G0[gn.index(B + s + ' Toe0')][1, 3] for s in 'LR')
py0 = Y0[yn.index(B + 'Pelvis')][:3, 3]; pg0 = G0[gn.index(B + 'Pelvis')][:3, 3]
k = (py0[1] - floor_y) / (pg0[1] - floor_g)
doc = y.glb.json
order = y.order
for clip in ('die1', 'die2'):
    T = g.clip_times(clip); dur = T[-1]
    times = np.linspace(0, dur, int(round(dur * FPS)) + 1)
    rot = {i: [] for i in range(len(yn)) if yn[i] and yn[i].startswith(('Bip01', 'Y'))}
    tra = {yn.index(B + 'Pelvis'): []}
    for t in times:
        Wg = g.world(g.sample(clip, t))
        Wy = {}
        for i in order:
            n = yn[i]
            par = parent[i]
            loc_rest = trs_matrix(*y.rest[i])
            if n == 'Scene Root' or n is None or not n.startswith(('Bip01', 'Y')):
                Wy[i] = (Wy[par] if par >= 0 else np.eye(4)) @ loc_rest; continue
            gname = MAP.get(n, n)
            W = (Wy[par] if par >= 0 else np.eye(4)) @ loc_rest      # default: bind local
            if n not in KEEP and gname in gn:
                gi = gn.index(gname)
                R = Wg[gi][:3, :3] @ G0[gi][:3, :3].T @ L.get(n, np.eye(3)) @ Y0[i][:3, :3]
                W = W.copy(); W[:3, :3] = R
                if n == B + 'Pelvis':
                    W[:3, 3] = py0 + (Wg[gi][:3, 3] - pg0) * k
            Wy[i] = W
            Lm = np.linalg.inv(Wy[par]) @ W if par >= 0 else W
            if i in rot: rot[i].append(matrix_quaternion(Lm[:3, :3]))
            if i in tra: tra[i].append(Lm[:3, 3])
    an = {'name': 'giant_' + clip, 'channels': [], 'samplers': []}
    ti = y.glb.append_accessor(times[:, None], 'SCALAR')
    for i, qs in rot.items():
        qs = np.array(qs)
        for j in range(1, len(qs)):
            if qs[j] @ qs[j - 1] < 0: qs[j] = -qs[j]
        an['samplers'].append({'input': ti, 'output': y.glb.append_accessor(qs, 'VEC4'), 'interpolation': 'LINEAR'})
        an['channels'].append({'sampler': len(an['samplers']) - 1, 'target': {'node': i, 'path': 'rotation'}})
    for i, ts in tra.items():
        an['samplers'].append({'input': ti, 'output': y.glb.append_accessor(np.array(ts), 'VEC3'), 'interpolation': 'LINEAR'})
        an['channels'].append({'sampler': len(an['samplers']) - 1, 'target': {'node': i, 'path': 'translation'}})
    doc['animations'].append(an)
    print('CLIP giant_' + clip, round(dur, 2), 's', len(times), 'frames, pelvis k', round(k, 3), 'end pelvis', np.round(tra[yn.index(B + 'Pelvis')][-1], 3))
y.glb.write(OUT)
print('WROTE', OUT)
