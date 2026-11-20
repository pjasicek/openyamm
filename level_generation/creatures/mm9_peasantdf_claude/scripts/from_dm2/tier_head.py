#!/usr/bin/env python3
"""Tier B head image (README deviation): MM9's PEASANTM1B paints a different man on the same head mesh (blond bowl
cut, clean-shaven, heavier face) where PEASANTM1A paints a dark-haired bearded one; a ramp cannot turn a beard into
shaved skin. The head material (<mesh>Head) gets one copy per extra tier with that tier's own head-set base colour and
normal (same HeadUV, same hands), mapped through KHR_materials_variants on every primitive using it (LODs included).
The body material's tiers stay the shared set + region mask + ramps (region_variants.py).
Usage: tier_head.py <in glb> <out glb> <head material> <variant>=<head set prefix> ..."""
import copy, io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
src, dst, mname = sys.argv[1:4]
extra = dict(a.split('=', 1) for a in sys.argv[4:])
doc, blob = RV.read_glb(src)
blob = bytearray(blob)


def add_image(path, flip_green=False):
    im = Image.open(path).convert('RGB')
    if flip_green:      # Meshy normal maps are +y down; prepare_actor_glb.py already converted tier A's (+y up)
        r, g, b = im.split(); im = Image.merge('RGB', (r, g.point(lambda v: 255 - v), b))
    buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    return len(doc['images']) - 1


variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
names = [m['name'] for m in doc['materials']]
hi = names.index(mname)
hm = doc['materials'][hi]
smp = doc['textures'][hm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
mats = {v: hi for v in variants}
for v, prefix in extra.items():
    m = copy.deepcopy(hm); m['name'] = f'{mname}_{v}'
    doc['textures'].append({'source': add_image(f'textures/{prefix}_head_basecolor.png'), 'sampler': smp})
    m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc['textures'].append({'source': add_image(f'textures/{prefix}_head_normal_1k.png', flip_green=True), 'sampler': smp})
    m['normalTexture'] = dict(hm.get('normalTexture', {}), index=len(doc['textures']) - 1)
    doc['materials'].append(m); mats[v] = len(doc['materials']) - 1
n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') == hi:
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}
            n += 1
RV.write_glb(dst, doc, bytes(blob))
print('TIER_HEAD', dst, 'head prims', n, 'variants', variants, round(len(blob) / 1e6, 1), 'MB')
