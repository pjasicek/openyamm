#!/usr/bin/env python3
"""Thicken the bare arms of an installed actor GLB in place (user review 2026-10-30: the MM6 female peasant's arms
"too thin, not natural"; ring fits of this Smart Topology body gave 28 / 32 / 14 mm radii below the sleeve, at the
elbow and at the wrist, where a grown woman's are about 40 / 37 / 24). In the full-detail mesh every arm vertex (arm,
forearm, twist and hand weight > 0.3 on one side) whose base-colour texel is skin is pushed out along its normal by
d(u), u the position along shoulder -> elbow -> wrist (bind joints): ADD mm at the elbow, the forearm and the wrist,
ramping in over 2 cm below the sleeve hem (the lowest sleeve texel on that arm) and out over 3 cm into the hand, scaled
by the arm weight. LOD and shadow meshes take the displacement of the nearest full-detail vertex. Skin, UVs,
textures and animation are untouched. Usage: arm_thicken.py in.glb out.glb --prefix mixamorig: [--add 11 6 9 9]"""
import argparse, io, sys, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gltf_rig import Glb

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--prefix', default='mixamorig:')
ap.add_argument('--add', nargs=4, type=float, default=[11, 6, 9, 9], help='mm below the hem, elbow, mid forearm, wrist')
a = ap.parse_args()
g = Glb(a.src); d = g.doc; P_ = a.prefix
skin = d['skins'][0]; J = skin['joints']; IBM = g.acc(skin['inverseBindMatrices']).reshape(-1, 4, 4)
bind = {g.names[j]: np.linalg.inv(IBM[k].T)[:3, 3] for k, j in enumerate(J)}
main = next(m for m in d['meshes'] if 'LOD' not in m['name'] and 'Shadow' not in m['name'])
pr = main['primitives'][0]
mat = d['materials'][pr['material']]
tex = d['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
img_def = d['images'][tex['source']]; bv = d['bufferViews'][img_def['bufferView']]
img = np.asarray(Image.open(io.BytesIO(bytes(g.bin[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))).convert('RGB'), float) / 255
H, Wd = img.shape[:2]
P = g.acc(pr['attributes']['POSITION']).astype(float); N = g.acc(pr['attributes']['NORMAL']).astype(float)
UV = g.acc(pr['attributes']['TEXCOORD_0']).astype(float)
Jt = g.acc(pr['attributes']['JOINTS_0']).astype(int); Wt = g.acc(pr['attributes']['WEIGHTS_0']).astype(float)
col = img[np.clip((UV[:, 1] % 1) * H, 0, H - 1).astype(int), np.clip((UV[:, 0] % 1) * Wd, 0, Wd - 1).astype(int)]
mx = col.max(1); sat = (mx - col.min(1)) / np.maximum(mx, 1e-3)
is_skin = (col[:, 0] > col[:, 2] + 0.08) & (sat > 0.15) & (sat < 0.65) & (mx > 0.35)
disp = np.zeros_like(P)
for side in ('Left', 'Right'):
    names = [P_ + side + 'Arm', P_ + side + 'ForeArm', P_ + side + 'Hand', side + 'ForeArmTwist1', side + 'ForeArmTwist2']
    ids = [J.index(g.node(n)) for n in names if n in g.names and g.node(n) in J]
    w = sum(np.where(Jt[:, k:k + 1] == np.array(ids)[None], Wt[:, k:k + 1], 0).sum(1) for k in range(4))
    S_, E, Wr = bind[P_ + side + 'Arm'], bind[P_ + side + 'ForeArm'], bind[P_ + side + 'Hand']
    L1, L2 = np.linalg.norm(E - S_), np.linalg.norm(Wr - E); Lt = L1 + L2
    best_u = np.zeros(len(P)); best_r = np.full(len(P), 9.0)
    for A, B, off, L in ((S_, E, 0.0, L1), (E, Wr, L1, L2)):
        dd = (B - A) / L; t = (P - A) @ dd; tc = np.clip(t, 0, L if off else L); q = A + np.outer(tc, dd)
        r = np.linalg.norm(P - q, axis=1); u = (off + t) / Lt
        better = r < best_r; best_r[better] = r[better]; best_u[better] = u[better]
    arm = (w > 0.3) & (best_r < 0.1)
    sleeve_u = best_u[arm & ~is_skin & (best_u < 0.52)]
    hem = float(np.percentile(sleeve_u, 98)) if len(sleeve_u) else 0.3
    ue = L1 / Lt; hand_end = 1.0 + 0.03 / Lt
    du = np.interp(best_u, [hem, hem + 0.02 / Lt, ue, (ue + 1) / 2, 1.0, hand_end],
                   [0, a.add[0], a.add[1], a.add[2], a.add[3], 0], left=0, right=0) / 1000
    k = np.clip((w - 0.3) / 0.4, 0, 1) * (arm & is_skin)
    disp += N * (du * k)[:, None]
    print('THICKEN', side, 'sleeve hem u %.2f (elbow %.2f)' % (hem, ue), 'verts pushed', int((du * k > 1e-4).sum()),
          'max mm %.1f' % (du * k).max() * 1 if False else 'max mm %.1f' % ((du * k).max() * 1000))
newP = P + disp
moved = np.linalg.norm(disp, axis=1) > 1e-6
tree = cKDTree(P)
done = set()
for m in d['meshes']:
    for p in m['primitives']:
        ai = p['attributes']['POSITION']
        if ai in done:
            continue
        done.add(ai)
        Q = g.acc(ai).astype(float)
        if ai == pr['attributes']['POSITION']:
            g.write_acc(ai, newP.astype(np.float32)); continue
        dist, idx = tree.query(Q)
        Qn = Q + np.where((dist < 0.02)[:, None], disp[idx], 0)
        g.write_acc(ai, Qn.astype(np.float32))
        print('THICKEN', m['name'], 'verts moved', int(((dist < 0.02) & moved[idx]).sum()))
g.save(a.dst)
print('SAVED', a.dst)
