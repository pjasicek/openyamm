#!/usr/bin/env python3
"""Write a solved fist (fist_solve.py output) into scripts/finger_poses.json as pose <name> (per-finger angles,
spread 0). Usage: set_pose.py <solve json> <side Left|Right> <pose name>"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
a = json.load(open(sys.argv[1]))[sys.argv[2]]['angles']; name = sys.argv[3]
p = HERE / 'scripts/finger_poses.json'; cfg = json.load(open(p))
cfg['poses'][name] = {'fingers': [0, 0, 0],
                      'per_finger': {f: a[k * 3:k * 3 + 3] for k, f in enumerate(('Index', 'Middle', 'Ring', 'Pinky'))},
                      'thumb': a[12:16], '_solved': f'followup/fist_solve.py ({sys.argv[1]}, {sys.argv[2]})'}
json.dump(cfg, open(p, 'w'), indent=1); print('POSE', name, cfg['poses'][name])
