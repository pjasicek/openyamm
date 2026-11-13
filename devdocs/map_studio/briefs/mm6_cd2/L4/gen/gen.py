#!/usr/bin/env python3
"""Measures cd2.blv sector by sector and writes the L4 rooms.yml.

Each sector of the original becomes one room on its floor outline, or several where its floor is terraces, a flight
of steps or a ramp; thin door-frame sectors become the thickness of an opening. Per-sector decisions that the
measurement cannot make are in overrides.py. Usage: gen.py [--wings 1,2,...]
"""
import sys, math, collections, json
from lib import *
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import set_precision
import overrides as OV

L4 = '/home/pjasicek/github/OpenYAMM/devdocs/map_studio/briefs/mm6_cd2/L4/'
EPS = 1e-6


def polys(g):
    if g is None or g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    return [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon' and p.area > 0]


def ring_pts(poly, tol=0.6):
    """Counter-clockwise integer corner list of a polygon's outer ring, collinear points removed."""
    p = poly.simplify(tol, preserve_topology=True)
    if p.geom_type != 'Polygon':
        p = max(polys(p), key=lambda q: q.area)
    if not p.exterior.is_ccw:
        p = Polygon(list(p.exterior.coords)[::-1])
    pts = [(int(round(x)), int(round(y))) for x, y in p.exterior.coords[:-1]]
    out = []
    for q in pts:
        if not out or out[-1] != q:
            out.append(q)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    # drop exactly collinear corners
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) == 0:
                out.pop(i)
                changed = True
                break
    return out


def outline_of(poly, maxpts=30):
    tol = 0.6
    pts = ring_pts(poly, tol)
    while len(pts) > maxpts and tol < 400:
        tol = max(8, tol * 1.6)
        pts = ring_pts(poly, tol)
    return pts


def is_convex(pts):
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) <= 0:
            return False
    return True


class Room:
    def __init__(self, rid, sector, pts, floor, ceiling):
        self.id = rid
        self.sector = sector
        self.pts = pts
        self.floor = floor
        self.ceiling = ceiling
        self.slope = None
        self.extra = {}
        self.notes = ''
        self.name = ''
        self.poly = Polygon(pts)

    def floor_low(self):
        return min(self.floor, self.slope['to']) if self.slope else self.floor

    def floor_high(self):
        return max(self.floor, self.slope['to']) if self.slope else self.floor


_nook_cache = {}


def nooks_of(si):
    """Doorway nooks: where the sector's floor runs a wall's thickness (up to 200) into a doorway whose end is a
    portal. They belong to the opening, not to the room's outline."""
    if si in _nook_cache:
        return _nook_cache[si]
    s = S[si]
    allp = [poly2(F[fi]) for fi in s['floor_faces']]
    allp = [p for p in allp if p is not None and p.area > 0]
    res = []
    if allp and si not in OV.NO_NOOKS:
        foot = unary_union(allp)
        for fi in s['portal_faces']:
            f = F[fi]
            n = nrm(f)
            if abs(n[2]) > 0.5:
                continue
            p = fpts(f)
            best = None
            for a in p:
                for b in p:
                    d = math.hypot(a[0] - b[0], a[1] - b[1])
                    if best is None or d > best[0]:
                        best = (d, a, b)
            w, a, b = best
            if w < 32:
                continue
            ux, uy = (b[0] - a[0]) / w, (b[1] - a[1]) / w
            # inward normal: toward the sector's floor
            nx, ny = -uy, ux
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if not foot.contains(Point(mid[0] + nx * 4, mid[1] + ny * 4)):
                nx, ny = -nx, -ny
                if not foot.contains(Point(mid[0] + nx * 4, mid[1] + ny * 4)):
                    continue
            found = None
            for L in (24, 48, 64, 96, 128, 144, 160, 192):
                # the strips just beside the doorway must be solid over the whole depth
                def rect(s0, s1, t0, t1):
                    return Polygon([(a[0] + ux * s0 + nx * t0, a[1] + uy * s0 + ny * t0),
                                    (a[0] + ux * s1 + nx * t0, a[1] + uy * s1 + ny * t0),
                                    (a[0] + ux * s1 + nx * t1, a[1] + uy * s1 + ny * t1),
                                    (a[0] + ux * s0 + nx * t1, a[1] + uy * s0 + ny * t1)])
                left = rect(-20, -2, 2, L - 2)
                right = rect(w + 2, w + 20, 2, L - 2)
                if foot.intersection(left).area > 20 or foot.intersection(right).area > 20:
                    break
                # and beyond the depth the floor must widen on at least one side
                l2 = rect(-20, -2, L + 2, L + 14)
                r2 = rect(w + 2, w + 20, L + 2, L + 14)
                if foot.intersection(l2).area > 100 or foot.intersection(r2).area > 100:
                    found = L
                    break
            if found:
                nook = rect(-1, w + 1, -1, found)
                if foot.area - foot.intersection(nook).area > 20000:
                    res.append(nook)
    _nook_cache[si] = res
    return res


def sector_faces(si):
    s = S[si]
    flats = collections.defaultdict(list)
    sloped = []
    cuts = list(nooks_of(si)) + [box(*b) for b in OV.CUT.get(si, ())]
    cut = unary_union(cuts) if cuts else None
    for fi in s['floor_faces']:
        f = F[fi]
        p = fpts(f)
        P = poly2(f)
        if P is not None and cut is not None:
            P = P.difference(cut)
        if P is None or P.area <= 0:
            continue
        zs = [q[2] for q in p]
        if max(zs) - min(zs) <= 2 and round(sum(zs) / len(zs)) in OV.DROP_Z.get(si, ()):
            continue
        if max(zs) - min(zs) > 2 and si in OV.FLATTEN:
            flats[OV.FLATTEN[si]].append(P)
            continue
        if max(zs) - min(zs) <= 2:
            flats[round(sum(zs) / len(zs))].append(P)
        else:
            sloped.append((P, p))
    return flats, sloped


def ceiling_of(si, poly=None):
    """The ceiling height that covers most of the sector (or of the part over `poly`)."""
    ce = collections.Counter()
    hi = None
    for fi in S[si]['ceiling_faces']:
        f = F[fi]
        p = fpts(f)
        P = poly2(f)
        if P is None:
            continue
        if poly is not None:
            a = P.intersection(poly).area
        else:
            a = P.area
        if a <= 1:
            continue
        zs = [q[2] for q in p]
        ce[round(max(zs))] += a
    if not ce:
        return None
    return max(ce.items(), key=lambda t: t[1])[0]


