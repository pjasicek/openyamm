#!/usr/bin/env python3
"""Handedness check: on a figure facing +Z in right-handed glTF (Y up), its anatomical right is at -X. Args: <glb>..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
for p in sys.argv[1:]:
    m = Model(Glb(p)); names = [n.get('name') for n in m.glb.json['nodes']]
    w = m.world({})
    h = {s: w[names.index(f'Bip01 {s} Hand')][:3, 3] for s in 'LR'}
    print(p.split('/')[-1], f"R Hand x {h['R'][0]:+.3f}, L Hand x {h['L'][0]:+.3f}; bone named R on the anatomical {'RIGHT' if h['R'][0] < h['L'][0] else 'LEFT'}")
