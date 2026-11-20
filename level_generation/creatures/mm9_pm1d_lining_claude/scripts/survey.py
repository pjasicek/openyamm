#!/usr/bin/env python3
"""Per piece of the body primitive: faces, dominant bones, region labels (body mask RGBA), y range. Usage: survey.py <glb>"""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_common as C  # noqa: E402
doc, binary, nd, prims, jn = C.load(sys.argv[1])
for name in ('PM1d_C', 'PM1dHead_C'):
    d = prims[name]; mat = next(m for m in doc['materials'] if m['name'] == name)
    mask = C.image(doc, binary, mat['extras']['openyamm_region_mask']['index'])
    col = C.image(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index'])
    inv = C.weld(d['P']); TT = inv[d['T']]; pc = C.pieces(TT, inv.max() + 1); fp = pc[TT[:, 0]]
    dj = d['J'][np.arange(len(d['J'])), d['W'].argmax(1)]
    uvc = d['UV'][d['T']].mean(1); m = C.texel(mask, uvc); lab = np.where(m.max(1) > 0.3, m.argmax(1), 4)
    print('==', name, 'mask', mask.shape, 'colour', col.shape)
    for p in sorted(set(fp), key=lambda p: -(fp == p).sum()):
        f = fp == p
        bones = Counter(jn[j] for j in dj[d['T'][f, 0]]).most_common(4)
        labs = Counter('RGBAn'[x] for x in lab[f])
        ys = d['P'][d['T'][f].ravel(), 1]
        print(f'  piece {p:5d} {f.sum():5d} tris y {ys.min():.3f}..{ys.max():.3f} regions {dict(labs)} bones {bones}')
