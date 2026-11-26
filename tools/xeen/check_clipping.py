#!/usr/bin/env python3
"""F76 (the player's pins 2026-11-26, XD-11 and XD-12): pieces of a built BLV that show where they should not.

Four rules, read from the installed BLV (`oymap export`):

- `sky.solid` (XD-11 p1 "here is something wrong", XD-12 p3): a face of a solid inside a room (a step's riser or side,
  a platform's side, a flight's cheek) drawn as sky. A flight or platform without its own surfaces takes the room's
  wall surface, and an open-air room's wall is the sky: the risers and sides of the Stairway to Heaven and of
  Darzog's sky stair drew the sky (the flat fog under the horizon), so the flight read as a ramp with saw-tooth
  notches in the wall beside it, or as a bare slab running into the wall. A sky face in sector S whose back (8
  behind its middle, at its middle height) lies inside S (under one of S's ceilings and over one of S's floors) is a
  solid's face. Fix: give the flight `riser` (and `tread`), the platform `surface`.
- `deco.through` (XD-12 p1/p2 "tree clipping through the wall"): a decoration whose drawn size reaches through a face
  it stands behind: a 3D model's footprint (its horizontal extent at its bound height, tools/xeen/deco_footprint.py),
  grown by the binding's `height_jitter`, crosses a wall face more than REACH into the room
  in front of it, within the decoration's height (or its top crosses another sector's floor above it). Only faces of
  other sectors than the one it stands in count (the crown shows in another room), and its own sector's walls (faces
  WALL_MIN high or more: a house in a yard); sky faces are not looked at (a crown seen over a parapet against the sky
  is meant); a prop leaning on furniture of its own room is check_prop_overlap.py's. Fix: a smaller decoration, or
  move it out.
- `piece.free` (XD-11 p2 "maybe here too", XD-12 p4 "here is also something strange"): an upright face, not sky, that
  stands free at both of its ends over at least FREE_MIN of its height: nothing but sky, portals or nothing touches
  its two upright edges there. A doorway's jambs standing above a parapet (the frame of a door with no wall round
  it), a stub of parapet between two terraces at one level that are joined everywhere else. Fix: build the wall round
  the frame (panels up to over its lintel), or open the stub (an opening over its whole length).
Findings looked at are listed in tools/xeen/check_clipping.yml (`keep`: map, rule, `at` [x, y] within 64 of the
face's middle or the decoration, or `name` the decoration's id, and `why`): kept by design (shown with `--kept`), or
`pending: true` with an `owner` (still printed, not failing: a site found and left to its map's lane).

Usage: tools/xeen/check_clipping.py <map.blv>... [--assets ROOT] [--all] [--rule RULE] [--kept]   exit 1 on any
finding not kept.
--all: every xeen_*.blv in assets_dev. Each line: the map, the rule, the face (index, texture, sector) or the
decoration, where, and by how much.
"""
import argparse
import glob
import json
import math
import os
import subprocess
import sys
import tempfile

import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(R, 'tools', 'xeen'))
import deco_footprint  # noqa: E402

OY = f'{R}/openyamm-studio/build-xeen/oymap'
SKY = 0x00400000
BEHIND = 8.0       # sky.solid: how far behind a sky face its back is looked at
REACH = 24.0       # deco.through: a crown reaching less than this past a face is not counted
WALL_MIN = 256.0   # deco.through: in its own sector only faces this tall count (walls, not furniture)
FREE_MIN = 96.0    # piece.free: free at both ends over at least this much of the face's height
TOUCH = 2.0        # piece.free: a face within this of an upright edge touches it
STEP = 16.0        # piece.free: heights looked at


def unit(n):
    return [c / 65536.0 for c in n]


def pip(x, y, poly):
    inside = False
    k = len(poly)
    for i in range(k):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % k][0], poly[(i + 1) % k][1]
        if (y1 > y) != (y2 > y):
            if x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x:
                inside = not inside
    return inside


def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


