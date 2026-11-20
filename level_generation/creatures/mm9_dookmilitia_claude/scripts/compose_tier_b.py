#!/usr/bin/env python3
"""Tier B's upper sleeves: MM9 has mail to the elbow, the Codex repaint kept A's cloth below the short mail cap. The sleeve's charts from tier C's paint up to the gold band (same layout, same mail). Project folder."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Z = np.load('work/faces.npz'); UV, MAT, PART, CO = Z['uv'], Z['mat'], Z['part'], Z['co']
S = 2048; im = Image.new('L', (S, S)); d = ImageDraw.Draw(im)
sel = (MAT == 1) & (PART == 3) & (np.abs(CO[:, :, 0]).mean(1) < 0.575)
for t in UV[sel]: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
m = ndimage.binary_dilation(np.asarray(im) > 0, iterations=3); soft = ndimage.gaussian_filter(m.astype(np.float32), 1.0)[..., None]
b = np.asarray(Image.open('textures/dook_torso_b_raw.png').convert('RGB'), np.float32); c = np.asarray(Image.open('textures/dook_torso_c_raw.png').convert('RGB'), np.float32)
Image.fromarray((b * (1 - soft) + c * soft + .5).astype('u1')).save('textures/dook_torso_b_raw.png')
s1 = np.asarray(Image.fromarray((soft[..., 0] * 255).astype('u1')).resize((1024, 1024)), np.float32)[..., None] / 255
nb = np.asarray(Image.open('textures/dook_torso_b_normal.png').convert('RGB'), np.float32); nc = np.asarray(Image.open('textures/dook_torso_c_normal.png').convert('RGB'), np.float32)
Image.fromarray((nb * (1 - s1) + nc * s1 + .5).astype('u1')).save('textures/dook_torso_b_normal.png')
print('TIER B sleeves', int(sel.sum()))
