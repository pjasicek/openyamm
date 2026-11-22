#!/usr/bin/env python3
"""Binding scale from the native sprite: the front silhouette (alpha area, width, height) of the standing worm with its
mound in Clouds 056.mon frame 5 (main connected component, the flying rock shards left out) at the Xeen bindings'
1.34 units/px, against the model's front silhouette in Standing at t = 0 (glTF -Z toward the viewer after the yaw
offset: the model faces -Y in Blender = +Z in glTF; the front view looks along the facing axis).
Usage: scale_measure.py <glb>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared' / 'floor'))
import glb_pose as G

UPX = 1.34
a = np.asarray(Image.open(ROOT / 'native' / 'mon_0005.png').convert('RGBA'))[..., 3] > 0
lab, n = ndimage.label(a); sz = ndimage.sum(a, lab, range(1, n + 1)); main = lab == (np.argmax(sz) + 1)
ys, xs = np.nonzero(main)
nat = dict(area=float(main.sum()) * UPX ** 2, width=(xs.max() - xs.min() + 1) * UPX, height=(ys.max() - ys.min() + 1) * UPX)

m = G.Model(G.Glb(sys.argv[1]))
posed = m.skinned_positions(m.world(m.sample('Standing', 0.0)))
RES = 1000.0                                        # px per model metre
img = Image.new('L', (2000, 2000), 0); d = ImageDraw.Draw(img)
for pts, tris in posed:
    for t in tris:
        p = pts[t]                                  # glTF: x right, y up; front view looks along z
        d.polygon([(1000 + q[0] * RES, 1800 - q[1] * RES) for q in p], fill=255)
mm = np.asarray(img) > 0
ys2, xs2 = np.nonzero(mm)
mod = dict(area=float(mm.sum()) / RES ** 2, width=(xs2.max() - xs2.min() + 1) / RES, height=(ys2.max() - ys2.min() + 1) / RES)
print('NATIVE units', {k: round(v, 1) for k, v in nat.items()})
print('MODEL m', {k: round(v, 3) for k, v in mod.items()})
print('SCALE by area', round((nat['area'] / mod['area']) ** 0.5, 1), 'by height', round(nat['height'] / mod['height'], 1),
      'by width', round(nat['width'] / mod['width'], 1))
