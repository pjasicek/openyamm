#!/usr/bin/env python3
"""v2 review sheets (after export_tree_v2.py), in review_v2/:
 - tree01_v2_compare.png: native sprite | LOD0 eye level | LOD0 three-quarter (Eevee, sun + sky), with mean colour and
   luminance 5/50/95 percentiles of the sprite and of the eye-level render;
 - tree01_v2_occlusion.png: the COLOR_0 canopy occlusion alone (eye level, back, three-quarter)."""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work_v2'); R = os.path.join(HERE, 'review_v2')
os.makedirs(R, exist_ok=True)
BLEND = os.path.join(W, 'tree.blend')


def render(prefix, views, mode='lit'):
    subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(HERE, 'scripts', 'render_review_v2.py'),
                    '--', prefix, BLEND, views, mode], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stats(im):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128; l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(1).tolist(), np.percentile(l[m], [5, 50, 95]).round(1).tolist()


def crop(im, width):
    im = im.crop(im.getbbox())
    return im.resize((width, int(width * im.height / im.width)), Image.LANCZOS)


render(os.path.join(W, 'rv'), 'eye,three_quarter')
render(os.path.join(W, 'rvo'), 'eye,back,three_quarter', 'occlusion')
sprite = Image.open(os.path.join(HERE, '..', '..', 'mm6_new_sorpigal', 'enhanced', '6tree01.png')).convert('RGBA')
eye = Image.open(os.path.join(W, 'rv_Tree_eye.png')).convert('RGBA')
tq = Image.open(os.path.join(W, 'rv_Tree_three_quarter.png')).convert('RGBA')
panels = [crop(sprite, 420), crop(eye, 420), crop(tq, 420)]
h = max(p.height for p in panels) + 40
sheet = Image.new('RGBA', (1300, h), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for k, (p, label) in enumerate(zip(panels, ('native 6tree01 (upscaled)', 'v2 LOD0 eye level', 'v2 LOD0 three-quarter'))):
    sheet.alpha_composite(p, (k * 440, h - p.height)); d.text((k * 440 + 4, 4), label, fill=(0, 0, 0, 255))
d.text((4, 18), f'sprite mean/lum5-50-95 {stats(sprite)}   v2 eye {stats(eye)}', fill=(0, 0, 0, 255))
sheet.convert('RGB').save(os.path.join(R, 'tree01_v2_compare.png'))
occ = [Image.open(os.path.join(W, f'rvo_Tree_{v}.png')).convert('RGBA') for v in ('eye', 'back', 'three_quarter')]
sheet = Image.new('RGBA', (sum(o.width for o in occ), occ[0].height), (90, 60, 120, 255))
x = 0
for o in occ:
    sheet.alpha_composite(o, (x, 0)); x += o.width
sheet.convert('RGB').save(os.path.join(R, 'tree01_v2_occlusion.png'))
print('REVIEW sprite', stats(sprite), 'v2', stats(eye))
