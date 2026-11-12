"""Keep mask of an m620 texture set: the largest connected piece keeps the approved colour and normal.
Head set (TP_CONFIG=texpass_head.json): the head skin; body set (texpass.json): the body skin, where every fresh paint
drew veins, a navel and the vest's dotted edge on the approved flat skin.

Originally: keep mask of the m620 head set (work layout uv_study_head): texels of the head skin piece (the largest connected
piece of the head primitive: face, ears, scalp, neck) keep the approved colour and normal; the hair volume and the
strands take the composed paint (study job 6 is a different, younger face with an olive neck, REPORT.md adoption notes).
Usage (TP_CONFIG=texpass_head.json): m620_head_keep.py <approved prefix> <out png>"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

import tp_common as C

approved, out = sys.argv[1:3]
d = np.load(C.lod0_path())
w = d['weld'][d['tri']]
n = int(w.max()) + 1
e = np.concatenate([w[:, [0, 1]], w[:, [1, 2]], w[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
piece = lab[w[:, 0]]
area = C.tri_area3(d['pos'][d['tri']])
skin = np.argmax(np.bincount(piece, area))
r = np.load(f'{approved}_raster2048.npz')
tid = r['tri_id']
keep = (tid >= 0) & (piece[np.maximum(tid, 0)] == skin)
Image.fromarray((keep * 255).astype(np.uint8)).save(out)
print('KEEP', out, 'faces', int((piece == skin).sum()), 'of', len(piece), 'texels', int(keep.sum()), 'of', int((tid >= 0).sum()))
