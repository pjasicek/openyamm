#!/usr/bin/env python3
"""PeasantHOM2 (row 59) as a new tier of the approved PeasantHOM1 runtime GLB, APPEND ONLY: the existing variants, materials,
images, meshes, skins and clips stay byte for byte as they are; a new KHR_materials_variants entry is added, with one new
material per tier-carrying material (a copy of tier A's) that points at the new tier's own base colour and normal images
and drops the region mask and ramps (HOM2 is its own paint: different clothes and a different man, so no ramps), and every
primitive mapped to the copied material gets one more mapping for the new variant (LODs and shadow meshes included).
The new images are appended at the end of the binary buffer, so every existing bufferView keeps its offset.

Usage (project folder): add_tier.py <in glb> <out glb> <variant> <base material>=<colour png>,<normal png> ...
  (normal pngs are Meshy-convention +y down and are converted to glTF +y up here, as prepare_actor_glb.py does)"""
import copy, io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV

src, dst, variant = sys.argv[1:4]
maps = {}
for a in sys.argv[4:]:
    k, v = a.split('=', 1); c, n = v.split(','); maps[k] = (c, n)
doc, blob = RV.read_glb(src)
blob = bytearray(blob)


def add_image(path, flip_green=False):
    im = Image.open(path).convert('RGB')
    if flip_green:
        r, g, b = im.split(); im = Image.merge('RGB', (r, g.point(lambda v: 255 - v), b))
    buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    return len(doc['images']) - 1


vlist = doc['extensions']['KHR_materials_variants']['variants']
assert variant not in [v['name'] for v in vlist]
vlist.append({'name': variant}); vi = len(vlist) - 1
names = [m['name'] for m in doc['materials']]
new = {}
for base, (col, nrm) in maps.items():
    bi = names.index(base); bm = doc['materials'][bi]
    m = copy.deepcopy(bm); m['name'] = base.rsplit('_', 1)[0] + '_' + variant.upper()
    smp = doc['textures'][bm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
    doc['textures'].append({'source': add_image(col), 'sampler': smp})
    m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1, 'texCoord': 0}
    doc['textures'].append({'source': add_image(nrm, flip_green=True), 'sampler': smp})
    m['normalTexture'] = dict(bm.get('normalTexture', {}), index=len(doc['textures']) - 1)
    for k in ('openyamm_region_mask', 'openyamm_region_ramps'):
        m.get('extras', {}).pop(k, None)
    doc['materials'].append(m); new[bi] = len(doc['materials']) - 1
n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        maps_ = prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings')
        if not maps_:
            continue
        a = next((mp['material'] for mp in maps_ if 0 in mp['variants']), None)
        assert a in new, (mesh['name'], a)
        maps_.append({'material': new[a], 'variants': [vi]}); n += 1
doc['buffers'][0]['byteLength'] = len(blob)
RV.write_glb(dst, doc, bytes(blob))
print('ADD_TIER', dst, variant, 'materials', {names[k]: doc['materials'][v]['name'] for k, v in new.items()}, 'primitives', n,
      round(len(blob) / 1e6, 1), 'MB')