def ceiling_tiers(si, poly):
    """A flat room's ceiling: the lowest level tier that covers a fifth of it, and the higher tiers as raised parts."""
    tiers = collections.defaultdict(list)
    for fi in S[si]['ceiling_faces']:
        f = F[fi]
        zs = [q[2] for q in fpts(f)]
        if max(zs) - min(zs) > 2:
            continue
        P = poly2(f)
        if P is None:
            continue
        P = P.intersection(poly)
        if P.area > 1:
            tiers[round(max(zs))].append(P)
    areas = {z: sum(p.area for p in v) for z, v in tiers.items()}
    if sum(areas.values()) < 0.5 * poly.area:
        # mostly a sloping vault: the height half of it lies under, with its level crown as the one raised part
        hs = []
        for fi in S[si]['ceiling_faces']:
            f = F[fi]
            P = poly2(f)
            if P is None:
                continue
            a = P.intersection(poly).area
            if a > 1:
                zs = [q[2] for q in fpts(f)]
                hs.append((sum(zs) / len(zs), a))
        hs.sort()
        acc, tot, main = 0, sum(a for z, a in hs), None
        for z, a in hs:
            acc += a
            if acc >= tot * 0.5:
                main = int(round(z))
                break
        raised = []
        if main is None:
            return ceiling_of(si, poly), []
        top = max(areas) if areas else main
        if top > main + 64 and areas[top] >= max(0.04 * poly.area, 20000):
            u = unary_union(tiers[top]).intersection(poly.buffer(-OV.CEILING_INSET))
            ps = polys(u)
            if ps:
                p = max(ps, key=lambda q: q.area)
                raised.append({'outline': [list(q) for q in outline_of(Polygon(p.exterior), 16)], 'ceiling': top})
        return main, raised
    big = [z for z in sorted(areas) if areas[z] >= 0.2 * poly.area]
    main = big[0] if big else max(areas.items(), key=lambda t: t[1])[0]
    raised = []
    inner = poly.buffer(-OV.CEILING_INSET)
    for z in sorted(areas):
        if z > main + 16 and areas[z] >= max(0.03 * poly.area, 20000):
            u = unary_union(tiers[z]).intersection(inner)
            for p in polys(u):
                if p.area >= 20000:
                    raised.append({'outline': [list(q) for q in outline_of(Polygon(p.exterior), 16)], 'ceiling': z})
    return main, raised


def ceil_at(si, poly):
    """The highest point of the sector's ceiling over `poly`, reading sloped ceiling faces where they are."""
    best = None
    for fi in S[si]['ceiling_faces']:
        f = F[fi]
        P = poly2(f)
        if P is None:
            continue
        inter = P.intersection(poly)
        if inter.is_empty or inter.area <= 1:
            continue
        n = nrm(f)
        p0 = fpts(f)[0]
        zs = [q[2] for q in fpts(f)]
        if abs(n[2]) < 0.05:
            continue
        d = n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]
        for g in polys(inter):
            for x, y in g.exterior.coords:
                z = (d - n[0] * x - n[1] * y) / n[2]
                z = min(max(z, min(zs)), max(zs))
                if best is None or z > best:
                    best = z
    return None if best is None else int(round(best))


def is_frame(si):
    """A door-frame sector: two parallel upright portals a wall's thickness apart and nothing else to stand in."""
    if si in OV.NOT_FRAME:
        return None
    s = S[si]
    pf = s['portal_faces']
    if len(pf) != 2:
        return None
    a, b = F[pf[0]], F[pf[1]]
    na, nb = nrm(a), nrm(b)
    if abs(na[2]) > 0.1 or abs(nb[2]) > 0.1:
        return None
    if abs(na[0] * nb[0] + na[1] * nb[1]) < 0.99:
        return None
    pa, pb = fpts(a), fpts(b)
    d = abs(sum((pb[0][k] - pa[0][k]) * na[k] for k in range(2)))
    if d > 200 and si not in OV.FORCE_FRAME:
        return None
    oa = a['room_behind'] if a['room'] == si else a['room']
    ob = b['room_behind'] if b['room'] == si else b['room']
    if oa == ob:
        return None
    wmax = 0
    for q in (pa, pb):
        wmax = max(wmax, max(math.hypot(u[0] - v[0], u[1] - v[1]) for u in q for v in q))
    za = min(q[2] for q in pa)
    zb = min(q[2] for q in pb)
    if abs(za - zb) > 4 and abs(za - zb) <= 80 and si not in OV.FORCE_FRAME:
        # its floor is a step between the two rooms: a room of its own, or the party could not climb through
        return None
    area = sum(poly2(F[fi]).area for fi in s['floor_faces'] if poly2(F[fi]) is not None)
    if area > d * wmax * 1.6 + 2000 and si not in OV.FORCE_FRAME:
        return None
    return (oa, ob, d)


