#!/usr/bin/env python3
"""Measure tree stands of a built X1 scene the way OUTDOOR_REBUILD_PROCEDURE.md "Tree spacing (measured)" does:
nearest tree (median / 10th pct / least, cells), density per cell of the ground within 2 cells of a tree, Clark-Evans R,
trees within 2 cells (median / 90th), unlike nearest pairs (observed / random), rim (outer 3 cells) / core nearest.
Usage: tree_spread.py <scene.yml>"""
import math, re, sys
from collections import Counter
import numpy as np

STANDS = {
    'dead forest': (['tree41', 'tree42'], [[19, 74], [50, 74], [50, 109], [19, 109]]),
    'meadow west': (['7tree13', '7tree16'], [[19, 37], [41, 37], [41, 74], [19, 74]]),
    'hills': (['7tree22', '7tree16'], [[19, 19], [103, 19], [103, 36], [19, 36]]),
    'marsh': (['swptree1', 'swptree2'], [[66, 78], [100, 78], [100, 100], [66, 100]]),
}

def read(path):
    text = open(path, encoding='latin-1').read()
    ents = text[text.index('\nentities:'):text.index('\nspawns:')]
    out = []
    for m in re.finditer(r'name: (\S+)\n(?:.*\n){0,3}?\s+position:\n\s+x: (-?\d+)\n\s+y: (-?\d+)', ents):
        out.append((m.group(1).lower(), int(m.group(2)) / 512.0 + 64, 64 - int(m.group(3)) / 512.0))
    return out

def inside(p, poly):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c

def edge(p, poly):
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy))
    return best

def measure(trees, poly):
    pts = np.array([(x, y) for _, x, y in trees])
    names = [n for n, _, _ in trees]
    n = len(pts)
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, 1e9)
    nn = d.min(axis=1)
    ni = d.argmin(axis=1)
    cells = set()
    for x, y in pts:
        for gx in range(int(x) - 2, int(x) + 3):
            for gy in range(int(y) - 2, int(y) + 3):
                if math.hypot(gx + 0.5 - x, gy + 0.5 - y) <= 2:
                    cells.add((gx, gy))
    dens = n / len(cells)
    R = nn.mean() / (0.5 / math.sqrt(dens))
    within = (d <= 2).sum(axis=1)
    unlike = np.mean([names[i] != names[ni[i]] for i in range(n)])
    c = Counter(names)
    rnd = 1 - sum((v / n) ** 2 for v in c.values())
    rim = [nn[i] for i in range(n) if edge(pts[i], poly) < 3]
    core = [nn[i] for i in range(n) if edge(pts[i], poly) >= 3]
    return ('%3d trees  nearest %.2f / %.2f / %.2f  per cell %.3f  R %.2f  within2 %d / %d  unlike %.2f / %.2f  rim/core %.2f / %.2f'
            % (n, np.median(nn), np.percentile(nn, 10), nn.min(), dens, R, np.median(within), np.percentile(within, 90),
               unlike, rnd, np.median(rim) if rim else 0, np.median(core) if core else 0))

if __name__ == '__main__':
    ents = read(sys.argv[1])
    for name, (kinds, poly) in STANDS.items():
        trees = [e for e in ents if e[0] in kinds and inside((e[1], e[2]), poly)]
        if len(trees) > 3:
            print('%-12s %s' % (name, measure(trees, poly)))
