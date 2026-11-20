#!/usr/bin/env python3
"""har: the knee joints on the straight hip-ankle line (x only; after leg_rings.py, which keeps the ring's y): the
baggy trousers' ring centre sat 4-5 cm inside that line. Edits work/joints_final.json. Args: none"""
import json
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'work' / 'joints_final.json'
d = json.loads(p.read_text()); J = d['joints']
for s in 'LR':
    th, ca, ft = J[f'{s}_Thigh'], J[f'{s}_Calf'], J[f'{s}_Foot']
    t = (th[2] - ca[2]) / (th[2] - ft[2]); x = th[0] + (ft[0] - th[0]) * t
    print('KNEE', s, 'x', ca[0], '->', round(x, 4)); ca[0] = round(x, 5)
d.setdefault('report', {})['knee_x'] = 'straight hip-ankle line (har)'
p.write_text(json.dumps(d, indent=1))
