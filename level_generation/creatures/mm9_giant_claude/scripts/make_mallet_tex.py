#!/usr/bin/env python3
"""Procedural PBR maps for the mallet on its uv_atlas.py layout (work/mallet.npz UVc), painted by position in the mallet's own frame
(MM9's Xhammer axes at our 0.3 scale: head along x, hexagonal section in (y, z), shaft along +y). MM9's GIANTMALLET design as the
shared base: dark oak planks along the head, two iron bands with rivets near each end, a round engraved iron boss on each slanted face,
end grain with an iron rim on the striking faces, a light ash shaft with a dark leather wrap over the grip run, iron ferrule and pommel.
The Forest Giant's steel head (YANMIRMALLET) is a ramp of the wood region. Region mask: R head wood, G iron bands and rims, B bosses
and rivets. Rendered at 1536, written at 768 (526 px per metre, the body 589). Writes textures/gi_mallet_{base,normal,orm,region_mask}.png."""
import numpy as np
from PIL import Image
from scipy import ndimage
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
Z = np.load(HERE / 'work' / 'mallet.npz'); V, F, UV = Z['V'], Z['F'], Z['UVc']
S, OUT = 1536, 768
rng = np.random.default_rng(9)
pos = np.zeros((S, S, 3)); nrm = np.zeros((S, S, 3)); cov = np.zeros((S, S), bool); part = np.zeros((S, S), np.int8)
T = V[F]; fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True)
cen = T.mean(1)
shaft = (np.hypot(cen[:, 0], cen[:, 2]) < 0.05) & (np.abs(T[:, :, 0]).max(1) < 0.05)        # 1 shaft, 0 head
for t in range(len(F)):
    u = UV[t]; x = u[:, 0] * S; y = (1 - u[:, 1]) * S
    x0, x1 = int(max(np.floor(x.min()) - 1, 0)), int(min(np.ceil(x.max()) + 1, S - 1)); y0, y1 = int(max(np.floor(y.min()) - 1, 0)), int(min(np.ceil(y.max()) + 1, S - 1))
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-12: continue
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
    b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
    c = 1 - a - b
    m = (a >= -0.03) & (b >= -0.03) & (c >= -0.03)
    pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * T[t, 0] + b[..., None] * T[t, 1] + c[..., None] * T[t, 2])[m]
    nrm[y0:y1 + 1, x0:x1 + 1][m] = fn[t]; cov[y0:y1 + 1, x0:x1 + 1][m] = True; part[y0:y1 + 1, x0:x1 + 1][m] = 1 if shaft[t] else 0
px, py, pz = pos[..., 0], pos[..., 1], pos[..., 2]
def noise3(p, scale, sig):
    """smooth value noise sampled at 3D points (a 64^3 field, trilinear)"""
    G = ndimage.gaussian_filter(rng.standard_normal((64, 64, 64)), sig); G /= G.std() + 1e-9
    q = (p * scale) % 63
    return ndimage.map_coordinates(G, [q[..., 0].ravel(), q[..., 1].ravel(), q[..., 2].ravel()], order=1, mode='wrap').reshape(p.shape[:-1])
col = np.zeros((S, S, 3)); hgt = np.zeros((S, S)); metal = np.zeros((S, S)); rough = np.full((S, S), 0.75); reg = np.zeros((S, S, 3))
iron = np.array([0.10, 0.095, 0.09])
# ---- head: sides and end caps
head = cov & (part == 0)
cap = head & (np.abs(nrm[..., 0]) > 0.9)
side = head & ~cap
th = np.arctan2(pz, py + 0.191)                                       # angle round the head's own axis
grain = noise3(np.stack([px * 0.15, (py + 0.191) * 6, pz * 6], -1), 9.0, 1.2) * 0.6 + noise3(np.stack([px * 0.4, (py + 0.191) * 14, pz * 14], -1), 9.0, 0.8) * 0.4
plank = np.abs(((th / (2 * np.pi) * 12) % 1.0) - 0.5) > 0.47
wood = np.array([0.16, 0.075, 0.035])[None, None] * (1 + 0.18 * grain[..., None]) * (1 - 0.5 * plank[..., None])
col[side] = wood[side]; hgt[side] = (0.5 + 0.06 * grain - 0.25 * plank)[side]; reg[side] = (1, 0, 0)
band = side & (np.abs(np.abs(px) - 0.195) < 0.021)
col[band] = iron * (1 + 0.12 * grain[band, None]); hgt[band] = 0.8; metal[band] = 0.85; rough[band] = 0.45; reg[band] = (0, 1, 0)
HEX = np.array([(-0.353, 0.100), (-0.191, 0.188), (-0.029, 0.100), (-0.029, -0.100), (-0.191, -0.188), (-0.353, -0.100)])
for k in (0, 1, 3, 4):                                                 # the slanted faces: boss and rivets
    a_, b_ = HEX[k], HEX[(k + 1) % 6]; mid = (a_ + b_) / 2; tdir = (b_ - a_) / np.linalg.norm(b_ - a_)
    rel = np.stack([py - mid[0], pz - mid[1]], -1); along = rel @ tdir; off = np.abs(rel @ np.array([-tdir[1], tdir[0]]))
    onf = side & (off < 0.02)
    r = np.hypot(px, along); m = onf & (r < 0.06)
    knot = 0.5 + 0.5 * np.sin(r / 0.06 * 26 + np.arctan2(along, px) * 5); ring = (np.abs(r / 0.06 - 0.85) < 0.08) | (np.abs(r / 0.06 - 0.45) < 0.06)
    bc = np.array([0.24, 0.235, 0.225])[None, None] * (0.8 + 0.3 * knot[..., None]) * (1 - 0.35 * ring[..., None])
    col[m] = bc[m]; hgt[m] = (0.85 + 0.05 * knot - 0.1 * ring)[m]; metal[m] = 0.85; rough[m] = 0.4; reg[m] = (0, 0, 1)
    for xc in (-0.195, 0.195):
        for al in (-0.06, 0.0, 0.06):
            rr = np.hypot(px - xc, along - al) / 0.009; m = onf & (rr < 1)
            col[m] = np.array([0.42, 0.41, 0.39]) * (1.1 - 0.3 * rr[m])[:, None]; hgt[m] = 0.95 - 0.1 * rr[m]; metal[m] = 0.9; rough[m] = 0.35; reg[m] = (0, 0, 1)
