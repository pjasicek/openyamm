#!/usr/bin/env python3
"""Per-tooth shortening from parts_gate.py: every rebuilt tooth that enters the body shrinks by its depth plus
0.5 mm (scales accumulate in work/part_scale.json; build_parts.py applies them). Usage: clearance.py"""
import json
from pathlib import Path
W = Path(__file__).resolve().parents[1] / 'work'
gate = json.loads((W / 'parts_gate.json').read_text())['per_piece_mm']
teeth = json.loads((W / 'rebuild.json').read_text())['teeth']
path = W / 'part_scale.json'; scale = json.loads(path.read_text()) if path.exists() else {}
for k, depth in gate.items():
    if int(k) >= len(teeth):
        continue
    L = teeth[int(k)]['length']
    scale[k] = round(scale.get(k, 1.0) * max(.5, (L + depth / 1000 - .0005) / L), 4)
path.write_text(json.dumps(scale, indent=1) + '\n'); print('SCALE', scale)
