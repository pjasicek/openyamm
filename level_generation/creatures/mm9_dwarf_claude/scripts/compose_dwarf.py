#!/usr/bin/env python3
"""Runtime maps from the 4K Meshy paints on the one upload layout (project folder): torso square = u 0..ST, limbs square = u ST..1, both from v 0, crops resized once with Lanczos.
Writes textures/dwarf_torso_{t}_raw.png (2048), dwarf_torso_{t}_normal.png (1K), dwarf_limbs_{t}_raw.png (1536), dwarf_limbs_normal.png (1K), dwarf_torso_orm.png, dwarf_limbs_orm.png. Args: <tiers>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ST, SL = 0.6, 0.4
M = Path('meshy'); T = Path('textures')
def crop(im, part, size, resample=Image.LANCZOS):
    W, H = im.size
    box = (0, H * (1 - ST), W * ST, H) if part == 'torso' else (W * ST, H * (1 - SL), W, H)
    return im.resize((size, size), resample, box=box)
ao = None
if (T / 'dwarf_ao_4k.png').exists():
    ao = Image.open(T / 'dwarf_ao_4k.png').convert('L')
    crop(ao, 'torso', 2048).save(T / 'dwarf_torso_ao.png'); crop(ao, 'limbs', 1536).save(T / 'dwarf_limbs_ao.png')
for t in 'a':
    j = M / f'dwarf_retex_{t}'
    base = Image.open(j / 'texture_urls_0_base_color.png').convert('RGB')
    nrm = Image.open(j / 'texture_urls_0_normal.png').convert('RGB')
    crop(base, 'torso', 2048).save(T / f'dwarf_torso_{t}_raw.png'); crop(base, 'limbs', 1536).save(T / f'dwarf_limbs_{t}_raw.png')
    for part in ('torso', 'limbs'):                              # Meshy's +y down -> glTF +y up, here, because the variants go in after prepare_actor_glb.py
        a_ = np.array(crop(nrm, part, 1024)); a_[..., 1] = 255 - a_[..., 1]
        Image.fromarray(a_).save(T / f'dwarf_{part}_{t}_normal.png')
    rough = Image.open(j / 'texture_urls_0_roughness.png').convert('L')
    metal = Image.open(j / 'texture_urls_0_metallic.png').convert('L')
    for part in ('torso', 'limbs'):                              # each tier's own roughness and metal: mail and plates differ per tier
        r = np.asarray(crop(rough, part, 1024), np.float32) / 255
        mt = np.asarray(crop(metal, part, 1024), np.float32) / 255
        a_ = np.asarray(crop(ao, part, 1024), np.float32) / 255 if ao else np.ones_like(r)
        orm = np.stack([a_, np.maximum(r, 0.42), np.clip(mt, 0, 1)], -1)
        Image.fromarray((orm * 255 + .5).astype('u1')).save(T / f'dwarf_{part}_{t}_orm.png')
print('COMPOSE done')
