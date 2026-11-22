#!/usr/bin/env python3
"""Town wall check (F19, the user 2026-11-22): walled towns are closed, and wall pieces meet flush.

  tools/xeen/wall_check.py [<stem>...] [--odm <built .odm> --sketch <sketch.yml>] [--png <dir>] [--list]

Reads each built outdoor map (assets_dev, or --odm/--sketch for a build folder) as the game collides with it, and the
enclosures in tools/xeen/town_walls.yml:

- `walls.open` (ERROR): a party (radius 37, plus 16) can walk from an enclosure's inside to the edge of its box without
  passing a gate. The gates, bridges and doors the config lists as `seals` are closed for the test; water tiles
  (without Water Walk), terrain too steep to climb (a triangle rising over 512, as the game's slope rule) and every
  upright model face from the ground to body height block. The message names the narrowest point on the way out,
  which is where the gap is.
- `walls.loose_end` (ERROR): an end of a wall that the config lists as part of a circuit stands on walkable land:
  nothing covers its end face and the ground a party width beyond it is neither water, a cliff nor the map's edge.
- `walls.slit` (ERROR): a wall's end face is open to the air but another wall, tower, gate or building stands less
  than 96 in front of it: a visible slit between two pieces (Vertigo's culvert and quay walls, 2026-11-22).
- `walls.step` (ERROR): a wall's end face is partly covered by the piece it meets and partly open, over a tenth of
  the face and more than 32 both across and up: the two pieces are of different thickness or height at the joint and
  nothing covers it (a step or a ledge). An enclosure's `joints_ok` lists pieces meant to stand proud (a bastion).
  A wall end inside a tower or building is covered by it: that is the way to join pieces of different height.

- `walls.water_end` (ERROR): a water end piece (`thing:water_end*`, tools/xeen/kit_pieces.py, D-94), the low pier a
  wall or tower ends in where it meets water, must end in water (the ground just past its nose is a water tile) and
  stand at least CLIMB (a step and a jump) over the land or water under every point of its top, so no party gets onto
  it from the bank and round the wall's end.

A wall end is the face at either end of a sketch wall's `line` (and the sides of a culvert's headwall), whatever the
map: the joint rules hold for every wall of every built outdoor map, the closure rules for the enclosures listed.
Exit 1 on an error. With --png, a picture per enclosure (grey blocked, blue water, brown steep, red the inside's
reach, green the outside's, yellow the seals, magenta the way out).
"""
from __future__ import annotations

import argparse
import fnmatch
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'util'))
import xeenlib  # noqa: E402
from map_export import parse_odm_file  # noqa: E402

CONFIG = Path(__file__).resolve().with_name('town_walls.yml')
BRIEFS = xeenlib.ROOT / 'devdocs' / 'xeen' / 'briefs'
TILE = 512
RES = 16                  # the closure grid, map units per cell
PARTY_R = 37 + 16         # the party's radius and a margin
BODY = (40, 120)          # an upright face blocks when it covers this band over the ground
UNTOUCHABLE = 0x20000000
PORTAL = 0x1
SLIT = 96                 # a piece this close in front of an open end face makes a slit
STEP = 32                 # an end face open over this much across and up next to a covering piece: a step
PIECE_KINDS = ('wall', 'culvert', 'building', 'barrier', 'bridge')
WATER_END = 'thing:water_end*'
CLIMB = 224               # a step of 128 over a jump of about 90: the least a water end stands over what is under it


def cell_to_world(p):
    return ((p[0] - 64) * TILE, (64 - p[1]) * TILE)


def world_to_cell(x, y):
    return (x / TILE + 64, 64 - y / TILE)


# -------------------------------------------------------------------------------------------------- terrain

