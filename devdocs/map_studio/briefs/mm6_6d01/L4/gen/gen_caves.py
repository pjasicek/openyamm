# First shell of Goblinwatch's caves (MM6 6d01.blv), written once from the original's export (oymap export --pretty).
# Each cave sector becomes one room: its outline is the plan boundary of its floor faces with the points that lie on a
# straight stretch taken out (they become points on that wall), its uneven floor and roof are the original's own
# vertices one for one (floor_points, ceiling_points) with the creases between faces of different planes as
# floor_lines/ceiling_lines. Banks (floor faces that are not level) take the bank texture by `steeper_than`.
# Where the original does what the studio does not build, the nearest honest thing is done and reported on stderr:
# cracks in the floor's edge are left out, points closer than 26 to another are merged, the roof is kept 16 over the
# floor (the original's banks meet its roof with no wall), floor triangles steeper than 2 up for 1 across have their
# high corner lowered (a short upright wall under the roof instead) and roof triangles steeper than 4 their low corner
# raised. Heights are adjusted on one table for all caves, so two caves keep the same mouth.
# Usage: python3 gen_caves.py <export.json> <sector list> > fragment.yml
import json, sys, collections, math

exp = json.load(open(sys.argv[1]))['map']
V = exp['vertices']; F = exp['faces']; S = exp['sectors']
SECTORS = [int(x) for x in sys.argv[2].split(',')]
# Faces that are not the cave's own floor or roof: door and doorway strips (a doorway's depth belongs to the wall
# between two rooms here), and the fountain in sector 44 (its tiers are platforms of the room).
EXCLUDE = {1679, 1666, 1473} | {i for i, f in enumerate(F) if f['texture'] in ('orWtr32', 'OrFyr32')}
# The shaft (sector 46) opens in the cave's floor at 128; the studio's floor hole needs a level upper room, so a
# landing room (s44h: the shaft's mouth and a strip south of it to the rim, level at 128 as the original's floor
# there) is cut out of the cave: its outline is notched round it.
NOTCH = {44: ((7218, 3030), [(7296, 3026), (7296, 3168), (7232, 3232), (7232, 3328), (7296, 3392), (7392, 3392),
                             (7456, 3328), (7456, 3232), (7392, 3168), (7392, 3022)])}
LANDING = [(7296, 3026), (7392, 3022), (7392, 3168), (7456, 3232), (7456, 3328), (7392, 3392), (7296, 3392),
           (7232, 3328), (7232, 3232), (7296, 3168)]
EXTRA_ROOF_LINES = {44: [((6912, 3216), (7232, 3232)), ((6912, 3216), (7232, 3328)), ((7218, 3030), (7296, 3168))]}
# Points left out by hand: rim points 5 inside the outline that make slivers the studio refuses as too steep.
DROP = {(44, 'floor'): [(6792, 7084), (7546, 3232), (7546, 3488)], (44, 'roof'): [(6792, 7084), (6728, 7084)]}
for sec in S:
    for key in ('floor_faces', 'ceiling_faces', 'portal_faces'):
        sec[key] = [f for f in sec[key] if f not in EXCLUDE]


def P(v):
    return tuple(V[v])


def log(*a):
    print('#', *a, file=sys.stderr)


def on_seg(p, a, b, tol=0.5):
    if p == a or p == b:
        return False
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L == 0:
        return False
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > tol * L:
        return False
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / L ** 2
    return 0 < t < 1


def area(r):
    return 0.5 * sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))


def inside_or_on(p, poly, tol=0.5):
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if tuple(p) == tuple(a) or on_seg(p, a, b, tol):
            return True
    c = False
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]):
            xi = x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1)
            if xi > p[0]:
                c = not c
    return c


def ring_of(faces):
    pts = {P(v)[:2] for f in faces for v in F[f]['vertices']}
    cnt = collections.Counter(); dirs = {}
    for fi in faces:
        vs = [P(v)[:2] for v in F[fi]['vertices']]
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            if a == b:
                continue
            mids = sorted([p for p in pts if on_seg(p, a, b)], key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
            chain = [a] + mids + [b]
            for j in range(len(chain) - 1):
                k = frozenset((chain[j], chain[j + 1])); cnt[k] += 1; dirs[k] = (chain[j], chain[j + 1])
    edges = [dirs[k] for k, c in cnt.items() if c == 1]
    nxt = collections.defaultdict(list)
    for a, b in edges:
        nxt[a].append(b)
    used = set(); rings = []
    for a, b in edges:
        if (a, b) in used:
            continue
        ring = [a]; cur = (a, b)
        while cur not in used:
            used.add(cur); ring.append(cur[1])
            c = cur[1]
            cands = [x for x in nxt[c] if (c, x) not in used]
            if not cands:
                break
            cur = (c, cands[0])
        rings.append(ring[:-1])
    return rings


def outline_of(si):
    rings = ring_of(S[si]['floor_faces'])
    ring = max(rings, key=lambda r: abs(area(r)))
    if area(ring) < 0:
        ring = ring[::-1]
    while True:
        seen = {}; dup = None
        for i, p in enumerate(ring):
            if p in seen:
                dup = (seen[p], i); break
            seen[p] = i
        if not dup:
            break
        i, j = dup
        inner = ring[i:j]; outer = ring[:i] + ring[j:]
        a, b = (inner, outer) if abs(area(inner)) < abs(area(outer)) else (outer, inner)
        log(f'S{si}: crack in the floor\'s edge left out at {ring[i]} (area {round(area(a))})')
        ring = b
    out = list(ring)
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            L = math.hypot(c[0] - a[0], c[1] - a[1])
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) == 0:
                del out[i]; changed = True; break
    return ring, out


