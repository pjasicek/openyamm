#!/usr/bin/env python3
"""Cuts a returned sheet into cells and writes 126x146 opaque RGBA portraits.

Usage: extract.py RAW.png OUTDIR ID [ID ...] [--grid COLSxROWS] [--crop ID=dx,dy,scale ...]
Cell boundaries come from the white gutters actually present in the sheet (rows/columns that are nearly all
bright and low-saturation); the nominal grid is only a fallback. Each cell is cropped to the 126:146 aspect at
the full cell height (or full width when the cell is narrower), centred, median-smoothed and resampled with Lanczos."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

TW, TH = 126, 146


def runs(mask):
    out, start = [], None
    for i, m in enumerate(mask):
        if not m and start is None:
            start = i
        if m and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def find_bands(white, axis, count, length):
    frac = white.mean(axis=axis)
    bands = [r for r in runs(frac > 0.85) if r[1] - r[0] > length * 0.08]
    if len(bands) == count:
        return bands, True
    step = length / count
    return [(int(i * step), int((i + 1) * step)) for i in range(count)], False


def cells(img, cols, rows):
    a = np.asarray(img.convert('RGB')).astype(np.int32)
    white = (a.min(axis=2) > 225) & ((a.max(axis=2) - a.min(axis=2)) < 25)
    xs, okx = find_bands(white, 0, cols, a.shape[1])
    ys, oky = find_bands(white, 1, rows, a.shape[0])
    return xs, ys, okx and oky


def trim_white(cell):
    """Removes leftover white border lines inside a cell box."""
    a = np.asarray(cell.convert('RGB')).astype(np.int32)
    white = (a.min(axis=2) > 225) & ((a.max(axis=2) - a.min(axis=2)) < 25)
    l, r, t, b = 0, a.shape[1], 0, a.shape[0]
    while l < r - 1 and white[:, l].mean() > 0.5: l += 1
    while r > l + 1 and white[:, r - 1].mean() > 0.5: r -= 1
    while t < b - 1 and white[t, :].mean() > 0.5: t += 1
    while b > t + 1 and white[b - 1, :].mean() > 0.5: b -= 1
    m = 3  # anti-aliased gutter edge
    return cell.crop((l + m, t + m, r - m, b - m))


def portrait(cell, dx=0.0, dy=0.0, scale=1.0):
    w, h = cell.size
    ch = h * scale
    cw = ch * TW / TH
    if cw > w * scale:
        cw = w * scale
        ch = cw * TH / TW
    cx = w / 2 + dx * w
    cy = h / 2 + dy * h
    x0 = min(max(cx - cw / 2, 0), w - cw)
    y0 = min(max(cy - ch / 2, 0), h - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    # A 5 px median at sheet resolution (about 2 px at the target) smooths skin and cloth texture towards the
    # waxy MM7 renders; a slight saturation lift matches their colour.
    smooth = cell.convert('RGB').filter(ImageFilter.MedianFilter(5))
    small = smooth.resize((TW, TH), Image.LANCZOS, box=box)
    return ImageEnhance.Color(small).enhance(1.1).convert('RGBA')


def main():
    args = sys.argv[1:]
    grid, crops, rest = (3, 4), {}, []
    i = 0
    while i < len(args):
        if args[i] == '--grid':
            c, r = args[i + 1].split('x'); grid = (int(c), int(r)); i += 2
        elif args[i] == '--crop':
            k, v = args[i + 1].split('='); crops[int(k)] = tuple(float(x) for x in v.split(',')); i += 2
        else:
            rest.append(args[i]); i += 1
    raw, outdir, ids = Path(rest[0]), Path(rest[1]), [int(x) for x in rest[2:]]
    img = Image.open(raw)
    xs, ys, ok = cells(img, *grid)
    print(raw.name, img.size, 'gutters found' if ok else 'NOMINAL GRID', 'xs', xs, 'ys', ys)
    outdir.mkdir(parents=True, exist_ok=True)
    for n, npc in enumerate(ids):
        if npc == 0:
            continue
        x, y = xs[n % grid[0]], ys[n // grid[0]]
        cell = trim_white(img.crop((x[0], y[0], x[1], y[1])))
        p = portrait(cell, *crops.get(npc, (0.0, 0.0, 1.0)))
        p.save(outdir / f'npc{10000 + npc}.png')
        print(npc, cell.size)


main()
