"""Meshy's arms are 29 % longer than MM9's (the tall crown set the scale). Sleeve and bracer are compressed along the arm axis, the hand rides along unchanged. Blender frame. Args: <in npz> <rig json> <out npz> [length]"""
import sys, json
import numpy as np
IN, RIG, OUT = sys.argv[1:4]; LEN = float(sys.argv[4]) if len(sys.argv) > 4 else 0.50
D = dict(np.load(IN)); co, comp = D['co'].copy(), D['comp']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
J = json.load(open(RIG))['joints']
sh = np.array(J['Bip01 R UpperArm']); wr = np.array(J['Bip01 R Hand']); el = np.array(J['Bip01 R Forearm'])
L = np.linalg.norm(wr - sh); u = (wr - sh) / L
k = LEN / L; print('arm', L, 'k', k)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
for s in (1, -1):
    uu = u * [s, 1, 1]; o = sh * [s, 1, 1]
    side = co[:, 0] * s > 0
    t = (co - o) @ uu; r = np.linalg.norm(co - o - np.outer(t, uu), axis=1)
    arm = side & np.isin(comp, [pid['torso'], pid['bracers']]) & (r < 0.13)
    m = (1 - ss(r, 0.10, 0.13)) * (arm | (side & (comp == pid['hands'])))
    m[side & (comp == pid['hands'])] = 1; m[side & (comp == pid['bracers'])] = 1
    shift = (1 - k) * np.clip(t - 0.03, 0, L - 0.03)
    shift[side & (comp == pid['hands'])] = (1 - k) * (L - 0.03)
    co[side] -= (m[side] * shift[side])[:, None] * uu
    print('moved', int((m > 0).sum()), 'max', float((m * shift).max()))
D['co'] = co
np.savez(OUT, **D)
