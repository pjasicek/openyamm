#!/usr/bin/env python3
"""Step 5 (README.md): the Meshy retexture request of one weapon kind in one tier.

  python3 -I meshy_request.py <kind> <tier> [version]

Each Codex master is checked against its guide (alpha IoU; below 0.8 it is refused) and cut to the guide's silhouette
(halos and stray background gone): work/<kind>/masters_t<tier>/clean_<view>.png. requests/<kind>_t<tier>_<version>.json:
meshy-7, original UVs, PBR, 4K, the clean masters as multiview, no text prompt (the tier's look is in the masters).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from codex_masters import NUMBER  # noqa: E402
from kinds import KINDS  # noqa: E402

kind, tier = sys.argv[1], int(sys.argv[2])
version = sys.argv[3] if len(sys.argv) > 3 else 'v1'
work = os.path.join(PROJECT, 'work', kind)
masters = os.path.join(work, f'masters_t{tier}')
images = []
for view in KINDS[kind]['views']:
    path = os.path.join(masters, f'{NUMBER[view]}_{view}.png')
    front = os.path.join(masters, '01_front.png')
    mirrored = False
    if not os.path.exists(path) and view == 'back' and os.path.exists(front):
        path, mirrored = front, True
        print('back: the front master mirrored')
    if not os.path.exists(path):
        print('missing', path)
        continue
    guide = Image.open(os.path.join(work, f'guide_{view}.png')).convert('RGBA')
    master = Image.open(path).convert('RGBA')
    if mirrored:
        master = master.transpose(Image.FLIP_LEFT_RIGHT)
    if master.size != guide.size:
        master = master.resize(guide.size, Image.LANCZOS)
    g = np.asarray(guide)[..., 3] > 128
    m = np.asarray(master)[..., 3] > 128
    iou = (g & m).sum() / max((g | m).sum(), 1)
    print(view, 'IoU %.3f' % iou)
    if iou < 0.8:
        print('refused', view)
        continue
    rgba = np.asarray(master).copy()
    rgba[..., 3] = np.asarray(guide)[..., 3]
    clean = os.path.join(masters, f'clean_{view}.png')
    Image.fromarray(rgba).save(clean)
    images.append(f'@file:{os.path.relpath(clean, PROJECT)}')
request = {'model_url': f'@file:work/{kind}/upload.glb', 'ai_model': 'meshy-7', 'enable_original_uv': True,
           'enable_pbr': True, 'texture_resolution': '4k', 'target_formats': ['glb'], 'multiview_image_urls': images}
os.makedirs(os.path.join(PROJECT, 'requests'), exist_ok=True)
out = os.path.join(PROJECT, 'requests', f'{kind}_t{tier}_{version}.json')
json.dump(request, open(out, 'w'), indent=1)
print(out, len(images), 'views')
