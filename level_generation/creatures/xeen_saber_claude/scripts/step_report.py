#!/usr/bin/env python3
"""Where the largest per-frame vertex steps happen: per clip the top frames (step cm) with the dominant joint of the
vertex that moved most. Usage: step_report.py <glb> [clip ...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as G
m = G.Model(G.Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
want = sys.argv[2:]
prim = [p for p in m.primitives if p['skinned']]
dom = np.concatenate([p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)] for p in prim])
for clip in m.clips:
    if want and clip not in want: continue
    P = np.stack([np.concatenate([pts for pts, _ in m.skinned_positions(m.world(m.sample(clip, t)))]) for t in m.clip_times(clip)])
    st = np.linalg.norm(np.diff(P, axis=0), axis=-1)
    top = np.argsort(st.max(1))[::-1][:4]
    print(clip, [(int(f), round(float(st[f].max() * 100), 1), names[m.joints[dom[st[f].argmax()]]] if dom[st[f].argmax()] < len(m.joints) else '?') for f in top])
