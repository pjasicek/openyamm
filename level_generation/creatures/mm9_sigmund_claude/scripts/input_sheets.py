"""Codex input sheets from the MM9 renders: <prefix>_views (q34, front, left, back, right), head views, skin x4.
Args: <review/mm9 dir> <render prefix> <head prefix> <skin png> <out dir> <suffix>"""
import sys
from PIL import Image
d, pre, hpre, skin, out, suf = sys.argv[1:7]
def crop(im):
    px = im.convert('RGB'); bg = px.getpixel((2, 2))
    from PIL import ImageChops
    diff = ImageChops.difference(px, Image.new('RGB', px.size, bg)).convert('L').point(lambda v: 255 if v > 12 else 0)
    b = diff.getbbox(); m = 16
    return im.crop((max(0, b[0]-m), max(0, b[1]-m), min(im.width, b[2]+m), min(im.height, b[3]+m)))
def row(names, h):
    ims = [crop(Image.open(f'{d}/{n}.png')) for n in names]
    ims = [im.resize((int(im.width * h / im.height), h), Image.LANCZOS) for im in ims]
    W = sum(i.width for i in ims) + 20 * (len(ims) + 1)
    s = Image.new('RGB', (W, h + 40), (107, 107, 107)); x = 20
    for im in ims: s.paste(im, (x, 20)); x += im.width + 20
    return s
row([f'{pre}_{v}' for v in ('q34', 'front', 'left', 'back', 'right')], 900).save(f'{out}/mm9_views_{suf}.png')
row([f'{hpre}_{v}' for v in ('front', 'left', 'q34', 'right', 'back')], 600).save(f'{out}/mm9_head_views_{suf}.png')
sk = Image.open(skin).convert('RGB'); sk.resize((sk.width * 4 if sk.width < 256 else sk.width * 2,) * 2, Image.NEAREST if False else Image.LANCZOS).save(f'{out}/mm9_skin_x4_{suf}.png')
print('SHEETS', suf)
