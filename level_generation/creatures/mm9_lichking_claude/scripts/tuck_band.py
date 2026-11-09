#!/usr/bin/env python3
"""r9: the crown's brow-band front arc ran just in front of the skull's painted (not hollow) eye sockets and showed as a bar across them.
r8 dropped those faces, which left their atlas charts empty (54.9 %); here the arc's vertices are moved 2.5 cm back, inside the skull, so the
faces stay (atlas 55.3 %) and nothing shows. Same selection as r8 (crown faces, |x| < 7 cm, z 1.44-1.515, front of the head).
Args: <in npz> <out npz>"""
import sys, numpy as np
D = dict(np.load(sys.argv[1])); co = D['co'].copy(); tri, comp = D['tri'], D['comp']; names = [str(x) for x in D['names']]
fc = comp[tri[:, 0]]; c = co[tri].mean(1)
sel = (fc == names.index('crown')) & (np.abs(c[:, 0]) < 0.07) & (c[:, 2] > 1.44) & (c[:, 2] < 1.515) & (c[:, 1] < -0.03)
v = np.unique(tri[sel]); co[v, 1] += 0.025
print('band faces', int(sel.sum()), 'vertices moved back', len(v))
D['co'] = co; np.savez(sys.argv[2], **D)
