#!/usr/bin/env python3
"""Open-sky check of the Xeen BLVs (D-97; the user's F21, 2026-11-22: "I don't see the roof" in Castle Xeen).

Sky shows inside a BLV only over places meant to be outdoors (courtyards, battlements and wall walks, roof terraces,
open shafts and pits, sky bridges, the planes' open ground). Every enclosed room or corridor has a ceiling.

For every installed `assets_dev/worlds/xeen/maps/xeen_<key>.blv` with sky faces (IndoorSky, 0x00400000) this lists each
sector under sky: its room (`L4/ids.lock.yml`), name, floor area, wall height (floor to the sky faces), its narrowest
width under the sky, and its **open share**: how much of the sky's rim lies over an opening (a portal reaching the sky
whose sill is at most SILL_MAX over the floor) into another open-sky sector, rather than over a wall.

ERRORS:
- a sky sector whose room is not listed as deliberately open in `tools/xeen/open_sky.yml` (its kind and a line from
  the map's brief);
- **a walk closed on both sides**: a battlements, wall_walk or bridge whose open area (it and the sky sectors its low
  openings join) opens on no side (open share under OPEN_MIN): from inside it reads as a corridor whose roof is missing
  (Castle Xeen's wall walks, 768-high walls both sides of an 800-wide walk; Castle Basenji's battlement walk);
- **a roofless enclosure**: any other listed room whose open area opens on no side and is narrower than WIDE times its
  walls' height. Kinds shaft, pit, canopy, skylight and ravine are exempt.

- a `skylight` (a smoke hole, a crack, an open hatch) whose sky covers more than SKYLIGHT_MAX of its floor.

Usage: check_open_sky.py [<key> ...] [--json OUT]   exit 1 on any error. Kinds: open_sky.yml's header.
Sky set in walls (a view out over a parapet) or floors is counted, not judged.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OY = f'{R}/openyamm-studio/build-xeen/oymap'
SKY = 0x00400000
SILL_MAX = 320      # an opening whose sill is this high or lower shows what lies beyond it below the skyline
OPEN_MIN = 0.10     # under this share of its rim over openings, a sky area is closed in on every side
KINDS = {'courtyard', 'battlements', 'wall_walk', 'terrace', 'shaft', 'pit', 'bridge', 'open_ground', 'garden', 'ruin',
         'deck', 'crater', 'arena', 'canopy', 'skylight', 'ravine'}
NARROW_OK = {'shaft', 'pit', 'canopy', 'skylight', 'ravine'}   # a well of light, leaves, a hole in a roof, a rock slot
LINEAR = {'battlements', 'wall_walk', 'bridge'}     # a walk: open on at least one side, whatever its width
WIDE = 0.75          # a closed-in yard or ruin reads open when its floor is at least this share of its walls' height
SKYLIGHT_MAX = 0.35  # a skylight opens at most this share of its room's floor: the rest is roof


def area_xy(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def hull(points):
    pts = sorted(set((round(p[0]), round(p[1])) for p in points))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def min_width(points):
    h = hull(points)
    if len(h) < 3:
        return 0.0
    best = math.inf
    for i in range(len(h)):
        (x1, y1), (x2, y2) = h[i], h[(i + 1) % len(h)]
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0:
            continue
        w = max(abs((x2 - x1) * (y1 - py) - (x1 - px) * (y2 - y1)) / L for px, py in h)
        best = min(best, w)
    return best


def pip2(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % len(poly)][0], poly[(i + 1) % len(poly)][1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def on_face(p, poly, n):
    """p within 6 units of the vertical face's plane and inside it (edge direction u, height z)."""
    nx, ny = n[0] / 65536, n[1] / 65536
    x0, y0, z0 = poly[0]
    if abs((p[0] - x0) * nx + (p[1] - y0) * ny) > 6:
        return False
    ux, uy = -ny, nx
    pu = (p[0] - x0) * ux + (p[1] - y0) * uy
    q = [((v[0] - x0) * ux + (v[1] - y0) * uy, v[2]) for v in poly]
    us = [a for a, _ in q]
    if pu < min(us) - 2 or pu > max(us) + 2:
        return False
    inside = False
    for i in range(len(q)):
        (a1, b1), (a2, b2) = q[i], q[(i + 1) % len(q)]
        if (b1 > p[2]) != (b2 > p[2]):
            ai = a1 + (p[2] - b1) * (a2 - a1) / (b2 - b1)
            if ai > pu:
                inside = not inside
    return inside


