#!/usr/bin/env python3
"""Cut design 2's combined 4K retexture (combined_upload.py: body at UVMap x 0.5 in the lower-left quadrant, head at the
head-upload UV x 0.5 in the lower-right quadrant, Blender UV space = the lower half of the image) into two job folders
the usual compose scripts read: meshy/<job>_body (the body upload's layout) and meshy/<job>_head (the head upload's
layout), each map at 2K (the quadrant's own resolution; no resampling).
Usage (project folder): split_combined.py meshy/combined_retexture_d2"""
import sys
from pathlib import Path
from PIL import Image
job = Path(sys.argv[1])
for part, box in (('body', lambda w, h: (0, h // 2, w // 2, h)), ('head', lambda w, h: (w // 2, h // 2, w, h))):
    out = job.parent / f'{job.name}_{part}'; out.mkdir(exist_ok=True)
    for name in ('base_color', 'normal', 'roughness', 'metallic'):
        f = job / f'texture_urls_0_{name}.png'
        if not f.exists():
            continue
        im = Image.open(f); w, h = im.size
        im.crop(box(w, h)).save(out / f.name)
    print('SPLIT', part, out, im.size)