def decompose(si):
    """Rooms of one sector."""
    flats, sloped = sector_faces(si)
    allp = [P for v in flats.values() for P in v] + [P for P, _ in sloped]
    if not allp:
        return []
    foot = unary_union(allp)
    terr = {z: unary_union(v) for z, v in flats.items()}
    slopeU = unary_union([P for P, _ in sloped]) if sloped else None
    slope_area = slopeU.area if slopeU is not None else 0
    dom = max(terr.items(), key=lambda t: t[1].area)[0] if terr else None
    dom_area = terr[dom].area if terr else 0
    second = sorted((t.area for z, t in terr.items() if z != dom), reverse=True)
    second_area = second[0] if second else 0
    mode = OV.MODE.get(si)
    if mode is None:
        mode = 'pieces'
    rooms = []
    if mode == 'single':
        k = 0
        for z in OV.SPLIT_Z.get(si, ()):
            for p in polys(terr[z]):
                k += 1
                poly = Polygon(p.exterior)
                rooms.append(Room('room:s%03d_%s' % (si, 'abcdefgh'[k - 1]), si, outline_of(poly), z, ceil_at(si, poly)))
            foot = foot.difference(terr[z].buffer(0.01))
            del terr[z]
        main = max(polys(foot), key=lambda p: p.area)
        if si in OV.CAVES and dom is not None:
            # a cave is its level floor; the rock banks that rise round it are its walls
            main = max(polys(terr[dom].buffer(1).buffer(-1)), key=lambda p: p.area)
        floor = OV.FLOOR.get(si, dom if dom is not None else round(min(p[2] for P, pp in sloped for p in pp)))
        cm, craised = ceiling_tiers(si, Polygon(main.exterior))
        ceil = OV.CEIL.get(si, cm)
        r = Room('room:s%03d' % si, si, outline_of(Polygon(main.exterior)), floor, ceil)
        r.fpoly = Polygon(main.exterior)
        if craised and si not in OV.NO_CEILING_LEVELS:
            r.extra['ceiling_levels'] = [c for c in craised if c['ceiling'] > ceil + 16]
        holes = []
        for h in main.interiors:
            hp = Polygon(h)
            if hp.area > 400 and not hp.buffer(-12).is_empty:
                holes.append(ring_pts(hp, 2.0))
        if holes:
            r.extra['holes'] = holes
        rooms.insert(0, r)
        if si in OV.CAVES and si not in OV.NO_BANKS:
            rooms += banks(si, r, max(polys(foot), key=lambda p: p.area), sloped)
        return rooms
    # pieces: flat terraces and ramps
    pieces = []  # dict(poly, kind, z, zlo, zhi, grad)
    for z, t in terr.items():
        for p in polys(t):
            pieces.append({'poly': p, 'kind': 'flat', 'z': z})
    if sloped:
        # group sloped faces that touch into ramps
        groups = []
        for P, pp in sloped:
            groups.append({'poly': P, 'pts': list(pp)})
        merged = True
        while merged:
            merged = False
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    inter = groups[i]['poly'].buffer(0.5).intersection(groups[j]['poly'].buffer(0.5))
                    if inter.area > 8:
                        groups[i] = {'poly': unary_union([groups[i]['poly'], groups[j]['poly']]),
                                     'pts': groups[i]['pts'] + groups[j]['pts']}
                        groups.pop(j)
                        merged = True
                        break
                if merged:
                    break
        for g in groups:
            pts = g['pts']
            # least squares plane z = a x + b y + c
            n = len(pts)
            mx = sum(p[0] for p in pts) / n
            my = sum(p[1] for p in pts) / n
            mz = sum(p[2] for p in pts) / n
            sxx = sum((p[0] - mx) ** 2 for p in pts)
            syy = sum((p[1] - my) ** 2 for p in pts)
            sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
            sxz = sum((p[0] - mx) * (p[2] - mz) for p in pts)
            syz = sum((p[1] - my) * (p[2] - mz) for p in pts)
            det = sxx * syy - sxy * sxy
            if abs(det) < 1e-6:
                a = sxz / sxx if sxx > 0 else 0
                b = syz / syy if syy > 0 else 0
            else:
                a = (sxz * syy - syz * sxy) / det
                b = (syz * sxx - sxz * sxy) / det
            for p in polys(g['poly']):
                pieces.append({'poly': p, 'kind': 'ramp', 'grad': (a, b), 'zlo': min(q[2] for q in pts),
                               'zhi': max(q[2] for q in pts)})
    # drop slivers into nothing
    pieces = [p for p in pieces if p['poly'].area >= OV.MIN_PIECE]
    # a ramp too short to stand on is a kerb, not a room
    def run_of(p):
        mr = p['poly'].minimum_rotated_rectangle
        c = list(mr.exterior.coords)
        return min(math.dist(c[0], c[1]), math.dist(c[1], c[2]))
    pieces = [p for p in pieces if p['kind'] != 'ramp' or run_of(p) >= 64]
    # so is a flat strip under 48 wide (the top of a door jamb, a kerb)
    pieces = [p for p in pieces if p['kind'] != 'flat' or run_of(p) >= 48]
    # merge runs of narrow flat steps into stairs
    pieces = merge_stairs(si, pieces)
    for pc in pieces:
        pc['ext'] = Polygon(pc['poly'].exterior)
    order = sorted(pieces, key=lambda p: -p['ext'].area)
    for pc in order:
        pc['parent'] = None
        pc['kids'] = []
    for i, pc in enumerate(order):
        # the smallest flat piece whose outer ring holds this one
        for j in range(i - 1, -1, -1):
            big = order[j]
            if big['kind'] != 'flat':
                continue
            if pc['poly'].difference(big['ext']).area < 0.02 * pc['poly'].area:
                if pc['parent'] is None or big['ext'].area < pc['parent']['ext'].area:
                    pc['parent'] = big
    for pc in order:
        if pc['parent'] is not None:
            pc['parent']['kids'].append(pc)
    k = 0
    for pc in order:
        if pc['parent'] is not None:
            continue
        poly = pc['ext']
        pts = outline_of(poly)
        rid = 'room:s%03d' % si + ('' if k == 0 else '_' + 'abcdefghijklmnopqrstuvwxyz'[k - 1] if k <= 26 else '_x%d' % k)
        k += 1
        if pc['kind'] == 'flat':
            cmain, craised = ceiling_tiers(si, poly)
            r = Room(rid, si, pts, pc['z'], cmain)
            r.fpoly = poly
            if craised and si not in OV.NO_CEILING_LEVELS:
                r.extra['ceiling_levels'] = craised
            levels, plats = [], []
            inner = poly.buffer(-16)
            for kid in pc['kids']:
                if kid['kind'] != 'flat':
                    r.notes += 'A ramp inside the room (to %d) is not drawn. ' % kid['zhi']
                    continue
                kp = kid['ext'].intersection(inner)
                if kp.is_empty or kp.geom_type != 'Polygon' or kp.area < 2000:
                    continue
                levels.append({'outline': [list(q) for q in outline_of(kp, 16)], 'floor': kid['z']})
                for g in kid['kids']:
                    if g['kind'] == 'flat' and g['z'] > kid['z'] and g['ext'].area >= 2000:
                        gp = g['ext'].buffer(-1)
                        plats.append({'outline': [list(q) for q in outline_of(gp, 16)], 'rise': g['z'] - kid['z']})
                    elif g['kind'] == 'flat' and g['ext'].area >= 2000:
                        r.notes += 'A floor at %d sunk inside the level at %d is not drawn (a level cannot hold another). ' % (g['z'], kid['z'])
            holes = []
            for hring in pc['poly'].interiors:
                hp = Polygon(hring)
                if hp.area > 400 and not hp.buffer(-12).is_empty and not any(k2['poly'].intersection(hp).area > 0.2 * hp.area for k2 in pc['kids']):
                    if poly.exterior.distance(hp) >= 32:
                        holes.append(ring_pts(hp, 2.0))
            if holes:
                r.extra['holes'] = holes
            if levels:
                r.extra['levels'] = levels
            if plats:
                r.extra['platforms'] = plats
        else:
            hull = poly.convex_hull
            if not is_convex(pts):
                pts = ring_pts(hull)
            gx, gy = pc['grad']
            gl = math.hypot(gx, gy) or 1
            # the wall at the high end: the edge whose outward normal points most up the slope
            best = None
            for i in range(len(pts)):
                a, b = pts[i], pts[(i + 1) % len(pts)]
                dx, dy = b[0] - a[0], b[1] - a[1]
                ln = math.hypot(dx, dy)
                ox, oy = dy / ln, -dx / ln
                sc = (ox * gx + oy * gy) / gl
                if best is None or sc > best[0] + 1e-6 or (abs(sc - best[0]) < 1e-6 and ln > best[2]):
                    best = (sc, i, ln)
            segs = OV.RAMP_SEGMENTS.get(si, 0)
            t = best[1]
            a, b = pts[t], pts[(t + 1) % len(pts)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy)
            ox, oy = dy / ln, -dx / ln
            vals = [p[0] * ox + p[1] * oy for p in pts]
            lo, hi = min(vals), max(vals)
            if segs == 0 and 'steps' not in pc and pc['zhi'] - pc['zlo'] >= 200 and len(pts) == 4:
                c_lo = ceil_at(si, poly.intersection(strip(ox, oy, lo, lo + (hi - lo) / 4)))
                c_hi = ceil_at(si, poly.intersection(strip(ox, oy, hi - (hi - lo) / 4, hi)))
                if c_lo is not None and c_hi is not None and abs(c_hi - c_lo) > 100:
                    segs = max(2, min(4, int(round((pc['zhi'] - pc['zlo']) / 180))))
            if segs > 1 and len(pts) == 4:
                for k2 in range(segs):
                    s0 = lo + (hi - lo) * k2 / segs
                    s1 = lo + (hi - lo) * (k2 + 1) / segs
                    part = poly.intersection(strip(ox, oy, round(s0), round(s1)))
                    ppts = outline_of(Polygon(part.exterior))
                    z0 = pc['zlo'] + (pc['zhi'] - pc['zlo']) * (round(s0) - lo) / (hi - lo)
                    z1 = pc['zlo'] + (pc['zhi'] - pc['zlo']) * (round(s1) - lo) / (hi - lo)
                    r = Room(rid + ('_r%d' % k2 if k2 else ''), si, ppts, int(round(z0)), None)
                    # the high wall of the part
                    bt = None
                    for i in range(len(ppts)):
                        pa, pb = ppts[i], ppts[(i + 1) % len(ppts)]
                        ddx, ddy = pb[0] - pa[0], pb[1] - pa[1]
                        l2 = math.hypot(ddx, ddy)
                        sc = (ddy / l2) * ox + (-ddx / l2) * oy
                        if bt is None or sc > bt[0]:
                            bt = (sc, i)
                    r.slope = {'to': int(round(z1)), 'toward': bt[1]}
                    r.ceiling = ceil_at(si, part)
                    r.extra['ramp_part'] = True
                    rooms.append(r)
                continue
            r = Room(rid, si, pts, pc['zlo'], None)
            r.slope = {'to': pc['zhi'], 'toward': best[1]}
            if 'steps' in pc:
                r.slope['steps'] = pc['steps']
            r.ceiling = ceil_at(si, poly)
        rooms.append(r)
    return rooms


