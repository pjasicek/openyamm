#!/usr/bin/env python3
"""Ledge shots (D-123, F42 of reviews/PLAYER_FEEDBACK_20261124.md, XD-05 p5 "here seems to be an invisible wall"):
a walkable lip over a lower hall with ranged monsters, where a monster's thin line of sight to a party standing back
from the lip clears the lip but its shot (a missile of radius 16) does not.

  tools/xeen/check_ledge_shots.py [--maps xeen_xd05 ...] [--assets ROOT] [--cache DIR] [--json]
      (default: every xeen_*.blv with a scene; run whole-world checks through tools/heavy.sh 4)

The engine's monster sight is a ray (eye at 0.9 of its height to the party's eye at +160, IndoorWorldRuntime.cpp); its
arrow or bolt is a sphere of radius 16. Standing a little back from a lip, the party is seen and shot at, but every
shot strikes the lip (an arrow leaves no mark), and the party's own bolts at the monster strike the ledge's floor: an
"invisible wall" to the player. D-123 keeps the shared AI as it is (the original tests a thin line) and fixes the map:
a low parapet (64-96) on the lip, so a party back from it is not seen and one at it shoots and is shot over it.

What is measured (on the built BLV, `oymap export`):
- a lip: an edge of a walkable floor face (normal up) with a drop of 128 or more just beyond it (no floor within 128
  below, 24 outward) and no wall standing on it;
- party spots on the floor 60, 140 and 220 back from the lip (every 128 along it);
- shooters: the ranged hostiles of check_arrivals.py (placed actors, the BLV's spawn markers and scene spawns whose
  rows have a missile or a spell) within 5,120 of the lip. D-132 (2026-11-24): each from its own post (where it is
  placed, the marker's or spawn's centre) and from the spots it can move to: walkable faces within its leash
  (`leash_radius`, else 1,024 of its post; 2D) that its post's floor reaches by walking (floor faces joined by shared
  edges with a rise of at most 56, the engine's 50 step), 64 or more below the lip, 256 to 3,000 beyond it (each
  face's middle and its corners pulled a quarter in);
- the sight line from the monster's eye to the party's eye is clear of every solid face and passes within 16 of the
  lip's edge (the shot's radius): the ray sees, the shot dies on the lip.
  `ledge.thin_shot` (error): from a monster's own post. `ledge.thin_shot_move` (warning): only from a spot it can move
  to. Exit 1 on an error. Kept sites: KEPT below, with reasons.
Open-air maps (D7, P1-P4, X8; D-122) are skipped (flyers, a passing graze, the outdoor MM6-MM8 norm). D-132: no
rebuild round for this check; each map fixes its errors at its next rebuild (move the shooter first, a 64 parapet on
landings and lookouts, else KEPT with a reason).
"""
import argparse
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_arrivals as arrivals  # noqa: E402

SHOT_RADIUS = 16.0
SETBACKS = (60.0, 140.0, 220.0)
DROP = 128.0
OUT = 24.0
SPACING = 128.0
BELOW = 64.0
RANGE = 5120.0
SPOTS_WITHIN = 3000.0
SPOTS_OFF = 256.0   # a monster right under the lip shooting straight up is not the case
NO_LEASH = 1024.0   # D-132: how far a monster without a leash is taken to move from its post
STEP = 56.0         # the engine's step (MaximumRise 50) with rounding
# (map stem, rounded lip midpoint) -> reason; a kept site is listed as `kept`.
KEPT = {}


