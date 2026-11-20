#!/usr/bin/env python3
"""Assemble the four 3104 x 2080 atlases (atlas_layout.py) of a built candidate from the texture files: head (installed
head maps, base colour with the de-streaked collar from head_collar.py), body (textures/nobl_body_*_1k), front detail
(textures/nobl_detail_*_2k). Gutters repeat the neighbouring section's edge (region-mask gutters stay empty).
Usage: atlas_final.py <in.glb> <out.glb>"""
import io, sys
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]; W, H = 3104, 2080
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools')); from merge_head_material import read_glb, image_of  # noqa: E402
idoc, ibin = read_glb(ROOT / 'assets_source/worlds/mm6/models/mm6_nobl.glb'); im = idoc['materials'][0]
islot = {'basecolor': im['pbrMetallicRoughness']['baseColorTexture']['index'],
         'metal_rough': im['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
         'normal': im['normalTexture']['index'], 'region_mask': im['extras']['openyamm_region_mask']['index']}
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = R.read_glb(src); binary = bytearray(binary); m = doc['materials'][0]
slots = {'basecolor': m['pbrMetallicRoughness']['baseColorTexture']['index'],
         'metal_rough': m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
         'normal': m['normalTexture']['index'], 'region_mask': m['extras']['openyamm_region_mask']['index']}
for name, tex in slots.items():
    mode = 'RGBA' if name == 'region_mask' else 'RGB'
    sfx = '' if name == 'region_mask' else ('_1k', '_2k')
    head = (Image.open(P / 'textures/nobl_head_basecolor_1k.png') if name == 'basecolor'
            else image_of(idoc, ibin, islot[name])[0].crop((1056, 0, 2080, 1024))).convert(mode)
    body = Image.open(P / f'textures/nobl_body_{name}{sfx[0] if sfx else ""}.png').convert(mode)
    det = Image.open(P / f'textures/nobl_detail_{name}{sfx[1] if sfx else ""}.png').convert(mode)
    assert head.size == body.size == (1024, 1024) and det.size == (2048, 2048), (head.size, body.size, det.size)
    a = Image.new(mode, (W, H)); a.paste(head, (0, 0)); a.paste(body, (0, 1056)); a.paste(det, (1056, 0))
    if name != 'region_mask':
        a.paste(head.crop((0, 1023, 1024, 1024)).resize((1024, 16)), (0, 1024))
        a.paste(body.crop((0, 0, 1024, 1)).resize((1024, 16)), (0, 1040))
        a.paste(a.crop((1023, 0, 1024, H)).resize((16, H)), (1024, 0))
        a.paste(det.crop((0, 0, 1, 2048)).resize((16, 2048)), (1040, 0))
    out = io.BytesIO(); a.save(out, 'PNG', optimize=True); data = out.getvalue()
    image = doc['images'][doc['textures'][tex]['source']]
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    image['bufferView'] = len(doc['bufferViews']) - 1; image['name'] = f'nobl_{name}_atlas_final'
    print('ATLAS', name, a.size)
doc, binary = R._compact(doc, binary)
R.write_glb(dst, doc, binary); print('WROTE', dst, dst.stat().st_size)
