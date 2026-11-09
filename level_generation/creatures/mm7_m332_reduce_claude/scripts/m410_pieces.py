#!/usr/bin/env python3
"""Per-face piece labels of the m410 rest mesh (work/mesh_in.npz) by connected piece (size, position, dominant bone)
-> work/pieces.npy: 1 torso shell (vest, bare arms, hands, neck), 2 head (face, ears, scalp), 3 knitted cap,
4 trousers, 5 boots, 6 shoulder caps, 7 coin pouch (right hip), 8 pouch flap/back (right hip), 9 dagger sheath (left
hip, with its mouth piece), 10 wrist band and gold bangles, 11 belt with the chest strap, 12 buckle, 13 red face mask,
14 eyes, 15 boot ornament (left calf); work/soles.npy: boot faces below 6 cm; work/regmask.npy: per-face mean region
mask (R vest/shoulder caps/cap, G trousers) sampled at 4 points per face from the GLB's region mask."""
import io, json, struct, sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
reg = np.zeros(len(f), int)
for p in np.flatnonzero(sizes):
    m = fl == p; vs = np.unique(f[m]); lo, hi = v[vs].min(0), v[vs].max(0); cp = v[vs].mean(0); s = sizes[p]
    w = W[vs].mean(0); top = names[int(np.argmax(w))]
    if s > 3000:
        r = 1
    elif top == 'B_Head' and lo[2] > 1.55 and hi[2] > 1.75:
        r = 3
    elif top == 'B_Head' and s > 1000:
        r = 2
    elif top == 'B_Head' and s > 130:
        r = 13
    elif top == 'B_Head':
        r = 14
    elif s > 700 and cp[2] < 1.1:
        r = 4
    elif 'Calf' in top and s > 300:
        r = 5
    elif 'Calf' in top:
        r = 15
    elif 'Clavicle' in top:
        r = 6
    elif 'ForearmTwist' in top:
        r = 10
    elif cp[0] > 0.05 and w[names.index('B_Pelvis')] > 0.7:
        r = 9
    elif cp[0] < -0.1 and s > 500:
        r = 7
    elif cp[0] < -0.1:
        r = 8
    elif lo[1] < -0.09 and hi[1] - lo[1] < 0.03:
        r = 12
    else:
        r = 11
    reg[m] = r
soles = (reg == 5) & (v[f].mean(1)[:, 2] < 0.06)
# region mask (material extras openyamm_region_mask) sampled per face
raw = open(sys.argv[1] if len(sys.argv) > 1 else 'work/mm7_m332_source_pre_reduce.glb', 'rb').read()
nj = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + nj]); binary = raw[28 + nj:]
ti = doc['materials'][0]['extras']['openyamm_region_mask']['index']; im = doc['images'][doc['textures'][ti]['source']]
bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
mask = np.asarray(Image.open(io.BytesIO(binary[o:o + bv['byteLength']])).convert('RGB'), np.float32) / 255
H, Wd = mask.shape[:2]; uv = d['wuv'].reshape(-1, 3, 2)
bc = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
pts = np.einsum('kj,fjc->fkc', bc, uv)
px = np.clip((pts[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
rm = mask[py, px].mean(1)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles); np.save('work/regmask.npy', rm)
nm = {1: 'torso shell', 2: 'head', 3: 'cap', 4: 'trousers', 5: 'boots', 6: 'shoulder caps', 7: 'pouch', 8: 'pouch flap',
      9: 'sheath', 10: 'bands', 11: 'belt+strap', 12: 'buckle', 13: 'mask', 14: 'eyes', 15: 'boot ornament'}
print({nm[k]: int((reg == k).sum()) for k in nm}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()))
print('torso shell faces with vest mask R>0.5:', int(((reg == 1) & (rm[:, 0] > .5)).sum()))
