#!/usr/bin/env python3
"""Fre pass 4 (orchestrator on r55: "the skin newly exposed at the temples and sides of the face is patchy - pale-orange polygon-shaped
blotches and hard-edged lighter/darker panels where old-bob paint/AO was healed"). The earlier heals (expose_skin, seam_skin) worked per
texel class, so their edges followed the UV charts and the old bob's outline. Here one smooth weight in 3D decides the region: texels of
the face shell (and the old hood's teeth) that the new hair does not cover, within RIN of the hair's open rim (fading out to ROUT), to the
side of the face (|x| from 4.5 to 5.8 cm), above the jaw line (z 0.565-0.585) and behind the brows (y > -0.09 to -0.075). There:
- base colour: a smooth field of the clean cheek/jaw skin around the region (Gaussian-weighted, sigma SIG, over the nearest K clean skin
  texels in 3D) plus a third of that source skin's fine detail, blended by the weight into the paint (soft edges, no chart shapes);
- normal map: blended by the weight toward flat (the cheek's own normals are close to flat);
- ORM: AO blended by the weight toward 1 (no trace of the old bob's occlusion).
Args: base <in png> <out png> | normal <in png> <out png> | orm <in png> <out png>   (project folder; the weight map is computed in the
base pass and saved to work/temple_w.npz for the other two)"""
import sys, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
MODE, SRC, DST = sys.argv[1:4]
RIN, ROUT = float(os.environ.get('RIN', '0.03')), float(os.environ.get('ROUT', '0.05')); SIG = 0.012; K = 64
def ss(x, a, b):
    k = np.clip((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k)
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
if MODE == 'base':
    U = np.load('work/uv.npz'); A = np.load('work/asm_frozen.npz'); names = [str(x) for x in U['names']]
    co = A['co'][U['orig']]; tri, uv, mat, comp = U['tri'], U['uv'], U['mat'], U['comp']
    KH, KS, K2 = names.index('head'), names.index('scarf'), names.index('hair2')
    POS = np.full((S, S, 3), np.nan); PART = np.full((S, S), -1)
    for f in np.where((mat == 1) & np.isin(comp[tri[:, 0]], [KH, KS]))[0]:
        q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
        if abs(np.linalg.det(T_)) < 1e-12: continue
        l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); bb = np.vstack([l, 1 - l.sum(0)]); ok = (bb >= -1e-4).all(0)
        if ok.any():
            yy, xx = gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)
            POS[yy, xx] = (bb[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1); PART[yy, xx] = comp[tri[f, 0]]
    ys, xs = np.where(PART >= 0); P = POS[ys, xs]; pt = PART[ys, xs]; col = im[ys, xs]
    C = np.array([0.0, 0.0, 0.665]); tube = A['hair2_tube'][U['orig']]
    capT = tri[(comp[tri] == K2).all(1) & ~tube[tri].any(1)]
    d = P - C; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
    t = raycast(C + u * 0.6, -u, co, capT); cov = np.isfinite(t) & (0.6 - t > r - 0.001)
    # the cap's open rim (welded rows of its boundary edges)
    ky = np.round(co, 5); _, wi = np.unique(ky, axis=0, return_inverse=True); wi = wi.ravel()
    e = np.sort(np.vstack([wi[capT[:, [0, 1]]], wi[capT[:, [1, 2]]], wi[capT[:, [2, 0]]]]), 1); ue, cn = np.unique(e, axis=0, return_counts=True)
    rim = co[np.isin(wi, np.unique(ue[cn == 1])) & (comp == K2)]
    dr, _ = cKDTree(rim).query(P)
    w = (1 - ss(dr, RIN, ROUT)) * ss(np.abs(P[:, 0]), 0.045, 0.058) * ss(P[:, 2], 0.565, 0.585) * ss(P[:, 1], -0.09, -0.075) * ~cov      # r59 (wider, sigma 1.5 cm) read as one flat pale panel: r58's band kept
    w = np.where(pt == KS, np.maximum(w, 1.0 * ~cov), w)
    # pass 5 (orchestrator on r62, confirmed in an unlit base-colour render: the temple panels are paint): the earlier heals
    # (expose_skin's old-cap band, seam_skin's old-cap test) cut hard edges in 3D. Every texel on the side of the head that differs from
    # Meshy's raw paint (pf_head_raw.png) counts as repainted; that mask is blurred in 3D (the mean over the 48 nearest texels) into a
    # soft weight, and the whole repainted area gets the same smooth cheek field with feathered edges
    RAW = np.asarray(Image.open('textures/pf_head_raw.png').convert('RGB'), np.float32) / 255
    if RAW.shape[0] != S: RAW = np.asarray(Image.open('textures/pf_head_raw.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float32) / 255
    side = (pt == KH) & ~cov & (np.abs(P[:, 0]) > 0.035) & (P[:, 2] > 0.55) & (P[:, 1] > -0.105)
    chg = side & (np.abs(col - RAW[ys, xs]).mean(1) > 0.035)
    sid = np.where(side)[0]; _, jn = cKDTree(P[sid]).query(P[sid], k=48); mb = chg[sid][jn].mean(1)
    wc = np.zeros(len(P)); wc[sid] = ss(mb, 0.05, 0.45) * ss(np.abs(P[sid, 0]), 0.035, 0.05) * ss(P[sid, 1], -0.105, -0.09)
    w = np.maximum(w, wc)
    w = w * ~((col.mean(1) < 0.45) & (P[:, 1] < -0.075) & (P[:, 2] > 0.68))      # the brows' tails stay
    # the circlet's front is painted on the face shell: it stays, and never feeds the skin field (r64: yellow smears at the temples)
    gold = (col[:, 1] > 0.42) & (col[:, 2] / np.maximum(col[:, 1], 1e-3) < 0.6) & (col[:, 1] / np.maximum(col[:, 0], 1e-3) > 0.62)
    goldz = np.zeros(len(P)); gi = np.where(gold)[0]
    if len(gi):
        dg, _ = cKDTree(P[gi]).query(P); goldz = 1 - ss(dg, 0.0, 0.004)
    w = w * (1 - goldz)
    # clean skin: the face shell outside the region and the hair, skin-coloured, beside the region (within 6 cm)
    hairlike = (col[:, 1] / np.maximum(col[:, 0], 1e-3) < 0.55) | (col.mean(1) < 0.36)
    srcm = (pt == KH) & ~cov & (w < 0.02) & ~hairlike & (P[:, 2] > 0.55) & ~chg & (goldz < 0.01)
    zone = w > 0.002; src = np.where(srcm)[0]; kd = cKDTree(P[src])
    dd, jj = kd.query(P[zone], k=K); gw = np.exp(-(dd / SIG) ** 2); gw /= np.maximum(gw.sum(1, keepdims=True), 1e-12)
    field = (col[src][jj] * gw[..., None]).sum(1)
    # fine detail of the nearest source texel (its offset from its own smooth neighbourhood)
    d1, j1 = kd.query(P[zone]); dd2, jj2 = kd.query(P[src][j1], k=24); det = col[src][j1] - col[src][jj2].mean(1)
    val = field + 0.33 * det
    wz = w[zone][:, None]; out = im.copy(); out[ys[zone], xs[zone]] = val * wz + col[zone] * (1 - wz)
    # thin teeth and slivers in the region sample the gutters round their charts (dark ticks at the temples, r57 profiles): the region's
    # texels are grown 3 px into texels of no head-set chart
    from scipy import ndimage as ni
    anyc = PART >= 0; sm = np.zeros((S, S), bool); sm[ys[zone], xs[zone]] = True
    for _ in range(3):
        g = ni.binary_dilation(sm) & ~anyc & ~sm
        if not g.any(): break
        acc = np.zeros_like(out); cnt = np.zeros((S, S))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                s2 = np.roll(np.roll(sm, dy, 0), dx, 1); acc += np.roll(np.roll(out, dy, 0), dx, 1) * s2[..., None]; cnt += s2
        out[g] = acc[g] / np.maximum(cnt[g], 1)[:, None]; sm |= g
    W = np.zeros((S, S), np.float32); W[ys, xs] = w; W[sm & ~anyc] = 1.0; np.savez('work/temple_w.npz', w=W)
    print('TEMPLESKIN base texels', int(zone.sum()), 'full weight', int((w > 0.98).sum()), 'sources', len(src))
else:
    W = np.load('work/temple_w.npz')['w']
    if W.shape[0] != S:
        W = np.asarray(Image.fromarray(W).resize((S, S), Image.BILINEAR))
    out = im.copy()
    if MODE == 'normal':
        out = im * (1 - W[..., None]) + np.array([0.5, 0.5, 1.0]) * W[..., None]
    elif MODE == 'orm':
        out[..., 0] = im[..., 0] * (1 - W) + 1.0 * W
    print('TEMPLESKIN', MODE, 'texels', int((W > 0.002).sum()))
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(DST)
