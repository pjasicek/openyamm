#!/usr/bin/env python3
"""Review-viewer / render GLB of one KHR_materials_variants tier: every primitive takes the variant's material; a material
with region ramps gets its ramps baked into a copy of its base colour with the engine rule (claude_shared/tier_textures.py,
as PeasantM7's viewer_tiers.py); the ramps are dropped from it (three.js has none). Usage: viewer_variant.py <glb> <out> <variant>"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
import tier_textures as TT
src, dst, variant = sys.argv[1:4]
doc, blob = RV.read_glb(src)
blob = bytearray(blob)
vi = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']].index(variant)
def image(i):
    bv = doc['bufferViews'][doc['images'][i]['bufferView']]; o = bv.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(blob[o:o + bv['byteLength']])))
used = set()
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        m = p.get('extensions', {}).pop('KHR_materials_variants', None)
        if m:
            p['material'] = next(x['material'] for x in m['mappings'] if vi in x['variants'])
        if 'extensions' in p and not p['extensions']:
            del p['extensions']
        used.add(p['material'])
for mi in sorted(used):
    mat = doc['materials'][mi]; ex = mat.get('extras', {})
    if 'openyamm_region_ramps' not in ex:
        continue
    bt = mat['pbrMetallicRoughness']['baseColorTexture']['index']
    base = np.asarray(image(doc['textures'][bt]['source']).convert('RGB'), np.float64) / 255
    mimg = image(doc['textures'][ex['openyamm_region_mask']['index']]['source']).convert('RGBA')
    mask = np.stack([np.asarray(c.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for c in mimg.split()], -1)
    out = TT.apply(base, mask, ex['openyamm_region_ramps'])
    buf = io.BytesIO(); Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}); blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f"{mat['name']}_{variant}"})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': doc['textures'][bt].get('sampler', 0)})
    mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    ex.pop('openyamm_region_ramps'); ex.pop('openyamm_region_mask')
doc['extensions'].pop('KHR_materials_variants')
doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
RV.write_glb(dst, doc, bytes(blob))
print('VIEWER_VARIANT', dst, variant)
