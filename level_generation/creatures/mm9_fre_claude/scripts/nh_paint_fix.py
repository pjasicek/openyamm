#!/usr/bin/env python3
"""Pass 7 round 2 paint fixes on the 4K head paint (orchestrator pre-screen of r76), in place, before the one downsample:
1. Crown: Meshy painted the masters' gold crown band (parting stripe and a V over each side) on the hair; only the circlet stays gold. Gold
   hair texels more than BAND m above the circlet's own height at their azimuth (10th percentile of the gold heights per 20-deg sector,
   smoothed round the head), outside the jewel ornament box at the forehead, take the hair colour of the same surface turned ROT deg round
   the head's vertical axis (whichever side is not gold), blended over a 3-px soft edge.
2. Jewel: saturated royal blue -> MM9 Fre's violet: blue texels (hue 200-262 deg, saturation > 0.35) on the forehead turned by HUE deg,
   red lifted.
Args: <4K png in> <4K png out>   (project folder; work/nh/head_uv.npz)"""
import os, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage as ni
Image.MAX_IMAGE_PIXELS = None
E = os.environ.get; BAND, ROT, HUE = float(E('BAND', '0.012')), float(E('ROT', '14')), float(E('HUE', '24'))
img = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32) / 255; S = img.shape[0]
D = np.load('work/nh/head_uv.npz'); uv, tri, co, fp = D['uv'], D['tri'], D['co'], D['fpiece']
H = tri[fp == 1]
def hue_sat(c):
    mx, mn = c.max(-1), c.min(-1); r, g, b = c[..., 0], c[..., 1], c[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, (mx - mn) / np.maximum(mx, 1e-3), mx
hue, sat, val = hue_sat(img)
goldmap = (val > 0.42) & (hue > 28) & (hue < 62) & (sat > 0.25)
bluemap = (hue > 200) & (hue < 262) & (sat > 0.35)
# texel -> 3D for hair triangles (only where gold or blue texels are)
pos = np.full((S, S, 3), np.nan, np.float32)
for t in np.vstack([H, tri[fp == 0]]):      # the jewel's lower half lies on the forehead skin piece
    p = np.c_[uv[t, 0] * S, (1 - uv[t, 1]) * S]
    x0, y0 = np.maximum(np.floor(p.min(0)).astype(int) - 2, 0); x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int) + 2, S - 1)
    if not (goldmap[y0:y1 + 1, x0:x1 + 1].any() or bluemap[y0:y1 + 1, x0:x1 + 1].any()): continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); q = np.c_[xs.ravel() + .5, ys.ravel() + .5]
    T = np.array([[p[1, 0] - p[0, 0], p[2, 0] - p[0, 0]], [p[1, 1] - p[0, 1], p[2, 1] - p[0, 1]]])
    if abs(np.linalg.det(T)) < 1e-9: continue
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]; ok = (l > -0.15).all(1)
    pos[ys.ravel()[ok], xs.ravel()[ok]] = l[ok] @ co[t]
on = ~np.isnan(pos[..., 0])
hairmask = np.zeros((S, S), bool)
from PIL import ImageDraw
_cv = Image.new('L', (S, S), 0); _dr = ImageDraw.Draw(_cv)
for t in H: _dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in t], fill=255)
hairmask = np.asarray(_cv) > 0
gy, gx = np.where(goldmap & on & hairmask); G = pos[gy, gx]
az = np.degrees(np.arctan2(G[:, 0], -(G[:, 1] - 0.005)))
cent = np.arange(-180, 180, 20) + 10; lev = np.array([np.percentile(G[np.abs((az - c + 180) % 360 - 180) < 15, 2], 10) if (np.abs((az - c + 180) % 360 - 180) < 15).sum() > 30 else np.nan for c in cent])
lev = np.where(np.isnan(lev), np.nanmedian(lev), lev); lev = (np.roll(lev, 1) + 2 * lev + np.roll(lev, -1)) / 4
circ = np.interp(az, np.r_[cent - 360, cent, cent + 360], np.r_[lev, lev, lev])
orn = (np.abs(G[:, 0]) < 0.035) & (G[:, 1] < -0.085) & (G[:, 2] < 0.768)
crown = (G[:, 2] > circ + BAND) & ~orn
cm = np.zeros((S, S), bool); cm[gy[crown], gx[crown]] = True
cm = ni.binary_dilation(cm, iterations=5) & on & hairmask
print('CROWN circlet heights by sector', lev.round(3).tolist(), 'crown texels', int(crown.sum()), 'with edge', int(cm.sum()))
# sample hair colour at the rotated surface point
hc = co[H].mean(1); kd = cKDTree(hc)
def locate(m):
    _, cand = kd.query(m, k=10); out = np.full((len(m), 2), np.nan); best = np.full(len(m), np.inf)
    for k in range(10):
        t = H[cand[:, k]]; a, b, c = co[t[:, 0]], co[t[:, 1]], co[t[:, 2]]
        n = np.cross(b - a, c - a); nn = (n * n).sum(1) + 1e-30; q = m - (((m - a) * n).sum(1) / nn)[:, None] * n
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1); d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01 + 1e-30; l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den; l0 = 1 - l1 - l2
        err = np.maximum(0, -np.minimum(np.minimum(l0, l1), l2)) + np.abs(((m - a) * n).sum(1)) / np.sqrt(nn)
        bet = err < best; best[bet] = err[bet]; out[bet] = (l0[:, None] * uv[t[:, 0]] + l1[:, None] * uv[t[:, 1]] + l2[:, None] * uv[t[:, 2]])[bet]
    return out
