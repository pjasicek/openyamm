#!/usr/bin/env python3
"""Final torso images: seam bands blended to the shared set's ramped colours (arm cut, neck), per-tier normal maps (A: tier A's normal moved across the UV layouts, frames rotated per face; B: Meshy's; C: from the mail's luminance).
Writes textures/zombie_torso_{a,b,c}_final.png, zombie_torso_{a,b,c}_normal.png (glTF +y up)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import tier_textures as TT
import project_lib as PL
TX = Path('textures'); F = np.load('work/faces.npz'); S = 1536
tors = F['torso'] > 0
uvt, uvb, co = F['uvt'][tors], F['uvb'][tors], F['co'][tors]
pos, nor, cov, bar, fid = PL.raster(uvt, co, S)
R = json.load(open(TX / 'zombie_ramps.json'))
e = R['materials'][0]
base = np.asarray(Image.open(TX / 'zombie_final_old2k.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for ch in Image.open(TX / 'zombie_region_mask_old.png').convert('RGBA').split()], -1)
auv = (bar[..., None] * uvb[fid]).sum(2)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
x, z = np.abs(pos[..., 0]), pos[..., 2]
w = np.maximum(np.clip((x - 0.27) / 0.04, 0, 1), np.clip((z - 0.765) / 0.03, 0, 1)) * (F['part'][tors][fid] == 0)
w = w * w * (3 - 2 * w)
for t in 'bc':
    src = TX / (f'zombie_torso_{t}.png' if t == 'b' else 'zombie_torso_c_raw.png')
    im = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
    if t == 'c':
        # the master's mail reads as leopard spots up close: colour stays, the rings become fine procedural mail (MM9's skin paints fine mail) where the master is grey
        hs = np.linalg.norm(pos[..., :1], axis=2)
        mx, mn = im.max(2), im.min(2)
        lo = np.stack([ndimage.gaussian_filter(im[..., c], 3.0) for c in range(3)], -1)
        lmx, lmn = lo.max(2), lo.min(2)
        mail = np.clip((0.2 - (lmx - lmn) / np.maximum(lmx, 1e-3)) / 0.08, 0, 1) * np.clip((lmx - 0.12) / 0.08, 0, 1)
        mail = ndimage.gaussian_filter(mail, 1.2)
        P = 7.0     # px per ring: 5 mm at about 1400 px/m
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
        row = np.floor(yy / (P * 0.866)); xs = xx + (row % 2) * P / 2
        cx = (np.floor(xs / P) + 0.5) * P; cy = (row + 0.5) * P * 0.866
        r = np.hypot(xs - cx, yy - cy) / (P * 0.5)
        ring = np.exp(-((r - 0.72) / 0.22) ** 2)
        tone = lo * (0.55 + 0.9 * ring[..., None]) 
        im = im * (1 - mail[..., None]) + tone * mail[..., None]
    rb = TT.apply(base, mask, e['ramps'][f'zombie_{t}']).astype(np.float32)
    ring = PL.sample(rb, auv)
    # a mail sleeve or vest edge stays design: only skin-coloured torso texels fade to the arm paint
    r_, g_, b_ = im[..., 0], im[..., 1], im[..., 2]
    grey = (im.max(2) - im.min(2)) < 0.09
    fade = w * (~grey if t == 'c' else 1.0)
    out = im * (1 - fade[..., None]) + ring * fade[..., None]
    Image.fromarray((np.clip(out[iy, ix], 0, 1) * 255 + 0.5).astype('u1')).save(TX / f'zombie_torso_{t}_final.png')
Image.open(TX / 'zombie_torso_a.png').save(TX / 'zombie_torso_a_final.png')
# normals. Meshy's maps: +y down in the file. A: per-face 2x2 from atlas tangents to torso tangents.
N = np.asarray(Image.open(TX / 'zombie_normal_1k.png').convert('RGB'), np.float32) / 127.5 - 1
N[..., :2] *= 0.5; N /= np.linalg.norm(N, axis=2, keepdims=True)
N[..., 1] *= -1     # glTF convention
def frames(uv, co):
    e1, e2 = co[:, 1] - co[:, 0], co[:, 2] - co[:, 0]; d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]; det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    T = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]; B = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]
    return T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12), B / np.maximum(np.linalg.norm(B, axis=1, keepdims=True), 1e-12)
Ta, Ba = frames(uvb, co); Tt, Bt = frames(uvt, co)
sn = PL.sample(N, auv)
aa = (Ta * Tt).sum(1)[fid]; ab = (Ba * Tt).sum(1)[fid]; ba = (Ta * Bt).sum(1)[fid]; bb = (Ba * Bt).sum(1)[fid]
nA = np.stack([sn[..., 0] * aa + sn[..., 1] * ab, sn[..., 0] * ba + sn[..., 1] * bb, sn[..., 2]], -1)
nA /= np.maximum(np.linalg.norm(nA, axis=2, keepdims=True), 1e-6)
def save(n, name, size=1024):
    im = Image.fromarray(((np.clip(n[iy, ix], -1, 1) + 1) * 127.5 + 0.5).astype('u1'))
    im.resize((size, size), Image.LANCZOS).save(TX / name)
save(nA, 'zombie_torso_a_normal.png')
Nb = np.asarray(Image.open(TX / 'zombie_torso_b_normal_soft.png').convert('RGB'), np.float32) / 127.5 - 1; Nb[..., 1] *= -1
Image.fromarray(((Nb + 1) * 127.5 + 0.5).astype('u1')).save(TX / 'zombie_torso_b_normal.png')
L = np.asarray(Image.open(TX / 'zombie_torso_c_final.png').convert('L'), np.float32) / 255
L = L - ndimage.gaussian_filter(L, 4)
gx, gy = np.gradient(L)
st = 2.5
nC = np.stack([-gx * st, gy * st, np.ones_like(L)], -1); nC /= np.linalg.norm(nC, axis=2, keepdims=True)
save(nC, 'zombie_torso_c_normal.png')
print('TORSO finished')
