"""Level pads under single things (2026-11-24; tools/xeen/town_fit_check.py `platforms.through`, `things.overhang`).

A platform stands on the land at its middle and a fountain or well likewise: on a slope the land rises through a
platform's top on its uphill side (the ground shows through the paving) or falls away under a fountain's foot (its
plinth hangs over the slope). `apply(sketch, key)` lays a `heights.terraces` pad under each thing listed for the map
in PADS: every node of the whole cells under the thing and MARGIN round it takes the land's height at the thing's
middle (rounded down to the land's 32 steps, so the studio's land never rounds up over the foot), the land outside
running back over SLOPE cells. The thing keeps its place and, within 31, its height (an arrival on a ledge stays where it was).

The land is read from the installed map (common/wild.py `_export`, as the bridge ends'), so a pad only changes what
is under its thing: run on a map built without it, it reads the land the pad will level.

Each pad's height is read once and kept in level_pad_heights.yml (map -> thing -> its `at` and height), and used as
long as the thing stays at that `at` (D-170, 2026-11-25): read again from the installed land, a pad drifted from
build to build where something graded after the terraces (a road, a bridge end) cut into it (X6's prospector's tent,
2688 -> 2656 at its centre where its lane ends). Moving a thing reads its land again; deleting its line does too.
"""
from __future__ import annotations

import fcntl
import math
import os

import yaml

import wild

MARGIN = 0.25       # cells of level land round the thing's footprint, before the outline goes out to whole cells
SLOPE = 1           # cells the land outside takes to run back to its own height
STEP = 32           # the studio's land heights come in these steps
FOUNTAIN_RADIUS = 192   # a fountain's default radius (map units) when it gives none

# The things each map levels the land under (the sites of tools/xeen/town_fit_pending.yml, 2026-11-24).
# D-174 (xeen-fb4-outdoor9, 2026-11-25): Freeda's tent and the prospector's tent stand at the foot of a mound and in
# the notch cut for them; no pad within CUT_LIMIT fits under them (the land under each tent's own cells differs 864 /
# 672) and without one each tent hangs 180-300 over the slope and is buried 320-420 at its back. Their pads (cuts
# 710 / 670 into the slope behind the tent, no path or landing on it) were looked at and are laid as before.
PADS = {
    'x4': ['thing:sky_crack_ledge', 'thing:olympian_fountain'],
    'x5': ['thing:freeda_tent'],
    'x6': ['thing:oasis_fountain', 'thing:prospector_tent'],
    'd5': ['thing:munchies_1', 'thing:munchies_2'],
    'd6': ['thing:pinnacle'],
}


def _footprint(thing):
    """Half extents in cells (x, y) of the thing's footprint round its `at`."""
    if thing.get('kind') == 'decoration' and 'radius' not in thing:
        import deco_footprint
        half = deco_footprint.footprint(thing.get('decoration', ''))[0] / 512.0
        return half, half
    if thing.get('size'):
        return thing['size'][0] / 1024.0, thing['size'][1] / 1024.0
    radius = float(thing.get('radius', FOUNTAIN_RADIUS)) / 512.0
    for tier in thing.get('tiers') or []:
        radius = max(radius, (float(thing.get('radius', FOUNTAIN_RADIUS)) + float(tier[0])) / 512.0)
    return radius, radius


