#!/usr/bin/env python3
"""(Cow copy of the Terror's; guard A = region mask G black hide, B udder/inner ears, A muzzle) Texture-guard images for mpqem.py from the installed GLB (bytes as installed): work/tex_<base>_<A|B|C>.png.
Tier A is the shared colour under a region mask with ramps, so its guard image is the region mask itself (R hide, G ribs,
B claws on the body; a rib or claw edge that moves is refused); B is the shared colour, C the tier-C colour."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_cow.glb')


def image(tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); return b[o:o + v['byteLength']]


mats = {m['name']: m for m in doc['materials']}
# Terror: one material per tier sharing one base colour and one region mask (tiers differ only by their ramps), so the
# guard reads the region mask (a region edge that moves is refused) and the shared base colour.
for base in ('Cow',):
    out = {'A': image(mats[base + '_A']['extras']['openyamm_region_mask']['index']),
           'B': image(mats[base + '_A']['pbrMetallicRoughness']['baseColorTexture']['index'])}
    for t, data in out.items():
        (HERE / 'work' / f'tex_{base}_{t}.png').write_bytes(data); print('TEX', base, t, len(data))
    # the mask is RGBA (red, green skin, blue, alpha = bone: teeth and claws) summing to 255: keep R, B, A as an RGB guard image
    import io
    import numpy as np
    from PIL import Image
    m = np.asarray(Image.open(io.BytesIO(out['A'])).convert('RGBA'))
    Image.fromarray(np.ascontiguousarray(m[..., [1, 2, 3]])).save(HERE / 'work' / f'tex_{base}_A.png')