class Terrain:
    def __init__(self, payload):
        rows = [line.split('\t') for line in (xeenlib.ENGINE_TABLES / 'terrain_tile_data_2.txt')
                .read_text(encoding='latin-1').splitlines()[1:]]
        self.h = np.array(payload['height_map'], dtype=np.int32).reshape(128, 128) * 32
        tiles = np.array(payload['tile_map']).reshape(128, 128)

        def flags(tile):
            if tile >= 234:
                return 0
            if tile >= 90:
                index = payload['tile_set_lookup_indices'][(tile - 90) // 36] + (tile - 90) % 36
            else:
                index = tile
            return int(rows[index][6], 0) if index < len(rows) else 0
        table = {t: flags(t) for t in np.unique(tiles)}
        self.wet = np.vectorize(lambda t: bool(table[t] & 2 and not table[t] & 0x100))(tiles)

    def ground(self, x, y):
        """The terrain's height at world points (arrays), on the game's triangles."""
        gx = np.clip(np.asarray(x, float) / TILE + 64, 0, 126.999)
        gy = np.clip(64 - np.asarray(y, float) / TILE, 0, 126.999)
        c, r = np.floor(gx).astype(int), np.floor(gy).astype(int)
        fx, fy = gx - c, gy - r
        z00, z10 = self.h[r, c], self.h[r, c + 1]
        z01, z11 = self.h[r + 1, c], self.h[r + 1, c + 1]
        upper = fx >= fy
        return np.where(upper, z00 + (z10 - z00) * fx + (z11 - z10) * fy,
                        z00 + (z11 - z01) * fx + (z01 - z00) * fy)

    def blocked(self, x, y):
        """(water, steep) at world points: water tiles, triangles rising over a tile, the rim below 256."""
        gx = np.asarray(x, float) / TILE + 64
        gy = 64 - np.asarray(y, float) / TILE
        off = (gx < 0) | (gx >= 127) | (gy < 0) | (gy >= 127)
        gx, gy = np.clip(gx, 0, 126.999), np.clip(gy, 0, 126.999)
        c, r = np.floor(gx).astype(int), np.floor(gy).astype(int)
        fx, fy = gx - c, gy - r
        z00, z10 = self.h[r, c], self.h[r, c + 1]
        z01, z11 = self.h[r + 1, c], self.h[r + 1, c + 1]
        upper = fx >= fy
        a = np.where(upper, np.maximum.reduce([z00, z10, z11]), np.maximum.reduce([z00, z01, z11]))
        b = np.where(upper, np.minimum.reduce([z00, z10, z11]), np.minimum.reduce([z00, z01, z11]))
        steep = ((a - b) > TILE) | (np.minimum.reduce([z00, z10, z01, z11]) < 256) | off
        return self.wet[r, c] & ~off, steep


# -------------------------------------------------------------------------------------------------- models

class Model:
    """One built model: its faces as vertex arrays with normals."""

    def __init__(self, record):
        self.name = record['name']
        verts = np.array([[v['x'], v['y'], v['z']] for v in record['vertices']], float)
        self.faces = []
        for face in record['faces']:
            pts = verts[face['vertex_indices'][:face['vertex_count']]]
            if len(pts) < 3:
                continue
            n = np.zeros(3)
            for i in range(len(pts)):     # Newell's normal
                a, b = pts[i], pts[(i + 1) % len(pts)]
                n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
            length = np.linalg.norm(n)
            if length < 1e-6:
                continue
            solid = not (face['attributes'] & (UNTOUCHABLE | PORTAL))
            self.faces.append((pts, n / length, solid))
        allpts = np.concatenate([f[0] for f in self.faces]) if self.faces else np.zeros((1, 3))
        self.lo, self.hi = allpts.min(0), allpts.max(0)
        upright = [f[0][:, :2] for f in self.faces if abs(f[1][2]) < 0.7]
        self.hull = None
        if upright:
            from scipy.spatial import ConvexHull
            pts2 = np.unique(np.round(np.concatenate(upright)), axis=0)
            try:
                hull = ConvexHull(pts2)
                self.hull = pts2[hull.vertices]
            except Exception:
                self.hull = None

    def contains(self, p):
        """Inside the closed model: an odd number of faces above the point, and within its walls' outline."""
        if np.any(p < self.lo - 1) or np.any(p > self.hi + 1):
            return False
        if self.hull is not None and not in_polygon(p[:2], self.hull, edge=2.0):
            return False
        crossings = 0
        for pts, n, _ in self.faces:
            if abs(n[2]) < 1e-3:
                continue
            if not in_polygon(p[:2], pts[:, :2]):
                continue
            # the face's plane height at p
            z = pts[0][2] - (n[0] * (p[0] - pts[0][0]) + n[1] * (p[1] - pts[0][1])) / n[2]
            if z > p[2]:
                crossings += 1
        return crossings % 2 == 1


def in_polygon(p, poly, edge=0.0):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                inside = not inside
    if inside or edge <= 0:
        return inside
    for i in range(n):
        a, b = np.asarray(poly[i], float), np.asarray(poly[(i + 1) % n], float)
        d = b - a
        t = 0.0 if not d.any() else max(0.0, min(1.0, float(np.dot(np.asarray(p) - a, d) / np.dot(d, d))))
        if np.hypot(*(a + t * d - p)) <= edge:
            return True
    return False


# -------------------------------------------------------------------------------------------------- map

class Map:
    def __init__(self, stem, odm=None, sketch=None):
        self.stem = stem
        key = stem.replace('xeen_', '')
        odm = Path(odm) if odm else xeenlib.WORLD / 'maps' / f'{stem}.odm'
        sketch = Path(sketch) if sketch else BRIEFS / key / 'L4' / 'sketch.yml'
        payload = parse_odm_file(odm)['payload']
        self.terrain = Terrain(payload)
        self.models = {}
        for record in payload['bmodels']:
            m = Model(record)
            self.models.setdefault(m.name, []).append(m)
        self.sketch = xeenlib.load_yaml(sketch) if sketch.exists() else {'structures': []}
        self.things = {s['id']: s for s in self.sketch.get('structures', []) if 'id' in s}

    def all_models(self):
        for ms in self.models.values():
            yield from ms


# -------------------------------------------------------------------------------------------------- wall ends

def wall_ends(mp):
    """(thing id, end point world xy, outward unit direction, half thickness) for every end of a wall line and
    each side of a culvert's headwall."""
    out = []
    for tid, s in mp.things.items():
        if tid not in mp.models:
            continue
        if s.get('kind') == 'wall' and len(s.get('line', [])) >= 2 and not s.get('closed'):
            line = [np.array(cell_to_world(p), float) for p in s['line']]
            half = s.get('thickness', 128) / 2
            for end, nxt in ((line[0], line[1]), (line[-1], line[-2])):
                d = end - nxt
                out.append((tid, end, d / np.linalg.norm(d), half))
        elif s.get('kind') == 'culvert':
            ms = mp.models[tid]
            lo = np.min([m.lo for m in ms], 0)
            hi = np.max([m.hi for m in ms], 0)
            turn = math.radians(s.get('turn', 0))
            across = np.array([math.cos(turn), math.sin(turn)])   # turn 0: the headwall runs east-west
            c = (lo[:2] + hi[:2]) / 2
            half_w = abs(np.dot(hi[:2] - lo[:2], across)) / 2
            depth = abs(np.dot(hi[:2] - lo[:2], [-across[1], across[0]])) / 2
            for sign in (1, -1):
                out.append((tid, c + sign * across * half_w, sign * across, depth))
    return out


def end_faces(mp, tid, end, direction, half):
    """The upright faces of the thing's models that close the end: facing out along the line, near its end."""
    faces = []
    for m in mp.models[tid]:
        for pts, n, solid in m.faces:
            if not solid or abs(n[2]) > 0.3:   # hidden twins have no solid face: not looked at
                continue
            n2 = n[:2] / max(np.linalg.norm(n[:2]), 1e-9)
            if np.dot(n2, direction) < 0.85:
                continue
            c = pts[:, :2].mean(0)
            rel = c - end
            if abs(np.dot(rel, direction)) > 160 or abs(np.dot(rel, [-direction[1], direction[0]])) > half + 160:
                continue
            faces.append((pts, n))
    return faces


def sample_face(pts, n, rows=8, cols=8, offset=6.0):
    """Points spread over a convex face, `offset` in front of it."""
    c = pts.mean(0)
    u = pts[1] - pts[0]
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    pu, pv = (pts - c) @ u, (pts - c) @ v
    out = []
    for i in range(rows):
        for j in range(cols):
            a = pu.min() + (pu.max() - pu.min()) * (j + 0.5) / cols
            b = pv.min() + (pv.max() - pv.min()) * (i + 0.5) / rows
            q = c + a * u + b * v
            if in_polygon((a, b), np.stack([pu, pv], 1)):
                out.append((q + n * offset, a, b))
    return out, u, v


def seal_distance(p, seals):
    best = 1e9
    for a, b in seals:
        a, b = np.array(cell_to_world(a), float), np.array(cell_to_world(b), float)
        d = b - a
        t = max(0.0, min(1.0, float(np.dot(p - a, d) / max(np.dot(d, d), 1e-9))))
        best = min(best, float(np.linalg.norm(a + t * d - p)))
    return best


def first_hit(q, d3, models, reach):
    """The first face of these models a ray from q along d3 meets within reach: (distance, normal, model) or None."""
    best = None
    for m in models:
        for pts, n, _ in m.faces:
            denom = float(np.dot(n, d3))
            if abs(denom) < 1e-6:
                continue
            t = float(np.dot(pts[0] - q, n)) / denom
            if t <= -8 or t > reach or (best and t >= best[0]):
                continue
            hit = q + d3 * t
            u = pts[1] - pts[0]
            u /= max(np.linalg.norm(u), 1e-9)
            v = np.cross(n, u)
            if in_polygon((float(np.dot(hit - pts[0], u)), float(np.dot(hit - pts[0], v))),
                          np.stack([(pts - pts[0]) @ u, (pts - pts[0]) @ v], 1), edge=1.0):
                best = (t, n, m)
    return best


def check_ends(mp, circuit_ids, seals=(), joints_ok=()):
    """Each wall end face sampled: a sample is covered when the ray along the wall's way out first meets the inside
    of another piece (the back of its face), open with a piece in front when it meets a face from outside within
    SLIT (a slit), else open."""
    errors = []
    # a hidden twin (untouchable: a ruin or a later stage shown by an event) is left out: one state at a time
    pieces = [m for tid, ms in mp.models.items() for m in ms
              if (mp.things.get(tid, {}).get('kind') in PIECE_KINDS or tid.startswith('building:'))
              and any(f[2] for f in m.faces)]
    for tid, end, direction, half in wall_ends(mp):
        faces = end_faces(mp, tid, end, direction, half)
        if not faces:
            continue
        near = [m for m in pieces if m.name != tid
                and np.all(m.lo[:2] - SLIT - half <= end) and np.all(end <= m.hi[:2] + SLIT + half)]
        # the ray may cross more than SLIT inside a big piece (a tower round a wall's end): look further for those
        near += [m for m in pieces if m.name != tid and m not in near
                 and np.all(m.lo[:2] - 1024 <= end) and np.all(end <= m.hi[:2] + 1024)
                 and m.lo[0] - 8 <= end[0] <= m.hi[0] + 8 and m.lo[1] - 8 <= end[1] <= m.hi[1] + 8]
        d3 = np.array([direction[0], direction[1], 0.0])
        covered, open_, slit, exposed = 0, 0, None, []
        for pts, n in faces:
            samples, u, v = sample_face(pts, n, offset=-2.0)
            for q, a, b in samples:
                ground = float(mp.terrain.ground(q[0], q[1]))
                if q[2] < ground + 2:
                    continue          # under the land: neither covered by a piece nor open
                hit = first_hit(q, d3, near, 2048)
                if (hit and (np.dot(hit[1], d3) > 0 or hit[0] <= 6)) or any(m.contains(q) for m in near):
                    covered += 1      # inside the piece it meets, or flush against it
                    continue
                open_ += 1
                exposed.append(q)
                if hit and hit[0] <= SLIT and (slit is None or hit[0] < slit[0]):
                    slit = (max(hit[0], 0.0), hit[2].name)
        if open_ == 0:
            continue
        where = world_to_cell(*end)
        heading = math.degrees(math.atan2(direction[1], direction[0])) % 360
        label = f'{tid} end at ({where[0]:.2f}, {where[1]:.2f}) heading {heading:.0f}'
        ex = np.array(exposed)
        side = float(np.ptp(ex @ np.array([-direction[1], direction[0], 0]))) if len(ex) > 1 else 0.0
        up = float(np.ptp(ex[:, 2])) if len(ex) > 1 else 0.0
        if covered:
            # a step shows as a block: open over a tenth of the face and more than STEP both across and up
            if open_ >= 0.1 * (covered + open_) and min(side, up) > STEP \
                    and not any(fnmatch.fnmatch(tid, g) for g in joints_ok):
                errors.append(f'walls.step: {label}: its end face is partly open beside the piece it meets '
                              f'({covered} of {covered + open_} samples covered; open {side:.0f} across, '
                              f'{up:.0f} up): match thickness and height at the joint or cover it')
            continue
        if slit:
            errors.append(f'walls.slit: {label}: open end face {slit[0]:.0f} from {slit[1]}: close the gap')
            continue
        if tid in circuit_ids and seal_distance(end, seals) > half + 96:
            beyond = [end + direction * d for d in (half / 2 + 24, PARTY_R * 2 + 16)]
            xs, ys = np.array([p[0] for p in beyond]), np.array([p[1] for p in beyond])
            wet, steep = mp.terrain.blocked(xs, ys)
            if not (wet | steep).all():
                errors.append(f'walls.loose_end: {label}: a circuit wall ends on walkable land; run it into deep '
                              f'water, a cliff or a tower, gatehouse or building')
    return errors


def check_water_ends(mp):
    """D-94: every water end piece ends in water and stands CLIMB over everything under its top."""
    errors = []
    for tid, ms in mp.models.items():
        if not fnmatch.fnmatch(tid, WATER_END):
            continue
        s = mp.things.get(tid, {})
        tops = [(pts, n) for m in ms for pts, n, solid in m.faces if solid and n[2] > 0.3]
        lo = np.min([m.lo for m in ms], 0)
        hi = np.max([m.hi for m in ms], 0)
        low = None
        for x in np.arange(lo[0] + 24, hi[0] - 23, 32.0):
            for y in np.arange(lo[1] + 24, hi[1] - 23, 32.0):
                zs = [pts[0][2] - (n[0] * (x - pts[0][0]) + n[1] * (y - pts[0][1])) / n[2]
                      for pts, n in tops if in_polygon((x, y), pts[:, :2])]
                if not zs:
                    continue
                over = max(zs) - float(mp.terrain.ground(x, y))
                if low is None or over < low[0]:
                    low = (over, x, y)
        if low is not None and low[0] < CLIMB - 8:
            c = world_to_cell(low[1], low[2])
            errors.append(f'walls.water_end: {tid}: its top stands only {low[0]:.0f} over the ground at '
                          f'({c[0]:.2f}, {c[1]:.2f}): at least {CLIMB} everywhere, or a party climbs onto it')
        # the nose: the end of the piece farthest out along its plot's long side
        at, size = s.get('at'), s.get('size')
        if not at or not size:
            continue
        long_y = size[1] >= size[0]
        ends = []
        for sign in (-1, 1):
            if long_y:
                ends.append((at[0] + size[0] / 2, at[1] + (size[1] if sign > 0 else 0) + sign * 0.15))
            else:
                ends.append((at[0] + (size[0] if sign > 0 else 0) + sign * 0.15, at[1] + size[1] / 2))
        wet = [bool(mp.terrain.blocked(*cell_to_world(e))[0]) for e in ends]
        if not any(wet):
            errors.append(f'walls.water_end: {tid}: neither end of it reaches water the party cannot walk in '
                          f'(looked at {ends[0]} and {ends[1]}): run its nose out past the bank')
    return errors


# -------------------------------------------------------------------------------------------------- closure

def disk(radius_cells):
    r = int(math.ceil(radius_cells))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xx * xx + yy * yy <= radius_cells * radius_cells


def raster_polygon(mask, poly, x0, y1):
    """Fill a polygon (world xy) into mask [row = (y1 - y) / RES, col = (x - x0) / RES], edges included."""
    from PIL import Image, ImageDraw
    img = Image.fromarray(mask.astype(np.uint8) * 255)
    draw = ImageDraw.Draw(img)
    px = [((x - x0) / RES, (y1 - y) / RES) for x, y in poly]
    if len(px) >= 3:
        draw.polygon(px, fill=255, outline=255)
    if len(px) >= 2:
        draw.line(px + [px[0]], fill=255, width=2)
    return np.array(img) > 0


def closure(mp, site, png=None):
    """(errors, notes) for one enclosure."""
    box = site['box']
    (x0, y1), (x1, y0) = cell_to_world(box[:2]), cell_to_world(box[2:])
    w, h = int((x1 - x0) / RES), int((y1 - y0) / RES)
    xs = x0 + (np.arange(w) + 0.5) * RES
    ys = y1 - (np.arange(h) + 0.5) * RES
    gx, gy = np.meshgrid(xs, ys)
    ground = mp.terrain.ground(gx, gy)
    wet, steep = mp.terrain.blocked(gx, gy)
    walls = np.zeros((h, w), bool)
    circuit = np.zeros((h, w), bool)
    floors = np.zeros((h, w), bool)
    for m in mp.all_models():
        in_circuit = m.name in site.get('circuit_ids', ())
        if m.hi[0] < x0 - 512 or m.lo[0] > x1 + 512 or m.hi[1] < y0 - 512 or m.lo[1] > y1 + 512:
            continue
        for pts, n, solid in m.faces:
            if not solid:
                continue
            if n[2] > 0.7:
                # a floor near the land or water (a bridge's deck): walkable even over water
                c = pts.mean(0)
                if c[2] <= float(mp.terrain.ground(c[0], c[1])) + 256:
                    floors |= raster_polygon(np.zeros((h, w), bool), pts[:, :2], x0, y1)
                continue
            if abs(n[2]) >= 0.7:
                continue
            c = pts.mean(0)
            g = float(np.min(mp.terrain.ground(pts[:, 0], pts[:, 1])))
            if pts[:, 2].min() > g + BODY[0] or pts[:, 2].max() < g + BODY[1]:
                continue
            face = raster_polygon(np.zeros((h, w), bool), pts[:, :2], x0, y1)
            walls |= face
            if in_circuit:
                circuit |= face
    blocked = ndimage.binary_dilation(walls, structure=disk(PARTY_R / RES))
    terrain_block = (wet | steep) & ~floors
    blocked |= terrain_block
    seals = np.zeros((h, w), bool)
    for a, b in site.get('seals', []):
        pa, pb = cell_to_world(a), cell_to_world(b)
        from PIL import Image, ImageDraw
        img = Image.fromarray(np.zeros((h, w), np.uint8))
        ImageDraw.Draw(img).line([((pa[0] - x0) / RES, (y1 - pa[1]) / RES), ((pb[0] - x0) / RES, (y1 - pb[1]) / RES)],
                                 fill=255, width=int(2 * PARTY_R / RES) + 2)
        seals |= np.array(img) > 0
    free = ~blocked & ~seals
    labels, _ = ndimage.label(free)
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    errors, notes = [], []
    reach = np.zeros((h, w), bool)
    path = []
    for seed in site['inside']:
        sx, sy = cell_to_world(seed)
        c, r = int((sx - x0) / RES), int((y1 - sy) / RES)
        if not (0 <= r < h and 0 <= c < w) or labels[r, c] == 0:
            errors.append(f'walls.config: {site["name"]}: inside point {seed} is blocked or outside the box')
            continue
        reach |= labels == labels[r, c]
        if labels[r, c] in border:
            path = way_out(free, (r, c))
            clear = ndimage.distance_transform_edt(~(walls | terrain_block | seals)) * RES
            to_circuit = ndimage.distance_transform_edt(~circuit) * RES if circuit.any() else clear
            near = [rc for rc in path if to_circuit[rc] < 700] or path
            pinch = min(near, key=lambda rc: clear[rc]) if near else (r, c)
            px, py = x0 + (pinch[1] + 0.5) * RES, y1 - (pinch[0] + 0.5) * RES
            cx, cy = world_to_cell(px, py)
            errors.append(f'walls.open: {site["name"]}: the inside at {seed} reaches the outside without a gate; '
                          f'the narrowest point on the way out is at ({cx:.2f}, {cy:.2f}) = ({px:.0f}, {py:.0f}), '
                          f'{2 * clear[pinch]:.0f} wide')
    if png:
        picture(png, walls, wet & ~floors, steep & ~floors, seals, reach, labels, border, path)
    return errors, notes


def way_out(free, start):
    """The shortest 4-connected way from start to the box's edge over free cells."""
    from collections import deque
    h, w = free.shape
    prev = {start: None}
    queue = deque([start])
    end = None
    while queue:
        r, c = queue.popleft()
        if r in (0, h - 1) or c in (0, w - 1):
            end = (r, c)
            break
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (r + dr, c + dc)
            if 0 <= q[0] < h and 0 <= q[1] < w and free[q] and q not in prev:
                prev[q] = (r, c)
                queue.append(q)
    path = []
    while end is not None:
        path.append(end)
        end = prev[end]
    return path[::-1]


def picture(png, walls, wet, steep, seals, reach, labels, border, path):
    from PIL import Image
    h, w = walls.shape
    img = np.full((h, w, 3), 235, np.uint8)
    outside = np.isin(labels, list(border)) & ~reach
    img[outside] = (170, 215, 160)
    img[reach] = (235, 150, 150)
    img[wet] = (90, 130, 220)
    img[steep] = (150, 110, 70)
    img[walls] = (60, 60, 60)
    img[seals] = (240, 210, 40)
    for r, c in path:
        img[r, c] = (220, 0, 220)
    Image.fromarray(img).save(png)


# -------------------------------------------------------------------------------------------------- main

def sites_of(config, stem):
    return config.get(stem, []) or []


def check_map(stem, config, odm=None, sketch=None, png_dir=None):
    mp = Map(stem, odm, sketch)
    errors, notes = [], []
    circuit, seals = set(), []
    for site in sites_of(config, stem):
        site['circuit_ids'] = {tid for tid in mp.models
                               for pattern in site.get('circuit', []) if fnmatch.fnmatch(tid, pattern)}
        circuit |= site['circuit_ids']
        seals += site.get('seals', [])
    joints_ok = set()
    for site in sites_of(config, stem):
        joints_ok |= set(site.get('joints_ok', []))
    errors += [f'{stem}: {e}' for e in check_ends(mp, circuit, seals, joints_ok)]
    errors += [f'{stem}: {e}' for e in check_water_ends(mp)]
    for site in sites_of(config, stem):
        png = None
        if png_dir:
            Path(png_dir).mkdir(parents=True, exist_ok=True)
            png = str(Path(png_dir) / f'{stem}_{site["name"].replace(" ", "_").lower()}.png')
        e, n = closure(mp, site, png)
        errors += [f'{stem}: {x}' for x in e]
        notes += [f'{stem}: {x}' for x in n]
    return errors, notes


def outdoor_stems():
    return sorted(p.stem for p in (xeenlib.WORLD / 'maps').glob('xeen_*.odm'))


def check_all(stems=None, png_dir=None):
    config = xeenlib.load_yaml(CONFIG) or {}
    errors, notes = [], []
    for stem in stems or outdoor_stems():
        e, n = check_map(stem, config, png_dir=png_dir)
        errors += e
        notes += n
    return errors, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stems', nargs='*')
    ap.add_argument('--odm')
    ap.add_argument('--sketch')
    ap.add_argument('--png')
    ap.add_argument('--list', action='store_true', help='list the configured enclosures')
    args = ap.parse_args()
    config = xeenlib.load_yaml(CONFIG) or {}
    if args.list:
        for stem, sites in config.items():
            for site in sites or []:
                print(f'{stem}: {site["name"]}: inside {site["inside"]}, {len(site.get("seals", []))} seals')
        return 0
    stems = [s if s.startswith('xeen_') else 'xeen_' + s for s in args.stems] or outdoor_stems()
    errors, notes = [], []
    for stem in stems:
        e, n = check_map(stem, config, args.odm, args.sketch, args.png)
        errors += e
        notes += n
    for line in notes:
        print(f'  note  {line}')
    for line in errors:
        print(f'  ERROR {line}')
    sites = sum(len(sites_of(config, s)) for s in stems)
    print(f'wall_check: {len(stems)} maps, {sites} enclosures, {len(errors)} errors')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
