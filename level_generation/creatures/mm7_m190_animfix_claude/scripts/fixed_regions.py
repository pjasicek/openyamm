#!/usr/bin/env python3
"""motion_audit region bad % per clip with the region map of a reference GLB (same mesh), so a reweight that moves
triangles between regions (the beard from spine to head) is compared on the same surface (follow-up m190).

    fixed_regions.py <reference glb> <glb> [<glb> ...] [--clips=Hit,Attack]

Per clip and region: the worst frame's bad share (motion_audit rule, 30 fps) with the reference's triangle regions,
then in brackets the share beyond the same GLB's Standing on that map."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa
R = motion_audit.REGIONS
SHOW = ['hand', 'arm', 'head', 'spine', 'leg']
args = [a for a in sys.argv[1:] if not a.startswith('--')]
clips = next((a.split('=', 1)[1].split(',') for a in sys.argv[1:] if a.startswith('--clips=')), None)
ref = motion_audit.Audit(args[0])
reg = ref.tri_region
for path in args[1:]:
    a = motion_audit.Audit(path)
    assert len(a.tris) == len(ref.tris)
    total = np.bincount(reg[a.valid], a.rest_area[a.valid], len(R))
    res = {}
    for c in (clips and ['Standing'] + [x for x in clips if x != 'Standing']) or list(a.model.clips):
        ts = a.model.clip_times(c)
        n = max(2, int(round((ts[-1] - ts[0]) * 30)) + 1)
        worst = np.zeros(len(R))
        for t in np.linspace(ts[0], ts[-1], n):
            posed, scale, pal, _ = a.pose(c, t)
            s1, s2, fold, live = a.deformation(posed, scale, pal)
            bad = live & ((s1 > 1.6) | (s2 < 0.55) | fold)
            worst = np.maximum(worst, np.bincount(reg[bad], a.rest_area[bad], len(R)) / np.maximum(total, 1e-20))
        res[c] = 100 * worst
    st = res['Standing']
    print('==', path)
    for c, v in res.items():
        print(f'{c:9s}', ' '.join(f'{k}:{v[R.index(k)]:5.1f}({v[R.index(k)] - st[R.index(k)]:+5.1f})' for k in SHOW))
