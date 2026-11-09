#!/usr/bin/env python3
"""Widen the four merged atlases of a built candidate from 2080 (body | gutter | head) to 3136 by appending a 32 px
gutter and the front detail section (textures/nobl_detail_*): the gutter repeats the head's last and the detail's first
column (the region-mask gutter stays empty). The candidate's UVs already address the 3136-wide layout (detail_uv.py).
Usage: detail_atlas.py <in.glb> <out.glb>"""
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
    old = Image.open(io.BytesIO(bytes(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])))
    old.load(); assert old.size == (2080, 1024), old.size
    part = Image.open(P / 'textures' / f'nobl_detail_{suffix}.png').convert(old.mode); assert part.size == (1024, 1024)
    atlas = Image.new(old.mode, (3136, 1024)); atlas.paste(old, (0, 0)); atlas.paste(part, (2112, 0))
    if suffix != 'region_mask':
        atlas.paste(old.crop((2079, 0, 2080, 1024)).resize((16, 1024)), (2080, 0))
        atlas.paste(part.crop((0, 0, 1, 1024)).resize((16, 1024)), (2096, 0))
    out = io.BytesIO(); atlas.save(out, 'PNG', optimize=True); data = out.getvalue()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    image['bufferView'] = len(doc['bufferViews']) - 1; image['name'] = image.get('name', '') .replace('_head_atlas', '_atlas3')
    print('DETAIL', suffix, image['name'], atlas.size)
doc, binary = R._compact(doc, binary)
R.write_glb(dst, doc, binary); print('WROTE', dst, dst.stat().st_size)
