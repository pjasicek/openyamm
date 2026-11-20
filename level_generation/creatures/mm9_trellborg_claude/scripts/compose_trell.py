#!/usr/bin/env python3
"""Runtime maps from the 4K Meshy paints on the one upload layout (project folder): colour resized once to 2048 with Lanczos, normal and ORM 1K per tier (roughness and metal differ: skin, fur, mail, plate). Writes textures/trell_body_{t}_raw.png, _normal.png, _orm.png, trell_body_ao.png. Args: <tiers>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
M = Path('meshy'); T = Path('textures')
ao = None
if (T / 'trell_ao_4k.png').exists():
    ao = Image.open(T / 'trell_ao_4k.png').convert('L'); ao.resize((2048, 2048), Image.LANCZOS).save(T / 'trell_body_ao.png')
for t in sys.argv[1]:
    j = M / f'trell_retex_{t}'
    Image.open(j / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS).save(T / f'trell_body_{t}_raw.png')
    a_ = np.array(Image.open(j / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS)); a_[..., 1] = 255 - a_[..., 1]
    Image.fromarray(a_).save(T / f'trell_body_{t}_normal.png')
    r = np.asarray(Image.open(j / 'texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    mt = np.asarray(Image.open(j / 'texture_urls_0_metallic.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    oc = np.asarray(ao.resize((1024, 1024), Image.LANCZOS), np.float32) / 255 if ao else np.ones_like(r)
    Image.fromarray((np.stack([oc, np.maximum(r, 0.42), np.clip(mt, 0, 1)], -1) * 255 + .5).astype('u1')).save(T / f'trell_body_{t}_orm.png')
print('COMPOSE done')
