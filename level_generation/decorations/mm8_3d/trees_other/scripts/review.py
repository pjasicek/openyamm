#!/usr/bin/env python3
"""Review sheets for one species (after export_tree.py), in review/<id>/:
 - compare.png: native x2 sprite | LOD0 front (eye level) | three-quarter | side (Eevee, sun + sky), with mean
   colour and luminance 5/50/95 percentiles of the sprite and of the front render;
 - occlusion.png: the COLOR_0 canopy occlusion alone (eye level, back, three-quarter). Usage: review.py <id>"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load()
HERE = common.TREES
W = spec['work']; R = spec['review']
BLEND = os.path.join(W, 'tree.blend')


def render(prefix, views, mode='lit'):
    subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(HERE, 'scripts', 'render_review.py'),
                    '--', spec['id'], prefix, BLEND, views, mode], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stats(im):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128; l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(1).tolist(), np.percentile(l[m], [5, 50, 95]).round(1).tolist()


def crop(im, width):
    im = im.crop(im.getbbox())
    return im.resize((width, int(width * im.height / im.width)), Image.LANCZOS)


render(os.path.join(W, 'rv'), 'eye,three_quarter,side')
render(os.path.join(W, 'rvo'), 'eye,back,three_quarter', 'occlusion')
sprite = Image.open(spec['sprite_path']).convert('RGBA')
eye = Image.open(os.path.join(W, 'rv_Tree_eye.png')).convert('RGBA')
tq = Image.open(os.path.join(W, 'rv_Tree_three_quarter.png')).convert('RGBA')
side = Image.open(os.path.join(W, 'rv_Tree_side.png')).convert('RGBA')
# common scale: the sprite and the renders at the same pixels per tree height
ref = sprite.crop(sprite.getbbox())
scale = 420 / max(ref.width, ref.height)


def fit(im):
    im = im.crop(im.getbbox())
    k = ref.height * scale / im.height if im is not ref else scale
    return im.resize((max(int(im.width * k), 1), max(int(im.height * k), 1)), Image.LANCZOS)


panels = [fit(ref), fit(eye), fit(tq), fit(side)]
step = max(p.width for p in panels) + 20
h = max(p.height for p in panels) + 40
sheet = Image.new('RGBA', (step * 4, h), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for k, (p, label) in enumerate(zip(panels, (f"native {spec['sprite']} (x2)", 'LOD0 front', 'LOD0 three-quarter',
                                            'LOD0 side'))):
    sheet.alpha_composite(p, (k * step + (step - p.width) // 2, h - p.height))
    d.text((k * step + 4, 4), label, fill=(0, 0, 0, 255))
d.text((4, 18), f'sprite mean/lum5-50-95 {stats(sprite)}   eye {stats(eye)}', fill=(0, 0, 0, 255))
sheet.convert('RGB').save(os.path.join(R, 'compare.png'))
occ = [Image.open(os.path.join(W, f'rvo_Tree_{v}.png')).convert('RGBA') for v in ('eye', 'back', 'three_quarter')]
sheet = Image.new('RGBA', (sum(o.width for o in occ), occ[0].height), (90, 60, 120, 255))
x = 0
for o in occ:
    sheet.alpha_composite(o, (x, 0)); x += o.width
sheet.convert('RGB').save(os.path.join(R, 'occlusion.png'))
print('REVIEW sprite', stats(sprite), 'eye', stats(eye))
