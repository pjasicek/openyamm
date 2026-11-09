#!/usr/bin/env python3
"""v2c muscle definition (user review 2026-10-21: "muscles need to stand out more ... chest, abs, arms"): a
multi-scale convexity map of the body skin baked from the rest mesh (work/rest_v6.npz from dump_posed.py on
work/rig_v6.blend, rest) into both UV layouts (work/uvraster_{UVMap,HeadUV}.npz on the same mesh).
Per skin vertex (garment 0): convexity = -(umbrella vector . vertex normal) / mean edge length (positive on muscle
bellies, negative in the separations: pec border, abs grid, deltoid/biceps/triceps grooves, serratus). Two band-passed scales:
FINE (2 minus 12 diffusion passes over the skin edges) and MUSCLE (8 minus 40 passes); each normalised by its 97th percentile of |value|
on the torso and arms, mixed 0.4 / 0.6, blended with a muscle-scale top-light term (band-passed upward normal, CAV_TOP 0.5) and
clipped to -1..1. Texels take the inverse-distance mean of their 4 nearest
skin vertices (rest positions). compose_m286.py multiplies the skin albedo by 1 + CAV_GAIN * cavity.
Writes work/cavity_UVMap.npy, work/cavity_HeadUV.npy and a preview work/cavity_UVMap.png."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parents[1]
W = P / 'work'
d = np.load(W / 'rest_v6.npz')
co, tris, gar, piece = d['co'], d['tris'], d['garment'], d['piece']
skin = (gar == 0) & (piece < 1000)
n = len(co)
fn = np.cross(co[tris[:, 1]] - co[tris[:, 0]], co[tris[:, 2]] - co[tris[:, 0]])
vn = np.zeros_like(co)
for k in range(3):
    np.add.at(vn, tris[:, k], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
E = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
E = np.unique(np.sort(E, axis=1), axis=0)
E = E[skin[E[:, 0]] & skin[E[:, 1]]]
acc = np.zeros_like(co); deg = np.zeros(n); el = np.zeros(n)
np.add.at(acc, E[:, 0], co[E[:, 1]]); np.add.at(acc, E[:, 1], co[E[:, 0]])
np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
np.add.at(el, E[:, 0], L); np.add.at(el, E[:, 1], L)
ok = deg > 0
umb = np.where(ok[:, None], acc / np.maximum(deg, 1)[:, None] - co, 0)
conv = np.where(ok, -(umb * vn).sum(1) / np.maximum(el / np.maximum(deg, 1), 1e-6), 0)


def diffuse(x, passes):
    x = x.copy()
    for _ in range(passes):
        a = np.zeros(n); dg = np.zeros(n)
        np.add.at(a, E[:, 0], x[E[:, 1]]); np.add.at(a, E[:, 1], x[E[:, 0]])
        np.add.at(dg, E[:, 0], 1); np.add.at(dg, E[:, 1], 1)
        x = np.where(dg > 0, 0.5 * x + 0.5 * a / np.maximum(dg, 1), x)
    return x


body_zone = skin & (co[:, 2] > 0.95) & (co[:, 2] < 1.62)        # torso, shoulders, arms (normalisation reference)
# band-pass: the limbs' and torso's own cylinder curvature (broad, 40 passes) is removed, only muscle relief stays
broad = diffuse(conv, 40)
fine, muscle = diffuse(conv, 2) - diffuse(conv, 12), diffuse(conv, 8) - broad
fine /= np.percentile(np.abs(fine[body_zone]), 97); muscle /= np.percentile(np.abs(muscle[body_zone]), 97)
# muscle-scale top light (the native's key light): band-passed upward normal, upper faces of each muscle lighter,
# under the pecs and over each abs block darker; the broad up/down orientation is removed (no doubled lighting)
nz = diffuse(vn[:, 2], 3) - diffuse(vn[:, 2], 30)
nz /= np.percentile(np.abs(nz[body_zone]), 97)
TOP = float(__import__('os').environ.get('CAV_TOP', '0.5'))
cav = np.clip((1 - TOP) * (0.4 * fine + 0.6 * muscle) + TOP * nz, -1, 1)
cav[~skin] = 0
sv = np.where(skin)[0]
tree = cKDTree(co[sv])
for layer in ('UVMap', 'HeadUV'):
    R = np.load(W / f'uvraster_{layer}.npz')
    pc, pos = R['piece'], R['pos']
    m = pc == 0
    dist, idx = tree.query(pos[m], k=4)
    w = 1.0 / np.maximum(dist, 1e-4)
    out = np.zeros(pc.shape, np.float32)
    out[m] = (cav[sv[idx]] * w).sum(1) / w.sum(1)
    np.save(W / f'cavity_{layer}.npy', out)
    if layer == 'UVMap':
        Image.fromarray(((out * 0.5 + 0.5) * 255).astype(np.uint8)).save(W / 'cavity_UVMap.png')
    print('CAVITY', layer, 'texels', int(m.sum()), 'p5/p50/p95', np.round(np.percentile(out[m], [5, 50, 95]), 3))
