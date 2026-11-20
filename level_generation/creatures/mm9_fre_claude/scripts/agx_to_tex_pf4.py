#!/usr/bin/env python3
"""The face renders that Codex repaints (view_uvtex.py, Blender's default AgX view transform) are not the texture's colours (a cheek texel
230/146/106 renders 195/142/116), so a projected repaint came out paler; align_face's skin gains used to hide that, and also cancelled any
warmer skin the repaint asked for. This maps a repaint from the AgX render space back to texture space: pairs of AgX and Standard renders
of the same head (args) give, for each repaint pixel, its nearest AgX colours' Standard colours plus the pixel's own offset from them.
Args: <repaint png> <out png> <agx render> <std render> [<agx render> <std render> ...]"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
src, dst = sys.argv[1:3]; pairs = sys.argv[3:]
A, B = [], []
for i in range(0, len(pairs), 2):
    a = np.asarray(Image.open(pairs[i]).convert('RGB'), np.float32).reshape(-1, 3); b = np.asarray(Image.open(pairs[i + 1]).convert('RGB'), np.float32).reshape(-1, 3)
    A.append(a[::7]); B.append(b[::7])
A = np.vstack(A); B = np.vstack(B)
key, ix = np.unique(np.round(A / 2).astype(int), axis=0, return_index=True); A, B = A[ix], B[ix]
kd = cKDTree(A)
im = np.asarray(Image.open(src).convert('RGB'), np.float32); flat = im.reshape(-1, 3)
d, j = kd.query(flat, k=8); w = 1.0 / np.maximum(d, 1.0); w /= w.sum(1, keepdims=True)
out = ((B[j] + (flat[:, None, :] - A[j])) * w[..., None]).sum(1)
Image.fromarray(np.clip(out, 0, 255).reshape(im.shape).astype('u1')).save(dst)
print('AGX2TEX', dst, 'pairs', len(A), 'mean shift', np.round((out - flat).mean(0), 1).tolist())
