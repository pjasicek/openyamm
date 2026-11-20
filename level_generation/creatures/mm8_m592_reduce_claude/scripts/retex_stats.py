#!/usr/bin/env python3
"""Texel statistics per anatomical region (dominant bone of each source face, rasterised into UV space):
UV coverage, texel density (texels per metre), linear-luminance p10/50/90 per region-mask channel, near-black texel
fraction, and per-region drift of the picked step. Usage: retex_stats.py <project> <creature tag> <picked tag>"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
proj, tag, pick = sys.argv[1:4]
S = f'{proj}/work/retex'
d = np.load(f'{proj}/work/mesh_in.npz'); fb = np.load(f'{proj}/work/src_face_bone.npz')
names = [str(n) for n in fb['names']]; bone = fb['bone']
assert len(bone) == len(d['faces']), (len(bone), len(d['faces']))
def region(n):
    if n in ('Head', 'Jaw'): return 'head'
    if n.startswith('Neck'): return 'neck'
    if 'Wing' in n: return 'wing'
    if n.startswith('Tail'): return 'tail'
    if any(k in n for k in ('Foot', 'Shin', 'Thigh', 'Toe', 'Tarsus')): return 'leg'
    return 'body'
reg = np.array([region(names[b]) if b >= 0 else 'body' for b in bone]); R = ['head', 'neck', 'body', 'wing', 'leg', 'tail']
base = np.asarray(Image.open(f'{S}/{tag}_base.png').convert('RGB'), np.float32) / 255
mask = np.asarray(Image.open(f'{S}/{tag}_mask.png').convert('RGB').resize(base.shape[1::-1], Image.NEAREST), np.float32) / 255
lin = np.where(base <= .04045, base / 12.92, ((base + .055) / 1.055) ** 2.4); Y = lin @ np.array([.2126, .7152, .0722])
H, W = Y.shape; uv = d['wuv'].reshape(-1, 3, 2); v = d['verts'][d['faces']]
lab = Image.new('L', (W, H), 255); dr = ImageDraw.Draw(lab)
order = np.argsort([R.index(r) for r in reg])[::-1]  # head drawn last wins overlaps
for i in order:
    pts = [(float(u % 1 * W) if u != 1 else W - 1, float((1 - vv % 1) * H)) for u, vv in uv[i]]
    dr.polygon(pts, fill=R.index(reg[i]))
lab = np.asarray(lab)
a3 = np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1) / 2
auv = np.abs(np.cross(uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0])) / 2
out = {'atlas': [W, H], 'regions': {}}
print(f'{tag}: atlas {W}x{H}, covered {100 * (lab < 255).mean():.1f} %')
for k, r in enumerate(R):
    sel = reg == r; m = lab == k
    dens = np.sqrt(auv[sel].sum() * W * H / max(a3[sel].sum(), 1e-12))
    row = {'faces': int(sel.sum()), 'texels': int(m.sum()), 'texels_per_m': round(float(dens)), 'near_black_pct': round(float(100 * (Y[m] < .003).mean()), 2) if m.any() else None}
    for ch in range(mask.shape[2]):
        mm = m & (mask[..., ch] > .5)
        if mm.sum() > 200:
            row[f'mask{ch}'] = {'share_pct': round(float(100 * mm.sum() / m.sum()), 1), 'Y_p10_50_90': [round(float(x), 4) for x in np.percentile(Y[mm], [10, 50, 90])]}
    none = m & (mask.max(2) < .5)
    if none.sum() > 200:
        row['unmasked'] = {'share_pct': round(float(100 * none.sum() / m.sum()), 1), 'Y_p10_50_90': [round(float(x), 4) for x in np.percentile(Y[none], [10, 50, 90])]}
    out['regions'][r] = row; print(' ', r, json.dumps(row))
# drift of the picked step per region (nearest source face)
c = np.load(f'{proj}/work/mesh_{pick}.npz'); dr_ = np.load(f'{proj}/work/drift_{pick}.npy')
ct = c['verts'][c['faces']]; ca = np.linalg.norm(np.cross(ct[:, 1] - ct[:, 0], ct[:, 2] - ct[:, 0]), axis=1) / 2
creg = reg[cKDTree(v.mean(1)).query(ct.mean(1))[1]]; out['drift'] = {}
for r in R:
    s = creg == r; bad = s & (dr_ > 40)
    out['drift'][r] = {'faces': int(s.sum()), 'over40': int(bad.sum()), 'over40_cm2': round(float(ca[bad].sum() * 1e4), 2), 'p99': round(float(np.percentile(dr_[s], 99)), 1) if s.any() else None}
print('  drift', json.dumps(out['drift']))
json.dump(out, open(f'{proj}/review/retexture/stats.json', 'w'), indent=1)
Image.fromarray(np.where(lab[..., None] == 255, 0, (np.array([[230, 60, 60], [230, 160, 60], [80, 180, 80], [80, 120, 230], [180, 80, 200], [200, 200, 80]])[np.minimum(lab, 5)])).astype(np.uint8)).resize((1024, 1024 * H // W)).save(f'{proj}/review/retexture/uv_regions.png')
