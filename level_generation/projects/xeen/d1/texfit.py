#!/usr/bin/env python3
"""A6 (2026-11-20, texture-fit rule): per texture on D1's models, how many faces show it more than once (u or v span
over the texture's logical size) and the largest repeat. Usage: texfit.py <export.json>"""
import collections
import glob
import json
import os
import sys
from PIL import Image

R = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..')
e = json.load(open(sys.argv[1]))['map']

def size(t):
    for p in glob.glob(os.path.join(R, 'assets_source/textures/native_mm6_mm8/*/textures/%s.bmp' % t)):
        return Image.open(p).size
    for p in glob.glob(os.path.join(R, 'assets_dev/worlds/*/textures_x2/%s.png' % t)):
        w, h = Image.open(p).size
        return w // 2, h // 2
    return None

stat = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, set()])
for b in e['bmodels']:
    for f in b['faces']:
        t = f['texture']
        us, vs = f['texture_us'], f['texture_vs']
        st = stat[t]
        st[0] += 1
        st[4].add(b['name'])
        st.append((max(us) - min(us), max(vs) - min(vs)))
sizes = {}
for t, st in sorted(stat.items()):
    s = sizes.setdefault(t, size(t))
    if not s:
        print('%-12s no size' % t)
        continue
    spans = st[5:]
    rep = [(du / s[0], dv / s[1]) for du, dv in spans]
    many = [r for r in rep if r[0] > 1.05 or r[1] > 1.05]
    mu = max(r[0] for r in rep)
    mv = max(r[1] for r in rep)
    print('%-12s %4dx%-4d faces %4d tiled %4d  max u x%.2f v x%.2f  e.g. %s'
          % (t, s[0], s[1], st[0], len(many), mu, mv, sorted(st[4])[:2]))
