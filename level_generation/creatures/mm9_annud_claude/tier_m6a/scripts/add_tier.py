#!/usr/bin/env python3
"""Tier pm6_a (MM9 row 47, PeasantM6a) on the approved, frozen Annud runtime GLB, APPEND ONLY (as
mm9_peasanthom2_claude/scripts/add_tier.py did for mm9_phom1.glb). Annud had no tiers: its two materials stay the
default (variant 0, what `MM9 54 Shopkeeper` draws without a `skin:`), byte for byte. Added at the end:
- the two region masks (body, head) as images at the end of the binary buffer, so every existing bufferView keeps
  its offset, and one texture each (the base colour texture's sampler);
- two materials, copies of "Annud" and "AnnudHead" sharing every existing image, with only openyamm_region_mask /
  openyamm_region_ramps extras added (CLAUDE_CREATURE_TEXTURES.md);
- KHR_materials_variants with the single variant pm6_a, and one mapping on every primitive drawn with either
  material (LOD0-3 and the shadow meshes).

Usage (tier_m6a/): add_tier.py <in glb> <out glb>"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
import region_variants as RV  # noqa: E402

VARIANT = 'pm6_a'
MATERIALS = {'Annud': ('Annud_PM6_A', 'textures/annud_m6a_region_mask.png'),
             'AnnudHead': ('AnnudHead_PM6_A', 'textures/annud_m6a_head_region_mask.png')}

src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src)
blob = bytearray(blob)
assert 'KHR_materials_variants' not in doc.get('extensions', {}), 'Annud already has variants'
ramp = json.loads(Path('textures/annud_m6a_ramps.json').read_text())['ramp']
names = [m['name'] for m in doc['materials']]
new = {}
for base, (name, mask_path) in MATERIALS.items():
    bi = names.index(base)
    bm = doc['materials'][bi]
    data = Path(mask_path).read_bytes()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                          'name': Path(mask_path).stem})
    sampler = doc['textures'][bm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
    doc['textures'].append({'sampler': sampler, 'source': len(doc['images']) - 1})
    m = copy.deepcopy(bm)
    m['name'] = name
    extras = m.setdefault('extras', {})
    extras['openyamm_region_mask'] = {'index': len(doc['textures']) - 1}
    extras['openyamm_region_ramps'] = [ramp]
    doc['materials'].append(m)
    new[bi] = len(doc['materials']) - 1
doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': VARIANT}]}
used = doc.setdefault('extensionsUsed', [])
if 'KHR_materials_variants' not in used:
    used.append('KHR_materials_variants')
mapped = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') in new:
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': new[prim['material']], 'variants': [0]}]}
            mapped += 1
doc['buffers'][0]['byteLength'] = len(blob)
RV.write_glb(dst, doc, bytes(blob))
print('ADD_TIER', dst, VARIANT, {names[k]: doc['materials'][v]['name'] for k, v in new.items()}, 'primitives', mapped,
      round(len(blob) / 1e6, 2), 'MB')
