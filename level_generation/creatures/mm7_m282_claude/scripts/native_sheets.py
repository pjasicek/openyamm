#!/usr/bin/env python3
"""Contact sheets of ORIGINAL native frames (palette-decoded, nearest-neighbour 3x, magenta background) as Codex inputs:
references_hd/native_views.png, native_palettes.png, native_actions.png."""
from pathlib import Path
import numpy as np
from PIL import Image
P = Path(__file__).resolve().parents[1]
NV = P / 'references/native_variants'
OUT = P / 'references_hd'


def crop(name, pal):
    im = Image.open(NV / f'{name}_{pal}.png')
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a)
    return im.crop((xs.min() - 4, ys.min() - 4, xs.max() + 5, ys.max() + 5))


def row(ims, pad=12, base_h=None):
    h = base_h or max(i.height for i in ims)
    w = sum(i.width for i in ims) + pad * (len(ims) + 1)
    c = Image.new('RGBA', (w, h + 2 * pad), (255, 0, 255, 255))
    x = pad
    for i in ims:
        c.alpha_composite(i, (x, pad + h - i.height)); x += i.width + pad
    return c


def stack(rows):
    w = max(r.width for r in rows)
    c = Image.new('RGBA', (w, sum(r.height for r in rows)), (255, 0, 255, 255))
    y = 0
    for r in rows:
        c.paste(r, (0, y)); y += r.height
    return c


def save(im, name, k=3):
    im.resize((im.width * k, im.height * k), Image.NEAREST).convert('RGB').save(OUT / name)
    print(name, im.width * k, im.height * k)


save(row([crop(f'm282sa{v}', 284) for v in range(5)]), 'native_views.png')
save(stack([row([crop('m282sa0', p), crop('m282sa1', p)]) for p in (283, 284, 285)]), 'native_palettes.png', 2)
save(stack([row([crop(f, 284) for f in ('m282wa2', 'm282wd2', 'm282sa2')]),
            row([crop(f, 284) for f in ('m282ab0', 'm282ad2', 'm282ae2', 'm282na0')])]), 'native_actions.png', 2)
