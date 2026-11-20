#!/usr/bin/env python3
"""Region bad % per clip of several GLBs side by side, and beyond Standing (follow-up m190).
    audit_table.py <glb> [<glb> ...] [--clips Hit,Attack]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa
args = [a for a in sys.argv[1:] if not a.startswith('--clips=')]
clips = next((a.split('=', 1)[1].split(',') for a in sys.argv[1:] if a.startswith('--clips=')), None)
REG = ['hand', 'arm', 'head', 'spine', 'leg']
for path in args:
    a = motion_audit.Audit(path)
    st, _ = a.clip('Standing', 30)
    s = {k: v['bad_pct'] for k, v in st['deform'].items()}
    print('==', Path(path).name, path)
    for c in (clips or list(a.model.clips)):
        r, _ = a.clip(c, 30)
        ts = a.model.clip_times(c)
        worst = 0.0
        for t in __import__('numpy').linspace(ts[0], ts[-1], max(2, int((ts[-1] - ts[0]) * 15) + 1)):
            posed, scale, pal, _w = a.pose(c, t)
            s1, s2, fold, live = a.deformation(posed, scale, pal)
            bad = live & ((s1 > 1.6) | (s2 < 0.55) | fold)
            worst = max(worst, a.rest_area[bad].sum() * 1e4)
        d = {k: v['bad_pct'] for k, v in r['deform'].items()}
        print(f'{c:9s}', ' '.join(f'{k}:{d.get(k, 0):5.1f}({d.get(k, 0) - s.get(k, 0):+5.1f})' for k in REG),
              f"badcm2 {worst:5.0f}", f"hot {r['hotspot']['joint']} {r['hotspot']['bad_pct']}", f"amp90 {r.get('amp_p90')}", f"inside {r['hand_inside_pct']}")
