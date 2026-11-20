#!/usr/bin/env python3
"""Quick iteration sheet (after build_tree.py): sprite | LOD0 eye | three-quarter | side, review/<id>/quick.png,
with mean colour and luminance percentiles. Usage: quick.py <id>"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load(); W = spec['work']


def stats(im):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128; l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(0).astype(int).tolist(), np.percentile(l[m], [5, 50, 95]).round(0).astype(int).tolist()


env = dict(os.environ, TREE_ONLY='Tree')
subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(common.TREES, 'scripts', 'render_review.py'),
                '--', spec['id'], os.path.join(W, 'qk'), os.path.join(W, 'tree.blend'), 'eye,three_quarter,side'],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(common.TREES, 'scripts', 'render_review.py'),
                '--', spec['id'], os.path.join(W, 'qkn'), os.path.join(W, 'tree.blend'), 'eye', 'lit', '540', 'noshadow'],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
sprite = Image.open(spec['sprite_path']).convert('RGBA')
print('QUICK noshadow eye', stats(Image.open(os.path.join(W, 'qkn_Tree_eye.png')).convert('RGBA')))
ims = [sprite] + [Image.open(os.path.join(W, f'qk_Tree_{v}.png')).convert('RGBA') for v in ('eye', 'three_quarter', 'side')]
ims = [i.crop(i.getbbox()) for i in ims]
ims = [i.resize((int(i.width * 480 / i.height), 480), Image.LANCZOS) for i in ims]
w = sum(max(i.width, 300) + 10 for i in ims)
sheet = Image.new('RGBA', (w, 520), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet); x = 0
for i, label in zip(ims, ('sprite', 'eye', 'three-quarter', 'side')):
    sheet.alpha_composite(i, (x, 40)); d.text((x + 2, 2), f'{label} {stats(i)}', fill=(0, 0, 0, 255)); x += max(i.width, 300) + 10
sheet.convert('RGB').save(os.path.join(spec['review'], 'quick.png'))
print('QUICK', stats(ims[0]), stats(ims[1]))