def banks(si, cave, foot, sloped):
    """The rock banks that rise from a cave's level floor to its rim: one sloped room behind each wall of the cave's
    outline, as wide as the wall, rising away from it."""
    out = []
    inner = Polygon(cave.pts)
    bank = Polygon(foot.exterior).difference(inner.buffer(0.01))
    fr = frames_of(cave.pts)
    n = len(cave.pts)
    faces_bank = [f for f in fr]

    def is_bank(i):
        f = fr[i]
        mx = f['o'][0] + f['al'][0] * f['len'] / 2 + f['out'][0] * 12
        my = f['o'][1] + f['al'][1] * f['len'] / 2 + f['out'][1] * 12
        return bank.contains(Point(mx, my))

    flags = [is_bank(i) for i in range(n)]
    k = 0
    fext = Polygon(foot.exterior).buffer(6)
    for i in range(n):
        if not flags[i] or fr[i]['len'] < 96:
            continue
        a, b = cave.pts[i], cave.pts[(i + 1) % n]
        nx, ny = fr[i]['out']
        # The build keeps a sloped floor flat only when the wall it rises from and the wall it rises to are
        # parallel: the bank is the cave wall's own stretch pushed straight out (a parallelogram).
        cell = None
        for h in range(1500, 150, -50):
            u = (int(round(nx * h)), int(round(ny * h)))
            pts = [b, a, (a[0] + u[0], a[1] + u[1]), (b[0] + u[0], b[1] + u[1])]
            poly = Polygon(pts)
            if not poly.is_valid:
                continue
            if poly.intersection(fext).area >= 0.93 * poly.area and poly.intersection(inner).area < 50:
                cell = (pts, poly, h)
                break
        if cell is None:
            continue
        pts, poly, h = cell
        if any(poly.intersection(o.poly).area > 1 for o in out):
            # shorten until it clears its neighbour
            continue
        ztop = None
        for P, pp in sloped:
            if P.intersection(poly).area > 100:
                z = max(q[2] for q in pp)
                ztop = z if ztop is None else max(ztop, z)
        if ztop is None or ztop - cave.floor < 48:
            continue
        if ztop - cave.floor > 0.85 * h:
            ztop = int(cave.floor + 0.85 * h)
        k += 1
        r = Room('%s_bank%02d' % (cave.id, k), si, pts, int(ztop), None)
        r.slope = {'to': cave.floor, 'toward': 0}
        r.ceiling = max(ceil_at(si, poly) or cave.ceiling, int(ztop) + 128)
        r.extra['bank'] = True
        r.extra['ramp_part'] = True
        r.notes = 'A rock bank: the cave floor rises here to its rim. The original banks are one surface round the cave; a slope is a room of its own, so each stretch stands between walls. '
        out.append(r)
    return out


def strip(ox, oy, s0, s1):
    """The band of the plane between two distances along the direction (ox, oy)."""
    B = 1e6
    ax, ay = -oy, ox
    return Polygon([(ox * s0 - ax * B, oy * s0 - ay * B), (ox * s1 - ax * B, oy * s1 - ay * B),
                    (ox * s1 + ax * B, oy * s1 + ay * B), (ox * s0 + ax * B, oy * s0 + ay * B)])


def merge_stairs(si, pieces):
    """Runs of narrow flat steps, each at most 40 above the last, become one stepped piece."""
    flat = [p for p in pieces if p['kind'] == 'flat']
    other = [p for p in pieces if p['kind'] != 'flat']

    def depth(p):
        mr = p['poly'].minimum_rotated_rectangle
        c = list(mr.exterior.coords)
        return min(math.dist(c[0], c[1]), math.dist(c[1], c[2]))

    narrow = [p for p in flat if depth(p) <= OV.STEP_DEPTH.get(si, 160)]
    wide = [p for p in flat if p not in narrow]
    used = set()
    out = []
    narrow.sort(key=lambda p: p['z'])
    for i, p in enumerate(narrow):
        if i in used:
            continue
        run = [i]
        used.add(i)
        grown = True
        while grown:
            grown = False
            top = narrow[run[-1]]
            for j, q in enumerate(narrow):
                if j in used:
                    continue
                if 0 < q['z'] - top['z'] <= 40 and q['poly'].buffer(1).intersection(top['poly']).area > 8:
                    cand = unary_union([narrow[k]['poly'] for k in run] + [q['poly']])
                    if cand.geom_type == 'Polygon' and cand.convex_hull.area <= cand.area * 1.03:
                        run.append(j)
                        used.add(j)
                        grown = True
                        break
        if len(run) == 1:
            out.append(p)
            continue
        # The build's stepped room has its last riser in the wall at the high end: the run's top tread is that
        # wall's far side, a landing of its own (or part of the room above).
        top = narrow[run[-1]]
        out.append(top)
        c0 = narrow[run[0]]['poly'].centroid
        c1 = top['poly'].centroid
        run = run[:-1]
        u = unary_union([narrow[k]['poly'] for k in run]).convex_hull
        out.append({'poly': u, 'kind': 'ramp', 'grad': (c1.x - c0.x, c1.y - c0.y), 'zlo': narrow[run[0]]['z'],
                    'zhi': top['z'], 'steps': len(run)})
    return wide + out + other


