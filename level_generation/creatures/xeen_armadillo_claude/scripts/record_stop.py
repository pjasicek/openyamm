#!/usr/bin/env python3
"""Record the stop point in creature_3d_progress.json (run under creature_workspace.py run)."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
st = json.load(open(ROOT / 'creature_3d_progress.json'))
st['stage'] = 'rigged, UV layout laid (ungated, xatlas fallback), clips not run; stopped by the lane session 2026-11-20'
st['next_action'] = {'owner': 'next lane S creature agent',
                     'step': 'gate the UV layout with texture_quality.py (atlas >= 65 %); redo uv_dillo.py if it '
                             'misses; then retexture_v1 (10 credits) and anim_dillo.py; see README "Resume here"'}
st['credits_spent'] = 10
json.dump(st, open(ROOT / 'creature_3d_progress.json', 'w'), indent=1)
print('recorded', {k: v.get('consumed_credits') for k, v in st['meshy']['jobs'].items()})
