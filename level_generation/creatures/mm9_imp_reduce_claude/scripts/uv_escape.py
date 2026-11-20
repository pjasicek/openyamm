#!/usr/bin/env python3
"""Faces whose UV triangle leaves the source's painted charts: rasterise the installed LOD0 UV triangles of each primitive
(coverage mask at RES, dilated by DIL texels), sample every candidate face's UV triangle and report faces with more than FRAC of
their samples outside the coverage (a seam-slid corner that drags a face across a gutter or into another island: the smeared
chevron on the Embalmed forearm, 2026-11-04). Imp copy (imp-reduce-20261104) of mm9_mummy_reduce_claude/scripts/uv_escape.py, reading the LOD0 primitives with bglbio.
Usage: uv_escape.py <installed.glb> <candidate.glb> [out.npy per candidate face]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bglbio as gb  # noqa: E402
RES = 2048; DIL = 2; FRAC = 0.02
def load(path):
    doc, b = gb.read(path); node = next(n for n in doc['nodes'] if n.get('name') == 'Imp' and 'mesh' in n)
    return {p['material'][:-2]: {'UV': p['TEXCOORD_0'].astype(float), 'T': p['T'], 'P': p['POSITION'].astype(float)}
            for p in gb.prims(doc, b, node['mesh'])}
S = load(sys.argv[1]); C = load(sys.argv[2])
bad_all = []
for name in ('Imp', 'ImpHead'):
    im = Image.new('L', (RES, RES)); d = ImageDraw.Draw(im)
    for t in S[name]['T']:
        d.polygon([tuple(S[name]['UV'][k] * RES) for k in t], fill=255)
    cov = ndimage.binary_dilation(np.asarray(im) > 0, iterations=DIL)
    UV, T, P = C[name]['UV'], C[name]['T'], C[name]['P']
    k = 12; i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
    w = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
    s = np.einsum('sk,fkc->fsc', w, UV[T])
    x = np.clip((s[..., 0] * RES).astype(int), 0, RES - 1); y = np.clip((s[..., 1] * RES).astype(int), 0, RES - 1)
    out = (~cov[y, x]).mean(1)
    bad = out > FRAC; bad_all.append(bad)
    print(name, len(T), 'faces leaving the charts', int(bad.sum()), 'worst', np.round(np.sort(out)[-5:], 3).tolist())
    for f in np.flatnonzero(bad)[:20]:
        print('   face', f, 'outside', round(float(out[f]), 3), 'centroid', P[T[f]].mean(0).round(3))
if len(sys.argv) > 3:
    np.save(sys.argv[3], np.concatenate(bad_all))
