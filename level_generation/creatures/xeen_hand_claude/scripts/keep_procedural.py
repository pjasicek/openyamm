#!/usr/bin/env python3
"""After grading: put the procedural gullet, tongue and fang texels (parts 2-4) back from the ungraded base colour, so the
AO and contrast of the grade do not change their designed gradients."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
part = np.load(ROOT / 'work/part_map_2k.npy')
keep = (part >= 2) & (part <= 4)
src = np.asarray(Image.open(ROOT / 'textures/hand_basecolor.png').convert('RGB'))
dst = np.array(Image.open(ROOT / 'textures/hand_basecolor_graded.png').convert('RGB'))
dst[keep] = src[keep]
Image.fromarray(dst).save(ROOT / 'textures/hand_basecolor_graded.png', optimize=True)
print('KEPT procedural texels', int(keep.sum()))
