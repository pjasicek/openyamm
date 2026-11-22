#!/usr/bin/env python3
"""A6 session 11 grades applied after `xtex.py finish` (deterministic; the pre-grade masters are kept in work/).

  grade_s11.py mirror   darkside/finished/xkmirror.png: chroma to 45 % round its own luma (pewter, not tan)
  grade_s11.py gorge    cloudside/finished/xogorge.png: the top band ramps per channel to 7plansky1's blue, so
                        the picture's top edge meets XD-27's sky roof without a pale strip

Rewrites the x4 master and its _x2/_x1 reductions as xtex.py finish does; run `xtex.py check` after.
"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
LUMA = np.array([0.2126, 0.7152, 0.0722])


def lin(v):
    v = np.asarray(v, float) / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def srgb(v):
    v = np.clip(v, 0, 1)
    return np.clip(np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055) * 255, 0, 255)


def write(project, name, rgb):
    finished = HERE / project / 'finished'
    keep = HERE / project / 'work' / f'{name}_pregrade.png'
    if not keep.exists():
        shutil.copy2(finished / f'{name}.png', keep)
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
    image.save(finished / f'{name}.png')
    w, h = image.size
    image.resize((w // 2, h // 2), Image.LANCZOS).save(finished / f'{name}_x2.png')
    image.resize((w // 4, h // 4), Image.LANCZOS).save(finished / f'{name}_x1.png')


def source(project, name):
    keep = HERE / project / 'work' / f'{name}_pregrade.png'
    path = keep if keep.exists() else HERE / project / 'finished' / f'{name}.png'
    return np.asarray(Image.open(path).convert('RGB'), float)


def mirror():
    rgb = lin(source('darkside', 'xkmirror'))
    y = (rgb @ LUMA)[..., None]
    out = y + (rgb - y) * 0.45
    write('darkside', 'xkmirror', srgb(out))


def gorge():
    rgb = lin(source('cloudside', 'xogorge'))
    sky = lin(np.asarray(Image.open(HERE / 'cloudside/pics/7plansky1.png').convert('RGB'), float))
    blue = sky[..., 2] > sky[..., 0] + 0.15
    sky_blue = sky[blue].mean(axis=0)
    h = rgb.shape[0]
    top = rgb[:max(4, h // 64)].reshape(-1, 3)
    top_blue = top[top[..., 2] > top[..., 0] + 0.15].mean(axis=0)
    gains = sky_blue / top_blue
    band = int(h * 0.14)
    ramp = np.ones(h)
    ramp[:band] = np.linspace(0.0, 1.0, band) ** 1.5
    weight = (1 - ramp)[:, None, None]
    out = rgb * (1 + (gains - 1) * weight)
    print('gorge top gains', gains.round(3), 'band rows', band)
    write('cloudside', 'xogorge', srgb(out))


{'mirror': mirror, 'gorge': gorge}[sys.argv[1]]()
