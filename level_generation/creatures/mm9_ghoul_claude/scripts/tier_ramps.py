#!/usr/bin/env python3
"""Colour tiers on the shared sets: region masks + ramps (arms, legs, trousers, face, hair). Colour only: the torso's design difference is the torso part (torso_images.py).
Body set: R skin, G cloth (trousers, wraps). Bone shin and sinew are in no region. Head set: R hair, G skin; teeth, eyes, wounds in no region.
Ramps: tier A fitted to its own paint; B and C by luminance rank onto the colours of their Codex masters, measured on the same region (masters projected on the atlas; head from the master's head box).
Writes textures/zombie_region_mask.png, zombie_head_region_mask.png, zombie_ramps.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
import tier_textures as TT
import project_lib as PL
import project_lib_v as PV
import soft_detail_tone as SD
TX = Path('textures')
F = np.load('work/faces.npz')
S = 2048


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx


def soft(m, s=1.0): return np.clip(ndimage.gaussian_filter(m.astype(np.float32), s) * 1.2, 0, 1)
def clean(m): return ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1)


def rank_target(base, weight, pool, tonepool=False):
    """tier look: every core texel takes the pool colour at its luminance rank."""
    core = weight >= 0.9
    lum = RV.luminance(base)[core]
    o = np.argsort(lum); 
    if tonepool: pool = SD.tone(pool)
    pl = RV.luminance(pool); po = np.argsort(pl); pool = pool[po]
    # smooth the sorted pool so the ramp keeps a single hue per level
    k = max(3, len(pool) // 40)
    sm = np.stack([ndimage.uniform_filter1d(pool[:, c], k, mode='nearest') for c in range(3)], 1)
    idx = (np.arange(len(o)) / max(len(o) - 1, 1) * (len(sm) - 1)).astype(int)
    tgt = base.copy(); vals = np.zeros((len(o), 3), np.float32); vals[o] = sm[idx]
    tgt[core] = vals
    return tgt


# ---------- body
base = np.asarray(Image.open(TX / 'zombie_final_old2k.png').convert('RGB'), np.float32) / 255
nb = (F['head'] == 0) & (F['torso'] == 0)
pos, nor, cov, bar, fid = PL.raster(F['uvb'][nb], F['co'][nb], S)
parts = F['part'][nb]
skip = cov & np.isin(parts[fid], (4,))          # the shin bone
h, s, v = hsv(base)
red = ((h < 16) | (h > 340)) & (s > 0.45)
skin = (h > 36) & (h < 80) & (v > 0.26) & cov & ~skip
cloth = cov & ~skin & ~red & ~skip
skin = clean(skin); cloth = clean(cloth) & ~skin
wS, wC = soft(skin), soft(cloth)
print('body skin %.3f cloth %.3f of cover' % (skin.sum() / cov.sum(), cloth.sum() / cov.sum()))
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
wS2 = wS[iy, ix]; wC2 = wC[iy, ix]
RV.write_mask([wS2, wC2], TX / 'zombie_region_mask_old.png', 1024)
tiers = {'zombie_a': base}
pb = {}
for t, pre in (('zombie_b', 'references_tiers/b_'), ('zombie_c', 'references_tiers/c_')):
    proj, have, rep = PL.project(pre, pos, nor, cov, F['co'])
    print(t, rep, 'have', int(have.sum()))
    pb[t] = (proj, have)
report = {}
ramp_b = {}
for name, w in (('skin', wS2), ('cloth', wC2)):
    tt = {'zombie_a': base}
    for t, (proj, have) in pb.items():
        pool = proj[(w >= 0.9) & have & np.isin(0, 0)]
        if name == 'skin':     # the masters' knee patches and arms; dark cloth that slipped in by misalignment is out
            hh, ss, vv = hsv(proj); pool = proj[(w >= 0.9) & have & (hh > 34) & (vv > 0.25)]
        else:
            hh, ss, vv = hsv(proj); pool = proj[(w >= 0.9) & have & ((hh < 40) | (vv < 0.3))]
        tt[t] = rank_target(base, w, pool, True)
        print(name, t, 'pool', len(pool), 'mean', (pool.mean(0) * 255).round(0))
    r, rep = RV.fit_ramps(base, tt, w)
    ramp_b[name] = r; report[name] = rep
print(report)
# ---------- head
hb = np.asarray(Image.open(TX / 'zombie_head_basecolor_final.png').convert('RGB'), np.float32) / 255
nh = F['head'] > 0
pos, nor, cov, bar, fid = PL.raster(F['uvh'][nh], F['co'][nh], S)
parts = F['part'][nh]
ex = cov & np.isin(parts[fid], (12, 13))
h, s, v = hsv(hb)
red = ((h < 18) | (h > 335)) & (s > 0.42) & (v > 0.2)
hairp = cov & (parts[fid] == 11)
lo = np.stack([ndimage.gaussian_filter(hb[..., c], 7) for c in range(3)], -1)
lh, ls, lv = hsv(lo)
hairc = cov & (lv < 0.5) & (lh < 42)
lo2 = np.stack([ndimage.gaussian_filter(hb[..., c], 3) for c in range(3)], -1)
lh2, ls2, lv2 = hsv(lo2)
fringe = cov & (lv2 < 0.47) & (lh2 < 42) & (pos[..., 2] > 0.938)
back = cov & (pos[..., 1] > 0.05) & (pos[..., 2] > 0.86)
faceq = (pos[..., 1] < -0.045) & (np.abs(pos[..., 0]) < 0.075) & (pos[..., 2] < 0.975)
neckside = (pos[..., 2] < 0.845) & (np.abs(pos[..., 0]) > 0.045) & (pos[..., 1] > -0.03)
hair0 = hairp | back | (hairc & (pos[..., 2] > 0.84) & ~faceq) | (fringe & faceq) | (hairc & neckside)
# a clean hairline: the mask is smoothed along the surface (no UV seams, no paint noise) and cut softly
hc, cc = F['uvh'][nh], F['co'][nh]
tri = PV.weld(cc); nv = tri.max() + 1
_, (i0, i1) = ndimage.distance_transform_edt(~cov, return_indices=True)
hair0p = hair0[i0, i1]
vv = PV.per_vertex(PL.sample(hair0p[..., None].astype(np.float32), hc.reshape(1, -1, 2))[0].reshape(-1, 3, 1), tri, nv)
vv = PV.smooth(vv, tri, nv, 4)
hf = PV.texel(vv, tri, bar, fid)[..., 0]
hairs = np.clip((hf - 0.38) / 0.24, 0, 1); hairs = hairs * hairs * (3 - 2 * hairs)
hairs = np.maximum(hairs, hairp.astype(np.float32)) * cov
ex2 = ndimage.binary_dilation(ex, iterations=2)
hairs = hairs * ~ex2 * (1 - (red & (pos[..., 1] < -0.02)))
# the crown: on MM9's Dripper the top of the head is bare grey scalp, the hair only at the sides and back
cf = np.clip((pos[..., 2] - 0.925) / 0.02, 0, 1) * np.clip((0.04 - pos[..., 1]) / 0.05, 0, 1) * np.clip((0.07 - np.abs(pos[..., 0])) / 0.03, 0, 1)
vc_ = PV.per_vertex(PL.sample(cf[..., None].astype(np.float32), hc.reshape(1, -1, 2))[0].reshape(-1, 3, 1), tri, nv)
cf = PV.texel(PV.smooth(vc_, tri, nv, 3), tri, bar, fid)[..., 0]
crown = hairs * cf; hairs2 = hairs * (1 - cf)
skinh = cov & (hairs < 0.5) & ~red & ~ex & ~(v < 0.08)
wK = soft(clean(skinh), 1.6) * (1 - hairs)
wH = hairs2; wC_ = crown
print('head hair %.3f crown %.3f skin %.3f' % ((hairs2 > 0.5).sum() / cov.sum(), (crown > 0.5).sum() / cov.sum(), (wK > 0.5).sum() / cov.sum()))
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
wH2 = wH[iy, ix]; wK2 = wK[iy, ix]; wC2h = wC_[iy, ix]
Image.fromarray((np.clip(np.stack([hb[..., 0] * (1 - wH2 * 0.7) + wH2 * 0.7, hb[..., 1] * (1 - wC2h * 0.7) + wC2h * 0.7, hb[..., 2] * (1 - wK2 * 0.7) + wK2 * 0.7], -1), 0, 1) * 255).astype('u1')).resize((1024, 1024)).save('review/raw/head_mask.png')
RV.write_mask([wH2, wK2, wC2h], TX / 'zombie_head_region_mask.png', 1024)
ramp_h = {}
# tier colours of the head from MM9's own skins, at the skin's hair and scalp and face corners (256 px): sides/back hair, crown, face
def mm9(i, box):
    im = np.asarray(Image.open(f'source/z{i}/skins/zombie{i}.png').convert('RGB'), np.float32) / 255
    x0, y0, x1, y1 = box
    return im[y0:y1, x0:x1].reshape(-1, 3)
for name, w in (('hair', wH2), ('skin', wK2), ('crown', wC2h)):
    tt = {'zombie_a': hb}
    for t, i in (('zombie_b', 2), ('zombie_c', 3)):
        if name == 'hair':
            pool = mm9(i, (48, 2, 92, 62)) * (0.66 if i == 2 else 1.0)
        elif name == 'crown':
            pool = mm9(i, (10, 1, 40, 11)) * np.array([0.66, 0.66, 0.6]) if i == 2 else mm9(i, (48, 2, 92, 62)) * 1.0
        else:
            pool = mm9(i, (8, 18, 44, 52)) * 0.86
            hh, ss, vv_ = hsv(pool[None])
            pool = pool[(hh[0] > 30) & (hh[0] < 90) & (vv_[0] > 0.22)]
        tt[t] = rank_target(hb, w, pool)
        print('head', name, t, 'pool', len(pool), (pool.mean(0) * 255).round(0))
    r, rep = RV.fit_ramps(hb, tt, w)
    ramp_h[name] = r; report['head_' + name] = rep
V = ['zombie_a', 'zombie_b', 'zombie_c']
out = {'variants': V, 'materials': [
    {'base': 'Zombie', 'prefix': 'Zombie', 'mask': 'zombie_region_mask.png', 'ramps': {t: [ramp_b['skin'][t], ramp_b['cloth'][t]] for t in V}},
    {'base': 'ZombieHead', 'prefix': 'ZombieHead', 'mask': 'zombie_head_region_mask.png', 'ramps': {t: [ramp_h['hair'][t], ramp_h['skin'][t], ramp_h['crown'][t]] for t in V}}]}
json.dump(out, open(TX / 'zombie_ramps.json', 'w'))
json.dump(report, open('work/ramps_report.json', 'w'), indent=1)
print('RAMPS done')
