"""The planes' review geometry and measures (A6's planes sub-agent, 2026-11-21): space outlines from the design's
`at`/`extent`, link ribbons, the walkable mask, and the figures each NOTES, plan totals and board quote. For the review
only; L2 draws the studio's own geometry from the plan's `at` and `extent`. After P5's geom.py (A5), not imported.
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import planes_design as D

RES = 32                        # units per pixel of the masks


class Plane:
    """One plane's design with its derived geometry."""

    def __init__(self, key):
        self.d = D.PLANES[key]
        self.key = key
        self.half = (self.d['room'][0] * 256, self.d['room'][1] * 256)
        self.space = {s['id']: s for s in self.d['spaces']}
        self.place = {p['id']: p for p in self.d['places']}
        self.polys = {s['id']: blob(s) for s in self.d['spaces']}

    # -------------------------------------------------------------------------------------------- shapes
    def link_ends(self, link):
        """Rim to rim along the line between the two middles; `end_b` pins the far end (a gate on the rim)."""
        a, b = self.space[link['a']], self.space[link['b']]
        if 'end_b' in link:
            return ray_exit(self.polys[link['a']], a['at'], link['end_b']), tuple(link['end_b'])
        return ray_exit(self.polys[link['a']], a['at'], b['at']), ray_exit(self.polys[link['b']], b['at'], a['at'])

    def ribbons(self):
        return {l['id']: capsule(*self.link_ends(l), l['width']) for l in self.d['links']}

    def to_px(self, pt):
        return ((pt[0] + self.half[0]) / RES, (self.half[1] - pt[1]) / RES)

    def mask(self, polys):
        w, h = int(2 * self.half[0] / RES), int(2 * self.half[1] / RES)
        img = Image.new('L', (w, h), 0)
        dr = ImageDraw.Draw(img)
        for poly in polys:
            dr.polygon([self.to_px(p) for p in poly], fill=255)
        return np.array(img) > 0

    def walk_mask(self):
        return self.mask(list(self.polys.values()) + list(self.ribbons().values()))

    def floor_at(self, pt):
        for s in self.d['spaces']:
            if point_in(pt, self.polys[s['id']]):
                return s['floor']
        for l in self.d['links']:
            p, q = self.link_ends(l)
            dx, dy = q[0] - p[0], q[1] - p[1]
            L2 = dx * dx + dy * dy or 1.0
            t = ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / L2
            off = abs((pt[0] - p[0]) * dy - (pt[1] - p[1]) * dx) / math.sqrt(L2)
            if -0.05 <= t <= 1.05 and off <= l['width'] / 2 + 64:
                za, zb = self.space[l['a']]['floor'], self.space[l['b']]['floor']
                return za + (zb - za) * min(1, max(0, t))
        return None

    def space_of(self, pt):
        for s in self.d['spaces']:
            if point_in(pt, self.polys[s['id']]):
                return s['id']
        return None

    # -------------------------------------------------------------------------------------------- figures
    def walk_segments(self):
        pts = self.d['walk']
        out, total = [], 0.0
        for a, b in zip(pts, pts[1:]):
            n = length(a, b)
            out.append((a, b, total, n))
            total += n
        return out, total

    def along(self, pt):
        best = None
        for a, b, start, n in self.walk_segments()[0]:
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / (n * n)))
            q = (a[0] + dx * t, a[1] + dy * t)
            off = length(pt, q)
            if best is None or off < best[1]:
                best = (start + n * t, off)
        return best

    def figures(self):
        d = self.d
        f = {'plane': d['code'], 'name': d['name'], 'form': d['form']}
        walk = self.walk_mask()
        px = RES * RES
        f['room_cells'] = list(d['room'])
        f['room_units'] = [d['room'][0] * 512, d['room'][1] * 512]
        f['walkable_area_m'] = round(walk.sum() * px / 1e6, 1)
        room_px = walk.size
        f['walkable_share'] = round(walk.sum() / room_px, 3)
        ys, xs = np.nonzero(walk)
        f['floor_bbox_cells'] = [round((xs.max() - xs.min()) * RES / 512, 1),
                                 round((ys.max() - ys.min()) * RES / 512, 1)]
        if 'low' in d:
            # the basin's low ground (lava, scree, sea) inside the rim, round the walkable floors
            inside = self.crater_mask()
            low = inside & ~walk
            f['low_area_m'] = round(low.sum() * px / 1e6, 1)
            f['low_share'] = round(low.sum() / inside.sum(), 3)
            if d['low']['banks'] == 'all':
                # banks everywhere but the protected set (P-2): the distance to the nearest ground that is not low
                # and not the sleeper's chamber or the gate's link (P1's lava)
                gate = [r for l, r in zip(d['links'], self.ribbons().values()) if l.get('gate')]
                ways = walk & ~self.mask([self.polys['room:chamber']] + gate)
                dist = ndimage.distance_transform_edt(~ways) * RES
            else:
                # ways out on every terrace and walk but the test's arena, the sleeper's chamber and the gate between
                ways = self.mask([self.polys[s['id']] for s in d['spaces'] if s['id'] not in ('room:arena',
                                                                                             'room:chamber')]
                                 + [r for l, r in zip(d['links'], self.ribbons().values()) if not l.get('gate')])
                dist = ndimage.distance_transform_edt(~ways) * RES
            f['bank_max'] = int(round(dist[low].max()))
            f['bank_p90'] = int(round(np.percentile(dist[low], 90)))
            if d['element'] == 'fire':          # P1's measure.json keys (pair 1's board and NOTES)
                f['lava_area_m'], f['lava_share_of_crater'] = f['low_area_m'], f['low_share']
                f['lava_bank_max'], f['lava_bank_p90'] = f['bank_max'], f['bank_p90']
        else:
            f['sky_share'] = round(1 - f['walkable_share'], 3)
            f['island_gaps'] = self.island_gaps()
        # the walk: arrival -> test -> sleeper -> the return dais
        segs, total = self.walk_segments()
        f['walk_length'] = round(total)
        f['walk_seconds'] = {'walking': round(total / D.WALK_SPEED), 'running': round(total / (2 * D.WALK_SPEED))}
        stations = {}
        for pid in ('poi:statue', 'poi:test', 'gate:sleeper', 'poi:sleeper', 'exit:dais'):
            a, off = self.along(self.place[pid]['at'])
            stations[pid] = {'along': round(a), 'off_line': round(off)}
        f['stations'] = stations
        f['walk_legs'] = {
            'arrival_to_test': stations['poi:test']['along'],
            'test_to_sleeper': stations['poi:sleeper']['along'] - stations['poi:test']['along'],
            'sleeper_to_way_out': stations['exit:dais']['along'] - stations['poi:sleeper']['along'],
        }
        # hostiles and kill XP
        groups = []
        xp_party = 0
        levels = []
        for g in d['groups']:
            row = D.ROWS[g['row']]
            xp_party += D.xp(row['level']) * g['count']
            levels += [row['level']] * g['count']
            groups.append({'id': g['id'], 'actor': row['actor'], 'count': g['count'], 'level': row['level'],
                           'at': list(g['at']), 'space': self.space_of(g['at']) or
                           (g['space'] if g.get('swims') else 'link')})
        test_xp = 0
        test_count = 0
        for g in d['test_group']:
            row = D.ROWS[g['row']]
            test_xp += D.xp(row['level']) * g['count']
            test_count += g['count']
            levels += [row['level']] * g['count']
        f['groups'] = groups
        f['field_hostiles'] = sum(g['count'] for g in d['groups'])
        f['test_hostiles'] = test_count
        f['placed_hostiles'] = f['field_hostiles'] + test_count
        f['group_count'] = len(d['groups']) + 1
        f['group_sizes'] = sorted({g['count'] for g in d['groups']})
        f['levels'] = [min(levels), max(levels)]
        f['level_mean'] = round(sum(levels) / len(levels), 1)
        f['kill_xp_party'] = xp_party + test_xp
        f['kill_xp_per_member'] = round((xp_party + test_xp) / 4)
        f['kill_xp_target_per_member'] = round(D.TARGET_KILL_XP_PER_MEMBER)
        f['kill_xp_vs_target'] = round(f['kill_xp_per_member'] / D.TARGET_KILL_XP_PER_MEMBER - 1, 3)
        by_row = {}
        for g in d['groups']:
            by_row[g['row']] = by_row.get(g['row'], 0) + g['count']
        for g in d['test_group']:
            by_row[g['row']] = by_row.get(g['row'], 0) + g['count']
        f['by_row'] = {D.ROWS[k]['actor']: v for k, v in by_row.items()}
        # first fight and quiet ground
        arr = self.place['entrance:d7_fall']['at']
        firsts = sorted((length(arr, g['at']), g['id']) for g in d['groups'])
        first_at = next(g['at'] for g in d['groups'] if g['id'] == firsts[0][1])
        f['first_fight'] = {'straight': round(firsts[0][0]), 'group': firsts[0][1],
                            'along_walk': round(self.along(first_at)[0])}
        f['landing_hostiles'] = sum(1 for g in groups if g['space'] == 'room:landing')
        f['nearest_group_to_way_up'] = round(min(length(self.place['exit:way_up']['at'], g['at'])
                                                 for g in d['groups']))
        # POI census (D-20: bound events chained within 400; landmarks, gates and the arrival out)
        pois = [(p['id'], p['at']) for p in d['places'] if p['id'].startswith(('poi:', 'exit:'))]
        f['poi_census'] = census(pois)
        nn = sorted(min(length(a[1], b[1]) for b in pois if b is not a) for a in pois)
        f['poi_spacing'] = {'median': round(nn[len(nn) // 2]), 'min': round(nn[0]), 'max': round(nn[-1])}
        f['chests'] = sum(1 for p in d['places'] if p['kind'] == 'chest')
        f['hazard_cells'] = d['hazard']['count']
        f['hazard_on_critical'] = sum(1 for c in d['hazard']['cells'] if self.along(c)[1] < 384)
        f['hazard_on_links'] = sum(1 for c in d['hazard']['cells'] if self.space_of(c) is None)
        f['hazard_in_arena'] = sum(1 for c in d['hazard']['cells'] if self.space_of(c) == 'room:arena')
        f['hazard_in_chamber'] = sum(1 for c in d['hazard']['cells'] if self.space_of(c) == 'room:chamber')
        f['p2'] = self.p2_lips()
        swim = [g for g in d['groups'] if g.get('swims')]
        if swim:
            f['swimmer_homes'] = {g['id']: {sid: round(poly_distance(self.polys[sid], g['at']))
                                            for sid in ('room:landing', 'room:arena', 'room:chamber')}
                                  for g in swim}
        # sanity: every place and group stands on a floor
        f['off_floor'] = [p['id'] for p in d['places'] if self.floor_at(p['at']) is None
                          and p['kind'] not in ('landmark',)]
        f['off_floor'] += [g['id'] for g in d['groups'] if self.floor_at(g['at']) is None and not g.get('swims')]
        f['swimmers_on_floor'] = [g['id'] for g in d['groups'] if g.get('swims') and self.floor_at(g['at']) is not None]
        f['off_floor'] += [f'hazard{i}' for i, c in enumerate(d['hazard']['cells']) if self.floor_at(c) is None]
        f['links'] = {}
        for l in d['links']:
            p, q = self.link_ends(l)
            f['links'][l['id']] = {'length': round(length(p, q)), 'width': l['width'],
                                   'rise': self.space[l['b']]['floor'] - self.space[l['a']]['floor']}
        floors = [s['floor'] for s in d['spaces']]
        f['floors'] = [min(floors), max(floors)]
        f['places'] = {p['id']: list(p['at']) for p in d['places']}
        cam = d['camera']
        f['camera'] = {'at': list(cam['at']), 'z': (self.floor_at(cam['at']) or 0) + cam['eye'],
                       'yaw_deg': cam['yaw_deg'], 'fov': cam['fov']}
        return f

    def p2_lips(self):
        """P-2: what touches the sleeper's chamber and the gate's link beyond the gate, and how far each wall or lip
        stands over it. Samples every 32 along the outlines, 64 outside; returns per neighbour the smallest lip,
        and the nearest higher floor within the drop reach."""
        d = self.d
        gate = next(l for l in d['links'] if l.get('gate'))
        p, q = self.link_ends(gate)
        rib = capsule(p, q, gate['width'])
        za, zb = self.space[gate['a']]['floor'], self.space[gate['b']]['floor']
        flank = d['gate_flank']
        chamber = self.polys['room:chamber']
        zc = self.space['room:chamber']['floor']
        low = d['low']['level'] if 'low' in d else None
        rim_kind = d['rim']['kind'] if 'rim' in d else None
        rim = d['rim']['height'] if 'rim' in d else None
        out = {}

        def floor_of_link(pt):
            dx, dy = q[0] - p[0], q[1] - p[1]
            t = max(0.0, min(1.0, ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / (dx * dx + dy * dy)))
            return za + (zb - za) * t, t * length(p, q)

        def neighbour(pt):
            for sid, poly in self.polys.items():
                if sid != 'room:chamber' and point_in(pt, poly):
                    return sid, self.space[sid]['floor']
            for l in d['links']:
                if l is gate:
                    continue
                if point_in(pt, capsule(*self.link_ends(l), l['width'])):
                    return l['id'], self.floor_at(pt)
            if 'rim' in d and not self.inside_rim(pt):
                return 'rim', None
            if low is None:
                return 'sky', None
            return d['low']['id'], low

        def record(key, lip, what):
            e = out.setdefault(key, {'lip_min': None, 'samples': 0, 'what': what})
            e['samples'] += 1
            if lip is not None and (e['lip_min'] is None or lip < e['lip_min']):
                e['lip_min'] = int(round(lip))

        for poly, kind in ((chamber, 'chamber'), (rib, 'link')):
            for pt, normal in outline_samples(poly, 32):
                probe = (pt[0] + normal[0] * 64, pt[1] + normal[1] * 64)
                if point_in(probe, chamber) or point_in(probe, rib):
                    continue
                if kind == 'chamber':
                    z = zc
                    along = None
                else:
                    z, along = floor_of_link(pt)
                nid, nz = neighbour(probe)
                if nid == gate['a'] and kind == 'link' and along is not None and along <= flank['length']:
                    record('gate_flank', flank['height'], flank['what'])
                elif nid == 'rim':
                    record('rim', rim, f"the {rim_kind} ({rim:,} high)")
                elif nid == 'sky':
                    record('sky', None, 'open sky (nothing to climb from)')
                elif nz is None:
                    record(nid, None, nid)
                else:
                    record(nid, z - nz, nid)
        # "not by any drop": the nearest floor higher than the chamber's (or the link's) within the drop reach
        drops = []
        for sid, poly in self.polys.items():
            if sid == 'room:chamber' or self.space[sid]['floor'] <= zc - D.P2_MIN_LIP:
                continue
            gap = poly_gap(poly, chamber)
            drops.append({'space': sid, 'floor': self.space[sid]['floor'], 'gap': round(gap)})
        for sid, poly in self.polys.items():
            if sid in (gate['a'], 'room:chamber'):
                continue
            if self.space[sid]['floor'] > min(za, zb) - D.P2_MIN_LIP:
                drops.append({'space': sid, 'onto': 'gate link', 'floor': self.space[sid]['floor'],
                              'gap': round(poly_gap(poly, rib))})
        lips = [e['lip_min'] for e in out.values() if e['lip_min'] is not None]
        near = [x for x in drops if x['gap'] < D.DROP_REACH]
        return {'approaches': out, 'lip_min': min(lips) if lips else None, 'drops_within_reach': near,
                'higher_floors': sorted(drops, key=lambda x: x['gap'])[:3],
                'holds': (min(lips) if lips else 999) >= D.P2_MIN_LIP and not near}

    def inside_rim(self, pt):
        rx, ry = self.half[0] - 384, self.half[1] - 384
        return abs(pt[0] / rx) ** 3.2 + abs(pt[1] / ry) ** 3.2 <= 1.0

    def crater_mask(self):
        """Fire: the lava's extent, the room inside the rim (an ellipse-squircle 512 inside the room)."""
        w, h = int(2 * self.half[0] / RES), int(2 * self.half[1] / RES)
        yy, xx = np.mgrid[0:h, 0:w]
        x = (xx + 0.5) * RES - self.half[0]
        y = self.half[1] - (yy + 0.5) * RES
        rx, ry = self.half[0] - 384, self.half[1] - 384
        return (np.abs(x / rx) ** 3.2 + np.abs(y / ry) ** 3.2) <= 1.0

    def rim_poly(self, n=72):
        rx, ry = self.half[0] - 384, self.half[1] - 384
        out = []
        for i in range(n):
            a = 2 * math.pi * i / n
            c, s = math.cos(a), math.sin(a)
            r = (abs(c) ** 3.2 / rx ** 3.2 + abs(s) ** 3.2 / ry ** 3.2) ** (-1 / 3.2)
            out.append((r * c, r * s))
        return out

    def island_gaps(self):
        """Air: the smallest open-sky gap between two islands not joined by a bridge (no jump across)."""
        joined = {frozenset((l['a'], l['b'])) for l in self.d['links']}
        best = None
        ids = list(self.polys)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if frozenset((ids[i], ids[j])) in joined:
                    continue
                g = poly_gap(self.polys[ids[i]], self.polys[ids[j]])
                if best is None or g < best[0]:
                    best = (round(g), ids[i], ids[j])
        spans = sorted(round(length(*self.link_ends(l))) for l in self.d['links'])
        return {'min_unbridged_gap': best[0], 'between': best[1:], 'bridge_spans': [spans[0], spans[-1]]}


# ------------------------------------------------------------------------------------------------ helpers
def blob(space, points=28):
    """A squarish outline with a fixed-seed wobble (P5's clouds); halls and arenas rounder."""
    cx, cy = space['at']
    w, h = space['extent']
    rng = np.random.default_rng(space['seed'] * 7919)
    wobble = {'arena': (0.97, 1.03), 'hall': (0.95, 1.04)}.get(space.get('kind'), (0.86, 1.10))
    n = {'arena': 2.0, 'hall': 3.0}.get(space.get('kind'), 2.6)
    wob = rng.uniform(*wobble, points)
    wob = (wob + np.roll(wob, 1) + np.roll(wob, -1)) / 3.0
    out = []
    for i in range(points):
        a = 2 * math.pi * i / points + space['seed'] * 0.13
        c, s = math.cos(a), math.sin(a)
        r = (abs(c) ** n / (w / 2) ** n + abs(s) ** n / (h / 2) ** n) ** (-1 / n)
        out.append((cx + r * c * wob[i], cy + r * s * wob[i]))
    return out


def ray_exit(poly, origin, target):
    ox, oy = origin
    dx, dy = target[0] - ox, target[1] - oy
    best = None
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - ox) * ey - (ay - oy) * ex) / den
        u = ((ax - ox) * dy - (ay - oy) * dx) / den
        if 0 <= t <= 1 and 0 <= u <= 1 and (best is None or t < best):
            best = t
    if best is None:
        return origin
    return (ox + dx * best, oy + dy * best)


def nearest_on_poly(poly, pt):
    best = None
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / d2))
        q = (a[0] + dx * t, a[1] + dy * t)
        if best is None or length(pt, q) < best[0]:
            best = (length(pt, q), q)
    return best[1]


