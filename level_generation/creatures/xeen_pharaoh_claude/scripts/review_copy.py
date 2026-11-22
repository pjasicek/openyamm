#!/usr/bin/env python3
"""Review copy: bake a skin's ramps into every LOD's base colour image so Blender shows the tier (not a runtime asset).
review_copy.py <in.glb> <skin> <out.glb>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared'))
sys.path.insert(0, str(ROOT / 'level_generation/creatures/xeen_tiers_claude'))
from tier_textures import apply  # noqa: E402
import add_region  # noqa: E402
from xeen_tiers import read  # noqa: E402
src, skin, out = sys.argv[1:4]
doc, binary = read(src)
vi = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']].index(skin)
# material per default material: find mapping for each primitive
done = set()
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        maps = prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
        target = next((mp['material'] for mp in maps if vi in mp['variants']), None)
        if target is None:
            continue
        default = doc['materials'][prim['material']]
        mat = doc['materials'][target]
        bi = default['pbrMetallicRoughness']['baseColorTexture']['index']
        img_i = doc['textures'][bi]['source']
        if img_i in done:
            prim['material'] = prim['material']
            continue
        done.add(img_i)
        base = np.asarray(Image.open(io.BytesIO(add_region.image_bytes(doc, binary, img_i))).convert('RGB'), float) / 255
        mi = doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']
        mk = Image.open(io.BytesIO(add_region.image_bytes(doc, binary, mi))).convert('RGBA')
        mask = np.stack([np.asarray(b, float) / 255 for b in mk.split()], -1)
        res = apply(base, mask, mat['extras']['openyamm_region_ramps'])
        buf = io.BytesIO(); Image.fromarray((np.clip(res, 0, 1) * 255 + 0.5).astype(np.uint8)).save(buf, 'PNG')
        binary = add_region.replace_image(doc, binary, img_i, buf.getvalue())
        doc['images'][img_i]['mimeType'] = 'image/png'
text = json.dumps(doc, separators=(',', ':')).encode(); text += b' ' * (-len(text) % 4)
binary = binary + b'\0' * (-len(binary) % 4)
import struct
Path(out).write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(text) + len(binary)) + struct.pack('<II', len(text), 0x4E4F534A) + text + struct.pack('<II', len(binary), 0x004E4942) + binary)
print('WROTE', out)
