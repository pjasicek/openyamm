#!/usr/bin/env python3
"""Per-tier head colour from the one Codex paint (head design is shared, hair, beard and collar are not). Hair and beard take MM9's tier colour for the same luminance quantile, the skin takes the tier body's skin tone, and the band over the seam takes the body's own pattern by reflection across the seam plane (fur, mail, harness run up to the seam: the head set has no outfit). Tusks, eyes and the ear ring keep the paint.
Writes textures/trell_head_{a,b,c}_final.png (S). Args: [S]"""
import sys
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
S = int(sys.argv[1]) if len(sys.argv) > 1 else 1536
T = Path('textures')
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
s2l = lambda a: np.where(a <= 0.04045, a / 12.92, ((np.maximum(a, 0) + 0.055) / 1.055) ** 2.4)
l2s = lambda a: np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 1e-6) ** (1 / 2.4) - 0.055)
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
SK = {t: load(f'source/true/skins/trellborg{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
yy, xx = np.mgrid[0:256, 0:256]
HAIR_PX = (xx > 70) & (xx < 108) & (yy > 2) & (yy < 75) | (xx > 30) & (xx < 70) & (yy < 16)
BEARD_PX = (xx < 34) & (yy > 92) & (yy < 118)
def table(px, n=16):
    la = SK['a'][px] @ LUM
    q = np.quantile(la, np.linspace(0, 1, n + 1)); out = {}
    for t, s in SK.items():
        c = s[px]; rows = []
        for i in range(n):
            m = (la >= q[i]) & (la <= q[i + 1])
            rows.append(c[m].mean(0))
        out[t] = ndimage.gaussian_filter1d(np.array(rows), 0.8, axis=0)
    return out
HAIR = table(HAIR_PX); BEARD = table(BEARD_PX)
print('TIERHAIR mid', {t: np.round(HAIR[t][8], 2).tolist() for t in 'abc'}, 'beard', {t: np.round(BEARD[t][8], 2).tolist() for t in 'abc'})
base = load(T / 'trell_head_a_raw.png'); H = base.shape[0]
Z = np.load('work/head_pos.npz'); pos, cov, prt = Z['pos'], Z['cov'], Z['prt']
# one paint source per feature: the tusks are mesh, so their painted copy on the lips and gums goes
tk = cKDTree(pos[cov & (prt >= 13)][::4]); dt = np.full((H, H), 1.0, np.float32); near = cov & (prt < 13) & (pos[..., 1] < -0.1) & (pos[..., 2] < 0.9)
dt[near] = tk.query(pos[near], k=1)[0]
cbase = base.max(2) - base.min(2)
pale = near & (dt < 0.03) & (base @ LUM > 0.33) & (cbase < 0.5 * base.max(2) + 0.02) & (base[..., 2] > 0.3)
pale = ndimage.binary_dilation(ndimage.binary_opening(pale, iterations=1), iterations=5) & near & (dt < 0.036)
print('TUSKPAINT texels', int(pale.sum()))
good = cov & (prt < 13) & ~pale
ix = ndimage.distance_transform_edt(~good, return_distances=False, return_indices=True)
fill = base[ix[0], ix[1]]; fill = ndimage.gaussian_filter(fill, (2.5, 2.5, 0))
pw = ndimage.gaussian_filter(pale.astype(np.float32), 1.2)[..., None]
base = np.where(cov[..., None] & (prt[..., None] < 13), base * (1 - pw) + fill * pw, base)
hb = np.load('work/hair_pts.npz'); th = cKDTree(hb['Hair']); tf = cKDTree(hb['Face'])
dh = np.full((H, H), 1.0, np.float32); df = np.full((H, H), 1.0, np.float32)
dh[cov] = th.query(pos[cov], k=1)[0]; df[cov] = tf.query(pos[cov], k=1)[0]
red = base[..., 0] / np.maximum(base[..., 1], 0.02) > 2.0
nofacefront = ~((np.abs(pos[..., 0]) < 0.09) & (pos[..., 1] < -0.13) & (pos[..., 2] < 0.9))
hair = (((dh < df + 0.003) | (red & nofacefront)) & cov & (prt < 13) & (pos[..., 2] > 0.8)).astype(np.float32)
hair = ndimage.gaussian_filter(hair, 2.0)
# beard: chin wedge, reddish strands against the jaw's paint
beard = (cov & (np.abs(pos[..., 0]) < 0.085) & (pos[..., 1] < -0.12) & (pos[..., 2] < 0.782) & (prt < 13)).astype(np.float32)
sat = (base[..., 0] - base[..., 2]) / np.maximum(base[..., 0], 0.05)
beard = ndimage.gaussian_filter(beard, 5) * np.clip((sat - 0.55) / 0.15, 0, 1)
beard = ndimage.gaussian_filter(beard, 1.5) * (1 - hair)
print('MASKS hair', float(hair[cov].mean()), 'beard', float(beard[cov].mean()))
Image.fromarray((np.dstack([hair, beard, np.zeros_like(hair)]) * 255).astype('u1')).save('work/v/head_masks.png')
ring = (cov & (prt < 13)) & (base[..., 0] > 0.65) & (base[..., 2] < 0.25) & (base[..., 1] > 0.45)   # gold ring and iris hot spots stay out
eyes = cov & (np.abs(np.abs(pos[..., 0]) - 0.055) < 0.05) & (pos[..., 1] < -0.15) & (np.abs(pos[..., 2] - 0.93) < 0.03)
keep = ndimage.gaussian_filter((ring | eyes | (prt >= 13)).astype(np.float32), 1.0)
def recolour(tab, tier, mask, gain):
    lum = base @ LUM; m = mask > 0.5
    qs = np.quantile(lum[m], np.linspace(0, 1, 17)); b = np.clip(np.searchsorted(qs, lum) - 1, 0, 15)
    mean = np.array([lum[m & (b == i)].mean() if (m & (b == i)).any() else 0.01 for i in range(16)], np.float32)
    return np.clip(tab[tier][b] * gain * (lum / np.maximum(mean[b], 1e-3))[..., None], 0, 1)
zb = np.load('work/body_pos.npz'); bp, bc = zb['pos'], zb['cov']
elbow = bc & (np.abs(np.abs(bp[..., 0]) - 0.5) < 0.06) & (np.abs(bp[..., 2] - 0.2) < 0.08)
neck = cov & (hair < 0.2) & (pos[..., 2] < 0.82) & (pos[..., 2] > 0.74) & (np.abs(pos[..., 0]) < 0.13)
C_ = np.array([0.0, 0.03, 0.76]); Nk = np.array([0.0, -0.25, 0.968]); Nk /= np.linalg.norm(Nk)
hh = (pos - C_) @ Nk
GAIN = {'a': 1.3, 'b': 1.25, 'c': 1.2}
band = cov & (prt < 13) & (hair < 0.5) & (hh < 0.095)
bq = bp[bc]; tb = cKDTree(bq[::2])
for t in 'abc':
    B = load(T / f'trell_body_{t}_final.png')
    out = base.copy()
    sk0 = s2l(base[neck]).mean(0); sk1 = s2l(B[elbow]).mean(0)
    g = np.clip(sk1 / sk0, 0.7, 1.08); print('SKIN', t, np.round(g, 2))
    skin = np.clip(l2s(s2l(base) * g), 0, 1)
    hc = recolour(HAIR, t, hair, GAIN[t]); bd = recolour(BEARD, t, beard, GAIN[t])
    out = skin * (1 - hair[..., None]) + hc * hair[..., None]
    out = out * (1 - beard[..., None]) + bd * beard[..., None]
    out = out * (1 - keep[..., None]) + base * keep[..., None]
    # collar: reflection of the body across the seam plane
    Q = pos[band] - 2 * np.outer(hh[band], Nk)
    _, idx = tb.query(Q, k=1)
    src = bq[::2][idx]
    colb = B[bc][::2][idx]
    w = np.clip(1 - (hh[band] - 0.015) / 0.075, 0, 1); w = w * w * (3 - 2 * w)
    wing = np.clip((np.abs(pos[band][:, 0]) - 0.15) / 0.03, 0, 1)
    w = np.maximum(w, wing) if False else w
    if t != 'a' or True:
        out[band] = out[band] * (1 - w[:, None]) + colb * w[:, None]
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).resize((S, S), Image.LANCZOS).save(T / f'trell_head_{t}_final.png')
print('HEADTIERS done')
