#!/usr/bin/env python3
"""Review sheets for the crown (after export_tree.py), in review/<id>/ (adapted from the MM8 batch's review.py):
 - compare.png: the drawn envelope silhouette | LOD0 front (eye level) | three-quarter | side (Eevee, sun + sky),
   with the crown's mean colour and luminance 5/50/95 percentiles (leaf pixels: above the stub);
 - context.png: with the trunk stand-in and ground (render_review.py): the party on the green 4,000 and 6,000 units
   out, at the trunk's foot looking up, below the crown's rim (`under`), and from 14,000 units (every LOD);
 - occlusion.png: the COLOR_0 occlusion alone (eye level, back, three-quarter). Usage: review.py <id>"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load()
HERE = common.TREES
W = spec['work']; R = spec['review']
BLEND = os.path.join(W, 'tree_export.blend')


def render(prefix, views, mode='lit', res=540):
    subprocess.run([common.BLENDER, '--background', '--python', os.path.join(HERE, 'scripts', 'render_review.py'),
                    '--', spec['id'], prefix, BLEND, views, mode, str(res)], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def stats(im, leaves_only=False):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128
    if leaves_only:                            # rows above the stub's top (the lowest ~22 % of the frame)
        m[int(m.shape[0] * 0.78):] = False
    l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(1).tolist(), np.percentile(l[m], [5, 50, 95]).round(1).tolist()


def crop(im, width):
    im = im.crop(im.getbbox())
    return im.resize((width, int(width * im.height / im.width)), Image.LANCZOS)


render(os.path.join(W, 'rv'), 'eye,three_quarter,side')
render(os.path.join(W, 'rvo'), 'eye,back,three_quarter', 'occlusion')
render(os.path.join(W, 'rvc'), 'green4k,green6k,foot,under,far', 'lit', 432)
sil = Image.open(spec['sprite_path']).convert('RGBA')
eye = Image.open(os.path.join(W, 'rv_Tree_eye.png')).convert('RGBA')
tq = Image.open(os.path.join(W, 'rv_Tree_three_quarter.png')).convert('RGBA')
side = Image.open(os.path.join(W, 'rv_Tree_side.png')).convert('RGBA')
panels = [crop(sil, 420), crop(eye, 420), crop(tq, 420), crop(side, 420)]
h = max(p.height for p in panels) + 40
sheet = Image.new('RGBA', (1760, h), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for k, (p, label) in enumerate(zip(panels, ('drawn envelope (revolved)', 'LOD0 front (eye level)', 'LOD0 three-quarter',
                                            'LOD0 side'))):
    sheet.alpha_composite(p, (k * 440, h - p.height)); d.text((k * 440 + 4, 4), label, fill=(0, 0, 0, 255))
crown_stats = stats(eye, leaves_only=True)
d.text((4, 18), f"crown mean / lum5-50-95 {crown_stats}   target sRGB {spec['leaves']['target_srgb']}", fill=(0, 0, 0, 255))
sheet.convert('RGB').save(os.path.join(R, 'compare.png'))
occ = [Image.open(os.path.join(W, f'rvo_Tree_{v}.png')).convert('RGBA') for v in ('eye', 'back', 'three_quarter')]
sheet = Image.new('RGBA', (sum(o.width for o in occ), occ[0].height), (90, 60, 120, 255))
x = 0
for o in occ:
    sheet.alpha_composite(o, (x, 0)); x += o.width
sheet.convert('RGB').save(os.path.join(R, 'occlusion.png'))
ctx = [('green4k', 'Tree', 'eye level on the green, 4,000 units'), ('green6k', 'Tree', 'eye level, 6,000 units'),
       ('foot', 'Tree', 'at the trunk foot, looking up 62 deg'), ('far', 'Tree', 'far, 14,000 units: LOD0'),
       ('far', 'Tree_LOD1', 'far: LOD1'), ('far', 'Tree_LOD2', 'far: LOD2'), ('far', 'Tree_LOD3', 'far: LOD3 impostor')]
tiles = []
for view, lod, label in ctx:
    im = Image.open(os.path.join(W, f'rvc_{lod}_{view}.png')).convert('RGB')
    tiles.append((im, label))
under = Image.open(os.path.join(W, 'rvc_Tree_under.png')).convert('RGBA')
bg = Image.new('RGBA', under.size, (150, 160, 175, 255)); bg.alpha_composite(under)
under = bg.convert('RGB').resize((int(under.width * 432 / under.height), 432))
tiles.insert(3, (under, 'below the crown rim (crown alone)'))
tw = max(t.width for t, _ in tiles); th = 432
cols = 2
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * (th + 18)), (150, 160, 175)); d = ImageDraw.Draw(sheet)
for k, (im, label) in enumerate(tiles):
    x, y = (k % cols) * tw, (k // cols) * (th + 18)
    sheet.paste(im, (x, y + 18)); d.text((x + 6, y + 3), label, fill=(0, 0, 0))
sheet.save(os.path.join(R, 'context.png'))
print('REVIEW crown', crown_stats, 'target', spec['leaves']['target_srgb'])
