#!/usr/bin/env python3
"""Installed vs reduced viewer shots (review/shots_<tier>_<rev>/, shots_queue.sh) per tier -> review/sheet_viewer_<t>.png.
Usage: viewer_sheets.py <rev, e.g. r71>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1] / 'review'; rev = sys.argv[1]
shots = ['st_front', 'st_q', 'st_back', 'walk_q', 'run_l', 'atk_q', 'death_q', 'hands_q', 'arms_atk']
for t in 'abc':
    W, Hh = 690, 508
    s = Image.new('RGB', (W * 3, (Hh * 2 + 20) * 3), (20, 20, 20)); d = ImageDraw.Draw(s)
    for n, sh in enumerate(shots):
        r, c = divmod(n, 3)
        for j, lab in enumerate(['r100', rev]):
            im = Image.open(H / f'shots_{t}_{lab}' / f'{sh}.png').convert('RGB')
            w, h = im.size; im = im.crop((int(w * .2), 0, int(w * .8), h)).resize((W, Hh))
            s.paste(im, (c * W, r * (2 * Hh + 20) + 20 + j * Hh))
        d.text((c * W + 4, r * (2 * Hh + 20) + 4), f'{t.upper()} {sh}: installed above, reduced {rev} below', fill=(240, 220, 120))
    s.save(H / f'sheet_viewer_{t}.png')