def sample(u2):
    return np.stack([ni.map_coordinates(img[..., c], [(1 - u2[:, 1]) * S - .5, u2[:, 0] * S - .5], order=1, mode='nearest') for c in range(3)], 1)
ty, tx = np.where(cm); P = pos[ty, tx]; out = img.copy()
best = np.zeros((len(P), 3), np.float32); done = np.zeros(len(P), bool)
for ang in (ROT, -ROT, 2 * ROT, -2 * ROT, 3 * ROT, -3 * ROT):
    a = np.radians(ang); c_, s_ = np.cos(a), np.sin(a); Q = P.copy(); Q[:, 1] -= 0.005
    R = np.c_[Q[:, 0] * c_ - Q[:, 1] * s_, Q[:, 0] * s_ + Q[:, 1] * c_, Q[:, 2]]; R[:, 1] += 0.005
    col = sample(locate(R)); h_, s2, v_ = hue_sat(col); okc = ~((v_ > 0.45) & (h_ > 25) & (h_ < 65) & (s2 > 0.28))
    sel = okc & ~done; best[sel] = col[sel]; done |= okc
for dv in ((0, 0.03, 0), (0, -0.03, 0), (0.03, 0, 0), (-0.03, 0, 0), (0, 0.05, 0)):      # the very top (rotation barely moves it)
    R = P + np.array(dv); col = sample(locate(R)); h_, s2, v_ = hue_sat(col); okc = ~((v_ > 0.4) & (h_ > 25) & (h_ < 65) & (s2 > 0.25))
    sel = okc & ~done; best[sel] = col[sel]; done |= okc
print('CROWN replaced', int(done.sum()), 'of', len(P))
w = ni.gaussian_filter(cm.astype(np.float32), 1.0)[ty, tx][:, None]
out[ty[done], tx[done]] = out[ty[done], tx[done]] * (1 - w[done]) + best[done] * w[done]
# tone match: the replacement was sampled from neighbouring strands and read as a lighter band over the crown (r77 'crown' shot); the
# replaced texels take the broad tone (normalised Gaussian, sigma 14 px at 4K) of the untouched hair round them
keep = hairmask & ~cm; sig = 14
num = np.stack([ni.gaussian_filter(out[..., c] * keep, sig) for c in range(3)], -1); den = ni.gaussian_filter(keep.astype(np.float32), sig)[..., None]
tgt = num / np.maximum(den, 1e-4)
num2 = np.stack([ni.gaussian_filter(out[..., c] * cm, sig) for c in range(3)], -1); den2 = ni.gaussian_filter(cm.astype(np.float32), sig)[..., None]
cur = num2 / np.maximum(den2, 1e-4)
ratio = np.clip(tgt / np.maximum(cur, 1e-3), 0.6, 1.4); wcm = ni.gaussian_filter(cm.astype(np.float32), 1.5)[..., None]
out = out * (1 - wcm) + out * ratio * wcm
print('CROWN tone matched, ratio p5/p50/p95', np.percentile(ratio[cm].mean(-1), [5, 50, 95]).round(2))
# jewel to violet
by, bx = np.where(bluemap & on); B = pos[by, bx]; jm = (np.abs(B[:, 0]) < 0.03) & (B[:, 1] < -0.09) & (B[:, 2] > 0.735)
by, bx = by[jm], bx[jm]; c = out[by, bx]
import colorsys
hsv = np.array([colorsys.rgb_to_hsv(*x) for x in c]); hsv[:, 0] = (hsv[:, 0] + HUE / 360) % 1; hsv[:, 1] *= 0.85
out[by, bx] = np.array([colorsys.hsv_to_rgb(*x) for x in hsv])
print('JEWEL texels to violet', len(by), 'mean before', (c.mean(0) * 255).round(0), 'after', (out[by, bx].mean(0) * 255).round(0))
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(sys.argv[2])