def crosses_outline(seg, poly):
    (ax, ay), (bx, by) = seg
    mid = ((ax + bx) / 2, (ay + by) / 2)
    if not inside_or_on(mid, poly):
        return True
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 0) - (v < 0)
    for i in range(len(poly)):
        c, d = poly[i], poly[(i + 1) % len(poly)]
        if len({tuple(c), tuple(d), (ax, ay), (bx, by)}) < 4:
            continue
        o1, o2 = orient((ax, ay), (bx, by), c), orient((ax, ay), (bx, by), d)
        o3, o4 = orient(c, d, (ax, ay)), orient(c, d, (bx, by))
        if o1 * o2 < 0 and o3 * o4 < 0:
            return True
    return False


def segs_cross(p, q):
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 0) - (v < 0)
    (a, b), (c, d) = p, q
    return orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0


def face_tris(fi):
    vs = [P(v) for v in F[fi]['vertices']]
    return [(vs[0], vs[i], vs[i + 1]) for i in range(1, len(vs) - 1)]


def zat(faces, xy):
    for fi in faces:
        vs = [P(v) for v in F[fi]['vertices']]
        n = F[fi]['plane_normal']
        if n[2] == 0:
            continue
        if inside_or_on(xy, [v[:2] for v in vs]):
            a = vs[0]
            return round(a[2] - (n[0] * (xy[0] - a[0]) + n[1] * (xy[1] - a[1])) / n[2])
    return None


def creases(faces):
    edge_faces = collections.defaultdict(list)
    for fi in faces:
        vs = [P(v) for v in F[fi]['vertices']]
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            if a[:2] != b[:2]:
                edge_faces[frozenset((a[:2], b[:2]))].append(fi)
    out = []
    for k, fs in edge_faces.items():
        if len(fs) == 2:
            n1 = F[fs[0]]['plane_normal']; n2 = F[fs[1]]['plane_normal']
            if max(abs(n1[i] - n2[i]) for i in range(3)) > 200:
                out.append(sorted(k))
    return sorted(out)


