#!/usr/bin/env python3
"""Retexture check, part 2: per region (labels of the reduced mesh carried to the source faces by nearest centroid),
linear luminance p10/50/90 and median hue/chroma of the skin texels (region mask R > 0.5) in each tier bake
(mm8_m600_claude/work/tier_nightmare_<t>_Nightmare.png, the engine ramp rule) and the shared base colour; plus
near-black skin samples (linear luminance < 0.002 in the base colour) per region, with their positions.
Writes work/retex_colour.json."""
import json
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
s = np.load('work/mesh_in.npz'); d = np.load('work/mesh_r55.npz')
bone = np.load('work/r55_dominant_bone.npy')


def region(b, z):
    if z < .03:
        return 'base'
    for pre, name in ((('JawFront', 'FrontTop'), 'mouth_front'), (('NeckL', 'JawL'), 'mouth_left_stalk'),
                      (('NeckR', 'JawR'), 'mouth_right_stalk'), (('EmbeddedEye',), 'embedded_eyes'), (('Eye',), 'eye_stalks')):
        if b.startswith(pre):
            return name
    return 'lumps_body'


rc = d['verts'][d['faces']].mean(1)
rlab = np.array([region(b, z) for b, z in zip(bone, rc[:, 2])])
sv, sf, su = s['verts'], s['faces'], s['wuv'].reshape(-1, 3, 2)
sc = sv[sf].mean(1); slab = rlab[cKDTree(rc).query(sc)[1]]
slab[sc[:, 2] < .03] = 'base'
rng = np.random.default_rng(2); B = rng.dirichlet((1, 1, 1), 16)
uvs = np.einsum('sk,fkc->fsc', B, su).reshape(-1, 2); pos = np.einsum('sk,fkc->fsc', B, sv[sf]).reshape(-1, 3)
lab = np.repeat(slab, len(B))
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
W = np.array([.2126, .7152, .0722])


def sample(path, size=None):
    im = np.asarray(Image.open(path).convert('RGB'), np.float32) / 255; H, Wd = im.shape[:2]
    x = np.clip((uvs[:, 0] % 1) * Wd, 0, Wd - 1).astype(int); y = np.clip((1 - uvs[:, 1] % 1) * H, 0, H - 1).astype(int)
    return lin(im[y, x])


mask = np.asarray(Image.open('../mm8_m600_claude/textures/body_region_mask.png').convert('RGBA'), np.float32) / 255
H, Wd = mask.shape[:2]
mx = np.clip((uvs[:, 0] % 1) * Wd, 0, Wd - 1).astype(int); my = np.clip((1 - uvs[:, 1] % 1) * H, 0, H - 1).astype(int)
skin = mask[my, mx, 0] > .5


def lch(rgb):
    # linear sRGB -> CIE Lab (D65) -> chroma, hue
    M = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]); xyz = rgb @ M.T / [.9505, 1, 1.089]
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    a = 500 * (f[:, 0] - f[:, 1]); b = 200 * (f[:, 1] - f[:, 2])
    return np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360


out = {}
srcs = {'base': '../mm8_m600_claude/textures/body_basecolor.png',
        **{t: f'../mm8_m600_claude/work/tier_nightmare_{t}_Nightmare.png' for t in 'abc'}}
for key, p in srcs.items():
    c = sample(p); L = c @ W; C, h = lch(c); out[key] = {}
    for r in sorted(set(lab)):
        m = (lab == r) & skin
        out[key][r] = {'lum_p10_50_90': np.round(np.percentile(L[m], [10, 50, 90]), 4).tolist(),
                       'chroma_p50': round(float(np.median(C[m])), 1), 'hue_p50': round(float(np.median(h[m])), 1),
                       'skin_samples': int(m.sum())}
base = sample(srcs['base']) @ W
dark = skin & (base < .002)
out['near_black_skin'] = {r: {'fraction': round(float((dark & (lab == r)).sum() / max(((lab == r) & skin).sum(), 1)), 4),
                              'samples': int((dark & (lab == r)).sum())} for r in sorted(set(lab))}
np.save('work/near_black_pos.npy', pos[dark])
open('work/retex_colour.json', 'w').write(json.dumps(out, indent=1) + '\n')
for k in ('base', 'a', 'b', 'c'):
    print(k); [print('  ', r, v) for r, v in out[k].items()]
print('near black', out['near_black_skin'])
