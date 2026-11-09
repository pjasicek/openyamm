#!/usr/bin/env python3
"""Fill the flat grey Meshy texels of hair faces (installed model: a grey diamond on the hair behind the left ear) with
hair texture: each texel inside a flagged face's UV triangle (dilated 2 px) takes the colour of the nearest clean
hair sample in rest-pose 3D. Flagged: hair-piece faces whose 16 samples have std < 0.02 and are neutral grey.
Usage: hair_fill.py -> work/basecolor_fixed.png"""
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; g = np.load('work/groups.npy')
im = Image.open('work/basecolor.png'); img = np.asarray(im.convert('RGB'), np.float32); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); tri = v[f]
B = np.random.default_rng(0).dirichlet((1, 1, 1), 16)
px = lambda u: np.stack([u[..., 0] % 1 * W, (1 - u[..., 1] % 1) * H], -1)
s = px(np.einsum('sk,fkc->fsc', B, uv)).astype(int); s[..., 0] = s[..., 0].clip(0, W - 1); s[..., 1] = s[..., 1].clip(0, H - 1)
col = img[s[..., 1], s[..., 0]] / 255
hair = g == 2; flat = hair & (col.std(1).mean(1) < .02) & (np.abs(col.mean(1)[:, 0] - col.mean(1)[:, 2]) < .03)
print('flat hair faces', np.where(flat)[0].tolist())
# clean hair samples: dense points with their texel colour
Bd = np.random.default_rng(1).dirichlet((1, 1, 1), 64); ok = np.where(hair & ~flat)[0]
pts = np.einsum('sk,fkc->fsc', Bd, tri[ok]).reshape(-1, 3)
sp = px(np.einsum('sk,fkc->fsc', Bd, uv[ok])).reshape(-1, 2).astype(int)
scol = img[sp[:, 1].clip(0, H - 1), sp[:, 0].clip(0, W - 1)]; tree = cKDTree(pts)
out = img.copy(); changed = 0
for i in np.where(flat)[0]:
    P = px(uv[i]); x0, y0 = np.floor(P.min(0)).astype(int) - 3; x1, y1 = np.ceil(P.max(0)).astype(int) + 3
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); q = np.stack([xs + .5, ys + .5], -1).reshape(-1, 2)
    T = np.array([[P[1, 0] - P[0, 0], P[2, 0] - P[0, 0]], [P[1, 1] - P[0, 1], P[2, 1] - P[0, 1]]])
    l12 = np.linalg.solve(T, (q - P[0]).T).T; bary = np.c_[1 - l12.sum(1), l12]
    inside = (bary >= -1e-6).all(1).reshape(xs.shape); inside = binary_dilation(inside, iterations=2)
    bc = np.clip(bary, 0, None); bc /= bc.sum(1, keepdims=True)
    p3 = bc @ tri[i]; _, nn = tree.query(p3)
    m = inside.ravel() & (xs.ravel() >= 0) & (xs.ravel() < W) & (ys.ravel() >= 0) & (ys.ravel() < H)
    # only overwrite texels that are themselves flat grey (do not touch neighbouring painted hair)
    cur = img[ys.ravel()[m], xs.ravel()[m]] / 255
    grey = (np.abs(cur[:, 0] - cur[:, 2]) < .04) & (cur.mean(1) > .55)
    yy, xx = ys.ravel()[m][grey], xs.ravel()[m][grey]
    out[yy, xx] = scol[nn[m][grey]]; changed += int(grey.sum())
Image.fromarray(out.clip(0, 255).astype(np.uint8)).convert(im.mode).save('work/basecolor_fixed.png')
print('FILLED', changed, 'texels')
