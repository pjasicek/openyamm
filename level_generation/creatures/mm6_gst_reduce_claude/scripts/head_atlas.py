#!/usr/bin/env python3
"""Paste the new 1K head maps (textures/) into the head half of the four merged atlases of a built candidate
(base colour, metallic-roughness, normal, region mask: body | 32 px gutter | head, tools/merge_head_material.py);
the gutter's head side repeats the head's first column (the mask gutter stays empty), the body half is untouched.
Unreferenced buffer data is compacted. Usage: head_atlas.py <in.glb> <out.glb>"""
import io, sys
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = R.read_glb(src); binary = bytearray(binary)
m = doc['materials'][0]
slots = {m['pbrMetallicRoughness']['baseColorTexture']['index']: 'basecolor_1k',
         m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']: 'metal_rough_1k',
         m['normalTexture']['index']: 'normal_1k', m['extras']['openyamm_region_mask']['index']: 'region_mask'}
assert all(x['pbrMetallicRoughness'].get('baseColorTexture', {}).get('index') == m['pbrMetallicRoughness']['baseColorTexture']['index']
           for x in doc['materials']), 'variants must share the atlases'
for tex, suffix in slots.items():
    image = doc['images'][doc['textures'][tex]['source']]; view = doc['bufferViews'][image['bufferView']]
    atlas = Image.open(io.BytesIO(bytes(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])))
    atlas.load(); assert atlas.size == (2080, 1024), atlas.size
    headmap = Image.open(P / 'textures' / f'gst_head_{suffix}.png').convert(atlas.mode); assert headmap.size == (1024, 1024)
    atlas.paste(headmap, (1056, 0))
    if suffix != 'region_mask':
        atlas.paste(headmap.crop((0, 0, 1, 1024)).resize((16, 1024)), (1040, 0))
    out = io.BytesIO(); atlas.save(out, 'PNG', optimize=True); data = out.getvalue()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    image['bufferView'] = len(doc['bufferViews']) - 1
    print('HEAD', suffix, image.get('name'))
doc, binary = R._compact(doc, binary)
R.write_glb(dst, doc, binary); print('WROTE', dst, dst.stat().st_size)
