#!/usr/bin/env python3
"""m254 G5 thumb fix (plain python, after fit_fingers.py, before finger_joints.py). The golem's thumbs leave the palm
only 8 cm from the wrist, so the connectivity cut keeps just their distal 3.5 cm and the walk back stopped at 0-0.4 cm:
the three thumb joints sat within 4 cm with a zig-zag centreline, and the source curl stretched the left thumb web to
5.7x (G5). Each thumb centreline is replaced by its straight PCA line, extended back toward the wrist by EXT (the
metacarpal inside the palm), resampled to 13 points. Rewrites work/fingers_fit.json. Env EXT (m, default 0.035)."""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(HERE, 'work', 'fingers_fit.json')
F = json.load(open(p)); EXT = float(os.environ.get('EXT', '0.035'))
for s in ('L', 'R'):
    t = np.array(F[s]['thumb']); c = t.mean(0); d = np.linalg.svd(t - c)[2][0]
    if d @ (t[-1] - t[0]) < 0:
        d = -d
    a, b = (t[0] - c) @ d, (t[-1] - c) @ d
    base, tip = c + d * (a - EXT), c + d * b
    F[s]['thumb'] = [list(map(float, base + (tip - base) * u)) for u in np.linspace(0, 1, 13)]
    print('THUMBFIX', s, 'length cm', round(float(np.linalg.norm(tip - base)) * 100, 1), 'base moved back cm', round(EXT * 100, 1))
json.dump(F, open(p, 'w'))