def apply(sketch, key, ids=None):
    """Pads under the things PADS lists for the map (laid as listed: their sites were looked at by hand), or under
    `ids` (auto's choice): those keep to CUT_LIMIT (D-174), a pad that would move the land more is left out and its
    thing sinks to its rim instead."""
    ruled = ids is not None
    ids = ids if ruled else (PADS.get(key) or [])
    if not ids:
        return []
    record = dict(_heights().get(key) or {})
    terrain = None
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
        def outline(margin):
            x0, x1 = math.floor(cx - hx - margin), math.ceil(cx + hx + margin)
            y0, y1 = math.floor(cy - hy - margin), math.ceil(cy + hy + margin)
            return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        at = [round(float(cx), 3), round(float(cy), 3)]
        kept = record.get(tid)
        margin = MARGIN
        if kept and kept.get('at') == at:
            height = int(kept['height'])
            margin = float(kept.get('margin', MARGIN))
        else:
            if terrain is None:
                terrain = wild._export('xeen_%s' % key) or {}
            if not terrain:
                notes.append('level pad %s: no installed map to read the land from (left out)' % tid)
                continue
            height = int(wild._terrain_at(terrain, cx, cy) // STEP * STEP)
            record[tid] = {'at': at, 'height': height}
        polygon = outline(margin)
        if ruled:
            if terrain is None:
                terrain = wild._export('xeen_%s' % key) or {}
            moved = _moved(terrain, polygon, height, sketch) if terrain else (0, None)
            # D-174 (xeen-fb4-outdoor9): a set piece (a tent, a well, a crate) does not sink as a rock does; over the
            # limit, its pad keeps to the cells its footprint touches (no MARGIN) if that keeps to the limit. The
            # choice is kept with its height (`margin: 0`): on the land built with it the wider pad would read as
            # level and come back (X1's Shepherd's spring, X6's Gorm's coach)
            if moved[0] > CUT_LIMIT and margin > 0 and thing.get('kind') != 'decoration':
                small = outline(0.0)
                moved_small = _moved(terrain, small, height, sketch)
                if moved_small[0] <= CUT_LIMIT:
                    polygon, moved, margin = small, moved_small, 0.0
                    record[tid] = dict(record[tid], margin=0)
            if moved[0] > CUT_LIMIT:
                notes.append(_left_out(terrain, thing, moved))
                continue
        pad = {'polygon': polygon, 'height': height, 'slope': SLOPE,
               'notes': 'level land under %s (common/level_pads.py)' % (thing.get('title') or tid)}
        pad = dict(pad, things=[thing])
        pads.append(dict(pad, parts=[pad]))
        notes.append('level pad %s at %d' % (tid, height))
    # F59 (2026-11-25): pads that touch become one pad over both, at the lower height: two pads side by side at
    # different heights left a step between them that tilted the dressing beside them (X1's orc-cave campfire and its
    # skull pile)
    merged = True
    while merged:
        merged = False
        for i in range(len(pads)):
            for j in range(i + 1, len(pads)):
                if pads[i].get('alone') or pads[j].get('alone'):
                    continue
                a, b = pads[i]['polygon'], pads[j]['polygon']
                if a[0][0] <= b[2][0] and b[0][0] <= a[2][0] and a[0][1] <= b[2][1] and b[0][1] <= a[2][1]:
                    x0, y0 = min(a[0][0], b[0][0]), min(a[0][1], b[0][1])
                    x1, y1 = max(a[2][0], b[2][0]), max(a[2][1], b[2][1])
                    both = {'polygon': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                            'height': min(pads[i]['height'], pads[j]['height']), 'slope': SLOPE,
                            'notes': pads[i]['notes'] + '; ' + pads[j]['notes'],
                            'things': pads[i]['things'] + pads[j]['things'],
                            'parts': pads[i]['parts'] + pads[j]['parts']}
                    # D-174: one pad over both keeps to CUT_LIMIT too (X2's lair pads at the lower one's 960 cut the
                    # bluff either side of the cave mouth from 1,632-1,888); if it would not, its decorations are
                    # left out (they sink to their rim) and its set pieces keep each its own pad, which kept to the
                    # limit alone, unmerged (xeen-fb4-outdoor9: X1's Travellers' tent and its fire, X5's tents and
                    # their fires, the Cyclops' two tents)
                    moved = _moved(terrain, both['polygon'], both['height'], sketch) if ruled and terrain else (0, None)
                    del pads[j]
                    if moved[0] > CUT_LIMIT:
                        del pads[i]
                        for part in both['parts']:
                            thing = part['things'][0]
                            if thing.get('kind') == 'decoration':
                                notes.append(_left_out(terrain, thing, moved))
                            else:
                                pads.append(dict(part, parts=[part], alone=True))
                                notes.append('level pad %s kept alone (one pad with its neighbours would move the '
                                             'land %d)' % (thing.get('id'), moved[0]))
                    else:
                        pads[i] = both
                    merged = True
                    break
            if merged:
                break
    if record != (_heights().get(key) or {}):
        _store(HEIGHTS, HEIGHTS_HEAD, key, record)
    if pads:
        sketch.setdefault('heights', {}).setdefault('terraces', []).extend(
            {k: v for k, v in pad.items() if k not in ('things', 'parts', 'alone')} for pad in pads)
    return notes


# ---- D-174 (agent xeen-fb4-fix7, 2026-11-25): a pad keeps to the land round it ----
# A pad is levelled at the land under its thing's middle over the whole cells round the footprint; a thing on the lip
# of a bluff (X2's lair campfire on the cave mouth's forecourt edge, read at 960) or two pads merged at the lower
# one's height levelled a bluff or filled a bank by hundreds: X2's lair pad cut the bluff either side of the cave
# mouth from 1,632-1,888 to 960 and the party leaving XD-27 landed 110 low (playthrough 15, Q-C23). A pad chosen by
# `auto` may move no node of its land more than CUT_LIMIT, up (fill) or down (cut); one that would is left out and
# its thing, if a decoration, sinks to its rim's lowest land as a rock does (`raise`). The land each node had is read
# from the installed map: the node itself where no pad levelled it yet, and its outline's land (the nodes one cell
# outside, which the pad's SLOPE leaves alone) carried across the pad, so that a map already built with the pad
# reads the same. A pad on a hillside cuts its uphill corner by the slope over about two cells (up to about 256 on
# the steep hillsides F59 levelled); a bluff or a bank is several times that. `python3 level_pads.py --check` lists
# every pad of every outdoor L4 over the limit (the pads PADS lists by hand are listed, not refused).
CUT_LIMIT = 256


def _node_land(terrain, x, y):
    width = terrain['width']
    x, y = max(0, min(width - 1, int(x))), max(0, min(width - 1, int(y)))
    return terrain['height_map'][y * width + x] * terrain['height_scale']


def _moved(terrain, polygon, height, sketch):
    """(most, node): how far the pad moves the land at its worst node (cut or fill), from the installed land. Water
    nodes keep their level under a pad (the studio's levelTerraces) and their bed is not land: they are skipped, and
    an outline node in water does not carry its bed across."""
    x0, x1 = min(p[0] for p in polygon), max(p[0] for p in polygon)
    y0, y1 = min(p[1] for p in polygon), max(p[1] for p in polygon)

    def dry(x, y):
        return None if wild._wet_node(sketch, x, y) else _node_land(terrain, x, y)
    nodes = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if not wild._wet_node(sketch, x, y)]
    # A map already built with this pad holds most of its nodes at its height; a node it does not hold there was laid
    # over after the pads (a cliff, a road's bed, a cave mouth's floor: D1's Sardaj tent on its cliff edge) and the
    # pad does not move it
    built = sum(1 for x, y in nodes if _node_land(terrain, x, y) == height) * 2 >= len(nodes)
    worst = (0, None)
    for x, y in nodes:
        here = _node_land(terrain, x, y)
        if built and here != height:
            continue
        lines = []
        for a, b, t in ((dry(x0 - 1, y), dry(x1 + 1, y), (x - x0 + 1) / (x1 - x0 + 2)),
                        (dry(x, y0 - 1), dry(x, y1 + 1), (y - y0 + 1) / (y1 - y0 + 2))):
            if a is not None and b is not None:
                lines.append(a + (b - a) * t)
        across = sum(lines) / len(lines) if lines else here
        # a cut reads the outline's land across too (a built map's node stands at the pad); a fill only the node's
        # own land: carried across from below a plateau's edge (D1's Sardaj tent) it reads as a fill that is not
        moved = max(max(here, across) - height, height - here)
        if moved > worst[0]:
            worst = (int(round(moved)), (x, y))
    return worst


