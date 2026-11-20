#!/usr/bin/env python3
"""Fre: the braid's bind pose turned back about MM9's Ponytail11 joint (2026-11-04). MM9's library clips turn the Ponytail chain ~13-19 deg
forward from the bind pose (MM9's own braid sticks out ~27 deg from the back at bind and hangs near the back in play); ours was built
hanging near the back, so every clip pushed it 3 cm into the back (gate_fre.py). A rigid turn by THETA keeps the braid's topology and UVs
(the head paint was made on the unturned braid, upload texturing/fre_head_upload.glb). Positions only. Args: <in uv/asm npz> <out npz> [theta deg]"""
import sys, json
import numpy as np
D = dict(np.load(sys.argv[1])); th = np.radians(float(sys.argv[3]) if len(sys.argv) > 3 else 18.0)
names = [str(x) for x in D['names']]; q = D['comp'] == names.index('braids')
J = np.array(json.load(open('work/rig.json'))['mm9']['FHP Ponytail11'])
co = D['co'].copy(); v = co[q] - J
y = v[:, 1] * np.cos(th) - v[:, 2] * np.sin(th); z = v[:, 1] * np.sin(th) + v[:, 2] * np.cos(th)
co[q] = J + np.c_[v[:, 0], y, z]; D['co'] = co; np.savez(sys.argv[2], **D)
print('BRAID turned', int(q.sum()), 'deg', round(float(np.degrees(th)), 1), 'tip', co[q][np.argmin(co[q][:, 2])].round(3))
