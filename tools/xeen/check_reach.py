#!/usr/bin/env python3
"""Reach check (the player's pins of 2026-11-24, F51): every pick-up, chest, barrel and clicked thing of an outdoor map
stands where the party walks to.

  tools/xeen/check_reach.py [<stem>...] [--odm <built .odm> --sketch <sketch.yml>] [--list]

On every built outdoor map of Xeen (or the given ones), the land the party walks on is found as the game draws it:
samples every SAMPLE units that are neither water nor steep (the game's rule: a tile whose four corners differ by more
than a tile is not walked up), plus the decks of bridges, piers, walkways, platforms and stairs (a deck
over water is walked on), inside the map's bounds (+-23,143: the party never walks past them), joined from the
party's start (the map's `start` arrival). Errors:

- `reach.thing`: a chest, crate, well, fountain, sketch item, clicked decoration (one with `effects` or a title) or
  container decoration (barrel, keg, crate, sack) with no walked-on sample within REACH of it: the player sees it
  (X1's orc camp barrels on the west road's hill, pin p23) and cannot get to it. A thing reached only by an intended
  means (flying, water walking, a ladder of the story) is kept in tools/xeen/check_reach.yml with its reason (the
  studio refuses words it does not know in a sketch, so the mark cannot stand on the thing itself).
- `reach.spawn`: a spawn point (`scene.yml` `spawns`) or a placed actor (`initial_state.actors`) past the bounds
  (|x| or |y| over BOUND: the monsters there never reach the party, X1's old road camps) or with no walked-on land
  within SPAWN_REACH (in a lake, on a cliff). Placed actors of a kept group (check_reach.yml `group:`: water
  creatures, flyers over a lava lake that come to the party) are exempt from the land rule, never from the bounds.

check_reach.yml `kept:` entries: `{map, thing: <id glob>, reason}` (a reach.thing) or `{map, group: <actor group>,
reason}` (reach.spawn's land rule for that placed group). Printed as `kept`, never failed; an entry that keeps
nothing is an error (drop it).

Clicked teleports (D-120): a clicked thing that the party reaches and whose `effects`/`else_effects` teleport it to a
point on the same map (no `map:`) joins the land around that point to the walked-on land (Medin's boat reaches X2's
island and its chest), repeated until nothing new is joined.

Exit 1 on an error. Run by every outdoor map job on its build before install (`--odm <build>/<stem>.odm --sketch
<L4>/sketch.yml`).
"""
from __future__ import annotations

import argparse
import fnmatch
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wall_check as W  # noqa: E402
import xeenlib  # noqa: E402

SAMPLE = 128            # walked-on samples this far apart
REACH = 320             # a thing this near a walked-on sample is reached (the party clicks within about 512)
DECK_KINDS = ('bridge', 'walkway', 'deck', 'platform', 'stairs')
TARGET_KINDS = ('chest', 'crate', 'well', 'fountain')
BOUND = 23143 - 37      # the party is held inside the map's bounds (OutdoorMapPackageMetadata.cpp's default; Xeen
                        # has no map_navigation rows): past them the travel prompt, never the land beyond
SPAWN_REACH = 384      # a spawn or actor this near walked-on land is reachable (monsters spread about a spawn point)
CONTAINERS = ('bigbarel', 'smlbarel', '7dec24', '7dec32', 'crate', 'keg', 'cask', 'sack', 'barrel')


def start_point(stem):
    path = xeenlib.WORLD / 'maps' / f'{stem}.studio.yml'
    for line in path.read_text().splitlines():
        if '{name: "start"' in line:
            values = line.split('at: [')[1].split(']')[0].split(',')
            return float(values[0]), float(values[1])
    return None


def steep_tiles(terrain, xs, ys):
    """The game's rule (OutdoorGeometryUtils.cpp outdoorTerrainSlopeTooHigh): a tile whose four corners differ by
    more than a tile is too steep to walk up; land under 256 is the rim's drop."""
    h = terrain.h
    c = np.clip(np.floor(xs / W.TILE + 64).astype(int), 0, 126)
    r = np.clip(np.floor(64 - ys / W.TILE).astype(int), 0, 126)
    corners = np.stack([h[r, c], h[r + 1, c], h[r, c + 1], h[r + 1, c + 1]])
    return (corners.max(0) - corners.min(0) > W.TILE) | (corners.min(0) < 256)


