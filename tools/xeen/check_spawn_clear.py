#!/usr/bin/env python3
"""Spawn clearance check (the player's pins of 2026-11-25, F63): no monster of an outdoor map starts inside or against
a solid model, or against the world's hull.

  tools/xeen/check_spawn_clear.py [<stem>...] [--odm <built .odm> --sketch <sketch.yml>]

Two rules, on the built map (its .odm and the .scene.yml beside it):

- `spawn.in_model` (error): a scene spawn point's circle (its `radius` plus BODY_SPAWN, the body of a monster it
  rolls) or a placed actor (its own `radius`) comes within its radius + CLEAR of a solid face of a built model
  (houses, tents, walls, props built as models: X5's Acme machine, p13) over the band its body stands in, or stands
  inside a closed model. Faces under its feet (a deck it stands on) and above its head do not count.
- `spawn.at_hull` (error): a spawn point or placed actor nearer than HULL_CLEAR to the land's edge with the void (the
  hull stands there: `rim.void_polygons`) or to the map's bounds (+-BOUND: the party is held inside them, X6 p4).

Exit 1 on any error.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_reach as R  # noqa: E402
import wall_check as W  # noqa: E402
import xeenlib  # noqa: E402

sys.path.insert(0, str(xeenlib.ROOT / 'level_generation' / 'projects' / 'xeen' / 'common'))
import rim  # noqa: E402

CLEAR = 32              # the least gap between a body and a solid face
BODY_SPAWN = 100        # a spawn point's monsters: the common body radius of the Xeen rows (actors carry their own)
FEET = 24               # a face wholly below the feet plus this is a floor the body stands on
HEIGHT = 160            # a body's height when the record gives none
HULL_CLEAR = 768        # the least distance from a spawn point or actor to the hull or the bounds
BOUND = R.BOUND


def scene_bodies(scene: Path):
    """[(label, x, y, z, radius, height)]: spawn points (their circle plus BODY_SPAWN) and placed actors."""
    out = []
    section = None
    cur = None
    for line in scene.read_text().splitlines():
        if line and not line.startswith(' '):
            section = line.split(':')[0]
            continue
        s = line.strip()
        if section == 'spawns' and s.startswith('- spawn_index:'):
            cur = {'label': f'spawn {s.split(":")[1].strip()}', 'spawn': True}
            out.append(cur)
        elif section == 'initial_state' and s.startswith('- actor_index:'):
            cur = {'label': f'actor {s.split(":")[1].strip()}', 'spawn': False}
            out.append(cur)
        elif cur is None:
            continue
        elif s[:2] in ('x:', 'y:', 'z:') and s[0] not in cur:
            cur[s[0]] = float(s[2:])
        elif s.startswith('radius:') and 'radius' not in cur:
            cur['radius'] = float(s.split(':')[1])
        elif s.startswith('height:') and 'height' not in cur:
            cur['height'] = float(s.split(':')[1])
        elif s.startswith('name:') and 'name' not in cur:
            cur['name'] = s.split(':', 1)[1].strip().strip('"')
    bodies = []
    for c in out:
        if 'x' not in c:
            continue
        r = c.get('radius', 0.0) + BODY_SPAWN if c['spawn'] else c.get('radius', BODY_SPAWN)
        label = c['label'] + (f' "{c["name"]}"' if c.get('name') else '')
        bodies.append((label, c['x'], c['y'], c.get('z', 0.0), r, c.get('height', HEIGHT)))
    return bodies


def seg_dist(p, a, b):
    d = b - a
    n = float(np.dot(d, d))
    t = 0.0 if n == 0 else max(0.0, min(1.0, float(np.dot(p - a, d)) / n))
    return float(np.hypot(*(a + t * d - p)))


def face_dist(p, z0, z1, pts):
    """2D distance from p to a face's footprint, counting only the part of the face in the band z0..z1; None when no
    part is in the band."""
    zs = pts[:, 2]
    if zs.max() < z0 or zs.min() > z1:
        return None
    xy = pts[:, :2]
    if W.in_polygon(p, xy) and np.ptp(xy[:, 0]) + np.ptp(xy[:, 1]) > 1:
        return 0.0
    return min(seg_dist(p, xy[i], xy[(i + 1) % len(xy)]) for i in range(len(xy)))


def check_map(stem, odm=None, sketch=None):
    mp = W.Map(stem, odm, sketch)
    scene = Path(odm).with_suffix('.scene.yml') if odm else xeenlib.WORLD / 'maps' / f'{stem}.scene.yml'
    voids = rim.void_polygons(mp.sketch)
    errors = []
    models = [(name, m) for name, ms in mp.models.items() for m in ms if m.faces]
    for label, x, y, z, r, h in scene_bodies(scene):
        p = np.array([x, y])
        need = r + CLEAR
        # the hull and the bounds
        edge = BOUND - max(abs(x), abs(y))
        cx, cy = x / W.TILE + 64, 64 - y / W.TILE
        near = rim.nearest_edge(voids, cx, cy) if voids else None
        hull = near[0] * W.TILE if near and not rim.in_void(voids, cx, cy) else None
        if rim.in_void(voids, cx, cy):
            hull = 0.0
        worst = min(edge, hull if hull is not None else edge)
        if worst < HULL_CLEAR:
            what = 'the hull' if hull is not None and hull <= edge else 'the bounds'
            errors.append(f'{stem}: spawn.at_hull: {label} at ({x:.0f}, {y:.0f}) is {max(worst, 0):.0f} from {what} '
                          f'(at least {HULL_CLEAR})')
        # solid model faces in the body's band
        z0, z1 = z + FEET, z + h
        hits = []
        for name, m in models:
            if np.any(p < m.lo[:2] - need) or np.any(p > m.hi[:2] + need) or m.lo[2] > z1 or m.hi[2] < z0:
                continue
            best = None
            for pts, n, solid in m.faces:
                if not solid:
                    continue
                d = face_dist(p, z0, z1, pts)
                if d is not None and (best is None or d < best):
                    best = d
            inside = m.contains(np.array([x, y, z + h / 2]))
            if inside or (best is not None and best < need):
                hits.append((0.0 if inside else best, name, inside))
        for d, name, inside in sorted(hits)[:1]:
            how = 'inside' if inside else f'{d:.0f} from a solid face of'
            errors.append(f'{stem}: spawn.in_model: {label} at ({x:.0f}, {y:.0f}, {z:.0f}) r {r:.0f} is {how} '
                          f'{name} (at least {need:.0f})')
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('stems', nargs='*')
    ap.add_argument('--odm')
    ap.add_argument('--sketch')
    a = ap.parse_args()
    errors = []
    for stem in a.stems or R.outdoor_stems():
        errors += check_map(stem, a.odm, a.sketch)
    for e in errors:
        print('ERROR', e)
    print(f'check_spawn_clear: {len(errors)} errors')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
