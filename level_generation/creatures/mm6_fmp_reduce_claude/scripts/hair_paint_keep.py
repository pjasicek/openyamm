"""Keep the hair faces whose own texels are partly skin- or cap-coloured (hair_blue.py test, > 10 %), plus one edge
ring: hairline and hidden under-cap paint that a cut pushes into view. Usage: hair_paint_keep.py <keep in> <keep out>"""
import sys, numpy as np
from hair_blue import bad
d = np.load('work/mesh_in.npz'); comp = np.load('work/comp.npy'); faces = d['faces']
hair = np.isin(comp, [11, 12, 16]); sel = np.zeros(len(faces), bool)
sel[hair] = bad(d['wuv'].reshape(-1, 3, 2)[hair]) > .1
ring = np.isin(faces, np.unique(faces[sel])).any(1) & hair
keep = np.load(sys.argv[1]) | ring
np.save(sys.argv[2], keep); print('painted hair', int(sel.sum()), 'with ring', int(ring.sum()), 'total keep', int(keep.sum()))
