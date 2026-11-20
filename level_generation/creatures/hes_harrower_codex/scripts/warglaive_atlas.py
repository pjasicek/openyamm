"""Paste the warglaives' baked textures (warglaive_texture.py bake: warglaives/<key>/tex/) into their free rects of
the shared armour atlas (warglaives/atlas_rects.json), in the atlas conventions: base colour (alpha 1), the normal map
as is (both are OpenGL tangent space with rows growing down and the rect keeps u and v), metal_rough R = specular mask
(0.75 gold, 0.24 elsewhere, as armour_texture.py), G = the baked roughness, B = 0; region mask R ivory, G gold, B glow,
A 0; material classes 9 for gold, 11 elsewhere. Texels outside a glaive's UV islands keep the island colours padded
4 px outward and no region. Rerun after armour_texture.py, which repaints the whole atlas. Args: none"""
import json, os
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures'); R = json.load(open(os.path.join(HERE, 'warglaives', 'atlas_rects.json')))
names = {k: os.path.join(T, f'hkr_armour_{k}.png') for k in ('basecolor', 'normal', 'metal_rough', 'region_mask', 'material_classes')}
A = {k: np.array(Image.open(p)) for k, p in names.items()}
for key, (x, y, w, h) in R['rects'].items():
    src = os.path.join(HERE, 'warglaives', key, 'tex')
    load = lambda n, mode=Image.BILINEAR: np.array(Image.open(os.path.join(src, n)).convert('RGB').resize((w, h), mode)).astype(np.float32) / 255
    base, nrm, mr = load('basecolor.png'), load('normal.png'), load('metal_rough.png')
    region, island = load('region.png', Image.NEAREST), load('island.png', Image.NEAREST)[..., 0] > 0.5
    gold = region[..., 1] > 0.5
    dist, (iy, ix) = distance_transform_edt(~island, return_indices=True)
    keep = island | (dist <= 4)
    for arr in (base, nrm, mr):
        arr[:] = arr[iy, ix]
    sl = (slice(y, y + h), slice(x, x + w))
    rgba = np.dstack([np.clip(base, 12 / 255, 243 / 255), np.ones((h, w))])
    A['basecolor'][sl] = np.where(keep[..., None], (rgba * 255).round().astype(np.uint8), A['basecolor'][sl])
    A['normal'][sl] = np.where(keep[..., None], (nrm * 255).round().astype(np.uint8), A['normal'][sl])
    orm = np.dstack([np.where(gold, .75, .24), mr[..., 1], np.zeros((h, w))])
    A['metal_rough'][sl] = np.where(keep[..., None], (orm * 255).round().astype(np.uint8), A['metal_rough'][sl])
    mask = np.dstack([region * island[..., None], np.zeros((h, w))])
    A['region_mask'][sl] = (mask * 255).round().astype(np.uint8)
    A['material_classes'][sl] = np.where(keep, np.where(gold, 9, 11), 0).astype(np.uint8)
    print('GLAIVE_ATLAS', key, 'rect', [x, y, w, h], 'island texels', int(island.sum()), 'gold', int((gold & island).sum()),
          'ivory', int(((region[..., 0] > .5) & island).sum()), 'glow', int(((region[..., 2] > .5) & island).sum()))
for k, p in names.items():
    Image.fromarray(A[k]).save(p)
