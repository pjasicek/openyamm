#!/usr/bin/env python3
"""Floor check of an exported GLB with claude_shared/floor/floor_audit.ModelFloor (no Blender): lowest visible point
(cm, model space, y = 0 is the floor) per clip. Writes review/floor_check.json. Usage: floor_check.py export/hes_drone.glb"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared' / 'floor'))
import floor_audit
mf = floor_audit.ModelFloor(Path(sys.argv[1]))
out = {}
for clip in ['Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Fidget', 'Death', 'Dead']:
    lows = mf.lows(clip)
    out[clip] = {'min_cm': round(min(lows) * 100, 2), 'max_cm': round(max(lows) * 100, 2), 'end_cm': round(lows[-1] * 100, 2)}
living = min(out[c]['min_cm'] for c in ['Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Fidget'])
out['living_min_cm'] = living
json.dump(out, open(ROOT / 'review' / 'floor_check.json', 'w'), indent=1)
print(json.dumps(out))
