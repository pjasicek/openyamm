#!/usr/bin/env python3
# XD-27 copy of output/studio_cal/a7/dressing/measure.py (A7): only KIND extended with this map's prop names.
"""Measure prop dressing in a BLV export (oymap export --out x.json): lane A7, devdocs/xeen/formats/DRESSING.md.

For each floor prop (barrels, casks, sacks, crates, heaps, bones, rocks): its sector, the 2D distance to the nearest
solid wall of that height, to the nearest portal (walls only) and door face; groups (props of one kind within LINK of
each other); props per sector. Usage: measure.py <export.json> [--json out]"""
import json, math, sys, collections
KIND = {'bigbarel': 'barrel', '7dec32': 'barrel', '7dec21': 'cask', 'bag01': 'sack', 'bag_A': 'sack',
        '7dec01': 'heap', '7dec10': 'heap', '7dec11': 'heap', '7dec18': 'bones', 'dec19': 'bones',
        '7rock03': 'rock', '7rock05': 'rock', 'smlbarel': 'barrel', 'dec03': 'barrel', 'floursac': 'sack', 'trasheap': 'heap', 'dec29': 'bones', '7dec20': 'bones', 'dec05': 'bones', 'Bucket': 'barrel', 'foodbowl': 'bones', '6rock01': 'rock', '6rock02': 'rock', '6rock03': 'rock', '6rock04': 'rock', '6rock05': 'rock', '6rock06': 'rock', '6rock08': 'rock', '6rock09': 'rock', '6rock12': 'rock', '6rock13': 'rock', 'rock03': 'rock', 'rock10': 'rock', 'sklplrev': 'heap', 'Corpse04': 'bones', 'Corpse02': 'table-top', 'dec04': 'heap', '7dec08': 'table-top', '7dec48': 'table-top'}
LINK = 200  # centre to centre: two barrels (radius 30-52) side by side are 128-192 apart
d = json.load(open(sys.argv[1])); m = d['map']
# A studio build names each entity by its id (deco:den_keg -> den_keg): --objects <objects.yml> maps it to its decoration.
if '--objects' in sys.argv:
    import yaml
    deco = {o['id'].split(':', 1)[1]: o['decoration'] for o in
            yaml.safe_load(open(sys.argv[sys.argv.index('--objects') + 1])).get('decorations', [])}
    for e in m['entities']:
        e['id'] = e['name']; e['name'] = deco.get(e['name'], e['name']); V = m['vertices']; F = m['faces']
doorfaces = set(f for dr in d.get('doors', []) for f in dr['faces'])

def seg_of(face):
    pts = [V[i] for i in face['vertices']]
    best = None
    for a in pts:
        for b in pts:
            l = (a[0]-b[0])**2 + (a[1]-b[1])**2
            if best is None or l > best[0]:
                best = (l, a, b)
    zs = [p[2] for p in pts]
    return best[1][:2], best[2][:2], min(zs), max(zs)

def dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-ax-t*dx, py-ay-t*dy)

walls, portals, doors = [], [], []
for i, f in enumerate(F):
    if f['plane_normal'][2] != 0:
        continue
    s = seg_of(f)
    if i in doorfaces: doors.append(s)
    elif f['is_portal']: portals.append(s)
    else: walls.append(s)
def inpoly(x, y, pts):
    c = False
    for k in range(len(pts)):
        (x1, y1), (x2, y2) = pts[k][:2], pts[k-1][:2]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            c = not c
    return c
floors = [(f, [V[i] for i in f['vertices']]) for f in F if f['plane_normal'][2] > 0 and not f['is_portal']]
def sector_at(x, y, z):
    best = None
    for f, pts in floors:
        fz = max(p[2] for p in pts)
        if fz <= z + 24 and inpoly(x, y, pts) and (best is None or fz > best[0]):
            best = (fz, f['room'])
    return best[1] if best else None
sector_of = {}
for ei, e in enumerate(m['entities']):
    if e['name'] in KIND:
        sector_of[ei] = sector_at(*e['position'])
props = []
for ei, e in enumerate(m['entities']):
    k = KIND.get(e['name'])
    if not k: continue
    x, y, z = e['position']
    def near(lst, zpad=40):
        c = [dist((x, y), a, b) for a, b, z0, z1 in lst if z0 - zpad <= z + 30 <= z1 + zpad]
        return round(min(c)) if c else None
    props.append({'i': ei, 'id': e.get('id', ''), 'name': e['name'], 'kind': k, 'pos': [x, y, z], 'sector': sector_of.get(ei),
                  'wall': near(walls), 'portal': near(portals), 'door': near(doors)})
# groups by kind family (barrel+cask together, sacks, others)
fam = lambda k: {'cask': 'barrel'}.get(k, k)
groups = []
seen = set()
for p in props:
    if p['i'] in seen: continue
    g = [p]; seen.add(p['i']); q = [p]
    while q:
        c = q.pop()
        for o in props:
            if o['i'] not in seen and fam(o['kind']) == fam(c['kind']) and \
               math.hypot(o['pos'][0]-c['pos'][0], o['pos'][1]-c['pos'][1]) <= LINK:
                seen.add(o['i']); g.append(o); q.append(o)
    groups.append(g)
def stats(v):
    v = sorted(x for x in v if x is not None)
    return {'n': len(v), 'min': v[0], 'median': v[len(v)//2], 'p90': v[int(len(v)*0.9)], 'max': v[-1]} if v else {}
out = {'map': d['file'] if 'file' in d else sys.argv[1], 'props': collections.Counter(p['kind'] for p in props)}
for k in sorted(set(fam(p['kind']) for p in props)):
    ps = [p for p in props if fam(p['kind']) == k]
    gs = [g for g in groups if fam(g[0]['kind']) == k]
    sizes = collections.Counter(len(g) for g in gs)
    out[k] = {'wall': stats([p['wall'] for p in ps]), 'portal': stats([p['portal'] for p in ps]),
              'door': stats([p['door'] for p in ps]), 'group_sizes': dict(sorted(sizes.items())),
              'groups_by_sector': collections.Counter((g[0]['sector'], len(g)) for g in gs).most_common()}
out['per_sector'] = collections.Counter(p['sector'] for p in props).most_common()
print(json.dumps(out, indent=1, default=str))
if '--list' in sys.argv:
    for p in props: print(p)