class Face:
    def __init__(self, i, f, V):
        self.i = i
        self.f = f
        self.P = [V[v] for v in f['vertices']]
        self.n = unit(f['plane_normal'])
        self.sky = bool(f['attributes'] & SKY)
        self.portal = bool(f.get('is_portal'))
        self.room = f['room']
        self.tex = f['texture']
        xs = [p[0] for p in self.P]
        ys = [p[1] for p in self.P]
        zs = [p[2] for p in self.P]
        self.box = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
        self.upright = abs(self.n[2]) < 0.1
        self.flat = abs(self.n[2]) > 0.99
        self.c = [sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)]
        if self.upright:
            h = math.hypot(self.n[0], self.n[1]) or 1.0
            self.u = (-self.n[1] / h, self.n[0] / h)       # along the face, horizontal
            self.uz = [(p[0] * self.u[0] + p[1] * self.u[1], p[2]) for p in self.P]

    def plane_z(self, x, y):
        nx, ny, nz = self.n
        p = self.P[0]
        return p[2] - (nx * (x - p[0]) + ny * (y - p[1])) / nz

    def side(self, p):
        q = self.P[0]
        return sum(self.n[k] * (p[k] - q[k]) for k in range(3))

    def near(self, p, tol):
        """Is the point within `tol` of this face (in its plane, inside or at its rim)?"""
        if abs(self.side(p)) > tol:
            return False
        if self.upright:
            a = p[0] * self.u[0] + p[1] * self.u[1]
            poly = self.uz
            q = (a, p[2])
        else:
            poly = [(v[0], v[1]) for v in self.P]
            q = (p[0], p[1])
        if pip(q[0], q[1], poly):
            return True
        return any(seg_dist(q[0], q[1], poly[k], poly[(k + 1) % len(poly)]) <= tol for k in range(len(poly)))

    def section(self, z):
        """The face's two ends at height z (the points of its rim there farthest apart along it), or None."""
        hits = []
        k = len(self.P)
        for j in range(k):
            a, b = self.P[j], self.P[(j + 1) % k]
            if (a[2] - z) * (b[2] - z) < 0:
                t = (z - a[2]) / (b[2] - a[2])
                hits.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), z))
            elif a[2] == z:
                hits.append((a[0], a[1], z))
        if len(hits) < 2:
            return None
        hits.sort(key=lambda h: h[0] * self.u[0] + h[1] * self.u[1])
        return hits[0], hits[-1]


