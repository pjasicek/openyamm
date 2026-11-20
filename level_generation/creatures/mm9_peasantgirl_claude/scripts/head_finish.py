#!/usr/bin/env python3
"""Head set: gentle grade per tier with the head AO, one shared normal (mean of the tiers' luminance detail), ORM. Project folder."""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ni
T = Path('textures')
for t in 'abc':
    subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / 'mk_head_ao.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.25', '--contrast', '1.0', '--saturation', '1.0', str(T / f'mk_head_{t}_raw.png')], stdout=subprocess.DEVNULL)
    Path(T / f'mk_head_{t}_raw_graded.png').rename(T / f'mk_head_{t}_final.png')
for t in 'abc':
    # skin down from the viewer's blown highlights, shadows lifted a little
    v = np.asarray(Image.open(T / f'mk_head_{t}_final.png').convert('RGB'), np.float32) / 255
    v = np.clip(v, 0, 1) ** 0.86 * np.array([0.84, 0.79, 0.73], np.float32)
    Image.fromarray((v * 255 + .5).astype('u1')).save(T / f'mk_head_{t}_final.png')
L = [np.asarray(Image.open(T / f'mk_head_{t}_final.png').convert('L'), np.float32) / 255 for t in 'abc']
hp = sum(l - ni.gaussian_filter(l, 6) for l in L) / 3
gx = ni.sobel(hp, axis=1) * 2.0; gy = ni.sobel(hp, axis=0) * 2.0
n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255 + .5).astype('u1')).save(T / 'mk_head_normal.png')
a = np.asarray(Image.open(T / 'mk_head_ao.png').convert('L'), np.float32) / 255
orm = np.stack([a, np.full_like(a, 0.7), np.zeros_like(a)], -1)
Image.fromarray((orm * 255 + .5).astype('u1')).save(T / 'mk_head_orm.png')
print('HEADFIN')
