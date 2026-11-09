"""Project the reduced mace ball back onto the source's exact sphere (the quadric collapse leaves 6 mm dents on the
54 mm ball; UVs are kept). Only vertices of the ball group (decimate_tex.py's per-face `group`, label 3) move, radially onto it. Usage: mace_snap_ball.py <in .npz> <out .npz>"""
import sys
import numpy as np
s = np.load('work/mace.npz'); comp = np.load('work/mace_dec/comp.npy')
ball = s['verts'][np.unique(s['faces'][comp == 3])]; ctr = ball.mean(0); R = float(np.median(np.linalg.norm(ball - ctr, axis=1)))
d = dict(np.load(sys.argv[1])); v = d['verts']
off = v - ctr; r = np.linalg.norm(off, axis=1)
m = np.zeros(len(v), bool); m[np.unique(d['faces'][d['group'] == 3])] = True
v[m] = ctr + off[m] / r[m, None] * R
np.savez(sys.argv[2], **d); print('SNAPPED', int(m.sum()), 'vertices onto r', round(R, 4))
