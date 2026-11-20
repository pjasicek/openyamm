#!/usr/bin/env python3
"""Head + hands set from a texture-pass head retexture (2026-10-30): the approved head set (compose_headhand.py) with
its head square replaced. compose_headhand.py resamples the Meshy head maps into the lower-left HEAD_SCALE square
(seam gain 1 for these separate head shells: the approved square equals the old return resized), so this pastes the
new return there - colour from 4K straight to the 1638 px square at 2K, normal and roughness to the 819 px square at
1K (ORM R 255, G roughness floor 128, B 0, as compose_headhand.py) - and keeps every texel outside the square from the
approved files, so the hands' graded MakeHuman skin and their flat normal/ORM stay byte for byte.

Usage (from the project folder): compose_head_texpass.py <approved prefix> <out prefix> <meshy head job dir>
Writes v2/textures/<out>_head_basecolor.png, <out>_head_normal_1k.png, <out>_head_metal_rough_1k.png."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

old, out, job = sys.argv[1:4]
T, J = Path('v2/textures'), Path(job)
S = 0.8


def paste(approved, new, mode):
    a = Image.open(T / approved).convert(mode)
    n = a.size[0]
    k = int(round(n * S))
    a.paste(new.resize((k, k), Image.LANCZOS), (0, n - k))
    return a


paste(f'{old}_head_basecolor.png', Image.open(J / 'texture_urls_0_base_color.png').convert('RGB'), 'RGB') \
    .save(T / f'{out}_head_basecolor.png')
paste(f'{old}_head_normal_1k.png', Image.open(J / 'texture_urls_0_normal.png').convert('RGB'), 'RGB') \
    .save(T / f'{out}_head_normal_1k.png')
rough = np.maximum(np.asarray(Image.open(J / 'texture_urls_0_roughness.png').convert('L')), 128).astype(np.uint8)
z = np.zeros_like(rough)
orm = Image.merge('RGB', [Image.fromarray(np.full_like(rough, 255)), Image.fromarray(rough), Image.fromarray(z)])
paste(f'{old}_head_metal_rough_1k.png', orm, 'RGB').save(T / f'{out}_head_metal_rough_1k.png')
print('COMPOSE_HEAD_TEXPASS', out, 'from', job)