def steepness(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    if abs(nz) < 400:
        return 0
    return math.hypot(nx, ny) / abs(nz)


# Pass 1: per sector, outline, points (with sliver aliases) and lines.
data = {}
TJ_LINES = {}
for si in SECTORS:
    s = S[si]
    fl = s['floor_faces']; ce = s['ceiling_faces']
    ring, cor = outline_of(si)
    if si in NOTCH:
        after, pts_in = NOTCH[si]
        i = cor.index(after)
        cor = cor[:i + 1] + pts_in + cor[i + 1:]
        log(f'S{si}: outline notched after {after}: {pts_in}')
    keep_first = set(cor) | {P(v)[:2] for f in s['portal_faces'] for v in F[f]['vertices']}

    def collect(faces, pick, label):
        h = {}
        for fi in faces:
            for v in F[fi]['vertices']:
                p = P(v); h.setdefault(p[:2], []).append(p[2])
        pts = {}
        for xy, zs in h.items():
            if len(set(zs)) > 1:
                log(f'S{si}: {label} vertex {xy} has heights {sorted(set(zs))}; taken {pick(zs)}')
            pts[xy] = pick(zs)
        alias = {}; kept = []
        for xy in sorted(pts, key=lambda q: (0 if q in keep_first else 1, q)):
            near = [k for k in kept if math.hypot(k[0] - xy[0], k[1] - xy[1]) < 26]
            if near and xy not in keep_first:
                alias[xy] = near[0]
            else:
                kept.append(xy)
        # T-junction points: a point lying on the straight line between two others (within 2.5 across, its height
        # within 24 of the line's) splits nothing the studio needs and makes slivers: left out.
        tj = []
        tj_lines = []
        for xy in kept:
            if xy in keep_first:
                continue
            others = [k for k in kept if k != xy and k not in tj and math.hypot(k[0] - xy[0], k[1] - xy[1]) < 700]
            done = False
            for i in range(len(others)):
                for j in range(i + 1, len(others)):
                    a, b = others[i], others[j]
                    L = math.hypot(b[0] - a[0], b[1] - a[1])
                    if L == 0:
                        continue
                    t = ((xy[0] - a[0]) * (b[0] - a[0]) + (xy[1] - a[1]) * (b[1] - a[1])) / L ** 2
                    d = abs((b[0] - a[0]) * (xy[1] - a[1]) - (b[1] - a[1]) * (xy[0] - a[0])) / L
                    if 0.02 < t < 0.98 and d < 2.5 and abs(pts[a] + t * (pts[b] - pts[a]) - pts[xy]) < 24:
                        tj.append(xy); alias[xy] = None; done = True
                        tj_lines.append((a, b)); break
                if done:
                    break
        for xy in tj:
            kept.remove(xy)
        if tj:
            log(f'S{si}: {label} T-junction points left out: {tj}')
        for xy in DROP.get((si, label), []):
            if xy in kept:
                kept.remove(xy); alias[xy] = None
                log(f'S{si}: {label} point {xy} left out by hand (a sliver along the rim)')
        dropped = [xy for xy in kept if not inside_or_on(xy, cor, tol=1.0)]
        for xy in dropped:
            alias[xy] = None
            kept.remove(xy)
        for k in list(alias):
            v = alias[k]
            while v is not None and v in alias:
                v = alias[v]
            alias[k] = v
        if alias:
            log(f'S{si}: {label} points merged or dropped: {alias}')
        # the line a T-junction point stood on is kept as a line (it is an edge of the original's faces)
        TJ_LINES[(si, label)] = [l for l in tj_lines if l[0] in kept and l[1] in kept]
        return {xy: pts[xy] for xy in kept}, alias

    fpts, falias = collect(fl, max, 'floor')
    cpts, calias = collect(ce, min, 'roof')
    for c in cor:
        if c not in fpts:
            z = zat(fl, c); fpts[c] = z
            log(f'S{si}: floor at corner {c} read off the faces: {z}')
        if c not in cpts:
            z = zat(ce, c)
            if z is None:
                z = max(cpts.values())
            cpts[c] = z
    data[si] = dict(fl=fl, ce=ce, cor=cor, fpts=fpts, cpts=cpts, falias=falias, calias=calias,
                    portal={P(v)[:2] for f in s['portal_faces'] for v in F[f]['vertices']})

# Pass 2: one height table for all caves (keyed by plan point), steep floors fixed.
FZ = {}; CZ = {}
for si, d in data.items():
    for xy, z in d['fpts'].items():
        FZ[xy] = z if xy not in FZ else max(FZ[xy], z)
    for xy, z in d['cpts'].items():
        CZ[xy] = z if xy not in CZ else min(CZ[xy], z)


def tri_list(si, key):
    d = data[si]
    alias = d['falias'] if key == 'fl' else d['calias']
    out = []
    for fi in d[key]:
        for t in face_tris(fi):
            q = tuple(alias.get(p[:2], p[:2]) for p in t)
            if None not in q and len(set(q)) == 3:
                out.append(q)
    return out


ALLF = [t for si in data for t in tri_list(si, 'fl')]
ALLC = [t for si in data for t in tri_list(si, 'ce')]
lowered = collections.Counter()
for _ in range(20000):
    bad = [t for t in ALLF if steepness(*[(p[0], p[1], FZ[p]) for p in t]) > 1.95]
    if not bad:
        break
    t = sorted(bad[0], key=lambda p: FZ[p])
    lo, mid, hi = t
    if FZ[hi] - 1 >= FZ[mid]:
        FZ[hi] -= 1; lowered[hi] += 1
    elif FZ[mid] - 1 >= FZ[lo]:
        # two corners at the top (a bank's rim): both come down
        FZ[hi] -= 1; lowered[hi] += 1
        FZ[mid] -= 1; lowered[mid] += 1
    else:
        FZ[lo] += 1; lowered[lo] -= 1
if lowered:
    log('floor heights changed for steep banks (negative: raised):', dict(lowered))

# The roof 16 over the floor wherever both have a point, and at roof points over the floor.
for si, d in data.items():
    for xy in d['cpts']:
        f = FZ.get(xy)
        if f is None:
            f = zat(d['fl'], xy)
        if f is not None and CZ[xy] < f + 16:
            CZ[xy] = f + 16
craised = collections.Counter()
for _ in range(20000):
    bad = [t for t in ALLC if steepness(*[(p[0], p[1], CZ[p]) for p in t]) > 3.9]
    if not bad:
        break
    t = sorted(bad[0], key=lambda p: CZ[p])
    lo, mid, hi = t
    if CZ[lo] + 1 <= CZ[mid]:
        CZ[lo] += 1; craised[lo] += 1
    else:
        CZ[hi] -= 1; craised[hi] -= 1
if craised:
    log('roof heights changed for steep roofs (negative: lowered):', dict(craised))


# Heights set by hand where the studio's own triangles (not the original's) came out too steep once T-junction points
# were left out: the mouth of caves 27 and 28.
FIX_FLOOR = {(-17280, 6592): -815, (7052, 6846): 388, (2752, 256): -768, (5576, 5120): 128, (17920, 8576): -768}
for xy, z in FIX_FLOOR.items():
    log(f'floor point {xy} set by hand from {FZ.get(xy)} to {z}')
    FZ[xy] = z


def fmt(l):
    return '[' + ', '.join(fmt(x) if isinstance(x, (list, tuple)) else str(x) for x in l) + ']'


for si in SECTORS:
    d = data[si]
    cor = d['cor']
    fpts = sorted([[x, y, FZ[(x, y)]] for (x, y) in d['fpts']])
    cpts = sorted([[x, y, CZ[(x, y)]] for (x, y) in d['cpts']])
    floor_z = min(p[2] for p in fpts)
    ceil_z = max(p[2] for p in cpts)

    def lines(faces, alias, pts):
        out = []
        for l in creases(faces):
            m = [alias.get(tuple(q), tuple(q)) for q in l]
            if None in m:
                continue
            m = sorted(tuple(q) for q in m)
            if m[0] != m[1] and crosses_outline(m, cor):
                log(f'S{si}: line {m} leaves the room (notch): left out')
                continue
            if m[0] != m[1] and m not in out and all(q in pts for q in m):
                out.append(m)
        return sorted(out)
    fl_lines = lines(d['fl'], d['falias'], d['fpts'])
    ce_lines = lines(d['ce'], d['calias'], d['cpts'])
    for key, ls in (('floor', fl_lines),):
        for a, b in TJ_LINES.get((si, key), []):
            m = sorted([tuple(a), tuple(b)])
            if m not in ls and not crosses_outline(m, cor) and not any(len({*m, *map(tuple, l)}) == 4 and segs_cross(m, l) for l in ls):
                ls.append(m)
    for l in EXTRA_ROOF_LINES.get(si, []):
        ce_lines.append(sorted(l))
        log(f'S{si}: roof line {l} added by hand (the notch round the shaft)')
    flat = collections.Counter(); steep = collections.Counter()
    for fi in d['fl']:
        (flat if F[fi]['plane_normal'][2] == 65536 else steep)[F[fi]['texture']] += 1
    print(f'  - id: room:s{si}')
    print(f'    name: Cave {si}')
    print('    theme: theme:cave')
    print(f'    outline: {fmt(cor)}')
    print(f'    floor: {floor_z}')
    print(f'    floor_points: {fmt(fpts)}')
    if fl_lines:
        print('    floor_lines:')
        for l in fl_lines:
            print(f'      - {fmt(l)}')
    if steep:
        print('    floor_surfaces:')
        print('      - {steeper_than: 0.1, surface: {texture: d2ceil4, size: [256, 256]}}')
    print('    steep_floor: true')
    print(f'    ceiling: {ceil_z}')
    print(f'    ceiling_points: {fmt(cpts)}')
    if ce_lines:
        print('    ceiling_lines:')
        for l in ce_lines:
            print(f'      - {fmt(l)}')
    print(f'    notes: "Original sector {si}: outline from its floor faces ({len(cor)} corners), floor and roof by the '
          f'original\'s own vertices one for one ({len(fpts)} floor points, {len(cpts)} roof points; see NOTES.md), creases as '
          f'lines. Level floor {dict(flat)}, banks {dict(steep)}."')


# The shaft's landing room: level floor at 128, the original's roof read at its corners (16 over the floor at the rim).
ce44 = S[44]['ceiling_faces']
if 44 not in SECTORS:
    sys.exit(0)
lp = []
for c in LANDING:
    z = CZ.get(c)
    if z is None:
        z = zat(ce44, c)
    lp.append([c[0], c[1], max(z, 144)])
print('  - id: room:s44h')
print('    name: Shaft mouth')
print('    theme: theme:cave')
print(f'    outline: {fmt([list(c) for c in LANDING])}')
print('    floor: 128')
print(f'    ceiling: {max(p[2] for p in lp)}')
print(f'    ceiling_points: {fmt(lp)}')
print('    notes: "Part of sector 44 round the shaft\'s mouth (the hole in its floor down to sector 46) and a strip south of it '
      'to the rim, level at 128 as the original\'s floor is there: the studio opens a floor only in a room whose floor is '
      'level. The roof is the original\'s read at its corners."')
