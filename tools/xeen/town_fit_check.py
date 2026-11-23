#!/usr/bin/env python3
"""Town fit check (the player's pins of 2026-11-22, F24-F28): how walls, houses, culverts and roads sit on the land.

  tools/xeen/town_fit_check.py [<stem>...] [--odm <built .odm> --sketch <sketch.yml>] [--list]

Every built outdoor map of Xeen (or the given ones; --odm/--sketch for a build folder), on the ground as the game
draws it (wall_check.py's terrain and models). Errors:

- `walls.hollow` (F26, F24): a hollow under a wall: a body (radius 37) looking in under one of its upright faces finds
  neither the land nor a face within HOLLOW_REACH: the wall's foot stands over the land, its underside is seen and a
  villager walks in under it and sticks (Vertigo's terrace wall: a slab across the middle of its slope, 192 over the
  street; pins p5, p15).
- `walls.buried` (F26): the land rises over a wall's top just behind it (more than BURIED over the top within
  BURIED_REACH): the wall reads as a band in a slope with a trench of grass between it and what stands behind
  (pin p6). A wall whose top follows the land is looked at too.
- `houses.buried_door` (F27): the land before a house door (32 to 160 in front of it, across its leaves) stands more
  than DOOR_BURY over the door's sill: the door is dug into a slope (pin p14).
- `gates.road_off` (F28): the road tiles through a gate (each `seals` line of tools/xeen/town_walls.yml that a road
  crosses) are centred more than ROAD_OFF from the passage's middle: the road runs into the tower beside the arch
  (pin p19). Road tiles are whole cells: a gate on a cell line has a road tile on one side of its middle.
- `culverts.ground_inside` (F25): the land inside a culvert's tunnel (between its front and its dark face) stands more
  than 16 over the tunnel's water: grass climbing into the arch under a black face (pin p3).
- `culverts.dry_water` (F25, D-95): a culvert's water face lies on dry land and shows (over the land there): a flat
  strip of water in a dry ditch.
- `culverts.open_side` (F25): a culvert's tunnel is open at its side: a body looking in at the side half-way along the
  tunnel sees no face turned toward it before the tunnel's middle (the outfall's block standing in the creek; p18).

- `actors.over_water` (F24): a walking actor (a row that neither flies nor swims, not `hostile: true`) placed over a
  water tile, on a bridge or a shore: its home is over the creek; it wanders back, steps off the bridge's side into
  the water and sticks against the rail (Vertigo Bridge's guards, pin p1).

Exit 1 on an error. Run by `towns.py --strict` (like wall_check.py; the sites listed in town_fit_pending.yml, found
on maps not rebuilt yet, are warnings there) and by every outdoor map job on its build before install
(`--odm <build>/<stem>.odm --sketch <L4>/sketch.yml`).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wall_check as W  # noqa: E402
import xeenlib  # noqa: E402

HOLLOW_REACH = 96        # a hollow this deep under a wall's face is one a body walks into
HOLLOW_LEAST = 64        # ... over at least this much of the face's length
HOLLOW_HIGH = 320        # a gap under a face higher than this is a passage (a gate's arch), not a hollow
BURIED = 48              # the land this much over a wall's top behind it
BURIED_REACH = 160
DOOR_BURY = 48           # the land this much over a door's sill before it
ROAD_OFF = 128           # a road's tiles centred this far off a gate passage's middle
FLUID = 0x10
ROAD_TILES = range(198, 234)   # the road tile set (the fourth set, 90 + 3 * 36)
DARK = ('7solid01', 'solid01', 'solid10')
STEP = 48


def world(p):
    return np.array(W.cell_to_world(p), float)


# ------------------------------------------------------------------------------------------------ ray against faces

class Faces:
    """Every model face of a map, for rays: (points, normal, box)."""

    def __init__(self, mp):
        self.items = []
        for m in mp.all_models():
            for pts, n, solid in m.faces:
                self.items.append((pts, n, pts.min(0) - 1, pts.max(0) + 1, solid, m.name))
        self.lo = np.array([i[2] for i in self.items]) if self.items else np.zeros((0, 3))
        self.hi = np.array([i[3] for i in self.items]) if self.items else np.zeros((0, 3))

    def first_hit(self, a, b, facing_only=True, skip_name=None):
        """The fraction along a->b of the first face crossed (facing back toward a when facing_only), else None."""
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        near = np.where(np.all(self.hi >= lo, 1) & np.all(self.lo <= hi, 1))[0]
        d = b - a
        best = None
        for k in near:
            pts, n, _, _, solid, name = self.items[k]
            if skip_name and name == skip_name:
                continue
            denom = float(np.dot(n, d))
            if abs(denom) < 1e-9 or (facing_only and denom >= 0):
                continue
            t = float(np.dot(n, pts[0] - a)) / denom
            if t < 0 or t > 1 or (best is not None and t >= best):
                continue
            hit = a + t * d
            axis = int(np.argmax(np.abs(n)))
            keep = [i for i in range(3) if i != axis]
            if W.in_polygon(hit[keep], pts[:, keep], edge=1.0):
                best = t
        return best


def terrain_hit(mp, a, b, steps=24):
    """The fraction along a->b where the segment first goes under the land, else None."""
    for k in range(1, steps + 1):
        t = k / steps
        p = a + (b - a) * t
        if float(mp.terrain.ground(p[0], p[1])) > p[2]:
            return t
    return None


# ------------------------------------------------------------------------------------------------ walls

def wall_things(mp):
    for tid, s in mp.things.items():
        if s.get('kind') == 'wall' and tid in mp.models:
            yield tid, s


def check_walls(mp, faces, errors, listing):
    for tid, s in wall_things(mp):
        hollow_run, worst, where = 0.0, 0.0, None
        # a gate's passage is a way through, not a hollow
        gates = [(world(g['at']), g.get('width', 256) / 2 + 96) for g in s.get('gates') or [] if 'at' in g]
        buried, bwhere = 0.0, None
        for m in mp.models[tid]:
            for pts, n, solid in m.faces:
                if not solid:
                    continue
                if abs(n[2]) < 0.3:
                    # an upright face: look in under its foot
                    low = pts[:, 2].min()
                    bottom = pts[np.abs(pts[:, 2] - low) < 2.0]
                    if len(bottom) < 2:
                        continue
                    a, b = bottom[np.argmin(bottom[:, 0] + bottom[:, 1])], bottom[np.argmax(bottom[:, 0] + bottom[:, 1])]
                    length = float(np.linalg.norm(b[:2] - a[:2]))
                    if length < 16:
                        continue
                    n2 = n[:2] / max(np.linalg.norm(n[:2]), 1e-9)
                    run = 0.0
                    for k in range(max(1, int(length // STEP))):
                        q = a + (b - a) * ((k + 0.5) / max(1, int(length // STEP)))
                        if any(np.linalg.norm(q[:2] - c) < r for c, r in gates):
                            continue
                        out = q[:2] + n2 * 8
                        g = float(mp.terrain.ground(out[0], out[1]))
                        if low - g < 40 or low - g > HOLLOW_HIGH:
                            continue      # flush, or a passage (a gate's arch) or a wall walk's merlons
                        z = (low + g) / 2
                        start = np.array([out[0], out[1], z])
                        if m.contains(start) or m.contains(np.array([out[0], out[1], low - 8])):
                            continue      # the face stands on more of the wall (a batter's top, a merlon)
                        end = np.array([q[0] - n2[0] * HOLLOW_REACH, q[1] - n2[1] * HOLLOW_REACH, z])
                        th = terrain_hit(mp, start, end)
                        fh = faces.first_hit(start, end, facing_only=False)
                        stop = min([t for t in (th, fh) if t is not None], default=None)
                        if stop is None or stop * (HOLLOW_REACH + 8) >= HOLLOW_REACH * 0.9:
                            run += length / max(1, int(length // STEP))
                            if low - g > worst:
                                worst, where = low - g, q
                    hollow_run = max(hollow_run, run)
                elif n[2] > 0.7:
                    # a top: the land just beyond its edges
                    top = pts[:, 2].max()
                    c = pts[:, :2].mean(0)
                    for i in range(len(pts)):
                        e0, e1 = pts[i][:2], pts[(i + 1) % len(pts)][:2]
                        mid = (e0 + e1) / 2
                        out = mid - c
                        L = np.linalg.norm(out)
                        if L < 1:
                            continue
                        out = out / L
                        for reach in (24, 80, BURIED_REACH):
                            p = mid + out * reach
                            over = float(mp.terrain.ground(p[0], p[1])) - top
                            if over > BURIED and over > buried:
                                buried, bwhere = over, mid
        if hollow_run >= HOLLOW_LEAST:
            errors.append(('walls.hollow', mp.stem, tid, 'a hollow under the wall %d over the land, %d long, at '
                           'cell (%.2f, %.2f): its foot stands over the land' % (worst, hollow_run,
                                                                                 *W.world_to_cell(*where[:2]))))
        if buried > 0:
            errors.append(('walls.buried', mp.stem, tid, 'the land rises %d over its top just behind it at cell '
                           '(%.2f, %.2f): the wall stands as a band in a slope' % (buried, *W.world_to_cell(*bwhere))))
        if listing:
            print('  %s %s hollow %d buried %d' % (mp.stem, tid, hollow_run, buried))


# ------------------------------------------------------------------------------------------------ houses

def check_doors(mp, errors, listing):
    """Door faces: upright faces with a door texture that carry an event (door_check.py's rule)."""
    import door_check as D
    classes = D.load_classes(xeenlib.ROOT / 'assets_dev')
    for record in mp.records:
        verts = np.array([[v['x'], v['y'], v['z']] for v in record['vertices']], float)
        for face in record['faces']:
            row = classes.get(face['texture_name'].lower())
            if not row or not row.get('door'):
                continue
            pts = verts[face['vertex_indices'][:face['vertex_count']]]
            if len(pts) < 3:
                continue
            nrm = np.zeros(3)
            for i in range(len(pts)):
                a, b = pts[i], pts[(i + 1) % len(pts)]
                nrm += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
            nrm /= max(np.linalg.norm(nrm), 1e-9)
            if abs(nrm[2]) > 0.1:
                continue
            n2 = nrm[:2] / np.linalg.norm(nrm[:2])
            along = np.array([-n2[1], n2[0]])
            sill = pts[:, 2].min()
            c = pts[:, :2].mean(0)
            half = np.ptp(pts[:, :2] @ along) / 2
            worst = -1e9
            for f in (32, 96, 160):
                for s in (-0.6, 0.0, 0.6):
                    p = c + n2 * f + along * half * s
                    worst = max(worst, float(mp.terrain.ground(p[0], p[1])) - sill)
            if listing:
                print('  %s %s door %s: land before it %+d over the sill' % (mp.stem, record['name'],
                                                                           face['texture_name'], worst))
            if worst > DOOR_BURY:
                errors.append(('houses.buried_door', mp.stem, record['name'], 'the land before its door rises %d over '
                               'the sill (cell %.2f, %.2f): the house is dug into a slope' %
                               (worst, *W.world_to_cell(*c))))


# ------------------------------------------------------------------------------------------------ gates

def gate_lines(mp, cfg):
    """(name, [a, b] cells) of every way through a wall: each `gates` entry of a sketch wall (the passage across the
    wall's line at its `at`, `width` wide) and each seal of town_walls.yml."""
    out = []
    for tid, s in mp.things.items():
        line = s.get('line') or []
        for g in s.get('gates') or []:
            if len(line) < 2 or 'at' not in g:
                continue
            at = np.array(g['at'], float)
            best = None
            for p, q in zip(line, line[1:] + ([line[0]] if s.get('closed') else [])):
                p, q = np.array(p, float), np.array(q, float)
                d = q - p
                t = np.clip(np.dot(at - p, d) / max(np.dot(d, d), 1e-9), 0, 1)
                dist = np.linalg.norm(p + t * d - at)
                if best is None or dist < best[0]:
                    best = (dist, d / np.linalg.norm(d))
            u = best[1]
            half = g.get('width', 256) / 2 / W.TILE
            out.append((tid, [list(at - u * half), list(at + u * half)]))
    for enc in cfg.get(mp.stem) or []:
        for seal in enc.get('seals', []):
            out.append((enc['name'], seal))
    return out


def check_gates(mp, cfg, errors, listing):
    tiles = mp.tiles
    seen = []
    for name, seal in gate_lines(mp, cfg):
        if True:
            a, b = np.array(seal[0], float), np.array(seal[1], float)
            if any(np.linalg.norm((a + b) / 2 - m) < 0.5 for m in seen):
                continue
            seen.append((a + b) / 2)
            ax = b - a
            L = np.linalg.norm(ax)
            if L < 1e-6:
                continue
            u = ax / L
            normal = np.array([-u[1], u[0]])
            covered = []
            # the road tiles the passage crosses: sample the seal line and a cell either side of it
            for k in range(0, 97):
                t = -1.0 + k / 96 * (L + 2.0)     # the passage and a cell beyond each end: the road's whole width
                hit = False
                for off in (-0.4, 0.0, 0.4):
                    p = a + u * t + normal * off
                    r, c = int(math.floor(p[1])), int(math.floor(p[0]))
                    if 0 <= r < 128 and 0 <= c < 128 and tiles[r, c] in ROAD_TILES:
                        hit = True
                if hit:
                    covered.append(t)
            if not covered:
                continue
            # the road's middle along the seal: the middle of the road cells' extent, measured on the seal line
            lo_t, hi_t = min(covered), max(covered)
            # widen to the whole cells under the samples
            mid = (lo_t + hi_t) / 2
            off = (mid - L / 2) * W.TILE
            if listing:
                print('  %s %s gate %s: road middle %+d from the passage middle' % (mp.stem, name, seal, off))
            if abs(off) > ROAD_OFF:
                errors.append(('gates.road_off', mp.stem, name, 'the road through the gate at %s is centred %d '
                               'off the passage\'s middle: it runs into the gate\'s tower; put the gate on the road '
                               'tiles\' middle (a cell\'s middle, x.5)' % ([[round(float(v), 2) for v in pt] for pt in seal], off)))


# ------------------------------------------------------------------------------------------------ culverts

def check_culverts(mp, faces, errors, listing):
    for tid, s in mp.things.items():
        if s.get('kind') != 'culvert' or tid not in mp.models:
            continue
        rec = [r for r in mp.records if r['name'] == tid]
        verts = [np.array([[v['x'], v['y'], v['z']] for v in r['vertices']], float) for r in rec]
        water, dark = None, None
        for r, vs in zip(rec, verts):
            for f in r['faces']:
                pts = vs[f['vertex_indices'][:f['vertex_count']]]
                if f['texture_name'].lower() in DARK:
                    dark = pts
                elif f['attributes'] & FLUID and water is None and np.ptp(pts[:, 2]) < 1:
                    water = pts    # the first water face is the tunnel's (the outflow follows)
        if water is None or dark is None:
            continue
        front_xy = world(s['at'])
        dark_c = dark[:, :2].mean(0)
        depth = float(np.linalg.norm(dark_c - front_xy))
        if depth < 1:
            continue
        back_dir = (dark_c - front_xy) / depth      # from the mouth's front to its dark face
        wz = float(water[:, 2].mean())
        crown = float(dark[:, 2].max())
        # ground inside the tunnel
        inside = max(float(mp.terrain.ground(*(front_xy + back_dir * depth * f))) for f in (0.25, 0.5, 0.75, 1.0))
        if inside - wz > 16:
            errors.append(('culverts.ground_inside', mp.stem, tid, 'the land inside its tunnel stands %d over the '
                           'tunnel\'s water: grass climbs in under the dark face' % (inside - wz)))
        # dry water
        wc = water[:, :2].mean(0)
        corners = np.vstack([water[:, :2], wc[None, :]])
        wet, _ = mp.terrain.blocked(corners[:, 0], corners[:, 1])
        g = float(np.min(mp.terrain.ground(corners[:, 0], corners[:, 1])))
        if not bool(wet.any()) and wz > g + 1:
            errors.append(('culverts.dry_water', mp.stem, tid, 'its water lies on dry land, %d over it: a flat strip '
                           'of water in a dry mouth (D-95: no water on dry land)' % (wz - g)))
        # open sides: look in at each side half-way along the tunnel
        across = np.array([back_dir[1], -back_dir[0]])
        half_w = float(np.abs((dark[:, :2] - dark_c) @ across).max())
        thick = float(s.get('thickness', 64))
        mid = front_xy + back_dir * min(depth - 4, thick + (depth - thick) * 0.5)
        wall_w = float((s.get('wall') or [s.get('width', 288) + 288])[0])
        open_at = []
        for sign in (1, -1):
            for z in np.linspace(wz + 24, crown - 16, 4):
                start = np.append(mid + sign * across * (max(half_w, wall_w / 2) + 48), z)
                if float(mp.terrain.ground(start[0], start[1])) > z:
                    continue
                end = np.append(mid, z)
                if terrain_hit(mp, start, end) is not None:
                    continue
                if faces.first_hit(start, end, facing_only=True) is None:
                    open_at.append((sign, z))
        if listing:
            print('  %s %s depth %d water %d inside %+d open %d' % (mp.stem, tid, depth, wz, inside - wz, len(open_at)))
        if open_at:
            errors.append(('culverts.open_side', mp.stem, tid, 'its tunnel is open at the side (%d of 8 looks in see '
                           'no face): the block\'s side shows the tunnel cut through' % len(open_at)))


# ------------------------------------------------------------------------------------------------ actors

def ground_rows():
    """The monster rows that walk (not `Fly` Y) and do not swim (no swimmer modifier), engine and Xeen tables."""
    rows = set()
    for path in (xeenlib.ROOT / 'assets_dev/engine/data_tables/monster_data.txt', xeenlib.WORLD / 'data_tables/monster_data.txt'):
        for line in path.read_text(encoding='latin-1').splitlines():
            f = line.split('\t')
            if len(f) > 10 and f[0].strip().isdigit() and f[9].strip().upper() == 'N':
                rows.add(f[0].strip())
    mods = (xeenlib.WORLD / 'modifiers.yml').read_text()
    for row in list(rows):
        if '\n  %s:' % row in mods and 'swim' in mods.split('\n  %s:' % row, 1)[1].split('\n  1', 1)[0]:
            rows.discard(row)
    return rows


def check_actors(mp, errors, listing):
    """`actors.over_water` (F24): a walking townsperson or guard (a peaceful actor: `hostile: false`, a talking NPC, or
    one of a group the sketch's relations make friendly) placed over water, on a bridge: its home is over the creek, it
    wanders back there and steps off the bridge's side into the water against the rail (Vertigo Bridge, pin p1)."""
    walkers = ground_rows()
    for k, a in enumerate(mp.sketch.get('actors') or []):
        at = a.get('at')
        if not at or a.get('hidden') or a.get('hostile') is True:
            continue
        if str(a.get('monster')) not in walkers:
            continue      # a flyer, a swimmer or an unknown row
        x, y = W.cell_to_world(at)
        wet, _ = mp.terrain.blocked(np.array([x]), np.array([y]))
        if bool(wet[0]):
            errors.append(('actors.over_water', mp.stem, 'actor %d (%s)' % (k, a.get('monster')), 'starts over water '
                           'at cell (%.2f, %.2f) (on a bridge or a shore): it wanders back there and sticks against '
                           'the rail or in the water; start it on land' % tuple(at)))


# ------------------------------------------------------------------------------------------------ driver

class FitMap(W.Map):
    def __init__(self, stem, odm=None, sketch=None):
        super().__init__(stem, odm, sketch)
        from map_export import parse_odm_file
        odm = Path(odm) if odm else xeenlib.WORLD / 'maps' / f'{stem}.odm'
        payload = parse_odm_file(odm)['payload']
        self.records = payload['bmodels']
        self.tiles = np.array(payload['tile_map']).reshape(128, 128)


def outdoor_stems():
    return sorted(p.stem for p in (xeenlib.WORLD / 'maps').glob('xeen_*.odm'))


def check_map(stem, odm=None, sketch=None, listing=False):
    errors = []
    mp = FitMap(stem, odm, sketch)
    faces = Faces(mp)
    cfg = yaml.safe_load(W.CONFIG.read_text()) or {}
    check_walls(mp, faces, errors, listing)
    check_doors(mp, errors, listing)
    check_gates(mp, cfg, errors, listing)
    check_culverts(mp, faces, errors, listing)
    check_actors(mp, errors, listing)
    return errors


def check_all(stems=None, listing=False):
    errors = []
    for stem in stems or outdoor_stems():
        errors += check_map(stem, listing=listing)
    return errors


PENDING = Path(__file__).resolve().with_name('town_fit_pending.yml')


def pending():
    """Sites found on 2026-11-23 on maps not yet rebuilt (town_fit_pending.yml: `<stem>: [<rule> <thing>, ...]`): a
    warning until their map's next rebuild fixes them; an entry whose fault is gone is an error (drop it)."""
    data = yaml.safe_load(PENDING.read_text()) if PENDING.exists() else {}
    return {(stem, entry) for stem, entries in (data or {}).items() for entry in entries or []}


def towns_check():
    """(errors, notes) as text lines for towns.py --strict."""
    known = pending()
    errors, notes, seen = [], [], set()
    for rule, stem, what, text in check_all():
        key = (stem, '%s %s' % (rule, what))
        seen.add(key)
        line = 'town_fit %s %s %s: %s' % (rule, stem, what, text)
        (notes if key in known else errors).append(line + (' (pending its map\'s rebuild)' if key in known else ''))
    for stem, entry in sorted(known - seen):
        errors.append('town_fit %s: %s is fixed: drop it from tools/xeen/town_fit_pending.yml' % (stem, entry))
    return errors, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stems', nargs='*')
    ap.add_argument('--odm')
    ap.add_argument('--sketch')
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()
    if args.odm:
        stem = args.stems[0] if args.stems else Path(args.odm).stem
        errors = check_map(stem, args.odm, args.sketch, args.list)
    else:
        errors = check_all(args.stems or None, args.list)
    for rule, stem, what, text in errors:
        print('ERROR %s %s %s: %s' % (rule, stem, what, text))
    print('town_fit_check: %d error(s)' % len(errors))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
