"""Fingertip positions in the hand frame for clip times: along (finger dir), palm-side (+ = toward palm), and the
tip's distance to the wrist, per finger. Hand frame from rest: Y = wrist->Middle1, Z = palm normal (graft json)."""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
g = gp.Glb(sys.argv[1]); m = gp.Model(g); names = [n.get('name') for n in g.json['nodes']]
fr = json.load(open(Path(__file__).resolve().parents[1] / 'work' / 'graft_v1.json'))['frames']
for spec in sys.argv[2:]:
    clip, t = spec.split('@'); t = float(t)
    w = m.world(m.sample(clip, t)) if clip != '-' else m.world({})
    w0 = m.world({})
    for key, tok in (('L', 'Left'), ('R', 'Right')):
        h = names.index(f'{tok}Hand')
        n = np.array(fr[key]['n']); n_g = np.array([n[0], n[2], -n[1]])
        # palm normal in the hand bone's local frame (rest)
        n_loc = w0[h][:3, :3].T @ n_g
        R = w[h][:3, :3]; o = w[h][:3, 3]
        row = []
        for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
            b = names.index(f'{tok}Hand{f}3'); tip = w[b] @ np.array([0, 0.025, 0, 1])
            rel = R.T @ (tip[:3] - o)
            row.append(f'{f[:2]} palm{rel @ n_loc * 100:5.1f} d{np.linalg.norm(rel) * 100:5.1f}')
        print(f'{clip}@{t} {tok}: ' + ' | '.join(row))