class Grid:
    def __init__(self, faces, cell=256):
        self.cell = cell
        self.d = {}
        for f in faces:
            b = f.box
            for gx in range(int(b[0] // cell) - 1, int(b[3] // cell) + 1):
                for gy in range(int(b[1] // cell) - 1, int(b[4] // cell) + 1):
                    self.d.setdefault((gx, gy), []).append(f)

    def at(self, x, y):
        return self.d.get((int(x // self.cell), int(y // self.cell)), [])


def deco_names(assets):
    """decoration_list_id -> internal name: engine rows and the Xeen world's rows (list id = row id - 1)."""
    out = {}
    for path in (f'{assets}/engine/data_tables/decoration_data.txt', f'{assets}/worlds/xeen/models/decoration_data.txt',
                 f'{assets}/worlds/xeen/data_tables/decoration_data.txt'):
        if not os.path.exists(path):
            continue
        for line in open(path, encoding='latin-1').read().splitlines()[2:]:
            cols = line.split('\t')
            if len(cols) > 5 and cols[0].strip().isdigit() and cols[1]:
                out[int(cols[0]) - 1] = (cols[1].lower(), cols[5])
    return out


def jitter_height(name):
    entry = deco_footprint._bindings('xeen').get(name)
    if entry and entry.get('model') and entry.get('height'):
        return float(entry['height']), float(entry.get('height_jitter') or 0.0)
    return None, 0.0


def check(path, assets, rules):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        d = json.load(open(t.name))
    m = d['map']
    V = m['vertices']
    doorfaces = {fi for door in d.get('doors', []) for fi in door['faces']}
    faces = [Face(i, f, V) for i, f in enumerate(m['faces'])]
    grid = Grid(faces)
    by_room = {}
    for f in faces:
        by_room.setdefault(f.room, []).append(f)
    stem = os.path.basename(path)
    found = []

    if 'sky.solid' in rules:
        for f in faces:
            if not f.sky or f.portal or not f.upright or f.i in doorfaces:
                continue
            p = [f.c[k] - BEHIND * f.n[k] for k in range(3)]
            over = under = False
            for g in by_room.get(f.room, []):
                if g.portal or g.upright or abs(g.n[2]) < 0.5:
                    continue
                if not (g.box[0] <= p[0] <= g.box[3] and g.box[1] <= p[1] <= g.box[4]):
                    continue
                if not pip(p[0], p[1], g.P):
                    continue
                z = g.plane_z(p[0], p[1])
                if g.n[2] > 0 and z < p[2]:
                    under = True
                if g.n[2] < 0 and z > p[2]:
                    over = True
            if over and under:
                found.append((stem, 'sky.solid', f"face {f.i} ({f.tex}, sector {f.room}) at "
                              f"({f.c[0]:.0f}, {f.c[1]:.0f}, {f.c[2]:.0f}): a solid's face drawn as sky",
                              (f.c[0], f.c[1]), f.tex))

    if 'deco.through' in rules:
        names = deco_names(assets)
        for e in m['entities']:
            nm = names.get(e['decoration_list_id'])
            if not nm:
                continue
            name = nm[0]
            h, jit = jitter_height(name)
            if h is None:
                continue          # a sprite: a billboard (a sconce on its wall), its table radius is not its size
            r = deco_footprint.footprint(name)[0]
            r *= 1.0 + jit
            h *= 1.0 + jit
            if r < REACH or h <= 0:
                continue
            cx, cy, cz = e['position']
            home = _sector_of(m, cx, cy, cz, by_room)
            worst = None
            seen = set()
            for gx in range(int((cx - r) // 256), int((cx + r) // 256) + 1):
                for gy in range(int((cy - r) // 256), int((cy + r) // 256) + 1):
                    for f in grid.d.get((gx, gy), []):
                        if f.i in seen or f.sky or f.portal or f.i in doorfaces:
                            continue
                        if f.room == home and f.box[5] - f.box[2] < WALL_MIN:
                            continue
                        seen.add(f.i)
                        b = f.box
                        if b[3] < cx - r or b[0] > cx + r or b[4] < cy - r or b[1] > cy + r:
                            continue
                        if b[5] <= cz or b[2] >= cz + h:
                            continue
                        if f.upright:
                            s = f.side((cx, cy, f.c[2]))
                            if s > -1.0 or -s > r:
                                continue
                            reach = r + s
                            if reach < REACH:
                                continue
                            half = math.sqrt(max(0.0, r * r - s * s))
                            a = cx * f.u[0] + cy * f.u[1]
                            hit = False
                            for ia in range(7):
                                ua = a - half + 2 * half * ia / 6
                                for iz in range(7):
                                    z = cz + h * iz / 6
                                    if pip(ua, z, f.uz):
                                        hit = True
                                        break
                                if hit:
                                    break
                            if hit and (worst is None or reach > worst[0]):
                                worst = (reach, f)
                        elif f.flat and f.n[2] > 0:
                            z = f.c[2]
                            if not (cz < z < cz + h):
                                continue
                            hit = any(pip(cx + r * 0.7 * math.cos(k * 0.785), cy + r * 0.7 * math.sin(k * 0.785), f.P)
                                      for k in range(8)) or pip(cx, cy, f.P)
                            reach = cz + h - z
                            if hit and reach >= REACH and (worst is None or reach > worst[0]):
                                worst = (reach, f)
            if worst:
                reach, f = worst
                found.append((stem, 'deco.through', f"{e['name']} ({name}, reach {r:.0f}, height {h:.0f}) at "
                              f"({cx}, {cy}, {cz}): {reach:.0f} through face {f.i} ({f.tex}, sector {f.room})",
                              (cx, cy), e['name']))

    if 'piece.free' in rules:
        for f in faces:
            if f.sky or f.portal or not f.upright or f.i in doorfaces:
                continue
            if f.box[5] - f.box[2] < FREE_MIN:
                continue
            free = 0.0
            top = None
            z = f.box[2] + STEP / 2
            while z < f.box[5]:
                sec = f.section(z)
                if sec and math.hypot(sec[1][0] - sec[0][0], sec[1][1] - sec[0][1]) >= 8:
                    ends_open = True
                    for p in sec:
                        x, y = p[0], p[1]
                        closed = False
                        for g in grid.at(x, y):
                            if g is f or g.portal:
                                continue
                            # a sky face in (or within 45 degrees of) the face's own plane is the wall going on
                            # as a window, sky over a band or a cliff's skyline: it closes the end; a sky face
                            # across the end (a sky wall beside a jamb) does not, nor does the back of a wall of
                            # no thickness (the face in the plane facing the other way)
                            dot = g.n[0] * f.n[0] + g.n[1] * f.n[1] + g.n[2] * f.n[2]
                            if (g.sky and abs(dot) < 0.7) or dot < -0.99:
                                continue
                            b = g.box
                            if not (b[0] - TOUCH <= x <= b[3] + TOUCH and b[1] - TOUCH <= y <= b[4] + TOUCH
                                    and b[2] - TOUCH <= z <= b[5] + TOUCH):
                                continue
                            if g.near(p, TOUCH):
                                closed = True
                                break
                        if closed:
                            ends_open = False
                            break
                    if ends_open:
                        free += STEP
                        top = z
                z += STEP
            if free >= FREE_MIN:
                found.append((stem, 'piece.free', f"face {f.i} ({f.tex}, sector {f.room}) at "
                              f"({f.c[0]:.0f}, {f.c[1]:.0f}), z {f.box[2]}-{f.box[5]}: stands free at both ends "
                              f"over {free:.0f} (up to {top:.0f})", (f.c[0], f.c[1]), f.tex))
    return found


def _sector_of(m, x, y, z, by_room):
    for s, sec in enumerate(m['sectors']):
        lo, hi = sec['min'], sec['max']
        if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] and lo[2] - 1 <= z <= hi[2]:
            for g in by_room.get(s, []):
                if not g.portal and g.flat and g.n[2] > 0 and pip(x, y, g.P) and abs(g.plane_z(x, y) - z) < 2:
                    return s
    return -1


def load_keep():
    """check_clipping.yml `keep`: findings looked at and kept, each with its reason."""
    path = os.path.join(R, 'tools', 'xeen', 'check_clipping.yml')
    if not os.path.exists(path):
        return []
    return (yaml.safe_load(open(path)) or {}).get('keep') or []


def kept(keep, stem, rule, xy, name):
    """The keep entry that matches a finding, or None."""
    for k in keep:
        if k['map'] != stem.replace('.blv', '') or k['rule'] != rule:
            continue
        if k.get('name') and k['name'] != name:
            continue
        if 'at' in k and math.hypot(k['at'][0] - xy[0], k['at'][1] - xy[1]) > k.get('within', 64):
            continue
        return k
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('maps', nargs='*')
    ap.add_argument('--assets', default=f'{R}/assets_dev')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--rule', action='append', choices=['sky.solid', 'deco.through', 'piece.free'])
    ap.add_argument('--kept', action='store_true', help='also list the findings check_clipping.yml keeps')
    a = ap.parse_args()
    maps = list(a.maps)
    if a.all:
        maps += sorted(glob.glob(f'{R}/assets_dev/worlds/xeen/maps/xeen_*.blv'))
    rules = set(a.rule or ['sky.solid', 'deco.through', 'piece.free'])
    keep = load_keep()
    n = k = w = 0
    for p in maps:
        for stem, rule, text, xy, name in check(p, a.assets, rules):
            entry = kept(keep, stem, rule, xy, name)
            if entry and entry.get('pending'):
                w += 1
                print(f'{stem}: {rule}: (pending: {entry.get("owner", "?")}) {text}')
            elif entry:
                k += 1
                if a.kept:
                    print(f'{stem}: {rule}: (kept) {text}')
            else:
                print(f'{stem}: {rule}: {text}')
                n += 1
    print(f'{n} finding(s), {w} pending and {k} kept (check_clipping.yml)')
    return 1 if n else 0


if __name__ == '__main__':
    sys.exit(main())
