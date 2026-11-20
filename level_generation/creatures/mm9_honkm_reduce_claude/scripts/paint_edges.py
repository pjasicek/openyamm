#!/usr/bin/env python3
"""Body-set faces that carry a paint boundary (a60's close-ups: the neckline's skin ellipse grew and a pale patch spread on the
Elder's blue collar when the robe faces across them were collapsed; the texture guard's mean test lets a boundary slide): per
face, the base colour (blurred 1.5 px) and the region mask at 10 barycentric points; a face whose samples span more than
DRGB (0-255, max over RGB of max-min) in the base colour or DMASK (0-255) in any mask channel is kept, plus one ring of
welded neighbours (RING=1). Usage: paint_edges.py <sets tag> <out name> -> work/<out>.npy per GLB face"""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
DRGB = float(os.environ.get('DRGB', '70')); DMASK = float(os.environ.get('DMASK', '90')); RING = int(os.environ.get('RING', '1'))
tag, outn = sys.argv[1:3]
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
P, T, UV = D['HonkM_A']['P'], D['HonkM_A']['T'], D['HonkM_A']['UV']; n = len(T)
base = ndimage.gaussian_filter(np.asarray(Image.open(HERE / 'work' / 'tex_HonkM_A_0.png').convert('RGB'), np.float32), (1.5, 1.5, 0))
mask = np.asarray(Image.open(HERE / 'work' / 'tex_HonkM_A_1.png').convert('RGBA'), np.float32)
B = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1], [8, 1, 1], [1, 8, 1], [1, 1, 8]], float)
B /= B.sum(1, keepdims=True)
uv = np.einsum('sk,fkc->fsc', B, UV[T])
def samp(im):
    H, W = im.shape[:2]
    return im[np.clip((uv[..., 1] % 1) * H, 0, H - 1).astype(int), np.clip((uv[..., 0] % 1) * W, 0, W - 1).astype(int)]
cb, cm = samp(base), samp(mask)
span_b = (cb.max(1) - cb.min(1)).max(1); span_m = (cm.max(1) - cm.min(1)).max(1)
cls = s['cls'][:n]
cand = np.isin(cls, [CLS.index(c) for c in ('robe', 'lined')])
hit = cand & ((span_b > DRGB) | (span_m > DMASK))
w = weld_ids(P); FT = w[T]
for _ in range(RING):
    vh = np.zeros(w.max() + 1, bool); vh[FT[hit].ravel()] = True
    hit |= cand & vh[FT].any(1)
out = np.zeros(len(s['cls']), bool); out[:n] = hit
print('PAINTEDGES', int(hit.sum()), 'of robe+lined', int(cand.sum()), 'base-only', int((cand & (span_b > DRGB)).sum()), 'mask-only', int((cand & (span_m > DMASK)).sum()))
np.save(HERE / 'work' / f'{outn}.npy', out)
