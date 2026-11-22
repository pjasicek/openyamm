# reftour.py <export.json> <out_dir> <tour.yml> [n]: a tour of the n largest sectors of a shipped map.
import json, sys, math
d = json.load(open(sys.argv[1]))['map']
out, tour, n = sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 8
V = d['vertices']
def xyz(i):
    v = V[i]
    return (v['x'], v['y'], v['z']) if isinstance(v, dict) else tuple(v)
cands = []
for si, s in enumerate(d['sectors']):
    if si == 0 or not s.get('floor_faces'):
        continue
    best = None
    for fi in s['floor_faces']:
        f = d['faces'][fi]
        if f['is_portal']:
            continue
        pts = [xyz(i) for i in f['vertices']]
        area = 0
        for a, b in zip(pts, pts[1:] + pts[:1]):
            area += a[0] * b[1] - b[0] * a[1]
        area = abs(area) / 2
        if best is None or area > best[0]:
            best = (area, pts)
    if not best:
        continue
    area, pts = best
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts); cz = min(p[2] for p in pts)
    w = s['max'][0] - s['min'][0]; h = s['max'][1] - s['min'][1]
    cands.append((area, si, cx, cy, cz, w, h))
cands.sort(reverse=True)
lines = [f'output_dir: {out}', 'exit: true', 'settle_seconds: 1.2', 'shots:']
for area, si, cx, cy, cz, w, h in cands[:n]:
    # stand back from the centre along the long axis, look along it
    if w >= h:
        x, y, yaw = cx - w * 0.3, cy, 0.0
    else:
        x, y, yaw = cx, cy - h * 0.3, 1.5708
    lines.append(f'  - {{name: s{si}, position: [{int(x)}, {int(y)}, {int(cz) + 2}], yaw: {yaw}, pitch: 0.05, commands: ["render hud off"]}}')
open(tour, 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
