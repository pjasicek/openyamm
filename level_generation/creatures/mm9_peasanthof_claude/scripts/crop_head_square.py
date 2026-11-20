#!/usr/bin/env python3
"""Meshy head maps from an upload that used the master's HeadUV (head islands scaled 0.8 into the lower-left UV square:
export_head_upload.py) cropped back to the full 0..1 layout that compose_headhand.py expects: image box x 0..0.8 W,
y 0.2 H..H, Lanczos-resized to the original size (reproduces meshy/head_retexture_a2r exactly).
Args: <meshy job dir> <out dir>"""
import os, sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
for n in ('base_color', 'metallic', 'normal', 'roughness'):
    f = f'{src}/texture_urls_0_{n}.png'
    im = Image.open(f); W, H = im.size
    im.crop((0, int(H * 0.2), int(W * 0.8), H)).resize((W, H), Image.LANCZOS).save(f'{dst}/texture_urls_0_{n}.png')
open(f'{dst}/README.txt', 'w').write(f'{os.path.basename(src)} textures cropped to the 0.8 head square (scripts/crop_head_square.py), '
                                     'as head_retexture_a2r.\n')
print('CROPPED', dst)
