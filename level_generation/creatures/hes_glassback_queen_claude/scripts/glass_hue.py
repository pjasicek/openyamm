#!/usr/bin/env python3
"""The Queen's glass atlas (textures/hgb_glass_basecolor_512.png): a copy of the family's
(../hes_glassback_claude/textures/, unchanged) with its teal glints turned ice-blue: hue +39 degrees on texels
saturated over 40/255 (viewer review 1: the crest read teal-green). Usage: glass_hue.py"""
import numpy as np
from PIL import Image
im = Image.open('../hes_glassback_claude/textures/hgb_glass_basecolor_512.png').convert('RGB')
hsv = np.asarray(im.convert('HSV')).astype(np.int32)
sat = hsv[..., 1] > 40
hsv[..., 0] = np.where(sat, (hsv[..., 0] + 28) % 256, hsv[..., 0])
Image.fromarray(hsv.astype(np.uint8), 'HSV').convert('RGB').save('textures/hgb_glass_basecolor_512.png')
print('GLASS hue-shifted, saturated share', round(float(sat.mean()), 3))
