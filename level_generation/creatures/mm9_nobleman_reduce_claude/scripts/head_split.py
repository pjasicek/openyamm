#!/usr/bin/env python3
"""Face skin vs hair on the Nobleman's one head shell (Meshy fused face and hair; master part 20 for both). Per GLB face of the
NbHead primitive: the mean base colour of every tier at seven barycentric samples, its distance to that tier's skin colour
(median of the cheek faces), and the face's position. Hair = hair-coloured in every tier (no skin paint in any tier), cleaned by connectivity
(see below); everything else of part 20 stays face skin (jaw, chin and painted beards included).
Writes work/head_hair.npy (per glb_parts face, True = hair) and review/head_split.png (front, side, back, top).
Env: HUE_A (tier A hue below which a sample is skin, default 25), SKIN_B / SKIN_C (RGB distance, default 45 / 75), BROW_Z (default 0.855), FRONT_Y (default -0.045), SKIN_ISLAND / HAIR_ISLAND (40 / 12)."""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
HUE_A = float(os.environ.get('HUE_A', '25')); SKIN_B = float(os.environ.get('SKIN_B', '45')); SKIN_C = float(os.environ.get('SKIN_C', '75')); BROW_Z = float(os.environ.get('BROW_Z', '0.855'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_nobleman.glb', 'Nobleman')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; mat = g['mat']
V = np.load(HERE / 'work' / 'mesh_in.npz')['verts']
pr = D['NbHead']; P, UV, T = pr['P'], pr['UV'], pr['T']
Pb = np.c_[P[:, 0], -P[:, 2], P[:, 1]]; Pb[:, 2] += V[:, 2].min() - Pb[:, 2].min() + (Pb[:, 2].min() - Pb[:, 2].min())
off = np.flatnonzero(mat == 2)[0]; hp = part[mat == 2]
# glTF y-up -> the Blender rig frame (as glb_sets.py): z += V.zmin (the GLB stands on y = 0 at its lowest point)
allz = np.concatenate([D[k]['P'][:, 1] for k in D]); Pb = np.c_[P[:, 0], -P[:, 2], P[:, 1] - allz.min() + V[:, 2].min()]
B = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float); B /= B.sum(1, keepdims=True)
col = []
for t in 'ABC':
    im = np.asarray(Image.open(HERE / 'work' / f'tex_NbHead_{t}.png').convert('RGB'), np.float32); H, W = im.shape[:2]
    uv = np.einsum('sk,fkc->fsc', B, UV[T])
    x = np.clip((uv[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H, 0, H - 1).astype(int)
    col.append(im[y, x])                                                      # (f, 7, 3)
col = np.stack(col)                                                           # (3, f, 7, 3)
c = Pb[T].mean(1)
cheek = (hp == 20) & (np.abs(c[:, 0]) > 0.03) & (np.abs(c[:, 0]) < 0.055) & (c[:, 1] < -0.04) & (c[:, 2] > 0.79) & (c[:, 2] < 0.82)
ref = np.median(col[:, cheek].reshape(3, -1, 3), axis=1)
print('cheek faces', int(cheek.sum()), 'skin ref', ref.round(0).tolist())
dist = np.linalg.norm(col - ref[:, None, None], axis=-1)                     # (3, f, 7)
# tier A's blond reads close to skin in RGB: hue tells them apart (skin about 20 deg, blond about 30); B white and C brown by
# RGB distance (cheek p90 35 / 69, crown p1 53 / 89)
def hue(x):
    r, g_, b_ = x[..., 0], x[..., 1], x[..., 2]; mx = x.max(-1); mn = x.min(-1)
    return np.where(mx == r, 60 * (g_ - b_) / np.maximum(mx - mn, 1), 120)
skin_s = np.stack([(hue(col[0]) < HUE_A) & (col[0].max(-1) > 120), dist[1] < SKIN_B, dist[2] < SKIN_C])   # (3, f, 7)
skin_any = skin_s.mean(-1).max(0) > 0.15                              # some skin paint in some tier
# clean labels by connectivity (welded positions): skin islands under SKIN_ISLAND faces inside the hair are hair (stray
# skin-tone flecks in the hair paint), hair islands under HAIR_ISLAND faces inside the face are skin (brows, beard flecks);
# the front of the face below the brow (y < FRONT_Y) is skin whatever its paint (painted beards on the jaw and chin)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
_, wv = np.unique(np.round(Pb, 6), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]
ed = np.concatenate([np.sort(FT[:, [0, 1]], 1), np.sort(FT[:, [1, 2]], 1), np.sort(FT[:, [2, 0]], 1)])
fid = np.tile(np.arange(len(T)), 3); key = ed[:, 0] * (wv.max() + 1) + ed[:, 1]
o = np.argsort(key); ks = key[o]; same = np.flatnonzero(ks[1:] == ks[:-1])
fa, fb = fid[o][same], fid[o][same + 1]
def islands(sel):
    m = sel[fa] & sel[fb]
    A = coo_matrix((np.ones(int(m.sum())), (fa[m], fb[m])), shape=(len(T), len(T)))
    _, lab = connected_components(A, directed=False); lab = np.where(sel, lab, -1)
    cnt = np.bincount(lab[lab >= 0], minlength=lab.max() + 1)
    return np.where(sel, cnt[np.maximum(lab, 0)], 0)
HAIR_MAIN = int(os.environ.get('HAIR_MAIN', '200')); SI = int(os.environ.get('SKIN_ISLAND', '40')); HI = int(os.environ.get('HAIR_ISLAND', '12')); FRONT_Y = float(os.environ.get('FRONT_Y', '-0.045'))
skin = (hp == 20) & skin_any
skin &= islands(skin) >= SI
hair = (hp == 20) & ~skin
hair &= islands(hair) >= HI
hair &= ~((c[:, 1] < FRONT_Y) & (c[:, 2] < BROW_Z))
hair &= islands(hair) >= HAIR_MAIN                                # only the hair mass itself (the jaw-corner flecks stay face)
print('head faces', len(T), 'part20', int((hp == 20).sum()), 'hair', int(hair.sum()), 'skin-any', int((skin_any & (hp == 20)).sum()))
out = np.zeros(len(part), bool); out[off:off + len(T)] = hair; np.save(HERE / 'work' / 'head_hair.npy', out)
# diagnostic views (painter's order, PIL)
from PIL import ImageDraw
cls = np.where(hp == 22, 3, np.where(hair, 1, np.where(skin_any, 0, 2)))   # yellow: hair paint kept as face
cc = [(230, 150, 128), (50, 100, 230), (240, 215, 25), (20, 20, 20)]
S = 1600; out_im = Image.new('RGB', (4 * 420, 520), 'white'); X = Pb[T]
views = [((0, 2), -1, 1), ((1, 2), 0, 1), ((0, 2), 1, -1), ((0, 1), 2, 1)]
if os.environ.get('SIDE_NEG'): X = X * [-1, 1, 1]     # (axes, depth axis/sign, x flip)
for k, ((i, j), dax, fl) in enumerate(views):
    dz = X[..., abs(dax) if dax != -1 else 1].mean(1) * (-1 if dax == -1 else 1) if dax != 0 else X[..., 0].mean(1)
    if k == 2: dz = X[..., 1].mean(1)
    if k == 3: dz = X[..., 2].mean(1)
    if k == 0: dz = -X[..., 1].mean(1)
    o = np.argsort(dz); dr = ImageDraw.Draw(out_im)
    xs = X[..., i] * fl; ys = X[..., j]
    x0, y1 = xs.min(), ys.max()
    for f in o:
        pts = [(k * 420 + 10 + (xs[f, m] - x0) * S, 10 + (y1 - ys[f, m]) * S) for m in range(3)]
        dr.polygon(pts, fill=cc[cls[f]], outline=(0, 0, 0))
out_im.save(HERE / 'review' / 'head_split.png')
