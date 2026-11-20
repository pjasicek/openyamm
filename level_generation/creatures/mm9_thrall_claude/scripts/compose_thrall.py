#!/usr/bin/env python3
"""Runtime maps from the three 4K Meshy paints on the one upload layout (project folder). Torso square = u 0..ST, limbs square = u ST..1, both from v 0: crops resized once with Lanczos.
Writes textures/thrall_torso_{a,b,c}_raw.png (2048), thrall_torso_{a,b,c}_normal.png (1K), thrall_limbs_{a,b,c}_raw.png (1792; only c ships, a and b are ramp targets), thrall_limbs_normal.png (1K), thrall_limbs_orm.png, thrall_torso_orm.png (1K: R AO, G roughness floor 0.5, B metallic), AO crops."""
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ST, SL = 0.55, 0.45
M = Path('meshy'); T = Path('textures')
def crop(im, part, size, resample=Image.LANCZOS):
    W, H = im.size
    if part == 'torso': box = (0, H * (1 - ST), W * ST, H)
    else: box = (W * ST, H * (1 - SL), W, H)
    return im.resize((size, size), resample, box=box)
ao = Image.open(T / 'thrall_ao_4k.png').convert('L')
crop(ao, 'torso', 2048).save(T / 'thrall_torso_ao.png'); crop(ao, 'limbs', 2048).save(T / 'thrall_limbs_ao.png')
for t in 'abc':
    j = M / f'thrall_retex_{t}'
    base = Image.open(j / 'texture_urls_0_base_color.png').convert('RGB')
    nrm = Image.open(j / 'texture_urls_0_normal.png').convert('RGB')
    crop(base, 'torso', 2048).save(T / f'thrall_torso_{t}_raw.png'); crop(base, 'limbs', 2048).save(T / f'thrall_limbs_{t}_raw.png')
    crop(nrm, 'torso', 1024).save(T / f'thrall_torso_{t}_normal.png')
    if t == 'c': crop(nrm, 'limbs', 1024).save(T / 'thrall_limbs_normal.png')
j = M / 'thrall_retex_c'
rough = Image.open(j / 'texture_urls_0_roughness.png').convert('L'); metal = Image.open(j / 'texture_urls_0_metallic.png').convert('L')
for part in ('torso', 'limbs'):
    r = np.asarray(crop(rough, part, 1024), np.float32) / 255
    aoc = np.asarray(crop(ao, part, 1024), np.float32) / 255
    orm = np.stack([aoc, np.maximum(r, 0.5), np.zeros_like(r)], -1)
    Image.fromarray((orm * 255 + .5).astype('u1')).save(T / f'thrall_{part}_orm.png')
print('COMPOSE done')
