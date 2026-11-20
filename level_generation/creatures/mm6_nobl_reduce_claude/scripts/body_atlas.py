#!/usr/bin/env python3
"""Paste the new 1K body maps (textures/nobl_body_*) into the body half of the four merged atlases of a built candidate
(body | 32 px gutter | head, tools/merge_head_material.py); the gutter's body side repeats the body's last column
(the mask gutter stays empty); the head half is untouched. Usage: body_atlas.py <in.glb> <out.glb>"""
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
for tex, suffix in slots.items():
    image = doc['images'][doc['textures'][tex]['source']]; view = doc['bufferViews'][image['bufferView']]
    atlas = Image.open(io.BytesIO(bytes(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])))
    atlas.load(); assert atlas.size == (2080, 1024), atlas.size
    part = Image.open(P / 'textures' / f'nobl_body_{suffix}.png').convert(atlas.mode); assert part.size == (1024, 1024)
    atlas.paste(part, (0, 0))
    if suffix != 'region_mask':
        atlas.paste(part.crop((1023, 0, 1024, 1024)).resize((16, 1024)), (1024, 0))
    out = io.BytesIO(); atlas.save(out, 'PNG', optimize=True); data = out.getvalue()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    image['bufferView'] = len(doc['bufferViews']) - 1
    print('BODY', suffix, image.get('name'))
doc, binary = R._compact(doc, binary)
R.write_glb(dst, doc, binary); print('WROTE', dst, dst.stat().st_size)