def survey(blv, key):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', blv, '--world', 'xeen', '--assets', f'{R}/assets_dev', '--out', t.name],
                       check=True, capture_output=True)
        d = json.load(open(t.name))
    m = d['map']
    V = m['vertices']
    F = m['faces']
    # sky overhead only: faces looking down (a roof's place); sky set in walls (windows onto the outside) and in floors
    # are views out, not missing roofs, and are counted apart
    sky = [i for i, f in enumerate(F) if f['attributes'] & SKY and f['plane_normal'][2] <= -0.3 * 65536]
    views = sum(1 for f in F if f['attributes'] & SKY and f['plane_normal'][2] > -0.3 * 65536)
    if views:
        print(f'       {key:6} {views} sky faces in walls or floors (views out, not roofs)')
    if not sky:
        return []
    lock = {}
    lp = f'{R}/devdocs/xeen/briefs/{key}/L4/ids.lock.yml'
    if os.path.exists(lp):
        lock = {v: k for k, v in ((yaml.safe_load(open(lp)) or {}).get('sectors') or {}).items()}
    rooms = {}
    rp = f'{R}/devdocs/xeen/briefs/{key}/L4/rooms.yml'
    if os.path.exists(rp):
        rooms = {r['id']: r for r in (yaml.safe_load(open(rp)) or {}).get('rooms') or []}
    by_sector = {}
    for i in sky:
        by_sector.setdefault(F[i]['room'], []).append(i)
    skysec = set(by_sector)
    out = []
    of_sector = {}
    for i, f in enumerate(F):
        of_sector.setdefault(f['room'], []).append(i)
        if f['is_portal'] and f['room_behind'] != f['room']:
            of_sector.setdefault(f['room_behind'], []).append(i)
    for s, faces in sorted(by_sector.items()):
        sec_faces = of_sector.get(s, [])
        floors = [i for i in sec_faces if F[i]['room'] == s and not F[i]['is_portal']
                  and F[i]['plane_normal'][2] >= 0.7 * 65536]
        floor_area = sum(area_xy([V[v] for v in F[i]['vertices']]) for i in floors)
        floor_z = min((V[v][2] for i in floors for v in F[i]['vertices']), default=0)
        sky_pts = [V[v] for i in faces for v in F[i]['vertices']]
        sky_z = sum(p[2] for p in sky_pts) / len(sky_pts)
        sky_area = sum(area_xy([V[v] for v in F[i]['vertices']]) for i in faces)
        verticals = []
        for i in sec_faces:
            if abs(F[i]['plane_normal'][2]) < 0.3 * 65536:
                poly = [V[v] for v in F[i]['vertices']]
                box = tuple(f(c[k] for c in poly) for k in range(3) for f in (min, max))
                verticals.append((i, poly, box))
        rim = 0.0
        open_len = 0.0
        joins = set()
        for i in faces:
            poly = [V[v] for v in F[i]['vertices']]
            for k in range(len(poly)):
                a, b = poly[k], poly[(k + 1) % len(poly)]
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L < 1:
                    continue
                n = max(1, int(L // 32))
                ex, ey = (b[1] - a[1]) / L, -(b[0] - a[0]) / L   # a horizontal normal of the edge
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                if pip2(mx + ex * 4, my + ey * 4, poly):
                    ex, ey = -ex, -ey                            # point it out of the sky face
                for j in range(n):
                    t = (j + 0.5) / n
                    rim += L / n
                    is_open = False
                    for pz in sorted({sky_z - 24, min(sky_z - 24, floor_z + SILL_MAX + 8)}):
                        hit = None
                        for step in range(0, 136, 8):            # through a reveal to the opening behind it
                            p = (a[0] + (b[0] - a[0]) * t + ex * step, a[1] + (b[1] - a[1]) * t + ey * step, pz)
                            for fi, fpoly, bx in verticals:
                                if (bx[0] - 8 <= p[0] <= bx[1] + 8 and bx[2] - 8 <= p[1] <= bx[3] + 8
                                        and bx[4] <= p[2] <= bx[5] and on_face(p, fpoly, F[fi]['plane_normal'])):
                                    hit = fi
                                    break
                            if hit is not None:
                                break
                        if hit is not None and F[hit]['attributes'] & SKY:   # a wall drawn as sky: the view out
                            is_open = True
                        elif hit is not None and F[hit]['is_portal']:
                            f = F[hit]
                            other = f['room_behind'] if f['room'] == s else f['room']
                            bottom = min(V[v][2] for v in f['vertices'])
                            if other in skysec and bottom - floor_z <= SILL_MAX:
                                is_open = True
                                joins.add(other)
                    if is_open:
                        open_len += L / n
        out.append({
            'map': key, 'sector': s, 'room': lock.get(s, ''), 'name': (rooms.get(lock.get(s, '')) or {}).get('name', ''),
            'floor_area': round(floor_area), 'sky_area': round(sky_area), 'height': round(sky_z - floor_z),
            'width': round(min_width(sky_pts)), 'open_share': round(open_len / rim, 3) if rim else 0.0,
            'joins': sorted(joins), 'sky_pts': [p[:2] for p in sky_pts],
        })
    # open areas: sky sectors joined by low openings
    idx = {r['sector']: r for r in out}
    for r in out:
        for o in r['joins']:
            if o in idx and r['sector'] not in idx[o]['joins']:
                idx[o]['joins'].append(r['sector'])
    for r in out:
        seen, stack = set(), [r['sector']]
        while stack:
            s = stack.pop()
            if s in seen or s not in idx:
                continue
            seen.add(s)
            stack += idx[s]['joins']
        r['area_sectors'] = sorted(seen)
        r['area_floor'] = sum(idx[s]['floor_area'] for s in seen)
        r['area_width'] = round(min_width([p for s in seen for p in idx[s]['sky_pts']]))
        r['area_open'] = max(idx[s]['open_share'] for s in seen)
    for r in out:
        del r['sky_pts']
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('keys', nargs='*')
    ap.add_argument('--json')
    a = ap.parse_args()
    decl = yaml.safe_load(open(f'{R}/tools/xeen/open_sky.yml')) or {}
    rows = []
    errors = 0
    maps = sorted(f for f in os.listdir(f'{R}/assets_dev/worlds/xeen/maps') if f.endswith('.blv'))
    for f in maps:
        key = f[len('xeen_'):-len('.blv')]
        if a.keys and key not in a.keys:
            continue
        for r in survey(f'{R}/assets_dev/worlds/xeen/maps/{f}', key):
            entry = ((decl.get(key) or {}).get(r['room'] or f"sector:{r['sector']}") or {})
            kind = entry.get('kind')
            problems = []
            if not kind:
                problems.append('not listed as deliberately open in tools/xeen/open_sky.yml')
            elif kind not in KINDS:
                problems.append(f'unknown kind {kind}')
            elif kind == 'skylight' and r['sky_area'] > SKYLIGHT_MAX * max(1, r['floor_area']):
                problems.append(f"not a skylight: the sky over {r['sky_area'] / max(1, r['floor_area']):.0%} of the floor")
            elif kind in LINEAR and r['area_open'] < OPEN_MIN:
                problems.append(f"a {kind} closed on both sides: {r['width']} wide between walls {r['height']} high, open "
                                f"share {r['area_open']:.0%} (open its outer side: sky over a parapet)")
            elif (kind not in NARROW_OK | LINEAR and r['area_open'] < OPEN_MIN
                  and r['area_width'] < WIDE * r['height']):
                problems.append(f"roofless enclosure: {r['area_width']} wide under {r['height']}-high walls, open share "
                                f"{r['area_open']:.0%}")
            r['kind'] = kind or ''
            r['problems'] = problems
            errors += bool(problems)
            rows.append(r)
            print(f"{'ERROR' if problems else 'ok   '} {key:6} s{r['sector']:<3} {r['room'] or '-':24} "
                  f"{r['kind'] or '-':11} floor {r['floor_area'] / 1e6:6.2f}M  h {r['height']:5}  w {r['width']:5}  "
                  f"open {r['open_share']:4.0%}  area {len(r['area_sectors'])}s {r['area_floor'] / 1e6:6.2f}M "
                  f"w{r['area_width']:5} open{r['area_open']:4.0%}" + (f"  <- {'; '.join(problems)}" if problems else ''))
    if a.json:
        json.dump(rows, open(a.json, 'w'), indent=1)
    print(f'{len(rows)} open-sky sectors, {errors} errors')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
