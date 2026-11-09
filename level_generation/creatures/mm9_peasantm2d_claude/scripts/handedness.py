#!/usr/bin/env python3
"""Handedness check: on a figure facing +Z in right-handed glTF (Y up), its anatomical right is at -X. Prints where MM9's bone names
and the weapon sit in the raw ABC conversion, the corrected source and the runtime GLB, and which hand holds the scimitar. Args: <glb>..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
for p in sys.argv[1:]:
    m = Model(Glb(p)); names = [n.get('name') for n in m.glb.json['nodes']]
    w = m.world({})
    h = {s: w[names.index(f'Bip01 {s} Hand')][:3, 3] for s in 'LR'}
    foot = w[names.index('Bip01 R Foot')][:3, 3]; toe = w[names.index('Bip01 R Toe0')][:3, 3]
    # the weapon bone's nearest hand and its chain of parents
    node = m.glb.json['nodes']; par = {c: i for i, n in enumerate(node) for c in n.get('children', [])}
    print(p.split('/')[-1], f"facing {'+Z' if (toe - foot)[2] > 0 else '-Z'}; R Hand x {h['R'][0]:+.3f}, L Hand x {h['L'][0]:+.3f}; anatomical side of the bone named R: {'RIGHT' if h['R'][0] < h['L'][0] else 'LEFT'}")
