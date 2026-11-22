#!/usr/bin/env python3
import pathlib
"""Check a studio project's floor props against DRESSING.md (lane A7, 2026-11-20).

Usage: check_dressing.py <L4 folder> <export.json of its built BLV>   (oymap export <blv> --out x.json)
Reads objects.yml decorations (kind by decoration_data's InternalName and Hint) and the built map's faces. Reports:
- CONTAINER-WALL: a barrel/cask/keg/sack/bag/crate/box centre more than 240 from the nearest wall (320 in a room whose
  id or name says store, cache, larder, hold, cellar or pantry);
- DOOR: a container centre within 192 of a door face; PORTAL: within 320 of a vertical portal (open doorway);
- LINE: any floor prop within its radius + 64 of the straight line between two openings of its room;
- CLUMP: 3 or more containers within 200 of each other outside a storeroom.
Wall-hung kinds (torches, sconces, banners) and lights are skipped."""
import json, math, sys, collections, yaml
R = str(pathlib.Path(__file__).resolve().parents[5]) + '/assets_dev/engine/data_tables/decoration_data.txt'
DD = {}
for line in open(R, encoding='latin-1'):
    c = line.rstrip('\n').split('\t')
    if len(c) > 5 and c[0].isdigit():
        DD[c[1].lower()] = (c[2].lower(), int(c[4] or 0))
CONT = ('barrel', 'cask', 'keg', 'sack', 'bag', 'crate', 'box')
SKIP = ('torch', 'sconce', 'banner', 'brazier', 'lamp', 'candle', 'chandelier', 'fire', 'light', 'stalactite')
STORE = ('store', 'cache', 'larder', 'hold', 'cellar', 'pantry', 'granary', 'stock')
L4 = sys.argv[1]; d = json.load(open(sys.argv[2])); m = d['map']; V = m['vertices']; F = m['faces']
objs = yaml.safe_load(open(L4 + '/objects.yml'))
rooms = {r['id']: r for r in (yaml.safe_load(open(L4 + '/rooms.yml')).get('rooms') or [])}
doorfaces = set(f for dr in d.get('doors', []) for f in dr['faces'])

def seg(face):
    pts = [V[i] for i in face['vertices']]
    a, b = max(((p, q) for p in pts for q in pts), key=lambda t: (t[0][0]-t[1][0])**2 + (t[0][1]-t[1][1])**2)
    return a[:2], b[:2], min(p[2] for p in pts), max(p[2] for p in pts)

def dist(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)

walls, portals, doors = [], [], []
opens = collections.defaultdict(list)  # sector -> opening centres
for i, f in enumerate(F):
    if f['plane_normal'][2] != 0:
        continue
    s = seg(f)
    mid = ((s[0][0]+s[1][0])/2, (s[0][1]+s[1][1])/2, s[2], s[0], s[1])
    if i in doorfaces:
        doors.append(s)
    elif f['is_portal']:
        portals.append(s)
        for r in (f['room'], f['room_behind']):
            opens[r].append(mid)
    else:
        walls.append(s)
def inpoly(x, y, pts):
    c = False
    for k in range(len(pts)):
        (x1, y1), (x2, y2) = pts[k][:2], pts[k-1][:2]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            c = not c
    return c
floors = [(f['room'], [V[i] for i in f['vertices']]) for f in F if f['plane_normal'][2] > 0 and not f['is_portal']]
def sector_at(x, y, z):
    best = None
    for r, pts in floors:
        fz = max(p[2] for p in pts)
        if fz <= z + 24 and inpoly(x, y, pts) and (best is None or fz > best[0]):
            best = (fz, r)
    return best[1] if best else None
ent = {e['name']: e for e in m['entities']}
props = []
for o in objs.get('decorations') or []:
    kind = str(o.get('decoration') or o.get('kind') or '').lower()
    hint, rad = DD.get(kind, ('', 32))
    key = o['id'].split(':', 1)[1]
    e = ent.get(key)
    if e is None or any(w in kind or w in hint for w in SKIP) or o.get('height'):
        continue
    x, y, z = e['position']
    room = o.get('room', ''); rname = (rooms.get(room, {}).get('name') or '').lower()
    store = any(w in room.lower() or w in rname for w in STORE)
    cont = any(w in hint or w in kind or w in o['id'] for w in CONT)  # also by the object's name (dec03 is a barrel)
    props.append(dict(id=o['id'], kind=kind, hint=hint, r=rad, pos=(x, y, z), room=room, store=store, cont=cont,
                      sector=sector_at(x, y, z)))
def planeDist(p, o):
    (ax, ay), (bx, by) = o[3], o[4]; L = math.hypot(bx-ax, by-ay) or 1
    return abs((bx-ax)*(ay-p[1]) - (ax-p[0])*(by-ay)) / L
issues = []
def near(lst, p):
    c = [dist(p['pos'][:2], a, b) for a, b, z0, z1 in lst if z0 - 40 <= p['pos'][2] + 30 <= z1 + 40]
    return min(c) if c else 1e9
for p in props:
    if p['cont']:
        w = near(walls, p); lim = 320 if p['store'] else 240
        if w > lim: issues.append(('CONTAINER-WALL', p['id'], p['kind'], round(w)))
        dd = near(doors, p)
        if dd < 192: issues.append(('DOOR', p['id'], p['kind'], round(dd)))
        pp = near(portals, p)
        if pp < 320: issues.append(('PORTAL', p['id'], p['kind'], round(pp)))
    o = [c for c in opens.get(p['sector'], []) if abs(c[2] - p['pos'][2]) < 300]
    for i in range(len(o)):
        for j in range(i + 1, len(o)):
            if planeDist(o[j], o[i]) < 64 and planeDist(o[i], o[j]) < 64:
                continue  # two openings in one wall: the line between them runs along the wall, not across the room
            dl = dist(p['pos'][:2], o[i][:2], o[j][:2])
            if dl < p['r'] + 64:
                issues.append(('LINE', p['id'], p['kind'], round(dl), 'between', tuple(round(v) for v in o[i][:2]), tuple(round(v) for v in o[j][:2])))
cs = [p for p in props if p['cont']]
seen = set()
for p in cs:
    if p['id'] in seen: continue
    g = [p]; seen.add(p['id']); q = [p]
    while q:
        c = q.pop()
        for o in cs:
            if o['id'] not in seen and math.hypot(o['pos'][0]-c['pos'][0], o['pos'][1]-c['pos'][1]) <= 200:
                seen.add(o['id']); g.append(o); q.append(o)
    if len(g) >= 3 and not any(x['store'] for x in g):
        issues.append(('CLUMP', ','.join(x['id'] for x in g), len(g), g[0]['room']))
print(f'{L4}: {len(props)} floor props ({len(cs)} containers), {len(issues)} findings')
for i in sorted(set(issues)):
    print('  ', *i)