def _sink(terrain, thing):
    """The `raise` that sinks a decoration to its rim's lowest land (None for anything else or when level)."""
    if thing.get('kind') != 'decoration' or 'raise' in thing:
        return None
    half = deco_footprint.footprint(str(thing.get('decoration', '')).lower())[0]
    drop = _rim_drop(terrain, thing, half) if half > 0 else 0
    return -int(round(drop)) if drop > SINK_DROP else None


def _left_out(terrain, thing, moved):
    sunk = _sink(terrain, thing)
    if sunk is not None:
        thing['raise'] = sunk
    return 'level pad %s left out: it would move the land %d at node %s (CUT_LIMIT %d)%s' % (
        thing.get('id'), moved[0], moved[1], CUT_LIMIT, '; sunk %d to its rim' % -sunk if sunk is not None else '')


HEIGHTS = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'level_pad_heights.yml')
HEIGHTS_HEAD = ('# Each level pad\'s height (common/level_pads.py apply): read once from the installed land at the thing\'s '
                '`at`, then\n# kept while the thing stays there, so a pad does not drift from build to build. Written '
                'by the outdoor generators.\n')


def _load(path):
    if os.path.exists(path):
        return yaml.safe_load(open(path)) or {}
    return {}


def _heights():
    return _load(HEIGHTS)


