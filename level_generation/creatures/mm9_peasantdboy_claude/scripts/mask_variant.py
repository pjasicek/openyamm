#!/usr/bin/env python3
"""Give one tier's body material its own region mask (boy b's open vest: the panel's texels move from the vest channel to
the shirt channel, tiers_boy.py -> textures/pboy_region_mask_b.png). The image is added once and the variant material's
`openyamm_region_mask` points at a new texture of it (same sampler as the shared mask); every other tier keeps the
shared mask. Usage: mask_variant.py <in glb> <out glb> <material name>=<mask png> ..."""
import io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src)
blob = bytearray(blob)
names = {m['name']: i for i, m in enumerate(doc['materials'])}
for spec in sys.argv[3:]:
    mname, png = spec.split('=', 1)
    mat = doc['materials'][names[mname]]
    old = doc['textures'][mat['extras']['openyamm_region_mask']['index']]
    buf = io.BytesIO(); Image.open(png).save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(png).stem})
    tex = dict(old); tex['source'] = len(doc['images']) - 1
    doc['textures'].append(tex)
    mat['extras']['openyamm_region_mask'] = {'index': len(doc['textures']) - 1}
    print('MASK_VARIANT', mname, png)
RV.write_glb(dst, doc, bytes(blob))
