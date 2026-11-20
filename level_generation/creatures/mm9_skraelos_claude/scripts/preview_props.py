#!/usr/bin/env python3
"""Preview npz: the assembled mesh + the held skull from work/held_skull.json (comp = new id). Args: <asm npz> <skull npz> <out npz>"""
import numpy as np, json, sys
D = dict(np.load(sys.argv[1])); H = json.load(open('work/held_skull.json')); S = np.load(sys.argv[2])
sco = S['co']; keep = S['label'] != 3
loc = (sco - np.array(H['eye_c'])) * H['scale'] - np.array(H['box_mid'])
P = loc @ np.array(H['R']).T + np.array(H['centre']); t = S['tri']; t = t[keep[t].all(1)]
n0 = len(D['co'])
np.savez(sys.argv[3], co=np.vstack([D['co'], P]), tri=np.vstack([D['tri'], t + n0]), comp=np.r_[D['comp'], np.full(len(P), D['comp'].max() + 1)])
