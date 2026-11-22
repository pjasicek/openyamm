#!/usr/bin/env python3
"""Record the selected HD masters' sha256 in creature_3d_progress.json (run under creature_workspace.py run)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
st = json.load(open(ROOT / 'creature_3d_progress.json'))
st['references_hd'] = {f: {'path': f'references_hd/{f}.png',
                           'sha256': hashlib.sha256((ROOT / f'references_hd/{f}.png').read_bytes()).hexdigest()}
                       for f in ('00_three_quarter', '01_front', '02_back', '03_left', '04_right')}
st['references_hd_gate'] = ('2026-11-20 Claude: identity, palette, pose and proportions agree with the native frames '
                            '(review/masters_gate.png); five claws per front foot, four per hind foot in every view '
                            '(the 74 px sprite shows 3-5 claw tips per foot); the right profile shows the tail a little '
                            'shorter than the left (retexture view only, geometry from 00)')
st['stage'] = 'masters accepted'
json.dump(st, open(ROOT / 'creature_3d_progress.json', 'w'), indent=1)
print('recorded')
