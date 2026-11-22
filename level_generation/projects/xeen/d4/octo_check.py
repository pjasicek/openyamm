#!/usr/bin/env python3
"""A6 (session 11): the octopods' reported positions in a hostility log (report_state lines) checked against D4's
lake (gen.py's in_lake, the islets out) and their homes' leash. Usage: octo_check.py <log>"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import re
import sys
import yaml
sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/d4')
import gen  # noqa: E402

scene = yaml.load(open(_REPO_ROOT + '/output/studio_cal/d4/build/xeen_d4.scene.yml'),
                  Loader=yaml.CSafeLoader)
home = {i: a for i, a in enumerate(scene['initial_state']['actors']) if a.get('monster_id') in (11470, 11471)}
bad = 0
for line in open(sys.argv[1]):
    m = re.search(r'ACTOR index=(\d+) .*position=([-\d.]+),([-\d.]+),([-\d.]+)', line)
    if not m or int(m.group(1)) not in home:
        continue
    i, X, Y, Z = int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    a = home[i]
    cx, cy = X / 512.0 + 64, 64 - Y / 512.0
    wet = gen.in_lake(cx, cy) and not any(gen.inside((cx, cy), p) for p in gen.ISLETS)
    d = math.hypot(X - a['position']['x'], Y - a['position']['y'])
    ok = wet and d <= a['leash_radius'] + 150
    bad += not ok
    print('actor %d (%d) at cell (%.1f, %.1f) z %d: %s, %d from home (leash %d)%s'
          % (i, a['monster_id'], cx, cy, Z, 'in water' if wet else 'ON LAND', d, a['leash_radius'],
             '' if ok else '  <-- FAIL'))
print('octopods out of water or leash:', bad)
sys.exit(1 if bad else 0)
