#!/usr/bin/env python3
"""Floor area and height per sector of a built BLV (as oymap metrics counts them), with the room the build named."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import json, subprocess, sys, math
blv, root = sys.argv[1], sys.argv[2]
out = subprocess.run([_REPO_ROOT + '/openyamm-studio/build/oymap', 'export', blv, '--world', 'mm7',
                      '--assets', root], capture_output=True, text=True).stdout
m = json.loads(out)['map']
V = m['vertices']
area = {}
for f in m['faces']:
    if f['is_portal']:
        continue
    p = [V[i] for i in f['vertices']]
    nx = ny = nz = 0.0
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
    ar = math.sqrt(nx * nx + ny * ny + nz * nz) / 2
    if ar > 0 and abs(nz) / (2 * ar) > 0.7 and f['plane_normal'][2] > 0:
        area[f['room']] = area.get(f['room'], 0) + abs(nz) / 2
names = {}
build_json = sys.argv[3] if len(sys.argv) > 3 else None
rows = []
for s, a in area.items():
    sec = m['sectors'][s]
    rows.append((a, s, sec['max'][2] - sec['min'][2]))
rows.sort(reverse=True)
vals = sorted(r[0] for r in rows)
n = len(vals)
q3 = vals[int(math.floor(0.75 * (n - 1) + 0.5))]
for a, s, h in rows:
    sec = m['sectors'][s]
    print('%9.0f  sector %2d  h %4d  x %d..%d y %d..%d' % (a, s, h, sec['min'][0], sec['max'][0], sec['min'][1], sec['max'][1]))
print('n', n, 'q3', q3)
