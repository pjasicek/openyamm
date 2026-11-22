# Each wall-mounted decoration: is a solid wall face right behind it (within 40 units, covering its point)?
# python3 wall_check.py <export.json> <objects.yml>
import json, sys, re
import numpy as np
d = json.load(open(sys.argv[1]))['map']
V = np.array(d['vertices'], float)
text = open(sys.argv[2]).read()
wall_ids = set()
for block in text.split('\n  - id: ')[1:]:
    head = block.split('\n')[0]
    if head.startswith('deco:') and re.search(r'\n    wall: ', block):
        wall_ids.add(head[5:])
faces = []
for f in d['faces']:
    n = np.array(f['plane_normal'], float) / 65536.0
    if f['is_portal'] or abs(n[2]) > 0.1:
        continue
    pts = V[f['vertices']]
    faces.append((n, pts))
bad = 0
for e in d['entities']:
    if e['name'] not in wall_ids:
        continue
    p = np.array(e['position'], float)
    best = None
    for n, pts in faces:
        dist = np.dot(p - pts[0], n)
        if abs(dist) > 40:
            continue
        t = np.array([-n[1], n[0], 0.0])
        s = (pts - pts[0]) @ t
        u = np.dot(p - pts[0], t)
        z = pts[:, 2]
        if s.min() - 1 <= u <= s.max() + 1 and z.min() - 1 <= p[2] <= z.max() + 1:
            best = dist if best is None or abs(dist) < abs(best) else best
    ok = best is not None
    bad += not ok
    print(('ok  ' if ok else 'AIR ') + f"{e['name']:24} {e['position']}" + ('' if not ok else f' wall {best:.0f} away'))
print('in the air:', bad)
