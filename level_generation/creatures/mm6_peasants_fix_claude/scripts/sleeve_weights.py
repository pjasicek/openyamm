#!/usr/bin/env python3
"""Make the puff sleeves and upper arms follow the upper-arm bone (user review 2026-10-30: the hanging arm slid out of
the sleeve's inner edge and the upper arm pinched under it). The female peasant's bind pose holds the arms 37 deg out
and 18 deg back, and her shoulder vertices were split about half and half between the upper arm and the clavicle and
spine, so a hanging arm turned the sleeve only halfway. In the full-detail mesh, every vertex near the upper arm that
the arm already influences and that is sleeve (white texel) or arm skin below SKIN_T moves its torso-side share
(clavicle, spine, neck) onto the upper-arm bone by a smoothstep along the arm: none above T0, all below T1 (metres
from the upper-arm head along the bind arm), faded out within SEAM of the bodice. LOD and shadow meshes copy joints
and weights from the nearest changed full-detail vertex.
Usage: sleeve_weights.py in.glb out.glb [--prefix mixamorig:] [--t0] [--t1] [--radius] [--seam] [--skin-t]"""
import argparse, io, sys, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gltf_rig import Glb

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--prefix', default='mixamorig:')
ap.add_argument('--t0', type=float, default=-0.10); ap.add_argument('--t1', type=float, default=0.0)
ap.add_argument('--radius', type=float, default=0.14); ap.add_argument('--seam', type=float, default=0.03)
ap.add_argument('--skin-t', type=float, default=0.06)
a = ap.parse_args()
g = Glb(a.src); d = g.doc
skin = d['skins'][0]; J = skin['joints']; IBM = g.acc(skin['inverseBindMatrices']).reshape(-1, 4, 4)
names = [g.names[j] for j in J]; slot = {n: k for k, n in enumerate(names)}
bind = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}
torso = np.array([n == a.prefix + 'Neck' or n.startswith(a.prefix + 'Spine') or n.endswith('Shoulder') for n in names])

main = next(m for m in d['meshes'] if 'LOD' not in m['name'] and 'Shadow' not in m['name'])
pr = main['primitives'][0]
mat = d['materials'][pr['material']]
tex = d['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
bv = d['bufferViews'][d['images'][tex['source']]['bufferView']]; o = bv.get('byteOffset', 0)
img = np.asarray(Image.open(io.BytesIO(bytes(g.bin[o:o + bv['byteLength']]))).convert('RGB'), float) / 255
H, Wd = img.shape[:2]
P = g.acc(pr['attributes']['POSITION']).astype(float); UV = g.acc(pr['attributes']['TEXCOORD_0']).astype(float)
Jt = g.acc(pr['attributes']['JOINTS_0']).astype(int); Wt = g.acc(pr['attributes']['WEIGHTS_0']).astype(float)
col = img[np.clip((UV[:, 1] % 1) * H, 0, H - 1).astype(int), np.clip((UV[:, 0] % 1) * Wd, 0, Wd - 1).astype(int)]
bodice = (col[:, 1] > col[:, 0] + 0.04) & (col[:, 1] > col[:, 2] + 0.04)
sleeve = col.min(1) > 0.55                                        # white cloth (the chest skin stays put)
near_bodice = cKDTree(P[bodice]).query(P)[0]                     # the armhole seam keeps its weights: the sleeve
seam = np.clip(near_bodice / a.seam, 0, 1)                         # top otherwise pokes out through the bodice
changed = np.zeros(len(P), bool)
for side in ('Left', 'Right'):
    arm = slot[a.prefix + side + 'Arm']
    A = bind[a.prefix + side + 'Arm']; E = bind[a.prefix + side + 'ForeArm']
    ax = (E - A) / np.linalg.norm(E - A)
    t = (P - A) @ ax; r = np.linalg.norm((P - A) - np.outer(t, ax), axis=1)
    has = Jt == arm; wa = (Wt * has).sum(1)
    sel = (wa > 0.02) & (r < a.radius) & (t > a.t0) & ~bodice & (sleeve | (t > a.skin_t))
    x = np.clip((t - a.t0) / (a.t1 - a.t0), 0, 1); k = x * x * (3 - 2 * x) * seam
    moved = Wt * torso[Jt] * (k * sel)[:, None]
    Wt = Wt - moved
    Wt[has] += np.repeat(moved.sum(1), 4).reshape(-1, 4)[has]       # one upper-arm slot per vertex
    changed |= moved.sum(1) > 1e-4
    print('SLEEVE', side, 'vertices reweighted', int((moved.sum(1) > 1e-4).sum()))
Wt /= Wt.sum(1, keepdims=True)
g.write_acc(pr['attributes']['WEIGHTS_0'], Wt.astype(np.float32))

tree = cKDTree(P)
done = {pr['attributes']['WEIGHTS_0']}
for m in d['meshes']:
    for p in m['primitives']:
        if p['attributes']['WEIGHTS_0'] in done:
            continue
        done.add(p['attributes']['WEIGHTS_0'])
        Q = g.acc(p['attributes']['POSITION']).astype(float)
        jq = g.acc(p['attributes']['JOINTS_0']).astype(int); wq = g.acc(p['attributes']['WEIGHTS_0']).astype(float)
        dist, idx = tree.query(Q)
        take = (dist < 0.02) & changed[idx]
        jq[take] = Jt[idx[take]]; wq[take] = Wt[idx[take]]
        g.write_acc(p['attributes']['JOINTS_0'], jq.astype(np.uint8))
        g.write_acc(p['attributes']['WEIGHTS_0'], wq.astype(np.float32))
        if 'WEIGHTS_1' in p['attributes']:                         # LOD1 carries eight influences: a copied vertex
            w1 = g.acc(p['attributes']['WEIGHTS_1']).astype(float)  # takes LOD0's four only
            w1[take] = 0
            g.write_acc(p['attributes']['WEIGHTS_1'], w1.astype(np.float32))
        print('SLEEVE', m['name'], 'vertices copied', int(take.sum()))
g.save(a.dst)
print('SAVED', a.dst)
