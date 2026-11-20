#!/usr/bin/env python3
"""Facet texture for the Crystal Walker v2 (work/uv_tris.npz from uv.py) -> textures/basecolor.png, textures/orm.png
(2048², glTF metallic-roughness: G roughness, B metal 0, R 1) and work/facets.npy.
Facets: edge-connected triangles whose normals stay within ANGLE of the facet's mean normal. Each facet gets one tone
around the native palette-596 sprite statistics (median RGB 165,109,137; hue 330, saturation 0.33) and a soft linear
gradient across it (a hint of internal reflection); per-facet roughness 0.11-0.20 so facets catch separate glints.
No painted white: glints come from the material. Each triangle is filled exactly (barycentric, 4x supersampled
coverage), and the islands are padded by nearest-texel fill, so no tone crosses a triangle or bleeds at seams."""
import colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]
SIZE, SS, ANGLE, SEED = 2048, 4, 22.0, 596
EYE, SOCKET = (1.0, .84, .32), (.16, .07, .12)   # review 2: eyes must read at game distance and indoors
d = np.load(P / 'work/uv_tris.npz'); uv, nrm, cen, vid = d['uv'], d['normal'], d['centre'], d['vid']
part = d['part'] if 'part' in d else np.zeros(len(uv), int)
n = len(uv)
# facets by region growing over shared edges
edges = {}
for t, (a, b, c) in enumerate(vid):
    for e in ((a, b), (b, c), (c, a)):
        edges.setdefault(tuple(sorted(e)), []).append(t)
nb = [[] for _ in range(n)]
for ts in edges.values():
    for i in ts:
        nb[i] += [j for j in ts if j != i]
e1, e2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
order = np.argsort(-np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]))   # largest UV area first
facet = -np.ones(n, int); cos_lim = np.cos(np.radians(ANGLE)); fid = 0
for s in order:
    if facet[s] >= 0:
        continue
    # round 7: tone groups are capped in size (head 3 triangles, body 6), so no merged group paints a patch
    cap = 3 if part[s] == 3 else 6
    facet[s] = fid; acc = nrm[s].copy(); stack = [s]; size = 1
    while stack and size < cap:
        t = stack.pop()
        for j in nb[t]:
            if size < cap and facet[j] < 0 and part[j] == part[s] and np.dot(nrm[j], acc / np.linalg.norm(acc)) > cos_lim:
                facet[j] = fid; acc += nrm[j]; stack.append(j); size += 1
    fid += 1
np.save(P / 'work/facets.npy', facet)
rng = np.random.default_rng(SEED)
H0, S0, V0 = 330 / 360, .33, .645
tone = []; rough = []
for f in range(fid):
    r = rng.random(); h, s, v = H0 + rng.normal(0, .008), S0 + rng.normal(0, .025), V0 + rng.normal(0, .035)
    if r < .03:
        h, s, v = 312 / 360 + rng.normal(0, .01), S0 + .06, v - .04      # violet: rare, isolated, a touch deeper
    elif r < .14:
        s, v = .29, .76 + rng.normal(0, .015)                             # light pink (round 6: no pale facets)
    elif r < .30:
        v += .085; s -= .03                                                # brighter
    elif r < .43:
        v -= .10; s += .05                                                 # deeper rose
    tone.append(colorsys.hsv_to_rgb(h % 1, float(np.clip(s, .1, .6)), float(np.clip(v, .38, .88))))
    rough.append(float(rng.uniform(.13, .22)))
