"""Level pads under single things (2026-11-24; tools/xeen/town_fit_check.py `platforms.through`, `things.overhang`).

A platform stands on the land at its middle and a fountain or well likewise: on a slope the land rises through a
platform's top on its uphill side (the ground shows through the paving) or falls away under a fountain's foot (its
plinth hangs over the slope). `apply(sketch, key)` lays a `heights.terraces` pad under each thing listed for the map
in PADS: every node of the whole cells under the thing and MARGIN round it takes the land's height at the thing's
middle (rounded down to the land's 32 steps, so the studio's land never rounds up over the foot), the land outside
running back over SLOPE cells. The thing keeps its place and, within 31, its height (an arrival on a ledge stays where it was).

The land is read from the installed map (common/wild.py `_export`, as the bridge ends'), so a pad only changes what
is under its thing: run on a map built without it, it reads the land the pad will level.
"""
from __future__ import annotations

import math

import wild

MARGIN = 0.25       # cells of level land round the thing's footprint, before the outline goes out to whole cells
SLOPE = 1           # cells the land outside takes to run back to its own height
STEP = 32           # the studio's land heights come in these steps
FOUNTAIN_RADIUS = 192   # a fountain's default radius (map units) when it gives none

# The things each map levels the land under (the sites of tools/xeen/town_fit_pending.yml, 2026-11-24).
PADS = {
    'x4': ['thing:sky_crack_ledge', 'thing:olympian_fountain'],
    'x6': ['thing:oasis_fountain'],
    'd5': ['thing:munchies_1', 'thing:munchies_2'],
    'd6': ['thing:pinnacle'],
}


def _footprint(thing):
    """Half extents in cells (x, y) of the thing's footprint round its `at`."""
    if thing.get('size'):
        return thing['size'][0] / 1024.0, thing['size'][1] / 1024.0
    radius = float(thing.get('radius', FOUNTAIN_RADIUS)) / 512.0
    for tier in thing.get('tiers') or []:
        radius = max(radius, (float(thing.get('radius', FOUNTAIN_RADIUS)) + float(tier[0])) / 512.0)
    return radius, radius


def apply(sketch, key):
    ids = PADS.get(key) or []
    if not ids:
        return []
    terrain = wild._export('xeen_%s' % key) or {}
    if not terrain:
        return ['level pads: no installed map to read the land from (left out)']
    notes = []
    pads = []
    by_id = {thing.get('id'): thing for thing in sketch.get('structures') or []}
    for tid in ids:
        thing = by_id.get(tid)
        if thing is None:
            notes.append('level pad %s: not in the sketch' % tid)
            continue
        cx, cy = thing['at'][0], thing['at'][1]
        hx, hy = _footprint(thing)
        if thing.get('turn') and float(thing['turn']) % 180 != 0:
            hx = hy = math.hypot(hx, hy)
        # Out to the whole cells round the footprint: the land between two nodes is a slope, so every node of a cell
        # the footprint touches is levelled (a margin short of the next node left the land rising at its edge)
        x0, x1 = math.floor(cx - hx - MARGIN), math.ceil(cx + hx + MARGIN)
        y0, y1 = math.floor(cy - hy - MARGIN), math.ceil(cy + hy + MARGIN)
        height = int(wild._terrain_at(terrain, cx, cy) // STEP * STEP)
        polygon = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        pads.append({'polygon': polygon, 'height': height, 'slope': SLOPE,
                     'notes': 'level land under %s (common/level_pads.py)' % (thing.get('title') or tid)})
        notes.append('level pad %s at %d' % (tid, height))
    if pads:
        sketch.setdefault('heights', {}).setdefault('terraces', []).extend(pads)
    return notes