def walked(mp, start):
    """(mask, xs, ys): the samples the party walks to from `start`."""
    n = 128 * 512 // SAMPLE
    coords = (np.arange(n) + 0.5) * SAMPLE - 64 * 512
    xs, ys = np.meshgrid(coords, -coords)       # row 0 is the north edge (y high)
    wet, _ = mp.terrain.blocked(xs, ys)
    free = ~wet & ~steep_tiles(mp.terrain, xs, ys) & (np.abs(xs) <= BOUND) & (np.abs(ys) <= BOUND)
    for tid, ms in mp.models.items():
        if (mp.things.get(tid) or {}).get('kind') not in DECK_KINDS:
            continue
        for m in ms:
            for pts, nrm, solid in m.faces:
                if nrm[2] < 0.7 or not solid:
                    continue
                lo, hi = pts[:, :2].min(0), pts[:, :2].max(0)
                c0, c1 = np.searchsorted(coords, [lo[0], hi[0]])
                r0, r1 = np.searchsorted(coords, [-hi[1], -lo[1]])
                for r in range(max(0, r0 - 1), min(n, r1 + 1)):
                    for c in range(max(0, c0 - 1), min(n, c1 + 1)):
                        if W.in_polygon((xs[r, c], ys[r, c]), pts[:, :2], edge=SAMPLE * 0.5):
                            free[r, c] = True
    labels, _ = ndimage.label(free)

    def around(x, y):
        c = int(np.clip((x + 64 * 512) // SAMPLE, 0, n - 1))
        r = int(np.clip((64 * 512 - y) // SAMPLE, 0, n - 1))
        window = labels[max(0, r - 4):r + 5, max(0, c - 4):c + 5]
        return set(window[window > 0].ravel().tolist())

    ids = around(*start)
    hops = teleports(mp.sketch)
    while True:
        mask = np.isin(labels, list(ids))
        pts = np.stack([xs[mask], ys[mask]], 1)
        new = set()
        for at, to in hops:
            if near_land(pts, at, REACH) is not None:
                new |= around(*to) - ids
        if not new:
            return mask, xs, ys
        ids |= new


def teleports(sketch):
    """[(thing world xy, destination world xy)] of every clicked thing that teleports within its own map."""
    out = []
    for s in sketch.get('structures') or []:
        if 'at' not in s:
            continue
        for effect in (s.get('effects') or []) + (s.get('else_effects') or []):
            t = effect.get('teleport') if isinstance(effect, dict) else None
            if isinstance(t, dict) and 'to' in t and not t.get('map'):
                out.append((np.array(W.cell_to_world(s['at']), float), (float(t['to'][0]), float(t['to'][1]))))
    return out


def near_land(pts, p, reach):
    """The distance from p to the nearest walked-on sample within reach, or None."""
    near = pts[(np.abs(pts[:, 0] - p[0]) <= reach) & (np.abs(pts[:, 1] - p[1]) <= reach)]
    if not len(near):
        return None
    d = np.hypot(*(near - p).T).min()
    return d if d <= reach else None


def scene_spawns(scene):
    """[(label, x, y, group)] of the scene's spawn points (group None) and placed actors (a line parse: the scene
    is large)."""
    out = []
    section = None
    cur = None
    for line in scene.read_text().splitlines():
        if line and not line.startswith(' '):
            section = line.split(':')[0]
            continue
        stripped = line.strip()
        if section == 'spawns' and stripped.startswith('- spawn_index:'):
            cur = {'label': f'spawn {stripped.split(":")[1].strip()}'}
            out.append(cur)
        elif section == 'initial_state' and stripped.startswith('- actor_index:'):
            cur = {'label': f'actor {stripped.split(":")[1].strip()}'}
            out.append(cur)
        elif cur is not None and stripped[:2] in ('x:', 'y:') and stripped[0] not in cur:
            cur[stripped[0]] = float(stripped[2:])
        elif cur is not None and cur['label'].startswith('actor') and stripped.startswith('group:') \
                and 'group' not in cur:
            cur['group'] = int(stripped.split(':')[1])
    return [(c['label'], c['x'], c['y'], c.get('group')) for c in out if 'x' in c and 'y' in c]


KEPT = Path(__file__).resolve().with_name('check_reach.yml')


def kept_entries(stem):
    import yaml
    data = yaml.safe_load(KEPT.read_text()) if KEPT.exists() else {}
    return [k for k in (data or {}).get('kept') or [] if k.get('map') == stem]


def targets(sketch):
    for s in sketch.get('structures') or []:
        kind = s.get('kind')
        if 'at' not in s:
            continue
        deco = str(s.get('decoration') or '')
        if kind in TARGET_KINDS or (kind == 'decoration' and (s.get('effects') or any(w in deco for w in CONTAINERS))):
            yield s['id'], s['at']
    for item in sketch.get('items') or []:
        if 'at' in item:
            yield item['id'], item['at']


def check_map(stem, odm=None, sketch=None, listing=False):
    mp = W.Map(stem, odm, sketch)
    start = start_point(stem)
    errors = []
    if start is None:
        return [f'{stem}: reach.start: no start arrival in {stem}.studio.yml']
    mask, xs, ys = walked(mp, start)
    pts = np.stack([xs[mask], ys[mask]], 1)
    kept = kept_entries(stem)
    used = set()
    for tid, at in targets(mp.sketch):
        p = np.array(W.cell_to_world(at), float)
        d = near_land(pts, p, REACH)
        keep = [i for i, k in enumerate(kept) if k.get('thing') and fnmatch.fnmatch(tid, k['thing'])]
        if d is None and keep:
            used.update(keep)
            print(f'kept {stem}: reach.thing: {tid} at {at} ({kept[keep[0]].get("reason")})')
        elif d is None:
            errors.append(f'{stem}: reach.thing: {tid} at {at} stands where the party cannot walk (no walked-on '
                          f'land within {REACH})')
        elif listing:
            print(f'{stem}: ok {tid} {d:.0f}')
    scene = Path(odm).with_suffix('.scene.yml') if odm else xeenlib.WORLD / 'maps' / f'{stem}.scene.yml'
    for label, x, y, group in scene_spawns(scene):
        p = np.array([x, y])
        if abs(x) > BOUND or abs(y) > BOUND:
            errors.append(f'{stem}: reach.spawn: {label} at ({x:.0f}, {y:.0f}) is past the map\'s bounds '
                          f'(+-{BOUND})')
        elif near_land(pts, p, SPAWN_REACH) is None:
            keep = [i for i, k in enumerate(kept) if group is not None and k.get('group') == group]
            if keep:
                used.update(keep)
                print(f'kept {stem}: reach.spawn: {label} (group {group}) ({kept[keep[0]].get("reason")})')
                continue
            errors.append(f'{stem}: reach.spawn: {label} at ({x:.0f}, {y:.0f}) has no walked-on land within '
                          f'{SPAWN_REACH}' + (f' (group {group})' if group is not None else ''))
    for i, k in enumerate(kept):
        if i not in used:
            errors.append(f'{stem}: reach.kept: the entry {k.get("thing") or "group %s" % k.get("group")} of '
                          f'check_reach.yml keeps nothing: drop it')
    return errors


def outdoor_stems():
    return [f'xeen_{k}' for k in 'x1 x2 x3 x4 x5 x6 x7 d1 d2 d3 d4 d5 d6'.split()]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('stems', nargs='*')
    ap.add_argument('--odm')
    ap.add_argument('--sketch')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    errors = []
    for stem in a.stems or outdoor_stems():
        errors += check_map(stem, a.odm, a.sketch, a.list)
    for e in errors:
        print('ERROR', e)
    print(f'check_reach: {len(errors)} errors')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
