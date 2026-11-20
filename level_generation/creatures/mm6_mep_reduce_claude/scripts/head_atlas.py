#!/usr/bin/env python3
"""Paste the new head maps (textures/mep_head_*.png, 1024) into the head half of every merged atlas the body
materials use (LOD0-3: body | 32 px gutter | head, head width (w - 32) / 2): base colour, metallic-roughness, normal,
region mask. The gutter's head side repeats the head's first column (the mask gutter stays as it is); the body half is
untouched. Unreferenced buffer data is compacted. Usage: head_atlas.py <in.glb> <out.glb>"""
import io, sys
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = R.read_glb(src); binary = bytearray(binary)
slots = {}
for m in doc['materials']:
    if not m['name'].startswith('Mep_'):
        continue
    for idx, suffix in ((m['pbrMetallicRoughness']['baseColorTexture']['index'], 'basecolor'),
                        (m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'], 'metal_rough'),
                        (m['normalTexture']['index'], 'normal'), (m['extras']['openyamm_region_mask']['index'], 'region_mask')):
        slots[doc['textures'][idx]['source']] = suffix
for source, suffix in sorted(slots.items()):
    image = doc['images'][source]; view = doc['bufferViews'][image['bufferView']]
    atlas = Image.open(io.BytesIO(bytes(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])))
    atlas.load(); w, h = atlas.size; hw = (w - 32) // 2; assert hw == h, atlas.size
    headmap = Image.open(P / 'textures' / f'mep_head_{suffix}.png').convert(atlas.mode)
    if hw != headmap.size[0]:
        headmap = headmap.resize((hw, hw), Image.BOX)
    atlas.paste(headmap, (w - hw, 0))
    if suffix != 'region_mask':
        atlas.paste(headmap.crop((0, 0, 1, hw)).resize((16, hw)), (w - hw - 16, 0))
    out = io.BytesIO(); atlas.save(out, 'PNG', optimize=True); data = out.getvalue()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    image['bufferView'] = len(doc['bufferViews']) - 1
    print('HEAD', suffix, image.get('name'), atlas.size)
doc, binary = R._compact(doc, binary)
R.write_glb(dst, doc, binary); print('WROTE', dst, dst.stat().st_size)