# end caps: end grain rings, an iron rim along the hexagon's edge
cr = np.hypot(py + 0.191, pz)
edge = np.full((S, S), 9.0)
for k in range(6):
    a_, b_ = HEX[k], HEX[(k + 1) % 6]; e = b_ - a_; L = np.linalg.norm(e); e /= L
    rel = np.stack([py - a_[0], pz - a_[1]], -1); t_ = np.clip(rel @ e, 0, L)
    edge = np.minimum(edge, np.linalg.norm(rel - t_[..., None] * e, axis=-1))
rings = 0.5 + 0.5 * np.sin(cr * 190 + noise3(np.stack([px, py * 3, pz * 3], -1), 9.0, 2.0) * 1.5)
endc = np.array([0.22, 0.12, 0.055])[None, None] * (0.75 + 0.35 * rings[..., None])
rim = cap & (edge < 0.022)
col[cap] = endc[cap]; hgt[cap] = (0.45 + 0.05 * rings)[cap]; rough[cap] = 0.8; reg[cap] = (1, 0, 0)
col[rim] = iron; hgt[rim] = 0.8; metal[rim] = 0.85; rough[rim] = 0.45; reg[rim] = (0, 1, 0)
# ---- shaft: ash along y, leather wrap over the grip run, iron ferrules and pommel
sh = cov & (part == 1)
phi = np.arctan2(pz, px)
ash = np.array([0.36, 0.23, 0.11])[None, None] * (1 + 0.15 * noise3(np.stack([np.cos(phi) * 0.3, py * 0.5, np.sin(phi) * 0.3], -1), 30.0, 1.0)[..., None])
wrap = sh & (py > 0.50) & (py < 1.22)
turns = 0.5 + 0.5 * np.sin((py * 60 + phi / (2 * np.pi)) * 2 * np.pi / 6.0 * 6)
leather = np.array([0.17, 0.10, 0.06])[None, None] * (0.8 + 0.35 * turns[..., None])
fer = sh & ((np.abs(py) < 0.03) | (py > 1.24) | (py < -0.36))
col[sh] = ash[sh]; hgt[sh] = 0.5; rough[sh] = 0.75
col[wrap] = leather[wrap]; hgt[wrap] = (0.55 + 0.15 * turns)[wrap]; rough[wrap] = 0.7
col[fer] = iron; hgt[fer] = 0.8; metal[fer] = 0.85; rough[fer] = 0.45; reg[fer] = (0, 1, 0)
# fill the gutters from the nearest covered texel, then write at the body's density
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
fill = lambda a: a[idx[0], idx[1]]
col, hgt, metal, rough, reg = fill(col), fill(hgt), fill(metal), fill(rough), fill(reg)
col = np.clip(col, 0, 1); srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(col, 1 / 2.4) - 0.055)
def save(arr, name, mode='RGB'):
    # per channel: PIL premultiplies RGBA by alpha when resizing, and the mask's unused alpha channel is 0
    chans = [Image.fromarray((np.clip(arr[..., c], 0, 1) * 255 + .5).astype('u1'), 'L').resize((OUT, OUT), Image.LANCZOS) for c in range(arr.shape[-1])]
    Image.merge(mode, chans).save(HERE / 'textures' / name)
save(srgb, 'gi_mallet_base.png')
gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 0.8))
n = np.dstack([-gx * 6, gy * 6, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
save(n * 0.5 + 0.5, 'gi_mallet_normal.png')
save(np.dstack([np.ones_like(rough), rough, metal]), 'gi_mallet_orm.png')
save(np.dstack([reg[..., 0], reg[..., 1], reg[..., 2], np.zeros((S, S))]), 'gi_mallet_region_mask.png', 'RGBA')
print('MALLETTEX done, covered', round(float(cov.mean()), 3), 'shaft texels', int(sh.sum()), 'caps', int(cap.sum()))
