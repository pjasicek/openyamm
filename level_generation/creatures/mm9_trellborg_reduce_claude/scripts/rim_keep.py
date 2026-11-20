#!/usr/bin/env python3
"""Thin painted strap rims of tier A (the white edges of the harness straps over the shoulders and chest, near-white in
trell_body_a_final.png) bend under the texture-aware collapse (f81: a jog in the left shoulder strap rim). Body faces whose tier A
paint is near-white (luminance > LUM) at any of 7 sample points, plus one ring, are kept exactly. Usage: rim_keep.py <base keep> <out>"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
LUM = float(os.environ.get('LUM', .72)); ZMIN = float(os.environ.get('ZMIN', -0.1))
d = np.load(HERE / 'work/mesh_in.npz'); V, F = d['verts'], d['faces']; L = np.load(HERE / 'work/labels.npz')
im = np.asarray(Image.open(HERE.parent / 'mm9_trellborg_claude/textures/trell_body_a_final.png').convert('RGB'), np.float32) / 255
H, W = im.shape[:2]
w = d['wuv'].reshape(-1, 3, 2)
B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
uv = np.einsum('kb,fbc->fkc', B, w)
c = im[np.clip(((1 - uv[..., 1]) * H).astype(int), 0, H - 1), np.clip(((uv[..., 0] % 1) * W).astype(int), 0, W - 1)]
white = ((c @ [.299, .587, .114]) > LUM).any(1) & (L['mat'] == 0) & (L['reg'] == 1) & (V[F][:, :, 2].mean(1) > ZMIN)
vs = np.zeros(len(V), bool); vs[F[white].reshape(-1)] = True; ring = vs[F].any(1) & (L['reg'] == 1)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= ring
np.save(sys.argv[2], keep); print('RIMKEEP white', int(white.sum()), 'with ring', int(ring.sum()), 'kept', n0, '->', int(keep.sum()))
