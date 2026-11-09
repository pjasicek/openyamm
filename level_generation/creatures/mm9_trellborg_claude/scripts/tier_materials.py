#!/usr/bin/env python3
"""Tier materials: MM9's three skins are three outfits (README, deviation): body colour, normal, ORM per tier; head colour per tier (hair, beard, collar) with shared normal and ORM; club shared. Maps every body primitive (LOD0-3) through KHR_materials_variants.
Args: <in glb> <out glb>"""
import copy, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
IN, OUT = sys.argv[1:3]
g = Glb(Path(IN)); d = g.json
VAR = ['trell_a', 'trell_b', 'trell_c']
B = lambda t: (f'trell_body_{t}_final.png', f'trell_body_{t}_normal.png', f'trell_body_{t}_orm.png')
Hd = lambda t: (f'trell_head_{t}_final.png', 'trell_head_normal.png', 'trell_head_orm.png')
SETS = {'Trellborg': [B('a'), B('b'), B('c')], 'TrellborgHead': [Hd('a'), Hd('b'), Hd('c')]}
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
    ids = []
    for v, (c, n, o) in zip(VAR, sets):
        m = copy.deepcopy(d['materials'][base_names[name]])
        m['name'] = f"{name}_{v[-1].upper()}"
        m['pbrMetallicRoughness']['baseColorTexture'] = dict(index=tex(c))
        m['pbrMetallicRoughness']['metallicRoughnessTexture'] = dict(index=tex(o))
        m['pbrMetallicRoughness']['metallicFactor'] = 0.0 if name != 'Trellborg' else {'a': 0.25, 'b': 0.0, 'c': 0.35}[v[-1]]
        m['normalTexture'] = dict(index=tex(n))
        m.setdefault('extras', {})['openyamm_specular'] = 0.0 if name != 'Trellborg' else {'a': 0.1, 'b': 0.0, 'c': 0.2}[v[-1]]
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
