#!/usr/bin/env python3
"""Per piece of each LOD0 primitive of the Bjarni GLB: faces, dominant bones, y range, mean colour (no region mask on Bjarni:
one skin). Usage: survey.py <glb>"""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_common as C  # noqa: E402
doc, binary, nd, prims, jn = C.load(sys.argv[1])
for name, d in prims.items():
    mat = next(m for m in doc['materials'] if m['name'] == name)
    col = C.image(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index'])
    inv = C.weld(d['P']); TT = inv[d['T']]; pc = C.pieces(TT, inv.max() + 1); fp = pc[TT[:, 0]]
    dj = d['J'][np.arange(len(d['J'])), d['W'].argmax(1)]
    uvc = d['UV'][d['T']].mean(1); rgb = C.texel(col, uvc)[:, :3]
    print('==', name, 'colour', col.shape)
    for p in sorted(set(fp), key=lambda p: -(fp == p).sum()):
        f = fp == p
        if f.sum() < 15:
            continue
        bones = Counter(jn[j].replace('Bip01 ', '') for j in dj[d['T'][f, 0]]).most_common(4)
        ys = d['P'][d['T'][f].ravel(), 1]
        print(f'  piece {p:5d} {f.sum():5d} tris y {ys.min():.3f}..{ys.max():.3f} rgb {np.round(rgb[f].mean(0), 2)} bones {bones}')
