#!/usr/bin/env python3
"""Overlay of a statue decoration (grey) and its ice creature copy at rest (orange) from front, side and top:
work/<statue>_ice/overlay.png. Usage: statue_overlay.py <statue>"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import prop_parts as pp  # noqa: E402
import ice_statues as ice  # noqa: E402


def main():
    statue = sys.argv[1]
    doc, binary = pp.read_glb(pp.HERE / 'work' / f'{statue}_ice' / f'mm9_deco_{statue}_anim.glb')
    raw = pp.Raw.__new__(pp.Raw)
    raw.doc, raw.bin, raw.pose, raw.tracks = doc, binary, (None, 0.0), {}
    raw.parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
    creature = ice.posed_points(raw, doc, binary, None, 0.0)
    sdoc, sbin = pp.read_glb(pp.SOURCE / f'mm9_deco_{statue}.glb')
    stat = np.concatenate([pp.array(sdoc, sbin, p['attributes']['POSITION']) for p in sdoc['meshes'][0]['primitives']])
    every = np.concatenate([creature, stat])
    lo, hi = every.min(0), every.max(0)
    size = 320
    k = 0.9 * size / (hi - lo).max()
    img = Image.new('RGB', (size * 3, size), 'white')
    draw = ImageDraw.Draw(img)
    for col, (i, j, flip) in enumerate([(0, 1, 1), (2, 1, 1), (0, 2, -1)]):
        for pts, colour in ((stat, (120, 120, 120)), (creature, (220, 120, 40))):
            for p in pts[::max(1, len(pts) // 4000)]:
                x = col * size + size / 2 + (p[i] - (lo[i] + hi[i]) / 2) * k
                y = size / 2 - flip * (p[j] - (lo[j] + hi[j]) / 2) * k
                draw.point((x, y), fill=colour)
    img.save(pp.HERE / 'work' / f'{statue}_ice' / 'overlay.png')


if __name__ == '__main__':
    main()
