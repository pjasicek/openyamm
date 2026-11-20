#!/usr/bin/env python3
"""Identical-camera review-viewer shots of every tier, installed (before) and texture pass (tp), and the sheet per
target world: claude_shared/texpass_viewer_shots.py with texpass.json "shots" (name:clip:time:view:focus[:cam:target]).
Writes review/shots/{before,tp}/<tier>_<name>.png and review/texpass_sheet_<tierprefix>.png."""
import subprocess
import sys

import tp

TOOL = tp.CREATURES / 'claude_shared' / 'texpass_viewer_shots.py'
specs = tp.CFG['shots']
names = ','.join(s.split(':')[0] for s in specs)
tiers = list(tp.CFG['tiers'])
for tag in ('before', 'tp'):
    out = tp.HERE / 'review' / 'shots' / tag
    out.mkdir(parents=True, exist_ok=True)
    for tier in tiers:
        subprocess.run([sys.executable, str(TOOL), 'shots', str(tp.HERE), str(out), f'{tier}_{tag}', *specs], check=True)
        for s in specs:            # <tier>_<tag>_<name>.png -> <tier>_<name>.png
            name = s.split(':')[0]
            (out / f'{tier}_{tag}_{name}.png').replace(out / f'{tier}_{name}.png')
groups = {}
for tier in tiers:
    groups.setdefault(tier.rsplit('_', 1)[0], []).append(tier)
for prefix, group in groups.items():
    subprocess.run([sys.executable, str(TOOL), 'sheet', str(tp.HERE / 'review' / f'texpass_sheet_{prefix}.png'),
                    str(tp.HERE / 'review' / 'shots' / 'before'), str(tp.HERE / 'review' / 'shots' / 'tp'),
                    ','.join(group), names], check=True)