def capsule(p, q, width):
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d * width / 2, dx / d * width / 2
    return [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]


def length(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def point_in(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def poly_gap(pa, pb):
    def seg_dist(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        d2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / d2))
        return length(p, (a[0] + dx * t, a[1] + dy * t))
    best = 1e18
    for P, Q in ((pa, pb), (pb, pa)):
        for p in P:
            for i in range(len(Q)):
                best = min(best, seg_dist(p, Q[i], Q[(i + 1) % len(Q)]))
    return best


def outline_samples(poly, step):
    """Points every `step` along a closed outline with their outward normals (either winding)."""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly)))
    sign = 1.0 if area > 0 else -1.0
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        n = length(a, b)
        if n < 1:
            continue
        tx, ty = (b[0] - a[0]) / n, (b[1] - a[1]) / n
        normal = (ty * sign, -tx * sign)
        k = max(1, int(n // step))
        for j in range(k):
            t = (j + 0.5) / k
            out.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), normal))
    return out


def poly_distance(poly, pt):
    if point_in(pt, poly):
        return 0.0
    return length(pt, nearest_on_poly(poly, pt))


def census(points, merge=400):
    parent = list(range(len(points)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if length(points[i][1], points[j][1]) <= merge:
                parent[root(i)] = root(j)
    return len({root(i) for i in range(len(points))})