# ---------------------------------------------------------------------------------------------------------------
def frames_of(pts):
    fr = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        fr.append({'o': a, 'al': (dx / ln, dy / ln), 'out': (dy / ln, -dx / ln), 'len': ln})
    return fr


def facing_pairs(A, B):
    """Every pair of facing parallel walls of two rooms as the build finds them, the build's choice first."""
    res = []
    fa, fb = frames_of(A.pts), frames_of(B.pts)
    for i, f in enumerate(fa):
        for j, g in enumerate(fb):
            if f['al'][0] * g['al'][0] + f['al'][1] * g['al'][1] > -1 + 1e-9:
                continue
            ox, oy = g['o'][0] - f['o'][0], g['o'][1] - f['o'][1]
            gap = ox * f['out'][0] + oy * f['out'][1]
            if gap < -EPS or gap > 512:
                continue
            ts = ox * f['al'][0] + oy * f['al'][1]
            lo, hi = max(0.0, ts - g['len']), min(f['len'], ts)
            if hi - lo > EPS:
                res.append({'i': i, 'j': j, 'gap': gap, 'lo': lo, 'hi': hi, 'f': f})
    best = None
    for r in res:
        if best is None or r['hi'] - r['lo'] > best['hi'] - best['lo'] + EPS:
            best = r
    return best, res


def edge_floor(room, i):
    """The floor height along wall i, or None when it rises along the wall."""
    if not room.slope:
        return room.floor
    t = room.slope['toward']
    fr = frames_of(room.pts)
    out = fr[t]['out']
    vals = [p[0] * out[0] + p[1] * out[1] for p in room.pts]
    lo, hi = min(vals), max(vals)
    a, b = room.pts[i], room.pts[(i + 1) % len(room.pts)]
    fa = (a[0] * out[0] + a[1] * out[1] - lo) / (hi - lo)
    fb = (b[0] * out[0] + b[1] * out[1] - lo) / (hi - lo)
    if abs(fa - fb) > 1e-6:
        return None
    if fa > 0.5:
        return room.slope['to']
    return room.floor


