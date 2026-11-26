#!/usr/bin/env python3
"""The wild-land rules of Xeen's outdoor maps on the installed maps (P2 feedback F29, F32, F33; 2026-11-23).

- `rim.event` (error): a map with a sea under its world rim (`water:sky` / `water:rim_sea` in its L4 sketch) has the
  rim-fall timer (`Xeen.rimFall(` in its map Lua, written by level_generation/projects/xeen/common/wild.py).
- `rim.point` (error): every return point of that event stands on the built map's land: at least 320 over the sea,
  within 64 of the height the generator read, on level ground (no node within one cell more than 192 off).
- `rim.pit` (error): no land near the rim (1,024 to 4,096 from the rim sea, past the rescue's margin
  Xeen.RimFallMargin) lies below Xeen.RimFallDepth (320) unless it is water: a hole by the rim the rescue misses.
- `wild.altar` (error): a shrine pavilion (a building part on posts with a click in the sketch) carries no click of its
  own; its altar (`<id>_altar`) does.
- `wild.campfire` (error): every campfire decoration of the sketch (common/wild.py FIRES) has an event, and the
  generated food-and-ring event (wild.CAMPFIRE_LUA) runs once (`once: true`); without it the fire refills forever.

- `rim.hull_step` (warning until each map's next rebuild, F60 X5 p4, 2026-11-25): a long hull piece (`xeen_hull4`,
  2,048 wide) over land varying more than common/rim.py HULL_STEP (128) along its span: rim.py now builds four short
  pieces there, each on its own land.
- `rim.fin` (error, D-192, 2026-11-26): a kerbless hull piece's built top (`xeen_hullf`, `xeen_hullfbn`: its z in the
  scene, the top strip of xeen_deco_hullf.glb at 0) stands over the land a walker stands on beside it, anywhere in
  common/rim.py `hull_band` (along its span and 64 past each end, 0.04-0.25 cells inland, void cells left out), on
  the game's terrain triangles. On rising land the engine refuses an uphill step against such a top (X6 p14: Great
  Worms held at the Sphinx cove). The F72 pieces over water (`raise` HULL_OVER_WATER) are left out; kerbed pieces
  never sink. A warning, not an error, for a piece already sunk the most (`raise` -HULL_SINK_MAX): only on cliffs no
  walker stands on (X7's lava-cove notch walls, the land falling 2,000 along one piece).

  python3 tools/xeen/check_wild.py [--assets ROOT] [--maps xeen_x1,...] [--check]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'xeen'))
sys.path.insert(0, str(ROOT / 'level_generation' / 'projects' / 'xeen' / 'common'))
import check_faces  # noqa: E402
import wild  # noqa: E402

OUTDOOR = ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6']


def check(key, assets: Path, cache: Path):
    stem = 'xeen_' + key
    findings = []
    warnings = []
    sketch = yaml.safe_load((ROOT / 'devdocs' / 'xeen' / 'briefs' / key / 'L4' / 'sketch.yml').read_text())
    lua = (assets / 'worlds' / 'xeen' / 'events' / 'maps' / (stem + '.lua')).read_text()
    data = check_faces.export_map(assets / 'worlds' / 'xeen' / 'maps' / (stem + '.odm'), assets, cache)
    terrain = check_faces.Terrain(data)
    seas = wild.rim_seas(sketch)
    if seas:
        match = re.search(r'Xeen\.rimFall\((\{.*?\}\}\}), (\{.*?\}\})', lua)
        if not match:
            findings.append(('rim.event', 'no rim-fall event in the map Lua (rebuild from the generator)'))
        else:
            for x, y, z, _ in re.findall(r'\{(-?\d+), (-?\d+), (-?\d+), (-?\d+)\}', match.group(2)):
                x, y, z = int(x), int(y), int(z)
                ground = terrain.height(x, y)
                near = [terrain.height(x + dx, y + dy) for dx in (-512, 0, 512) for dy in (-512, 0, 512)]
                if ground < 320 or abs(ground - z) > 64 or max(near) - min(near) > 384:
                    findings.append(('rim.point', 'return point (%d, %d, %d): the land there is %d (around %d-%d)'
                                     % (x, y, z, ground, min(near), max(near))))
        world_seas = [[wild.W(cx, cy) for cx, cy in sea] for sea in seas]
        for gy in range(2, 126):
            for gx in range(2, 126):
                wx, wy = wild.W(gx + 0.5, gy + 0.5)
                h = terrain.height(wx, wy)
                if h >= 320:
                    continue
                if any(wild._inside(sea, wx, wy) for sea in world_seas):
                    continue
                distance = min(edge_distance(sea, wx, wy) for sea in world_seas)
                if distance <= 1024 or distance > 4096:
                    continue      # the rescue's margin; low land far from the rim is a valley, not the rim's foot
                if any(body_covers(body, gx + 0.5, gy + 0.5) for body in (sketch.get('water') or {}).get('bodies') or []):
                    continue
                findings.append(('rim.pit', 'land below 320 at cell (%d, %d), height %d, away from the rim sea'
                                 % (gx, gy, h)))
    import rim  # noqa: E402 (common/rim.py: HULL_STEP, PIECE_LONG)
    for thing in sketch.get('structures') or []:
        if thing.get('kind') == 'decoration' and str(thing.get('decoration', '')).startswith('xeen_hull4'):
            cx, cy = thing['at']
            along = abs(math.sin(math.radians(float(thing.get('turn', 0))))) < 0.5   # faces n/s: runs along x
            half = rim.PIECE_LONG / 2.0
            lands = [terrain.height(*wild.W(cx + f * half, cy) if along else wild.W(cx, cy + f * half))
                     for f in (-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1)]
            if max(lands) - min(lands) > rim.HULL_STEP:
                warnings.append(('rim.hull_step', '%s (%s) at %s: the land under its span runs %d-%d'
                                 % (thing['id'], thing['decoration'], thing['at'], min(lands), max(lands))))
        if thing.get('kind') == 'building':
            for part in thing.get('parts') or []:
                if isinstance(part, dict) and part.get('posts') and part.get('effects') \
                        and 'shrine' in ('%s %s' % (part.get('title') or '', thing.get('title') or '')).lower():
                    findings.append(('wild.altar', '%s: the pavilion carries the click; put it on an altar'
                                     % thing['id']))
        if thing.get('kind') == 'decoration' and thing.get('decoration') in wild.FIRES \
                and thing['id'] not in wild.FIRE_SKIP and not thing.get('effects'):
            findings.append(('wild.campfire', '%s (%s): no event' % (thing['id'], thing.get('decoration'))))
        fire_lua = [effect for effect in thing.get('effects') or []
                    if isinstance(effect, dict) and 'a ring in the ashes' in str(effect.get('lua') or '')]
        if fire_lua and thing.get('once') is not True:
            findings.append(('wild.campfire', '%s: the campfire event is not `once: true`' % thing['id']))
    fins, fin_warnings = fin_findings(sketch, assets / 'worlds' / 'xeen' / 'maps' / (stem + '.scene.yml'),
                                      data['terrain'])
    return findings + fins, warnings + fin_warnings


SCENE_DECORATION = re.compile(r'name: (\S+)\n\s+decoration_list_id: \d+\n\s+ai_attributes: \d+\n\s+position:\n'
                              r'\s+x: (-?\d+)\n\s+y: (-?\d+)\n\s+z: (-?\d+)')


def fin_findings(sketch, scene: Path, terrain):
    """`rim.fin`: each kerbless hull piece of the sketch, its top from the built scene, against rim.hull_band's land;
    returns (errors, warnings)."""
    import rim  # noqa: E402 (common/rim.py: the band hull_sink sinks the pieces under)
    pieces = [thing for thing in sketch.get('structures') or []
              if thing.get('kind') == 'decoration' and str(thing.get('decoration', '')).startswith(rim.SINKING)
              and (thing.get('raise') or 0) <= 0]
    if not pieces:
        return [], []
    built = [(name, int(x), int(y), int(z)) for name, x, y, z in SCENE_DECORATION.findall(scene.read_text())
             if name.startswith(rim.SINKING)]
    polygons = rim.void_polygons(sketch)
    findings, warnings = [], []
    for thing in pieces:
        cx, cy = thing['at']
        wx, wy = wild.W(cx, cy)
        match = [b for b in built if b[0] == thing['decoration'] and abs(b[1] - wx) <= 2 and abs(b[2] - wy) <= 2]
        if not match:
            findings.append(('rim.fin', '%s (%s) at %s: not in the built scene (rebuild the map)'
                             % (thing['id'], thing['decoration'], thing['at'])))
            continue
        top = match[0][3]
        turn = math.radians(float(thing.get('turn', 0)))
        nx, ny = math.sin(turn), -math.cos(turn)     # the front (outward, into the void) in cells, y south
        low = rim.hull_band_low(terrain, polygons, cx, cy, -ny, nx, nx, ny, rim.PIECE_SHORT / 2.0)
        if low is not None and top > low:
            clamped = (thing.get('raise') or 0) <= -rim.HULL_SINK_MAX
            (warnings if clamped else findings).append((
                'rim.fin', '%s (%s) at %s: its top %d stands %.1f over the land beside it (lowest %.1f along its span '
                'and %d past its ends; raise %s)' % (thing['id'], thing['decoration'], thing['at'], top, top - low, low,
                                                     round(rim.HULL_FIN_REACH * 512), thing.get('raise', 0))))
    return findings, warnings


def edge_distance(polygon, x, y):
    best = float('inf')
    for index, a in enumerate(polygon):
        b = polygon[index - 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = dx * dx + dy * dy
        share = 0.0 if length == 0 else max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / length))
        best = min(best, ((x - a[0] - dx * share) ** 2 + (y - a[1] - dy * share) ** 2) ** 0.5)
    return best


def body_covers(body, cx, cy):
    polygon = body.get('polygon')
    return bool(polygon) and wild._inside(polygon, cx, cy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--assets', default=str(ROOT / 'assets_dev'))
    parser.add_argument('--maps')
    parser.add_argument('--cache', default=str(ROOT / 'output' / 'xeen_fb' / 'faces_cache'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    keys = [m.replace('xeen_', '') for m in args.maps.split(',')] if args.maps else OUTDOOR
    total = 0
    for key in keys:
        findings, warnings = check(key, Path(args.assets), Path(args.cache))
        steps = [w for w in warnings if w[0] == 'rim.hull_step']
        for rule, text in steps[:3] + [w for w in warnings if w[0] != 'rim.hull_step']:
            print('xeen_%s warn %s: %s' % (key, rule, text))
        if steps:
            print('xeen_%s: %d warning(s) rim.hull_step (until the map is rebuilt with common/rim.py HULL_STEP)'
                  % (key, len(steps)))
        rules = {}
        for rule, text in findings:
            rules[rule] = rules.get(rule, 0) + 1
            if rule != 'rim.pit' or rules[rule] <= 5:
                print('xeen_%s error %s: %s' % (key, rule, text))
        print('xeen_%s: %s' % (key, ', '.join('%s %d' % kv for kv in sorted(rules.items())) or 'clean'))
        total += len(findings)
    print('%d maps, %d errors' % (len(keys), total))
    return 1 if args.check and total else 0


if __name__ == '__main__':
    sys.exit(main())