class Floors:
    """Walkable faces of a Geometry, with a fast floor lookup."""

    def __init__(self, geo):
        self.geo = geo
        self.idx = [i for i, n in enumerate(geo.normals) if n[2] > 0.7]
        self.lo = geo.lo[self.idx]
        self.hi = geo.hi[self.idx]

    def below(self, p, up=64.0, down=4096.0):
        """The highest floor z under p (within `up` above p.z and `down` below), or None."""
        hit = self.face_below(p, up, down)
        return hit and hit[0]

    def face_below(self, p, up=64.0, down=4096.0):
        """(z, k) of the highest floor under p (k: index into self.idx), or None."""
        x, y, z = p
        cand = np.nonzero((self.lo[:, 0] <= x) & (self.hi[:, 0] >= x) & (self.lo[:, 1] <= y) & (self.hi[:, 1] >= y))[0]
        best = None
        for k in cand:
            fi = self.idx[k]
            poly = self.geo.polys[fi]
            inside = False
            for e in range(len(poly)):
                x1, y1, x2, y2 = poly[e][0], poly[e][1], poly[(e + 1) % len(poly)][0], poly[(e + 1) % len(poly)][1]
                if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
            if not inside:
                continue
            n = self.geo.normals[fi]
            fz = (self.geo.ds[fi] - n[0] * x - n[1] * y) / n[2]
            if z - down <= fz <= z + up and (best is None or fz > best[0]):
                best = (fz, k)
        return best

    def walk_components(self):
        """A component number per floor face: faces joined where two edges overlap in plan (32 or more, collinear)
        with a rise of at most STEP between them at the overlap."""
        lines = {}
        for k, fi in enumerate(self.idx):
            poly = self.geo.polys[fi]
            for e in range(len(poly)):
                a, b = poly[e], poly[(e + 1) % len(poly)]
                d = b[:2] - a[:2]
                ln = float(np.hypot(*d))
                if ln < 8:
                    continue
                u = d / ln
                if u[0] < -1e-6 or (abs(u[0]) <= 1e-6 and u[1] < 0):
                    u = -u
                off = u[0] * a[1] - u[1] * a[0]
                key = (round(math.atan2(u[1], u[0]) * 200), round(off / 8))
                t1, t2 = float(u @ a[:2]), float(u @ b[:2])
                if t1 > t2:
                    t1, t2, a, b = t2, t1, b, a
                lines.setdefault(key, []).append((k, t1, t2, a[2], b[2]))
        parent = list(range(len(self.idx)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for edges in lines.values():
            edges.sort(key=lambda q: q[1])
            for i, (k1, s1, e1, za1, zb1) in enumerate(edges):
                for k2, s2, e2, za2, zb2 in edges[i + 1:]:
                    if s2 > e1 - 32:
                        break
                    if k1 == k2 or find(k1) == find(k2):
                        continue
                    lo, hi = max(s1, s2), min(e1, e2)
                    if hi - lo < 32:
                        continue
                    t = (lo + hi) / 2
                    z1 = za1 + (zb1 - za1) * (t - s1) / max(e1 - s1, 1e-6)
                    z2 = za2 + (zb2 - za2) * (t - s2) / max(e2 - s2, 1e-6)
                    if abs(z1 - z2) <= STEP:
                        parent[find(k1)] = find(k2)
        return [find(i) for i in range(len(self.idx))]


def segment_distance(p1, q1, p2, q2):
    """The shortest distance between segments p1q1 and p2q2 (3D)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a <= 1e-9 and e <= 1e-9:
        return float(np.linalg.norm(r))
    if a <= 1e-9:
        s, t = 0.0, min(max(f / e, 0.0), 1.0)
    else:
        c = d1 @ r
        if e <= 1e-9:
            t, s = 0.0, min(max(-c / a, 0.0), 1.0)
        else:
            b = d1 @ d2
            den = a * e - b * b
            s = min(max((b * f - c * e) / den, 0.0), 1.0) if den > 1e-9 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, min(max(-c / a, 0.0), 1.0)
            elif t > 1.0:
                t, s = 1.0, min(max((b - c) / a, 0.0), 1.0)
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def lips(geo, floors):
    """[(a, b, outward, z)]: floor edges with a drop beyond them."""
    out = []
    seen = set()
    for fi in floors.idx:
        poly = geo.polys[fi]
        centre = poly.mean(0)
        for e in range(len(poly)):
            a, b = poly[e], poly[(e + 1) % len(poly)]
            key = tuple(sorted((tuple(np.round(a)), tuple(np.round(b)))))
            if key in seen:
                continue
            seen.add(key)
            edge = b[:2] - a[:2]
            length = float(np.linalg.norm(edge))
            if length < 48 or abs(a[2] - b[2]) > 24:
                continue
            nrm = np.array([edge[1], -edge[0]]) / length
            if nrm @ (centre[:2] - a[:2]) > 0:
                nrm = -nrm
            z = (a[2] + b[2]) / 2
            mid = (a[:2] + b[:2]) / 2
            probe = mid + nrm * OUT
            fz = floors.below((probe[0], probe[1], z), up=DROP - 1, down=8192.0)
            if fz is not None and fz > z - DROP:
                continue
            inner = np.array([mid[0] - nrm[0] * 8, mid[1] - nrm[1] * 8, z + 48])
            outer = np.array([probe[0], probe[1], z + 48])
            if geo.blocked(inner, outer):
                continue
            out.append((np.array(a, float), np.array(b, float), nrm, z, length))
    return out


def check_map(world, stem, cache):
    if stem in arrivals.OPEN_AIR:
        return []
    scene = arrivals.load_yaml(os.path.join(world.xeen, 'maps', stem + '.scene.yml'))
    data = arrivals.export(stem, world.assets, cache)
    geo = arrivals.Geometry(data)
    floors = Floors(geo)
    shooters = [h for h in arrivals.hostiles(world, scene, stem + '.blv', data['map'].get('spawns') or [])
                if any(world.shoots(m) for m in h['rows'])]
    if not shooters:
        return []
    leash = {'actor %d' % a['actor_index']: a.get('leash_radius') or 0
             for a in scene['initial_state'].get('actors') or []}
    comp = floors.walk_components()
    low_spots, low_comp = [], []
    for k, fi in enumerate(floors.idx):
        poly = geo.polys[fi]
        c = poly.mean(0)
        for q in [c] + [c + 0.75 * (v - c) for v in poly]:
            low_spots.append(q)
            low_comp.append(comp[k])
    low_spots, low_comp = np.array(low_spots), np.array(low_comp)
    # the spots each shooter can move to: its leash circle, on floor its post walks to
    reach = {}
    for h in shooters:
        hit = floors.face_below(h['at'], up=64.0, down=256.0)
        radius = leash.get(h['id']) or NO_LEASH
        if hit is None:
            reach[h['id']] = np.zeros(len(low_spots), bool)
            continue
        d = np.hypot(low_spots[:, 0] - h['at'][0], low_spots[:, 1] - h['at'][1])
        reach[h['id']] = (low_comp == comp[hit[1]]) & (d <= radius)
    findings = {}
    for a, b, nrm, z, length in lips(geo, floors):
        mid = (a[:2] + b[:2]) / 2
        near = [h for h in shooters if math.dist(h['at'][:2], mid) <= RANGE]
        if not near:
            continue
        d2 = np.hypot(low_spots[:, 0] - mid[0], low_spots[:, 1] - mid[1])
        pick = (d2 <= SPOTS_WITHIN) & (low_spots[:, 2] <= z - BELOW) & ((low_spots[:, :2] - mid) @ nrm > SPOTS_OFF)
        # (spot, height, who, own post): the posts first, then each spot once with the tallest monster that reaches it
        spots = [(np.array(h['at'], float), h['height'], h, True) for h in near]
        movers = {}
        for h in near:
            for q in np.nonzero(pick & reach[h['id']])[0]:
                if q not in movers or h['height'] > movers[q][1]:
                    movers[q] = (low_spots[q], h['height'], h, False)
        spots += list(movers.values())
        steps = max(1, int(length // SPACING))
        for k in range(steps):
            f = (k + 0.5) / steps
            s = a[:2] + (b[:2] - a[:2]) * f
            for back in SETBACKS:
                p = s - nrm * back
                pz = floors.below((p[0], p[1], z), up=8.0, down=8.0)
                if pz is None:
                    continue
                eye = np.array([p[0], p[1], pz + arrivals.PARTY_EYE])
                for hp, height, h, own in spots:
                    if hp[2] > z - BELOW or math.dist(hp[:2], p) > RANGE or (hp[:2] - s) @ nrm <= 0:
                        continue
                    m_eye = hp + [0, 0, max(24.0, height * 0.9)]
                    gap = segment_distance(m_eye, eye, a, b)
                    if gap >= SHOT_RADIUS or geo.blocked(m_eye, eye):
                        continue
                    key = (round((a[0] + b[0]) / 2), round((a[1] + b[1]) / 2), round(z))
                    row = findings.setdefault(key, {'map': stem, 'lip': [list(np.round(a).astype(int)),
                                                                          list(np.round(b).astype(int))],
                                                    'z': round(z), 'spots': set(), 'monsters': {}, 'posts': {},
                                                    'example': None})
                    row['spots'].add((round(p[0]), round(p[1]), back))
                    who = '%s %s (%s) at (%d, %d, %d)' % (h['id'], h['name'], h['monster'], *h['at'])
                    if own:
                        row['posts'][h['id']] = who
                    else:
                        row['monsters'][h['id']] = who
                    better = row['example'] is None or (own and not row['example']['own']) or \
                        (own == row['example']['own'] and gap < row['example']['gap'])
                    if better:
                        row['example'] = {'party': [round(p[0]), round(p[1]), round(pz)], 'back': back,
                                          'monster': who if own else '%s moved to (%d, %d, %d)' % (who, *hp),
                                          'gap': round(gap, 1), 'own': own}
    out = []
    for key, row in sorted(findings.items()):
        row['spots'] = sorted(row['spots'])
        if (stem, key[:2]) in KEPT:
            row['rule'] = 'kept'
            row['reason'] = KEPT[(stem, key[:2])]
        else:
            row['rule'] = 'ledge.thin_shot' if row['posts'] else 'ledge.thin_shot_move'
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--maps', nargs='+')
    ap.add_argument('--assets', default=os.path.join(arrivals.ROOT, 'assets_dev'))
    ap.add_argument('--cache')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    world = arrivals.World(os.path.abspath(args.assets))
    if args.maps:
        stems = [m if m.startswith('xeen_') else 'xeen_' + m for m in args.maps]
    else:
        stems = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(world.xeen, 'maps', 'xeen_*.blv'))
                       if os.path.exists(p[:-4] + '.scene.yml') and os.path.basename(p)[:-4] not in arrivals.OPEN_AIR)
    rows = []
    for stem in stems:
        rows += check_map(world, stem, args.cache)
    if args.json:
        print(json.dumps(rows, indent=1, default=list))
    else:
        for r in rows:
            e = r['example']
            print('%s %s lip (%d, %d)-(%d, %d) at z %d: %d party spots, %d monsters from their posts, %d moved; e.g. '
                  'the party at (%d, %d, %d), %d back: the line from %s clears the lip by %.1f' % (
                      r['rule'], r['map'], *r['lip'][0][:2], *r['lip'][1][:2], r['z'], len(r['spots']),
                      len(r['posts']), len(r['monsters']), *e['party'], e['back'], e['monster'], e['gap']))
            for who in sorted(r['posts'].values()):
                print('    from its post: ' + who)
            if r['rule'] == 'kept':
                print('    kept: ' + r['reason'])
        errors = sorted({r['map'] for r in rows if r['rule'] == 'ledge.thin_shot'})
        warns = sorted({r['map'] for r in rows if r['rule'] == 'ledge.thin_shot_move'})
        print('%d maps (open-air skipped); %d lips with thin shots from a post (errors) on %d maps: %s; %d from spots a '
              'monster can move to (warnings) on %d maps: %s' % (
                  len(stems), sum(r['rule'] == 'ledge.thin_shot' for r in rows), len(errors), ' '.join(errors),
                  sum(r['rule'] == 'ledge.thin_shot_move' for r in rows), len(warns), ' '.join(warns)))
        return 1 if errors else 0
    return 1 if any(r['rule'] == 'ledge.thin_shot' for r in rows) else 0


if __name__ == '__main__':
    sys.exit(main())
