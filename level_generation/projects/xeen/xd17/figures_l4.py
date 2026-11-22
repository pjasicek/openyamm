#!/usr/bin/env python3
"""XD-17: the town figures (TOWN_FEEL's definitions, render_xd17.figures) measured on the built layout
(places_l2.py), lanes as the centre lines of their rectangles. Writes ../mockups/figures_l4.json."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
from pathlib import Path

import places_l2 as L
import render_xd17 as R


def centre_lines():
    out = {}
    for k, rects in list(L.LANES.items()) + [('square', L.SQUARE)]:
        for n, (x0, y0, x1, y1) in enumerate(rects):
            if x1 - x0 >= y1 - y0:
                out[f'{k}#{n}'] = [(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)]
            else:
                out[f'{k}#{n}'] = [((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)]
    return out


L.LANES = centre_lines()
L.CAMERAS = L.TOUR
L.PASSAGE = L.PASSAGE[:2] and [((L.PASSAGE[0][0] + L.PASSAGE[1][0]) / 2, (L.PASSAGE[0][1] + L.PASSAGE[1][1]) / 2),
                               (-6144, 4096), ((L.PASSAGE[3][0] + L.PASSAGE[4][0]) / 2, (L.PASSAGE[3][1] + L.PASSAGE[4][1]) / 2)]
R.P = L
f = R.figures()
pathlib.Path(_REPO_ROOT, 'output/studio_cal/xd17').joinpath('mockups/figures_l4.json').write_text(json.dumps(f, indent=1))
print(json.dumps(f, indent=1))
