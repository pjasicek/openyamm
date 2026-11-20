#!/usr/bin/env python3
"""Per-tier base colours on the head material (faces differ between tiers; hair and skin are painted, not ramped).
region_variants.py leaves the head material alone: here each variant gets a copy with its own base colour image (normal and ORM
shared), every head primitive maps the variants to the copies, and the first variant keeps the existing image.
Usage: head_variants.py in.glb out.glb <head material> <config json>
config: {"honk_a": null, "honk_b": "<png>", "honk_c": "<png>"} (null: the GLB's own image); paths relative to the project."""
import copy, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
import region_variants as RV
src, dst, head, cfg = sys.argv[1:5]
tiers = json.load(open(cfg))
doc, binary = RV.read_glb(src)
binary = bytearray(binary)
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
hi = next(i for i, m in enumerate(doc['materials']) if m['name'] == head)
doc['materials'][hi].setdefault('extras', {})
for k in ('openyamm_specular',):
    doc['materials'][hi]['extras'][k] = 0.0
doc['materials'][hi]['pbrMetallicRoughness']['metallicFactor'] = 0.0
ids = {}
for name in variants:
    png = tiers.get(name)
    if png is None:
        ids[name] = hi
        continue
    data = Path(png).read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{head}_{name}'})
    old = doc['textures'][doc['materials'][hi]['pbrMetallicRoughness']['baseColorTexture']['index']]
    doc['textures'].append({**old, 'source': len(doc['images']) - 1})
    m = copy.deepcopy(doc['materials'][hi]); m['name'] = f'{head}_{name}'
    m['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
    doc['materials'].append(m); ids[name] = len(doc['materials']) - 1
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        if p.get('material') == hi:
            p.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [
                {'material': ids[n], 'variants': [variants.index(n)]} for n in variants]}
RV.write_glb(dst, doc, bytes(binary))
print('HEADVARIANTS', variants, {k: v for k, v in ids.items()})
