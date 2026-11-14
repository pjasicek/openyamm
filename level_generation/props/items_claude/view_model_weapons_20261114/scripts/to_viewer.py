#!/usr/bin/env python3
"""In-game captures -> the skins viewer's JPEGs (1280 x 720, quality 82):
ingame/<tag>/<kind>_<place>/<t1..t4|ours>_<idle|swing|swing2>.png -> <viewer>/img/w_<kind>_<place>_<tier>_<pose>.jpg

  python3 -I to_viewer.py <tag> <viewer dir> <kind> [<kind> ...]
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
tag, viewer = sys.argv[1], sys.argv[2]
out = os.path.join(viewer, 'img')
os.makedirs(out, exist_ok=True)
written = []
for kind in sys.argv[3:]:
    for place in ('outdoor', 'indoor'):
        d = os.path.join(PROJECT, 'ingame', tag, f'{kind}_{place}')
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith('.png'):
                continue
            tier, pose = f[:-4].split('_', 1)
            name = f'w_{kind}_{place}_{tier}_{pose}.jpg'
            Image.open(os.path.join(d, f)).convert('RGB').resize((1280, 720), Image.LANCZOS).save(
                os.path.join(out, name), quality=82)
            written.append(name)
print(len(written), 'images')
print('\n'.join(written))