tone = np.array(tone); rough = np.array(rough)
grad_dir = rng.normal(size=(fid, 3)); grad_dir /= np.linalg.norm(grad_dir, axis=1, keepdims=True)
# vertex-level gradient value per triangle corner: position along the facet's direction, scaled to +-0.05
W = SIZE * SS
col = np.zeros((W, W, 3), np.float32); rgh = np.zeros((W, W), np.float32); cov = np.zeros((W, W), bool)
gem = np.zeros((W, W), bool)
# triangle corner positions are not in the npz; approximate the corner offset from UV (islands keep proportions)
for t in range(n):
    f = facet[t]; p = uv[t] * W; p[:, 1] = W - p[:, 1]
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, W - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    (ax, ay), (bx, by), (cx, cy) = p
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-9:
        continue
    l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
    l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
    l3 = 1 - l1 - l2
    m = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
    if not m.any():
        continue
    # gradient: along a per-facet direction in UV space (islands are rigid copies of the surface)
    g2 = grad_dir[f, :2] / (np.linalg.norm(grad_dir[f, :2]) + 1e-9)
    gx = ((xs - W / 2) * g2[0] + (ys - W / 2) * g2[1]) / W * 2.2
    shade = 1 + .06 * np.sin(gx * 9 + f)
    sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
    if part[t] == 1:     # amber gem eye: bright, alternating facet brightness, glossy
        col[sl][m] = np.array(EYE) * (1.0 if t % 2 else .86); rgh[sl][m] = .06; cov[sl][m] = True; gem[sl][m] = True; continue
    if part[t] == 2:     # dark plum socket around the eye
        col[sl][m] = np.array(SOCKET); rgh[sl][m] = .3; cov[sl][m] = True; continue
    lift = 1.0
    if part[t] == 3 and nrm[t][2] < -.2:   # the authored head's underside (jaw, throat) sits in shadow under the
        lift = 1.0 + .40 * min(1.0, (-nrm[t][2] - .2) / .5)   # muzzle and read as a dark slit: bake a little bounce
    cx, cy, cz = cen[t]
    if part[t] == 0 and abs(cx) < .13 and cy < -.10 and 1.40 < cz < 1.58:   # the throat under the jaw, same reason
        lift = 1.30
    # round 6: broad head planes caught the sky reflection at grazing angles and read pale; a little more roughness on
    # the head lowers that Fresnel sheen while the facets keep small glints
    col[sl][m] = tone[f] * shade[m][:, None] * lift; rgh[sl][m] = rough[f] + (.11 if part[t] == 3 else 0); cov[sl][m] = True
# supersampled coverage -> downsample, then pad islands by nearest covered texel
col = col.reshape(SIZE, SS, SIZE, SS, 3); covs = cov.reshape(SIZE, SS, SIZE, SS)
w = covs.sum((1, 3)).astype(np.float32)
base = (col * covs[..., None]).sum((1, 3)) / np.maximum(w, 1)[..., None]
rr = (rgh.reshape(SIZE, SS, SIZE, SS) * covs).sum((1, 3)) / np.maximum(w, 1)
filled = w > 0
# round 6 ("some faces on the head are still white-ish"): glints come only from the material. Every crystal texel is
# capped at the palette-596 light-pink end (native sprite pixels at value p75-p90: 0.74-0.84, saturation 0.33-0.26):
# value at most 0.78, saturation at least 0.27, hue kept; the amber eye gems are exempt
iseye = gem.reshape(SIZE, SS, SIZE, SS).any((1, 3))
mx = base.max(-1); mn = base.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
crys = filled & ~iseye
v2 = np.minimum(mx, .78); s2 = np.maximum(sat, .27)
scale = np.where(mx > 0, v2 / np.maximum(mx, 1e-6), 0)[..., None]
lo = (v2 * (1 - s2))[..., None]
cur_lo = (mn * scale[..., 0])[..., None]
rng_ = np.maximum(v2[..., None] - cur_lo, 1e-6)
capped = lo + (base * scale - cur_lo) / rng_ * (v2[..., None] - lo)
base = np.where(crys[..., None], capped, base)
idx = ndimage.distance_transform_edt(~filled, return_distances=False, return_indices=True)
base = base[idx[0], idx[1]]; rr = rr[idx[0], idx[1]]
(P / 'textures').mkdir(exist_ok=True)
Image.fromarray((np.clip(base, 0, 1) * 255 + .5).astype(np.uint8)).save(P / 'textures/basecolor.png')
orm = np.stack([np.ones_like(rr), rr, np.zeros_like(rr)], -1)
Image.fromarray((orm * 255 + .5).astype(np.uint8)).save(P / 'textures/orm.png')
lum = (base[filled] @ np.array([.299, .587, .114]))
print('FACETS', fid, 'mean tris/facet', round(n / fid, 2), 'coverage', round(filled.mean(), 3),
      'median rgb', (np.median(base[filled], 0) * 255).round(), 'lum 5/50/95', np.percentile(lum, [5, 50, 95]).round(3))
