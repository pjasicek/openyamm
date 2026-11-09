#!/usr/bin/env python3
"""Review sheet review/<id>/compare.png: the native x2 sprite | LOD0 front | three-quarter | side | high view, then
every LOD from the front at a common scale (triangles from work/<id>/stats.json when present) and each at its
approximate switch size. Prints mean colours (all, foliage-like, flower-like pixels, the sprite's rule) of the sprite
and LOD0 front, and each LOD's colour and coverage against the previous level. Usage: sheet.py <id>"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprite_maps import classify, INV

T = 340
BG = (104, 116, 128, 255)


def tile(im, size=T, box=None):
    im = im.convert('RGBA')
    if box is None:
        box = im.getbbox() or (0, 0, im.width, im.height)
    im = im.crop(box)
    s = (size - 12) / max(im.width, im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    bg = Image.new('RGBA', (size, size), BG)
    bg.alpha_composite(im, ((size - im.width) // 2, size - 6 - im.height))
    return bg


def stats(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32)
    m = a[..., 3] > 128
    rgb = a[m][:, :3]
    fl = classify(rgb)
    f = lambda x: x.mean(0).round().astype(int).tolist() if len(x) else None
    return {'all': f(rgb), 'leaf': f(rgb[~fl]), 'flower': f(rgb[fl]), 'cover': int(m.sum()),
            'flower_frac': round(float(fl.mean()), 3) if len(rgb) else 0}


def main(sid):
    e = INV[sid]
    rdir = os.path.join(HERE, 'review', sid, 'renders')
    sprite = Image.open(os.path.join(ROOT, 'assets_dev/engine/decorations_x2', e['files'][0]))
    views = [('front', 'lod0_front'), ('3/4', 'lod0_three_quarter'), ('side', 'lod0_side'), ('high', 'lod0_top')]
    st_path = os.path.join(HERE, 'work', sid, 'stats.json')
    tris = json.load(open(st_path))['triangles'] if os.path.exists(st_path) else None
    lods = sorted(f for f in os.listdir(rdir) if f.endswith('_front.png'))
    W = T * max(5, len(lods) * 2)
    sheet = Image.new('RGBA', (W, 2 * (T + 22) + 4), (255, 255, 255, 255)); d = ImageDraw.Draw(sheet)
    sheet.paste(tile(sprite), (0, 20)); d.text((4, 4), f'{sid} native x2 ({e["hint"]}, h{e["height"]})', fill='black')
    for i, (label, f) in enumerate(views):
        sheet.paste(tile(Image.open(os.path.join(rdir, f + '.png'))), ((i + 1) * T, 20))
        d.text(((i + 1) * T + 4, 4), f'LOD0 {label}', fill='black')
    # LOD row: common scale (same render framing), crop to the union box
    ims = [Image.open(os.path.join(rdir, f)) for f in lods]
    box = None
    for im in ims:
        b = im.getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    y = T + 44
    prev = None
    for i, im in enumerate(ims):
        sheet.paste(tile(im, box=box), (i * T, y))
        s = stats(im)
        label = f'LOD{i}' + (f' {tris[i]} tris' if tris else '')
        if prev:
            dc = np.abs(np.array(s['all']) - np.array(prev['all'])).max()
            label += f'  dcol {dc:.0f} cov {s["cover"] / prev["cover"]:.2f}'
        d.text((i * T + 4, y - 16), label, fill='black')
        prev = s
        # approximate switch size: 120 px tall thumbnails, next to the common-scale tiles
        small = tile(im, size=T, box=box).resize((T // 3, T // 3), Image.BOX).resize((T // 3, T // 3))
        sheet.paste(small, (len(ims) * T + i * (T // 3 + 8), y + T - T // 3))
    out = os.path.join(HERE, 'review', sid, 'compare.png')
    sheet.convert('RGB').save(out)
    ss = stats(sprite); s0 = stats(Image.open(os.path.join(rdir, 'lod0_front.png')))
    print('SHEET', out)
    print('  sprite', {k: ss[k] for k in ('all', 'leaf', 'flower', 'flower_frac')})
    print('  lod0  ', {k: s0[k] for k in ('all', 'leaf', 'flower', 'flower_frac')})
    asp = []
    for v in ('front', 'side'):
        b = Image.open(os.path.join(rdir, f'lod0_{v}.png')).getbbox()
        asp.append((b[2] - b[0]) / (b[3] - b[1]))
    sb = sprite.getbbox()
    print('  aspect w/h: sprite %.2f, LOD0 front %.2f side %.2f' % ((sb[2] - sb[0]) / (sb[3] - sb[1]), *asp))


if __name__ == '__main__':
    for sid in sys.argv[1:]:
        main(sid)