def _store(path, head, key, value, flow=None):
    """Rewrite one map's entry of a shared yml under a lock (the lanes regenerate several maps at once)."""
    os.makedirs(os.path.join(wild.REPO, 'output', 'xeen_locks'), exist_ok=True)
    with open(os.path.join(wild.REPO, 'output', 'xeen_locks', 'level_pads.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = (yaml.safe_load(open(path)) if os.path.exists(path) else None) or {}
        if value:
            data[key] = value
        else:
            data.pop(key, None)
        with open(path + '.tmp', 'w') as out:
            out.write(head)
            yaml.safe_dump(data, out, sort_keys=True, default_flow_style=flow)
        os.replace(path + '.tmp', path)


# ---- F59 (agent xeen-fb4-outdoor, 2026-11-25): every placed thing on every outdoor map ----
# The player's pins of 2026-11-25 found the same fault on things nobody had listed: Freeda's tent and the Cyclops'
# outpost off their hillsides (X5 p3, p8, p9), a half-buried wagon with one end in the air (X6 p11), a skull pile on
# a steep slope (X4 p7), a boulder over its shadow (X1 p28). `auto(sketch, key)` (run by wild.apply on every outdoor
# map) looks at every placed thing:
# - a set piece with a foot of its own (PAD_KINDS, or a decoration that is titled, clicked or a pile) whose land
#   differs more than PAD_RELIEF across its footprint gets a level pad as above; the chosen ones are kept in
#   level_pads.yml, because a padded thing's land is level at the next run and would otherwise lose its pad;
# - a plain natural decoration (rock, stump, bones, log) of some size stands sunk to its rim's lowest land (`raise`):
#   a boulder lies half buried on a slope instead of hanging over it. The land is not changed for these.
# tools/xeen/town_fit_check.py `things.overhang` and `decorations.slope` list any left.

import os  # noqa: E402
import sys  # noqa: E402

import yaml  # noqa: E402

sys.path.insert(0, os.path.join(wild.REPO, 'tools', 'xeen'))
import deco_footprint  # noqa: E402

KEPT = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'level_pads.yml')
PAD_KINDS = {'tent', 'fountain', 'well', 'portal', 'crate', 'stone_ring'}
PAD_RELIEF = 32          # land this uneven under a set piece's footprint gets a pad
SINK_DROP = 16           # a natural decoration this far over its rim's lowest land sinks to it
SINK_LEAST = 32          # decorations smaller than this (half length) are left alone
SINK_RING = 0.75
SET_WORDS = ('skl', 'skull', 'pile', 'wagon', 'cart', 'statue', 'altar', 'stall', 'hay')   # hay: haybales
# by decoration_data.txt's description: what lies where the land puts it (half sunk on a slope reads right)
NATURAL_WORDS = ('rock', 'boulder', 'stump', 'log', 'bones', 'skeleton', 'corpse', 'trash', 'wood',
                 'rune stone',   # rock65-70 'ancient rune stone': set in the ground (X3's yard_2)
                 'basalt')       # F73 (2026-11-26, X7 p6): the world's model boulders (xeen_basalt1-3, xeen_boulder)
                                 # stood upright at their middle's land on the crags, tilted-looking and half in air
SET_LARGEST = 384        # a set piece wider than this (a Sphinx, a hull piece) is a building's matter, not a pad's


def _kept():
    if os.path.exists(KEPT):
        return yaml.safe_load(open(KEPT)) or {}
    return {}


def _relief(terrain, thing):
    cx, cy = thing['at'][0], thing['at'][1]
    hx, hy = _footprint(thing)
    if thing.get('turn') and float(thing['turn']) % 180 != 0:
        hx = hy = math.hypot(hx, hy)
    lands = [wild._terrain_at(terrain, cx + hx * fx, cy + hy * fy) for fx in (-1, -0.5, 0, 0.5, 1)
             for fy in (-1, -0.5, 0, 0.5, 1)]
    return max(lands) - min(lands)


SLOPE_GAP = 20           # tools/xeen/town_fit_check.py SLOPE_GAP (24) less a margin for the land's rounding


def _rim_drop(terrain, thing, half):
    """How far the land at a thing's middle stands over the lowest land at SINK_RING of its radius."""
    cx, cy = thing['at'][0], thing['at'][1]
    mid = wild._terrain_at(terrain, cx, cy)
    return mid - min(wild._terrain_at(terrain, cx + math.cos(a) * half * SINK_RING / 512.0,
                                      cy + math.sin(a) * half * SINK_RING / 512.0)
                     for a in [k * math.pi / 6 for k in range(12)])


def _wet_under(sketch, thing):
    cx, cy = thing['at'][0], thing['at'][1]
    hx, hy = _footprint(thing)
    return any(wild._wet(sketch, cx + hx * fx, cy + hy * fy) for fx in (-1, 0, 1) for fy in (-1, 0, 1))


def _ground(terrain, cx, cy):
    """The land at a cell point on the game's triangles (tools/xeen/wall_check.py Terrain.ground), not bilinear:
    F73 (2026-11-26, X7 p6): on a crag's edge the two differ by tens, and boulders sunk by the bilinear land still
    stood 28-51 over their rim as the game draws it."""
    width, scale, heights = terrain['width'], terrain['height_scale'], terrain['height_map']
    x0, y0 = int(math.floor(cx)), int(math.floor(cy))
    fx, fy = cx - x0, cy - y0

    def h(x, y):
        x, y = max(0, min(width - 1, x)), max(0, min(width - 1, y))
        return heights[y * width + x] * scale
    z00, z10, z01, z11 = h(x0, y0), h(x0 + 1, y0), h(x0, y0 + 1), h(x0 + 1, y0 + 1)
    if fx >= fy:
        return z00 + (z10 - z00) * fx + (z11 - z10) * fy
    return z00 + (z11 - z01) * fx + (z01 - z00) * fy


def _natural(name):
    return any(word in deco_footprint.description(name) for word in NATURAL_WORDS)


def _is_set_decoration(thing):
    name = str(thing.get('decoration', '')).lower()
    if thing.get('title') or thing.get('effects') or thing.get('event') or thing.get('hint'):
        return not _natural(name) or 'skl' in name
    return any(word in name for word in SET_WORDS)


def auto(sketch, key):
    terrain = wild._export('xeen_%s' % key) or {}
    if not terrain:
        return []
    kept = _kept()
    chosen = set(kept.get(key) or [])
    listed = set(PADS.get(key) or [])
    notes = []
    for thing in sketch.get('structures') or []:
        tid, kind = thing.get('id'), thing.get('kind')
        if not tid or 'at' not in thing or thing.get('on') or thing.get('floor') is not None:
            continue
        if not isinstance(thing['at'], list) or len(thing['at']) < 2 or tid in listed:
            continue
        if kind == 'decoration':
            name = str(thing.get('decoration', '')).lower()
            half, _ = deco_footprint.footprint(name)
            # the world's own models are set pieces (idols, sphinxes, statues), except its rocks (F73: X7 p6)
            if half < SINK_LEAST or half > SET_LARGEST or 'tree' in name or (name.startswith('xeen_')
                                                                              and not _natural(name)):
                continue
            if _is_set_decoration(thing):
                probe = dict(thing, radius=half)
                # 2026-11-25 (xeen-fb4-outdoor2): also the check's own measure (town_fit_check decorations.slope: the
                # middle more than SLOPE_GAP over the lowest land at 0.75 of the radius): X2's Yak skull pile had 26
                # relief across its footprint (no pad) and stood 24-26 over its rim
                if tid in chosen or ((_relief(terrain, probe) > PAD_RELIEF or _rim_drop(terrain, thing, half) > SLOPE_GAP)
                                     and not _wet_under(sketch, probe)):
                    chosen.add(tid)
                continue
            if 'raise' in thing or not _natural(name):
                continue
            cx, cy = thing['at'][0], thing['at'][1]
            mid = _ground(terrain, cx, cy)
            ring = min(_ground(terrain, cx + math.cos(a) * half * SINK_RING / 512.0,
                               cy + math.sin(a) * half * SINK_RING / 512.0)
                       for a in [k * math.pi / 6 for k in range(12)])
            if mid - ring > SINK_DROP:
                thing['raise'] = -int(round(mid - ring))
                notes.append('sink %s (%s) %d to its rim' % (tid, name, mid - ring))
        elif kind in PAD_KINDS:
            if tid in chosen or (_relief(terrain, thing) > PAD_RELIEF and not _wet_under(sketch, thing)):
                chosen.add(tid)
    present = {thing.get('id') for thing in sketch.get('structures') or []}
    chosen = (chosen & present) - listed     # a thing PADS lists by hand is laid by apply(sketch, key), not here
    if chosen != set(kept.get(key) or []):
        _store(KEPT, '# Things that stand on a level pad (common/level_pads.py auto, F59): written by the outdoor '
               'generators;\n# a padded thing\'s land is level afterwards, so the choice is kept here.\n', key,
               sorted(chosen), flow=False)
    record = _heights().get(key) or {}
    if set(record) - chosen - listed:     # heights of things no longer padded
        _store(HEIGHTS, HEIGHTS_HEAD, key, {tid: v for tid, v in record.items() if tid in chosen | listed})
    return notes + apply(sketch, key, sorted(chosen))


def check(keys=None):
    """D-174: every level pad of each outdoor L4 sketch that moves the installed land more than CUT_LIMIT."""
    briefs = os.path.join(wild.REPO, 'devdocs', 'xeen', 'briefs')
    found = []
    for key in sorted(keys or os.listdir(briefs)):
        path = os.path.join(briefs, key, 'L4', 'sketch.yml')
        if not os.path.exists(path) or not os.path.exists(os.path.join(briefs, key, 'L4', 'project.yml')):
            continue
        sketch = yaml.safe_load(open(path)) or {}
        terraces = [t for t in (sketch.get('heights') or {}).get('terraces') or []
                    if 'common/level_pads.py' in str(t.get('notes', ''))]
        terrain = wild._export('xeen_%s' % key) if terraces else None
        for terrace in terraces if terrain else []:
            moved = _moved(terrain, terrace['polygon'], terrace['height'], sketch)
            if moved[0] > CUT_LIMIT:
                titles = {t.get('id'): t.get('title') or t.get('id') for t in sketch.get('structures') or []}
                hand = any(('under %s ' % titles.get(tid, tid)) in terrace['notes'] for tid in PADS.get(key) or [])
                if not hand:
                    found.append((key, moved, terrace))
                print('%s: %s at %d moves the land %d at node %s%s' % (
                    key, terrace['notes'].replace(' (common/level_pads.py)', ''), terrace['height'], moved[0],
                    moved[1], ' (listed by hand in PADS)' if hand else ''))
    return found


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=check.__doc__)
    parser.add_argument('--check', action='store_true', help='list the pads over CUT_LIMIT; exit 1 if any')
    parser.add_argument('maps', nargs='*', help='outdoor map keys (x1 ... d6); default every outdoor L4')
    args = parser.parse_args()
    sys.exit(1 if check(args.maps) and args.check else 0)
