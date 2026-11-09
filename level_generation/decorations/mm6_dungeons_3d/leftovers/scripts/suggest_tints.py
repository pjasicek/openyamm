#!/usr/bin/env python3
"""Suggest COLOR_0 tints for a hanged corpse: runs albedo.py on work/<corpse>_export.glb and compares with the
native sprite: the body against the sprite's whole mean, the rope or chain material against the sprite's top rows
(rope/chain only, above the body). Prints linear multipliers to multiply into the current tints.
Usage: suggest_tints.py <corpse> <rope material: Rope|Steel> <top rows (x2 px) holding only rope/chain>"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
name, prop, rows = sys.argv[1], sys.argv[2], int(sys.argv[3])


def lin(c):
    c = np.asarray(c, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


sprite = np.asarray(Image.open(REPO / 'assets_dev/engine/decorations_x2' / f'{name}_p143.png').convert('RGBA'), float)
opaque = sprite[..., 3] > 128
native_all = sprite[opaque][:, :3].mean(0)
native_top = sprite[:rows][opaque[:rows]][:, :3].mean(0)
out = subprocess.run(['/snap/bin/blender', '--background', '--python', str(HERE / 'scripts/albedo.py'), '--',
                      str(HERE / 'work' / f'{name}_export.glb')], capture_output=True, text=True).stdout
albedo = {}
for line in out.splitlines():
    if line.startswith('ALBEDO'):
        parts = line.replace('(', '').replace(')', '').replace(',', '').split()
        albedo[parts[1]] = [int(v) for v in parts[2:5]]
print('native all', native_all.round(), 'native top', native_top.round(), 'albedo', albedo)
print('Body x', tuple(np.round(lin(native_all) / lin(albedo['all']), 3)))
if prop in albedo:
    print(prop, 'x', tuple(np.round(lin(native_top) / lin(albedo[prop]), 3)))