def build(wings=None):
    rooms = []
    by_sector = collections.defaultdict(list)
    frames = {}
    log = []
    for si in range(len(S)):
        if not S[si]['floor_faces']:
            continue
        if si in OV.SKIP:
            continue
        if wings is not None and OV.wing_of(si) not in wings:
            continue
        fr = is_frame(si)
        if fr:
            frames[si] = fr
            continue
        rs = decompose(si)
        for r in rs:
            r.name = OV.NAMES.get(si, 'Sector %d' % si)
            rooms.append(r)
            by_sector[si].append(r)
    # manual replacements of whole sectors
    for si, spec in OV.MANUAL.items():
        if wings is not None and OV.wing_of(si) not in wings:
            continue
        for r in by_sector.get(si, []):
            rooms.remove(r)
        by_sector[si] = []
        for k, sp in enumerate(spec):
            r = Room(sp['id'], si, [tuple(p) for p in sp['outline']], sp['floor'], sp['ceiling'])
            r.slope = sp.get('slope')
            r.name = sp.get('name', OV.NAMES.get(si, 'Sector %d' % si))
            r.notes = sp.get('notes', '')
            r.extra = {k2: v for k2, v in sp.items() if k2 in ('levels', 'platforms', 'pillars', 'flights', 'parapets', 'ceiling_levels', 'beams', 'theme', 'bands', 'walls', 'rough')}
            rooms.append(r)
            by_sector[si].append(r)
    for r in rooms:
        if r.ceiling is None or r.ceiling <= r.floor_high() + 64:
            log.append('ceiling of %s guessed (%s over floor %s)' % (r.id, r.ceiling, r.floor_high()))
            r.ceiling = r.floor_high() + 256
        if r.sector in OV.CEIL and len(by_sector[r.sector]) == 1:
            r.ceiling = OV.CEIL[r.sector]
    # ---- banks give way to every other room: under a room that stands over them they take its floor as ceiling
    kept_banks = []
    for r in [x for x in rooms if x.extra.get('bank')]:
        ok = True
        for o in rooms:
            if o is r or (o.extra.get('bank') and o not in kept_banks):
                continue
            if o.poly.intersects(r.poly) and o.poly.intersection(r.poly).area > 1:
                if o.floor_low() >= r.floor_high() + 128 and not o.extra.get('bank'):
                    r.ceiling = min(r.ceiling, int(o.floor_low()))
                elif o.floor_low() < r.ceiling and r.floor_low() < o.ceiling:
                    ok = False
                    break
        if ok:
            kept_banks.append(r)
        else:
            rooms.remove(r)
            by_sector[r.sector].remove(r)
            log.append('%s: a rock bank that would share space with %s is left solid' % (r.id, o.id))
    # ---- landings ------------------------------------------------------------------------------------------
    # The build joins two rooms through their longest pair of facing walls. Where a ramp or flight runs along the
    # room it also meets at its foot or head, that pair is the ramp's side, where no opening can be. A landing 48
    # deep cut from the ramp's end meets the room through the end wall instead.
    for A in list(rooms):
        if not A.slope or A.extra.get('ramp_part'):
            continue
        carved = set()
        for B in list(rooms):
            if B is A or B.poly.distance(A.poly) > 1:
                continue
            best, res = facing_pairs(A, B)
            if best is None or edge_floor(A, best['i']) is not None:
                continue
            alts = [r for r in res if edge_floor(A, r['i']) is not None and r['gap'] < 1 and r['hi'] - r['lo'] >= 64]
            if not alts:
                continue
            alt = max(alts, key=lambda r: r['hi'] - r['lo'])
            zend = edge_floor(A, alt['i'])
            if zend in carved:
                continue
            f = alt['f']
            fr = frames_of(A.pts)
            tw_out = fr[A.slope['toward']]['out']
            ox, oy = f['out']
            s_edge = f['o'][0] * ox + f['o'][1] * oy
            band = strip(ox, oy, s_edge - 48, s_edge + 1)
            piece = A.poly.intersection(band)
            rest = A.poly.difference(band)
            if piece.geom_type != 'Polygon' or rest.geom_type != 'Polygon' or rest.area < 4000:
                continue
            carved.add(zend)
            Lr = Room(A.id + ('_lo' if zend == A.floor else '_hi'), A.sector, outline_of(piece), zend, A.ceiling)
            Lr.name = A.name
            Lr.notes = 'A landing cut from the end of the slope beside it, so that the two meet the next room through an end wall.'
            rooms.append(Lr)
            by_sector[A.sector].append(Lr)
            A.pts = outline_of(rest)
            A.poly = Polygon(A.pts)
            bt = None
            for i, fr2 in enumerate(frames_of(A.pts)):
                sc = fr2['out'][0] * tw_out[0] + fr2['out'][1] * tw_out[1]
                if bt is None or sc > bt[0]:
                    bt = (sc, i)
            A.slope['toward'] = bt[1]
    # ---- openings from portals ---------------------------------------------------------------------------
    openings = []
    seen = set()

    def portal_info(fi):
        f = F[fi]
        p = fpts(f)
        xs = [q[0] for q in p]
        ys = [q[1] for q in p]
        zs = [q[2] for q in p]
        n = nrm(f)
        # plan segment: the two extreme points
        best = None
        for a in p:
            for b in p:
                d = math.hypot(a[0] - b[0], a[1] - b[1])
                if best is None or d > best[0]:
                    best = (d, a, b)
        # height of the sides (lowest of the upper corners at either end) for arches
        if best[0] < 8:
            # A portal squeezed shut by a door that slides sideways: the doorway is as wide as the door's travel.
            for dd in DOORS:
                if set(f['vertices']) & set(dd['vertex_ids']):
                    dx, dy = dd['direction']['x'] / 65536, dd['direction']['y'] / 65536
                    ln = dd['move_length']
                    still = [q for i, q in zip(f['vertices'], p) if i not in dd['vertex_ids']] or p
                    a0 = still[0]
                    # the leaf's edge travels from the jamb by the door's length, toward or away from its direction
                    b0 = (a0[0] - dx * ln, a0[1] - dy * ln, a0[2])
                    best = (ln, a0, b0)
                    break
        # an arched portal: its sides end lower than its point
        side = None
        if len(p) > 4 and best[0] >= 8:
            ends = []
            for e in (best[1], best[2]):
                ends.append(max(q[2] for q in p if math.hypot(q[0] - e[0], q[1] - e[1]) < 2))
            side = max(ends)
        return {'face': fi, 'a': best[1], 'b': best[2], 'w': best[0], 'z0': min(zs), 'z1': max(zs), 'side': side,
                'c': ((best[1][0] + best[2][0]) / 2, (best[1][1] + best[2][1]) / 2), 'n': n, 'pts': p}

    def room_at(si, pinfo, other=None):
        """The room of sector si whose outline the portal lies on."""
        cands = by_sector.get(si, [])
        best = None
        seg = LineString([pinfo['a'][:2], pinfo['b'][:2]])
        for r in cands:
            if r.extra.get('bank'):
                continue
            d = r.poly.exterior.distance(Point(pinfo['c']))
            ov = r.poly.exterior.buffer(2).intersection(seg).length
            zfit = 0 if r.floor_low() - 45 <= pinfo['z0'] <= r.ceiling else 1
            zd = min(abs(pinfo['z0'] - r.floor_low()), abs(pinfo['z0'] - r.floor_high()))
            if r.floor_low() <= pinfo['z0'] <= r.floor_high():
                zd = 0
            key = (zfit, 0 if ov >= 30 else 1, int(zd // 60), -round(ov), d)
            if best is None or key < best[0]:
                best = (key, r)
        return best[1] if best else None

    pairs = []
    for fi, f in enumerate(F):
        if not f['is_portal']:
            continue
        a, b = f['room'], f['room_behind']
        if fi in seen:
            continue
        pairs.append((fi, a, b))
    done_frames = set()
    links = []  # (roomA, roomB, pinfo, depthnote)
    for fi, a, b in pairs:
        pi = portal_info(fi)
        if abs(pi['n'][2]) > 0.5:
            log.append('portal face %d between sectors %d and %d lies flat (an opening in a floor): not drawn' % (fi, a, b))
            continue
        if a in frames or b in frames:
            fs = a if a in frames else b
            if fs in done_frames:
                continue
            done_frames.add(fs)
            oa, ob, d = frames[fs]
            pfs = [portal_info(x) for x in S[fs]['portal_faces']]
            # the narrower of the frame's two portals is the doorway
            pm = min(pfs, key=lambda q: (q['w'], q['z1'] - q['z0']))
            pa = [q for q in pfs if (F[q['face']]['room'] if F[q['face']]['room'] != fs else F[q['face']]['room_behind']) == oa][0]
            pb = [q for q in pfs if q is not pa][0]
            if oa in frames or ob in frames:
                log.append('frame %d joins another frame: not drawn' % fs)
                continue
            ra, rb = room_at(oa, pa), room_at(ob, pb)
            if ra is None or rb is None:
                if (wings is None):
                    log.append('frame %d: a side has no room (%s, %s)' % (fs, oa, ob))
                continue
            links.append((ra, rb, pm, 'frame sector %d' % fs, pa, pb))
            continue
        ra, rb = room_at(a, pi), room_at(b, pi)
        if ra is None or rb is None:
            if wings is None:
                log.append('portal %d: a side has no room (%d, %d)' % (fi, a, b))
            continue
        links.append((ra, rb, pi, '', pi, pi))
    for (ia, ib, cx, cy, w, z0, z1, why) in OV.EXTRA_OPENINGS:
        ra = [r for r in rooms if r.id == ia]
        rb = [r for r in rooms if r.id == ib]
        if ra and rb:
            pi = {'face': -1, 'a': (cx - w / 2, cy, z0), 'b': (cx + w / 2, cy, z0), 'w': w, 'z0': z0, 'z1': z1,
                  'c': (cx, cy), 'n': (0, 1, 0), 'pts': [], 'side': None}
            links.append((ra[0], rb[0], pi, why, pi, pi))
    # inside a sector: neighbouring pieces are open to each other
    for si, rs in by_sector.items():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if (rs[i].id, rs[j].id) in OV.NO_JOIN or (rs[j].id, rs[i].id) in OV.NO_JOIN:
                    continue
                if rs[i].extra.get('bank') and rs[j].extra.get('bank'):
                    continue
                best, res = facing_pairs(rs[i], rs[j])
                if best and best['gap'] < 1 and best['hi'] - best['lo'] >= 32:
                    links.append((rs[i], rs[j], None, 'pieces of sector %d' % si, None, None))
    used_walls = collections.defaultdict(list)
    n_op = 0
    for ra, rb, pi, why, pa, pb in links:
        if ra is rb:
            continue
        oid = 'open:%s_%s' % (ra.id.split(':')[1], rb.id.split(':')[1])
        base = oid
        k = 2
        while oid in seen:
            oid = '%s_%d' % (base, k)
            k += 1
        best, res = facing_pairs(ra, rb)
        if best is None:
            log.append('%s: no facing parallel walls between %s and %s (%s)' % (oid, ra.id, rb.id, why))
            continue
        fa_ = edge_floor(ra, best['i'])
        fb_ = edge_floor(rb, best['j'])
        if fa_ is None or fb_ is None:
            log.append('%s: the wall the build would choose runs along a slope (%s)' % (oid, why))
            continue
        bottom = max(fa_, fb_)
        top_max = min(ra.ceiling, rb.ceiling)
        f = best['f']
        o = {'id': oid, 'from': ra.id, 'to': rb.id}
        shared = best['hi'] - best['lo']
        if pi is None:
            o['width'] = 'full'
            o['height'] = 'full'
            lo, hi = best['lo'], best['hi']
        else:
            sc = (pi['c'][0] - f['o'][0]) * f['al'][0] + (pi['c'][1] - f['o'][1]) * f['al'][1]
            # is the portal on the wall pair the build will choose?
            off = abs((pi['c'][0] - f['o'][0]) * f['out'][0] + (pi['c'][1] - f['o'][1]) * f['out'][1])
            if off > best['gap'] + 8 or sc < best['lo'] - 8 or sc > best['hi'] + 8:
                log.append('%s: the original doorway at %d,%d is not on the pair of walls the build chooses (longest shared stretch); drawn where the build puts it' % (oid, pi['c'][0], pi['c'][1]))
                sc = (best['lo'] + best['hi']) / 2
            w = pi['w']
            if w >= shared - 1:
                o['width'] = 'full'
                lo, hi = best['lo'], best['hi']
            else:
                if w + 32 > shared:
                    w = shared - 32
                w = int(w)
                if w < 32:
                    log.append('%s: only %.0f of shared wall; not drawn (%s)' % (oid, shared, why))
                    continue
                o['width'] = w
                c = min(max(sc, best['lo'] + 16 + w / 2), best['hi'] - 16 - w / 2)
                o['along'] = round((c - best['lo']) / shared, 4)
                lo = round(c - w / 2)
                hi = lo + w
            z0, z1 = pi['z0'], pi['z1']
            sill = z0 - bottom
            if sill > 4:
                o['sill'] = int(round(sill))
            else:
                sill = 0
            h = z1 - (bottom + sill)
            for rr in (ra, rb):
                # a doorway taller than the room's main ceiling: the room is at least that high where it stands
                if z1 > rr.ceiling and not rr.extra.get('bank'):
                    cmax = ceil_at(rr.sector, rr.poly)
                    if cmax is not None and cmax >= z1 - 1:
                        rr.ceiling = int(z1)
                        if rr.extra.get('ceiling_levels'):
                            rr.extra['ceiling_levels'] = [c for c in rr.extra['ceiling_levels'] if c['ceiling'] > rr.ceiling + 16]
            top_max = min(ra.ceiling, rb.ceiling)
            if bottom + sill + h > top_max:
                h = top_max - bottom - sill
            if h < 48:
                log.append('%s: opening only %d high between floors %s/%s and ceilings %s/%s; not drawn (%s)' % (oid, h, fa_, fb_, ra.ceiling, rb.ceiling, why))
                continue
            side = pi.get('side')
            if side is not None and z1 - side >= 24 and side - (bottom + sill) >= 64 and bottom + sill + h >= z1 - 1 \
                    and z1 <= top_max - 16:
                o['shape'] = 'arch'
                o['height'] = int(side - (bottom + sill))
                o['apex'] = int(h)
            elif abs(top_max - (bottom + sill + h)) < 1 and o['width'] == 'full':
                o['height'] = 'full'
            else:
                o['height'] = int(h)
        # holes in one wall may not overlap along it, whatever their heights
        clash = False
        for key, (l2, h2, oid2) in [((ra.id, best['i']), x) for x in used_walls[(ra.id, best['i'])]]:
            if lo < h2 + 16 and l2 < hi + 16:
                clash = oid2
        tlo = None
        if clash:
            log.append('%s: stands over or under %s in the same wall of %s; a wall takes one opening per stretch, not drawn (%s)' % (oid, clash, ra.id, why))
            continue
        # the same test on the far room's wall, in its own coordinates
        g = frames_of(rb.pts)[best['j']]
        ts = (g['o'][0] - f['o'][0]) * f['al'][0] + (g['o'][1] - f['o'][1]) * f['al'][1]
        blo, bhi = ts - hi, ts - lo
        for (l2, h2, oid2) in used_walls[(rb.id, best['j'])]:
            if blo < h2 + 16 and l2 < bhi + 16:
                clash = oid2
        if clash:
            log.append('%s: stands over or under %s in the same wall of %s; not drawn (%s)' % (oid, clash, rb.id, why))
            continue
        used_walls[(ra.id, best['i'])].append((lo, hi, oid))
        used_walls[(rb.id, best['j'])].append((blo, bhi, oid))
        seen.add(oid)
        if why:
            o['notes'] = why
        o['_gap'] = best['gap']
        openings.append(o)
    return rooms, openings, frames, log, by_sector


TEXSIZE = {}


def tex_size(name):
    if name not in TEXSIZE:
        import subprocess
        o = subprocess.run(['/home/pjasicek/github/OpenYAMM/openyamm-studio/build/oymap', 'assets', name, '--assets',
                            '/home/pjasicek/github/OpenYAMM/assets_dev', '--world', 'mm6', '--kind', 'texture'],
                           capture_output=True, text=True).stdout
        sz = None
        try:
            for t in json.loads(o)['textures']:
                if t['name'].lower() == name:
                    sz = t['size']
        except Exception:
            pass
        TEXSIZE[name] = sz
    return TEXSIZE[name]


def surfaces(rooms, openings):
    """Reads each room's floor, ceiling and wall textures off the original: the floor and ceiling by area over the
    room, each wall by looking out through it at eye height from three places."""
    import numpy as np
    import cmp as C
    om = {'vertices': V, 'faces': F}
    A, B, Cc, T, FI = C.tris(om, skip=LEAF)
    themes = {}
    holes = collections.defaultdict(list)
    for o in openings:
        pass
    origins, dirs, meta = [], [], []
    for r in rooms:
        fr = frames_of(r.pts)
        z = r.floor_low() + min(160, (r.ceiling - r.floor_low()) * 0.5)
        for i, f in enumerate(fr):
            for t in (0.25, 0.5, 0.75):
                x = f['o'][0] + f['al'][0] * f['len'] * t - f['out'][0] * 10
                y = f['o'][1] + f['al'][1] * f['len'] * t - f['out'][1] * 10
                zz = z
                if r.slope:
                    zz = (r.floor + r.slope['to']) / 2 + 120
                origins.append((x, y, zz)); dirs.append((f['out'][0], f['out'][1], 0.0)); meta.append((r, i))
    dist, idx = C.cast(A, B, Cc, np.array(origins, float), np.array(dirs, float))
    votes = collections.defaultdict(collections.Counter)
    for (r, i), d, k in zip(meta, dist, idx):
        lim = 700 if r.sector in OV.CAVES else 140
        if k >= 0 and d <= lim and T[k] not in OV.NOT_WALL_TEXTURES:
            votes[(r.id, i)][T[k]] += 1
    for r in rooms:
        fl = collections.Counter(); ce = collections.Counter()
        poly = getattr(r, 'fpoly', r.poly)
        for fi in S[r.sector]['floor_faces']:
            P = poly2(F[fi])
            if P is not None:
                a = P.intersection(poly).area
                if a > 1:
                    fl[F[fi]['texture'].lower()] += a
        for fi in S[r.sector]['ceiling_faces']:
            P = poly2(F[fi])
            if P is not None:
                a = P.intersection(poly).area
                if a > 1:
                    ce[F[fi]['texture'].lower()] += a
        wl = collections.Counter()
        fr = frames_of(r.pts)
        per = {}
        for i, f in enumerate(fr):
            v = votes.get((r.id, i))
            if v:
                t = v.most_common(1)[0][0]
                per[i] = t
                wl[t] += f['len']
        wall = wl.most_common(1)[0][0] if wl else 'd2wctra'
        floor = fl.most_common(1)[0][0] if fl else 'crdrf2'
        ceil = ce.most_common(1)[0][0] if ce else 'd2ceil3'
        for t in (wall, floor, ceil):
            if tex_size(t) is None:
                wall, floor, ceil = [x if tex_size(x) else d for x, d in ((wall, 'd2wctra'), (floor, 'crdrf2'), (ceil, 'd2ceil3'))]
        key = (wall, floor, ceil)
        themes.setdefault(key, 0)
        themes[key] += 1
        r.theme_key = key
        ws = []
        for i, t in sorted(per.items()):
            if t != wall and tex_size(t):
                ws.append({'wall': i, 'surface': {'texture': t, 'size': tex_size(t)}})
        if ws and not r.extra.get('walls'):
            r.extra['walls'] = ws
    return themes


def theme_id(key):
    if key == ('d2wctra', 'crdrf2', 'd2ceil3'):
        return 'theme:darkmoor'
    return 'theme:' + '_'.join(key)


def fmt_pts(pts):
    return '[' + ', '.join('[%d, %d]' % (p[0], p[1]) for p in pts) + ']'


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def emit(rooms, openings, path):
    out = ['format: 0']
    themes = surfaces(rooms, openings)
    out.append('themes:')
    for key in sorted(themes, key=lambda k: theme_id(k)):
        out.append('  - id: %s' % theme_id(key))
        out.append('    wall: {texture: %s, size: %s}' % (key[0], tex_size(key[0])))
        out.append('    floor: {texture: %s, size: %s}' % (key[1], tex_size(key[1])))
        out.append('    ceiling: {texture: %s, size: %s}' % (key[2], tex_size(key[2])))
        out.append('    notes: "%s: walls %s, floor %s, ceiling %s, read off the original; %d room(s)."' % (
            'The castle stone, about 98 %% of the original by area' if theme_id(key) == 'theme:darkmoor' else 'Variant',
            key[0], key[1], key[2], themes[key]))
    out.append('defaults: {theme: theme:darkmoor, ambient: 13}')
    out.append('rooms:')
    for r in sorted(rooms, key=lambda r: r.id):
        out.append('  - id: %s' % r.id)
        out.append('    name: %s' % q(r.name))
        out.append('    outline: %s' % fmt_pts(r.pts))
        out.append('    floor: %d' % r.floor)
        if r.slope:
            s = '{to: %d, toward: %d' % (r.slope['to'], r.slope['toward'])
            if r.slope.get('steps'):
                s += ', steps: %d' % r.slope['steps']
            out.append('    slope: ' + s + '}')
        out.append('    ceiling: %d' % r.ceiling)
        th = r.extra.get('theme') or OV.THEME_OF.get(r.sector) or theme_id(r.theme_key)
        if th and th != 'theme:darkmoor':
            out.append('    theme: %s' % th)
        for key, val in OV.FEATURES.get(r.id, {}).items():
            r.extra[key] = list(r.extra.get(key, [])) + val
        for key in ('rough', 'bands', 'walls', 'pillars', 'platforms', 'levels', 'ceiling_levels', 'flights', 'parapets', 'beams'):
            if r.extra.get(key):
                out.append('    %s: %s' % (key, json.dumps(r.extra[key])))
        if r.extra.get('holes') and not r.extra.get('pillars'):
            out.append('    pillars:')
            for h in r.extra['holes']:
                out.append('      - {outline: %s}' % fmt_pts(h))
        notes = r.notes or OV.NOTES.get(r.sector, '')
        notes = ('Original sector %d. ' % r.sector + notes).strip()
        out.append('    notes: %s' % q(notes))
    out.append('openings:')
    for o in sorted(openings, key=lambda o: o['id']):
        out.append('  - id: %s' % o['id'])
        out.append('    from: %s' % o['from'])
        out.append('    to: %s' % o['to'])
        for k in ('along', 'width', 'height', 'sill', 'shape', 'apex'):
            if k in o:
                out.append('    %s: %s' % (k, o[k]))
        if o.get('notes'):
            out.append('    notes: %s' % q(o['notes']))
    open(path, 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    wings = None
    if '--wings' in sys.argv:
        wings = set(int(x) for x in sys.argv[sys.argv.index('--wings') + 1].split(','))
    rooms, openings, frames, log, by_sector = build(wings)
    emit(rooms, openings, L4 + 'rooms.yml')
    open(D + 'gen_log.txt', 'w').write('\n'.join(log) + '\n')
    json.dump({'rooms': [{'id': r.id, 'sector': r.sector, 'pts': r.pts, 'floor': r.floor, 'ceiling': r.ceiling,
                          'floor_high': r.floor_high(), 'slope': r.slope} for r in rooms],
               'frames': {str(k): v for k, v in frames.items()},
               'openings': [{k: v for k, v in o.items()} for o in openings]}, open(D + 'gen_rooms.json', 'w'))
    print('%d rooms from %d sectors, %d frames, %d openings, %d log lines' % (
        len(rooms), len(by_sector), len(frames), len(openings), len(log)))
