#!/usr/bin/env python3
"""Preview of a local teeth fix (not applied to any runtime asset): the teeth texels (piece 2 of the creature's UV raster)
with a green/olive hue (60-170 deg, saturation > 0.2) take the median colour of the clean teeth texels scaled to their
own luminance; ramps never touch teeth, so the stain otherwise stays green on the B/C tiers.
Writes work/teeth_ivory_basecolor.png and review/retex/teeth_fix_preview.png (UV crops before / after)."""
import numpy as np
from PIL import Image
r = np.load('../mm8_m600_claude/work/uvraster_UVMap.npz'); teeth = r['piece'] == 2
im = np.asarray(Image.open('../mm8_m600_claude/textures/body_basecolor.png').convert('RGB'), np.float32) / 255
mx, mn = im.max(2), im.min(2); sat = (mx - mn) / (mx + 1e-6)
rgb = im; cmax = rgb.argmax(2); d = mx - mn + 1e-6
h = np.where(cmax == 0, ((rgb[..., 1] - rgb[..., 2]) / d) % 6, np.where(cmax == 1, (rgb[..., 2] - rgb[..., 0]) / d + 2,
                                                                  (rgb[..., 0] - rgb[..., 1]) / d + 4)) * 60
stain = teeth & (h > 60) & (h < 170) & (sat > .2)
clean = np.median(im[teeth & ~stain], 0); W = np.array([.2126, .7152, .0722])
lum = im @ W; out = im.copy()
out[stain] = np.clip(clean[None] * (lum[stain] / (clean @ W))[:, None], 0, 1)
Image.fromarray((out * 255 + .5).astype(np.uint8)).save('work/teeth_ivory_basecolor.png')
ys, xs = np.where(stain); cy, cx = int(np.median(ys)), int(np.median(xs))
box = (max(cx - 160, 0), max(cy - 160, 0), max(cx - 160, 0) + 320, max(cy - 160, 0) + 320)
a = Image.fromarray((im * 255).astype(np.uint8)).crop(box).resize((480, 480), Image.NEAREST)
b = Image.fromarray((out * 255).astype(np.uint8)).crop(box).resize((480, 480), Image.NEAREST)
sheet = Image.new('RGB', (960, 480)); sheet.paste(a, (0, 0)); sheet.paste(b, (480, 0)); sheet.save('review/retex/teeth_fix_preview.png')
print('stained teeth texels', int(stain.sum()), 'of', int(teeth.sum()), 'clean ivory', np.round(clean, 3))
