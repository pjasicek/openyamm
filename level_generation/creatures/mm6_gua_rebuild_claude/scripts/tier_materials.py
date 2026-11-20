#!/usr/bin/env python3
"""Tier materials: one material per variant, the tiers differ in pattern, not only colour (leather; chain with a leather mantle; chain and steel), so each has its own colour, normal and
ORM images (see README: why no ramps here), head set and halberd shared where MM9 shares them. Maps every primitive (LOD0-3, shadow) through KHR_materials_variants.
Args: <in glb> <out glb>"""
import copy, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
IN, OUT = sys.argv[1:3]
g = Glb(Path(IN)); d = g.json
VAR = ['guard_a', 'guard_b', 'guard_c']
SETS = {'Guard': [('guard_a_final.png', 'guard_a_normal_1k.png', 'guard_a_metal_rough_1k.png'), ('guard_b_final.png', 'guard_b_normal_1k.png', 'guard_b_metal_rough_1k.png'), ('guard_c_final.png', 'guard_c_normal_1k.png', 'guard_c_metal_rough_1k.png')],
        'GuardHead': [('guard_heada_final.png', 'guard_heada_normal_1k.png', 'guard_heada_metal_rough_1k.png')] + [('guard_headc_final.png', 'guard_headc_normal_1k.png', 'guard_headc_metal_rough_1k.png')] * 2,
        'Halberd': [('halberd_a_basecolor.png', 'halberd_a_normal.png', 'halberd_a_orm.png')] * 2 + [('halberd_c_basecolor.png', 'halberd_c_normal.png', 'halberd_c_orm.png')]}
imcache = {}


def tex(fn):
    if fn in imcache: return imcache[fn]
    data = Path('textures', fn).read_bytes()
    g.bin = bytes(g.bin) + b'\0' * (-len(g.bin) % 4)
    d['bufferViews'].append(dict(buffer=0, byteOffset=len(g.bin), byteLength=len(data)))
    g.bin += data
    d['images'].append(dict(name=fn[:-4], mimeType='image/png', bufferView=len(d['bufferViews']) - 1))
    d['textures'].append(dict(source=len(d['images']) - 1, sampler=0) if d.get('samplers') else dict(source=len(d['images']) - 1))
    imcache[fn] = len(d['textures']) - 1
    return imcache[fn]


base_names = {m['name']: i for i, m in enumerate(d['materials'])}
maps = {}
for name, sets in SETS.items():
    if name not in base_names: continue
    ids = []
    for v, (c, n, o) in zip(VAR, sets):
        m = copy.deepcopy(d['materials'][base_names[name]])
        m['name'] = f"{name}_{v[-1].upper()}"
        m['pbrMetallicRoughness']['baseColorTexture'] = dict(index=tex(c))
        m['pbrMetallicRoughness']['metallicRoughnessTexture'] = dict(index=tex(o))
        m['pbrMetallicRoughness']['metallicFactor'] = 0.0
        m['normalTexture'] = dict(index=tex(n))
        m.setdefault('extras', {})['openyamm_specular'] = 0.0 if name != 'Halberd' else 0.25
        if name == 'Guard' and v == 'guard_b':                  # the mantle: the only colour-only difference, a region ramp over tier A's leather texels
            m['extras']['openyamm_region_mask'] = dict(index=tex('guard_b_region_mask.png'))
            m['extras']['openyamm_region_ramps'] = [json.load(open('textures/guard_b_ramp.json'))]
        d['materials'].append(m); ids.append(len(d['materials']) - 1)
    maps[base_names[name]] = ids
prims = 0
for mesh in d['meshes']:
    for pr in mesh['primitives']:
        mt = pr.get('material')
        if mt in maps:
            pr['material'] = maps[mt][0]
            pr.setdefault('extensions', {})['KHR_materials_variants'] = dict(mappings=[dict(material=maps[mt][k], variants=[k]) for k in range(3)])
            prims += 1
d.setdefault('extensions', {})['KHR_materials_variants'] = dict(variants=[dict(name=v) for v in VAR])
if 'KHR_materials_variants' not in d.setdefault('extensionsUsed', []): d['extensionsUsed'].append('KHR_materials_variants')
sys.path.insert(0, '../claude_shared')
import region_variants as RV
d, binary = RV._compact(d, bytes(g.bin))
RV.write_glb(OUT, d, binary)
print('TIERS', OUT, prims, 'primitives', len(d['images']), 'images', round(len(binary) / 1e6, 1), 'MB')
