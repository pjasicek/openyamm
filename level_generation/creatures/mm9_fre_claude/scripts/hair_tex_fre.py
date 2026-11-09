#!/usr/bin/env python3
"""Fre pass 4: the texture set of PeasantF2's transplanted hair (material FreHair, F2's head-set UVs; F2's copper-red tier B paint, normal
and ORM copied to work/f2/). 1. Recolour: F2's hair texels take the per-channel mean and spread of Fre's own chestnut-auburn (the old cap's
hair texels in Fre's r43 head paint, circlet excluded), so the strands, their shading and the tapering hairline of F2's paint stay.
2. Circlet: every hair texel looks along its ray from the head centre at the old cap (pre-pass-4 asm/uv, its outer faces) and takes the old
paint there when it is the circlet (gold or the violet jewel), feathered by a 1 px edge; under it the strand normal is flattened and the
roughness lowered. Texels round the hair islands are padded 4 px. Args: none (project folder) -> textures/fre_hair_{base,normal,orm}.png"""
import os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage as ni
C = np.array([0.0, 0.0, 0.665])
def raster(co, tri, uv, S):
    """3D position per texel of the faces (nan elsewhere)."""
    P = np.full((S, S, 3), np.nan)
    for t in tri:
        q = uv[t] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        T = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
        if abs(np.linalg.det(T)) < 1e-12: continue
        l = np.linalg.solve(T, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); b = np.vstack([l, 1 - l.sum(0)]); ok = (b >= -1e-4).all(0)
        if ok.any(): P[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = (b[:, ok].T[:, :, None] * co[t][None]).sum(1)
    return P
def pad(img, mask, n):
    out = img.copy(); m = mask.copy()
    for _ in range(n):
        g = ni.binary_dilation(m) & ~m
        if not g.any(): break
        acc = np.zeros_like(out); cnt = np.zeros(m.shape)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                sm = np.roll(np.roll(m, dy, 0), dx, 1); acc += np.roll(np.roll(out, dy, 0), dx, 1) * sm[..., None]; cnt += sm
        out[g] = acc[g] / np.maximum(cnt[g], 1)[:, None]; m |= g
    return out
# ---- hair texels (current geometry)
U = np.load('work/uv.npz'); A = np.load('work/asm_frozen.npz')
hm = U['mat'] == 2; B0 = np.asarray(Image.open('work/f2/pf_head_b_fix.png').convert('RGB'), np.float32) / 255; S = B0.shape[0]
PH = raster(A['co'][U['orig']], U['tri'][hm], U['uv'], S); on = ~np.isnan(PH[..., 0])
# the circlet goes on the cap only (r44: a gold blob on the braid's tie, the old cap's paint along the same rays)
capf = hm & ~A['hair2_tube'][U['orig']][U['tri']].any(1); PC = raster(A['co'][U['orig']], U['tri'][capf], U['uv'], S); oncap = ~np.isnan(PC[..., 0])
# ---- old paint: Fre's r43 head texture on the old cap's outer faces
U0 = np.load('work/pre_pass4/uv.npz'); A0 = np.load('work/pre_pass4/asm_frozen.npz'); n0 = [str(x) for x in U0['names']]
OLD = np.asarray(Image.open('work/pre_pass4/pf_head_b_face.png').convert('RGB'), np.float32) / 255; S0 = OLD.shape[0]
cf = (U0['comp'][U0['tri'][:, 0]] == n0.index('hood4')) & (U0['mat'] == 1) & ~U0['inner']
PO = raster(A0['co'][U0['orig']], U0['tri'][cf], U0['uv'], S0); oo = ~np.isnan(PO[..., 0]); oy, ox = np.where(oo); oc = OLD[oy, ox]
gold = (oc[:, 1] > 0.42) & (oc[:, 1] / np.maximum(oc[:, 0], 1e-3) > 0.58) & (oc[:, 2] / np.maximum(oc[:, 1], 1e-3) < 0.6);      # not skin (B/G 0.85)
vio = (oc[:, 2] > oc[:, 1] + 0.08) & (oc[:, 2] > 0.22)
circ = gold | vio
# 1 px grow of the circlet in the old paint (its anti-aliased rim)
CM = np.zeros((S0, S0), bool); CM[oy[circ], ox[circ]] = True; CM = ni.binary_dilation(CM) & oo
hair_old = oc[~CM[oy, ox]]; mu_t, sd_t = hair_old.mean(0), hair_old.std(0)
# ---- 1. recolour
hs = B0[on]; mu_s, sd_s = hs.mean(0), hs.std(0)
base = B0.copy(); base[on] = np.clip((hs - mu_s) / sd_s * sd_t + mu_t, 0, 1)
# ---- 1b. F2's paint and AO darken toward its own nape (its hair hung lower there): on Fre the cap's lower edge read as a black helmet
# rim (r48 back views). Within RIMD of the cap's open rim the local mean brightness (8 px, inside the hair texels) is lifted toward the
# median of the hair, strands kept; the AO is floored at 0.85 there
_tc = U['tri'][capf]; _ky = np.round(A['co'][U['orig']], 5); _, _wi = np.unique(_ky, axis=0, return_inverse=True); _wi = _wi.ravel()
_ce = np.sort(np.vstack([_wi[_tc[:, [0, 1]]], _wi[_tc[:, [1, 2]]], _wi[_tc[:, [2, 0]]]]), 1); _ue, _cn = np.unique(_ce, axis=0, return_counts=True)
_rimp = A['co'][U['orig']][np.isin(_wi, np.unique(_ue[_cn == 1]))]
# r60: the cap's opening under the braid's tie is rim too, and its feather drew a pale halo round the tie: rim within 3 cm of the tube out
_tube = A['co'][np.where(A['hair2_tube'])[0]]; _dt, _ = cKDTree(_tube).query(_rimp)
_rimp = _rimp[(_dt > 0.03) & ~((_rimp[:, 1] > 0.04) & (_rimp[:, 2] > 0.635))]      # (the tie sits on the cap: the back above the nape too)
hy0, hx0 = np.where(on); _dr, _ = cKDTree(_rimp).query(PH[hy0, hx0]); RIMD = 0.05
_w = np.zeros((S, S), np.float32); _k = np.clip(1 - _dr / RIMD, 0, 1); _w[hy0, hx0] = _k * _k * (3 - 2 * _k)
_lum = base.mean(2) * on; _m = ni.gaussian_filter(on.astype(np.float32), 8); _bl = ni.gaussian_filter(_lum, 8) / np.maximum(_m, 1e-4)
_med = float(np.median(base[on].mean(1))); _gain = np.clip(_med / np.maximum(_bl, 1e-3), 1.0, 2.2)
base = base * (1 + (_gain - 1) * _w)[..., None]; base = np.clip(base, 0, 1)
RIMW = _w
# soft hairline: within FEATHER of the open rim the hair paint mixes toward skin, more in the strand gaps (lighter than the local mean)
# than on the strands, so the edge reads as thinning strands over skin instead of a cut sheet
FEATHER = float(os.environ.get('FEATHER', '0.008')); SKIN = np.array([0.80, 0.55, 0.43])
if os.path.exists('work/temple_w.npz'):      # pass 5: the feather mixes toward the healed temple skin's own tone
    _Wt = np.load('work/temple_w.npz')['w']; _Hb = np.asarray(Image.open('textures/pf_head_b_face.png').convert('RGB'), np.float32) / 255
    if _Hb.shape[0] == _Wt.shape[0] and (_Wt > 0.9).sum() > 100: SKIN = _Hb[_Wt > 0.9].mean(0)
_kf = np.clip(1 - _dr / FEATHER, 0, 1); _F = np.zeros((S, S), np.float32); _F[hy0, hx0] = _kf
_l2 = base.mean(2); _hp = (_l2 - ni.gaussian_filter(_l2 * on, 3) / np.maximum(ni.gaussian_filter(on.astype(np.float32), 3), 1e-4)) * on
_h01 = np.clip(0.5 + _hp / 0.12, 0, 1); _mix = np.clip(_F * (0.45 + 0.75 * _h01), 0, 1)[..., None] * on[..., None]
base = base * (1 - _mix) + SKIN * _mix
# ---- 2. circlet by direction from the head centre
do = PO[oy, ox] - C; do /= np.linalg.norm(do, axis=1, keepdims=True)
hy, hx = np.where(on); dh = PH[hy, hx] - C; dh /= np.linalg.norm(dh, axis=1, keepdims=True)
dd, j = cKDTree(do).query(dh)
cm_h = CM[oy[j], ox[j]] & (dd < 0.02) & oncap[hy, hx]
CMH = np.zeros((S, S), np.float32); CMH[hy[cm_h], hx[cm_h]] = 1
CMH = np.clip(ni.gaussian_filter(CMH, 0.6) * 1.6, 0, 1) * on
COL = np.zeros_like(base); COL[hy, hx] = oc[j]
base = base * (1 - CMH[..., None]) + COL * CMH[..., None]
base = pad(base, on, 4)
Image.fromarray((base * 255 + 0.5).astype('u1')).save('textures/fre_hair_base.png')
N0 = np.asarray(Image.open('work/f2/pf_head_normal.png').convert('RGB'), np.float32) / 255
flat = np.array([0.5, 0.5, 1.0]); nrm = N0 * (1 - CMH[..., None]) + flat * CMH[..., None]
Image.fromarray((pad(nrm, on, 4) * 255 + 0.5).astype('u1')).save('textures/fre_hair_normal.png')
O0 = np.asarray(Image.open('work/f2/pf_head_orm.png').convert('RGB'), np.float32) / 255; orm = O0.copy()
orm[..., 1] = O0[..., 1] * (1 - CMH) + 0.45 * CMH
orm[..., 0] = np.maximum(orm[..., 0], 0.85 * RIMW + orm[..., 0] * (1 - RIMW))
Image.fromarray((pad(orm, on, 4) * 255 + 0.5).astype('u1')).save('textures/fre_hair_orm.png')
print('HAIRTEX hair texels', int(on.sum()), 'circlet texels', int((CMH > 0.5).sum()), 'old circlet texels', int(CM.sum()),
      'colour', mu_s.round(3).tolist(), '->', mu_t.round(3).tolist())
