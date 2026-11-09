#!/usr/bin/env python3
"""Installed vs new goblin surface definition on the same 3D texels (installed_lookup): normal-map tilt (mean angle
from the surface normal), albedo luminance local contrast (std of a 3 px high-pass), muscle-scale shading (luminance relative to its
3D neighbourhood within 2.5 / 5 cm) and the normal maps' size and
material scale. Regions: torso front, arms, legs (body skin) and face. Usage: definition_metrics.py [new.glb]"""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools')); from build_actor_lods import read_glb  # noqa: E402


def images(path):
    doc, binary = read_glb(path); m = doc['materials'][0]
    def img(tex):
        v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]; s = v.get('byteOffset', 0)
        return np.asarray(Image.open(io.BytesIO(binary[s:s + v['byteLength']])).convert('RGB'), np.float32) / 255
    return img(m['pbrMetallicRoughness']['baseColorTexture']['index']), img(m['normalTexture']['index']), m['normalTexture'].get('scale', 1.0)


def sample(img, uv):
    h, w = img.shape[:2]; x = np.clip(uv[:, 0] * w - .5, 0, w - 1); y = np.clip((1 - uv[:, 1]) * h - .5, 0, h - 1)
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1) for c in range(3)], -1)


old_c, old_n, old_s = images(ROOT / 'assets_source/worlds/mm6/models/mm6_gob2.glb')
new_c, new_n, new_s = images(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'export/mm6_gob2.glb')
W = 1024 + 32 + 1024
lum = lambda c: c @ np.array([.2126, .7152, .0722])
hp = lambda L: L - ndimage.gaussian_filter(L, 3)
report = {'normal_map_size': {'installed': list(old_n.shape[:2]), 'new': list(new_n.shape[:2])},
          'normal_scale': {'installed': old_s, 'new': new_s}}
for label, x0 in (('body', 0), ('head', 1056)):
    R = np.load(HERE / 'work' / f'uvraster_{label}.npz'); L = np.load(HERE / 'work' / f'installed_lookup_{label}.npz')
    piece, pos = R['piece'], R['pos']; cov = piece >= 0
    # new atlas: this set's half; texel (y, x) of the 1K set
    nc = new_c[:, x0:x0 + 1024]; nn = new_n[:, x0:x0 + 1024]
    regions = {'body': {'torso_front': (piece == 0) & (np.abs(pos[..., 0]) < .16) & (pos[..., 1] < 0) & (pos[..., 2] > .95) & (pos[..., 2] < 1.3),
                        'arms': (piece == 0) & (np.abs(pos[..., 0]) > .3) & (pos[..., 2] > .8),
                        'legs': np.isin(piece, [0, 1, 2]) & (pos[..., 2] < .75)},
               'head': {'face': (piece == 0) & (pos[..., 1] < -.05) & (pos[..., 2] > 1.38)}}[label]
    # installed values at the same 3D points, as images in the new layout
    oc = np.zeros_like(nc); on = np.zeros_like(nn); idx = cov & (L['uv'][..., 0] >= 0)
    oc[idx] = sample(old_c, L['uv'][idx]); on[idx] = sample(old_n, L['uv'][idx])
    for name, m in regions.items():
        m = m & idx & ~ndimage.binary_dilation(~cov, iterations=3)
        tilt = lambda n: float(np.degrees(np.arccos(np.clip((n[m] * 2 - 1)[:, 2] / np.linalg.norm(n[m] * 2 - 1, axis=1), -1, 1))).mean())
        report[name] = {'texels': int(m.sum()),
                        'normal_tilt_deg': {'installed': round(tilt(on), 2), 'new': round(tilt(nn), 2)},
                        'albedo_local_contrast': {'installed': round(float(hp(lum(oc))[m].std()), 4), 'new': round(float(hp(lum(nc))[m].std()), 4)},
                        'albedo_mean_lum': {'installed': round(float(lum(oc)[m].mean()), 4), 'new': round(float(lum(nc)[m].mean()), 4)}}
        P = pos[m]; tree = cKDTree(P); sub = np.random.default_rng(0).choice(len(P), min(3000, len(P)), replace=False)
        for r in (0.025, 0.05):
            nb = tree.query_ball_point(P[sub], r)
            for key, img in (('installed', oc), ('new', nc)):
                Lm = lum(img)[m]
                report[name].setdefault(f'shading_{int(r * 1000)}mm', {})[key] = round(float(np.std([Lm[i] / max(Lm[n].mean(), 1e-4) - 1 for i, n in zip(sub, nb)])), 4)
print(json.dumps(report, indent=1))
