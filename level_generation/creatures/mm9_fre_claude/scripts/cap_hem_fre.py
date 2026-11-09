#!/usr/bin/env python3
"""Fre (2026-11-04, viewer r3 back views): between the hair cap's hem and the bodice's collar at the back of the neck the viewer showed
background slivers, F1's ragged collar points and a flat yellow strip of unpainted collar. The hem's outer rings behind the ears are
lowered DROP m and eased OUT m away from the neck axis, so the hair overlaps the collar the way a bob rests on it. Positions only (the
paint and UVs of the cap stay; hair strands stretch by a few percent); lining and rim rows follow their outer twins' parameters.
Args: <in uv npz> <out uv npz> [DROP OUT]   (project folder; ring/alpha parameters from work/asm_frozen.npz)"""
import sys
import numpy as np
U = dict(np.load(sys.argv[1])); DROP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.022; OUT = float(sys.argv[4]) if len(sys.argv) > 4 else 0.006
A = np.load('work/asm_frozen.npz'); names = [str(x) for x in A['names']]; K4 = names.index('hood4')
par = A['f4_param'][U['orig']]; cap = A['comp'][U['orig']] == K4
K = par[cap, 2].max()
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
al = par[:, 1]; ring = par[:, 2]
w_back = ss(al, 15, 45) * (1 - ss(al, 135, 165))                     # behind the ears (alpha 90 = the nape)
w_ring = ss(ring, K - 3, K)                                            # the outer three rings, full at the hem
w = np.where(cap, w_back * w_ring, 0.0)
co = U['co'].copy()
rad = co[:, :2] - np.array([0.0, 0.02]); rn = np.linalg.norm(rad, axis=1, keepdims=True); rad = rad / np.maximum(rn, 1e-9)
co[:, 2] -= DROP * w; co[:, :2] += OUT * w[:, None] * rad
U['co'] = co; np.savez(sys.argv[2], **U)
print('CAPHEM moved', int((w > 0.01).sum()), 'rows, drop mm', DROP * 1000, 'out mm', OUT * 1000)
