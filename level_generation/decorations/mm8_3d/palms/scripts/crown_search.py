#!/usr/bin/env python3
"""Grid search of crown settings with crown_profile.py (no fit): score = mean |model reach - sprite reach| over the
height bands where the sprite has leaves + |top - 1|. Usage: crown_search.py <id> '<json list of trial dicts>'"""
import json, subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
sid, trials = sys.argv[1], json.loads(sys.argv[2])
res = []
for t in trials:
    t = dict(t, fit=False)
    out = subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(here, 'crown_profile.py'), '--', sid,
                          json.dumps(t)], capture_output=True, text=True, errors='replace').stdout
    j = json.loads(next(l for l in out.splitlines() if l.startswith('JSON'))[5:])
    err = [abs(m - s) for m, s in zip(j['model'], j['sprite'])]
    score = sum(err) / len(err) + abs(j['top'] - 1.0)
    res.append((score, t, j))
    print(f"{score:.3f} top {j['top']:.2f} model {j['model']} {t}", flush=True)
best = min(res, key=lambda r: r[0])
print('BEST', round(best[0], 3), json.dumps(best[1]), 'sprite', best[2]['sprite'])
