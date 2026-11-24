"""Shared wild-land rules for Xeen's outdoor generators (P2 feedback F29, F32, F33; agent xeen-fb2-wild, 2026-11-23).

Each outdoor map's gen.py calls `apply(sketch, '<key>')` on its finished sketch just before writing it:

- **Shrine altars (F32).** A shrine pavilion (a `building` part on `posts` whose click gives something) gets an altar
  block under its roof, and the click moves onto the altar: the pavilion keeps only its title. As MM6's prefab shrines
  (OUTE1 event 261 on the altar faces of `shrineE` only) and MM7's "Shrine" (hint) / "Altar" (the click) pairs.
- **Campfires (F33).** Every campfire decoration without an event of its own feeds the party once (MM8 Global 285/286
  "Camp Fire": food, then the event is gone) and a character with Perception finds a small ring on the cursor (MM7's
  campfire, Global 1162/1163 here); the status line says what was found (F13). `once: true` gives each fire a map
  variable of its own: evt.ChangeEvent(0), MM8's way, only works on native interactive decorations (a decoration
  variable), not on a studio thing, and left every fire giving food and rings forever (Discord, 2026-11-24).
- **The rim fall (F29).** The sea under the world rim (`water:sky` / `water:rim_sea`, level 0) gets a timer event: a
  party in it or in the rim's foot below Xeen.RimFallDepth (not flying) is lifted back onto the rim at the nearest of
  a few return points and falls the last Xeen.SkyFallHeight (xeen_common.lua `Xeen.rimFall`). The return points
  stand on the built map's land (the installed ODM's heights, read through `oymap export`), at least three cells in
  from the sea, on level ground, away from structures.
- **Bridge ends (F48, agent xeen-fb3-outdoor, 2026-11-24).** A bridge or pier whose deck is level at `height` meets
  the land at each end that stands on land: the land under its last cell and a cell and a half beyond it is set to
  the deck less BRIDGE_SINK (a `heights.terraces` pad, its edge running back over BRIDGE_SLOPE cells), so the party
  walks on and off it without a step (The Great Bridge, the causeway and the jetties stood 56-87 over the land at
  their ends; Medin's jetty ran 102 into its bank). An end over water (a pier's head) and an end that stands far
  over or under the land by design (more than BRIDGE_DESIGN: a jetty that ends in the air, a rope walk between
  trees) are left; the land is read from the installed map (as the rim fall's points).
- **House tents (F47).** A tent that is a house (`house:`) has a closed front with a door, and the house's click is on
  the door only (the studio puts a tent's event on its door face when it has one): an open tent took the click on
  every face of its canvas, so Ebenezer's Tent opened from deep inside it (X3 p9).
- **Free-standing mouths (F50).** A cave mouth that stands free on open land (`free: true`) with a shell of the
  ground's own dirt or grass (or none) is built of stone (FREE_SHELL): on flat land a dirt shell reads as a plain
  brown wedge, not a way in (the Tomb of a Thousand Terrors, X3 p8). Shipped mouths take the ground's texture only
  where the shell is the hillside.

`tools/xeen/check_rim.py`, `tools/xeen/check_wild.py` and `tools/xeen/town_fit_check.py` (`bridges.step`) check the
built maps.
"""
from __future__ import annotations

import json
import math
import os
import subprocess

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..'))
FIRES = {'cmpfyr00', 'ckfyr00', 'dec24', 'dec25', 'dec04', '7dec02'}
# fires that are set pieces of a talk or a quest, and fires that are not camp fires
FIRE_SKIP = {'thing:parley_fire', 'thing:cinder_smoke'}
RIM_SEAS = {'water:sky', 'water:rim_sea'}
RIM_VOIDS = {'void:sky', 'void:rim_sea', 'void:cove'}   # void:cove: X6's notch (agent xeen-rimmap-b)
CACHE = os.path.join(REPO, 'output', 'xeen_rim_cache')

CAMPFIRE_LUA = ('local food = math.random(1, 3) evt.Add(Food, food) '
                'local ring = IsAtLeast(PerceptionSkill, 1) '
                'if ring then evt.GiveItem(1, ItemType.Ring_) end '
                'if ring then evt.StatusText("Food by the fire (+" .. food .. "), and a ring in the ashes.") '
                'else evt.StatusText("You find food by the fire (+" .. food .. ").") end')
# final cloud round (2026-11-24): the door 128 wide, the width of xvdoor's picture (192 laid it 1.5 times across:
# oymap audit `doors.tiled` on Ebenezer's Tent)
TENT_DOOR = {'wall_height': 192, 'door_width': 128, 'door_height': 192, 'door': 'xvdoor'}
GROUND_SHELLS = {'7dirttyl', 'dirttyl', 'grastyl', '7grastyl', 'dirt', 'grass'}
FREE_SHELL = 'cwb1'      # the stone the other cave mouths and adits are built of
BRIDGE_SINK = 8          # the pad under a deck's end stands this far under the deck
BRIDGE_SLOPE = 2         # cells the land takes to run back from the pad
BRIDGE_DESIGN = 200      # an end this far off the land is meant to stand off it
CLICK_KEYS = ('condition', 'effects', 'else_effects', 'locked_text', 'question', 'once', 'lua')


def W(x, y):
    return (x - 64) * 512.0, (64 - y) * 512.0


# ---- F32: shrine altars ----

def _part_middle(thing, part):
    """A building part's middle in cells (the plot's `at` is its north-west corner, parts in units from it)."""
    ax, ay = thing['at']
    if part.get('shape') == 'round' or 'radius' in part:
        px, py = part['at']
    else:
        px, py = part['at'][0] + part['size'][0] / 2.0, part['at'][1] + part['size'][1] / 2.0
    return [round(ax + px / 512.0, 3), round(ay + py / 512.0, 3)]


def shrine_altars(sketch):
    notes = []
    added = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'building' or thing.get('turn'):
            continue
        for part in thing.get('parts') or []:
            if not isinstance(part, dict) or not part.get('posts'):
                continue
            holder = part if part.get('effects') else (thing if thing.get('effects') else None)
            title = '%s %s' % (part.get('title') or '', thing.get('title') or '')
            if holder is None or 'shrine' not in title.lower():
                continue          # a bell frame, a lean-to: their click is the thing itself
            altar = {'id': thing['id'] + '_altar', 'kind': 'platform', 'at': _part_middle(thing, part),
                     'size': [192, 128], 'height': 128,
                     'title': part.get('title') or thing.get('title') or 'Altar'}
            wall = (part.get('textures') or {}).get('wall') or (thing.get('textures') or {}).get('wall')
            if wall:
                altar['textures'] = {'wall': wall, 'top': wall}
            for key in CLICK_KEYS:
                if key in holder:
                    altar[key] = holder.pop(key)
            altar['notes'] = ('F32 (P2 pin p16, 2026-11-23): the shrine\'s altar under its roof carries the click; '
                              'the pavilion keeps its title (MM6 OUTE1 261, MM7 "Shrine"/"Altar").')
            added.append(altar)
            notes.append('altar under %s at %s' % (thing['id'], altar['at']))
    sketch['structures'] = list(sketch.get('structures') or []) + added
    return notes


# ---- F33: campfires ----

def campfires(sketch):
    notes = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'decoration' or thing.get('decoration') not in FIRES:
            continue
        if thing['id'] in FIRE_SKIP or any(key in thing for key in CLICK_KEYS):
            continue
        thing['once'] = True
        thing['effects'] = [{'lua': CAMPFIRE_LUA}]
        if not thing.get('title'):
            thing['title'] = 'Campfire'
        notes.append('campfire %s' % thing['id'])
    return notes


# ---- F29: the rim fall ----

def _export(stem):
    """The installed map's terrain; XEEN_WILD_MAPS=<folder> reads <stem>.odm from that folder instead (a scratch
    build of the same map whose land changed: its return points then follow the new land, D-109)."""
    os.makedirs(CACHE, exist_ok=True)
    folder = os.environ.get('XEEN_WILD_MAPS') or os.path.join(REPO, 'assets_dev', 'worlds', 'xeen', 'maps')
    odm = os.path.join(folder, stem + '.odm')
    out = os.path.join(CACHE, stem + ('.scratch' if os.environ.get('XEEN_WILD_MAPS') else '') + '.odm.json')
    if not os.path.exists(odm):
        return None
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(odm):
        subprocess.run([os.path.join(REPO, 'openyamm-studio', 'build-xeen', 'oymap'), 'export', odm, '--world',
                        'xeen', '--assets', os.path.join(REPO, 'assets_dev'), '--out', out],
                       capture_output=True, text=True, timeout=600, check=True)
    return json.load(open(out))['map']['terrain']


def _inside(poly, x, y):
    hit = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def rim_seas(sketch):
    """The rim's polygons (cells): the sea under it, or its `void` once common/rim.py has turned the sea into one
    (U-12)."""
    return [body['polygon'] for body in (sketch.get('water') or {}).get('bodies') or []
            if body.get('id') in RIM_SEAS and (body.get('level') or 0) <= 0] + \
        [void['polygon'] for void in sketch.get('void') or [] if void.get('id') in RIM_VOIDS]


def reachable_nodes(terrain, start):
    """Terrain nodes the party walks to from `start` (cells): over land at 320 or more, no step between neighbours
    over 384 (a triangle whose corners differ by more than 512 slides the party down)."""
    width = terrain['width']
    scale = terrain['height_scale']
    heights = terrain['height_map']
    seen = {start}
    todo = [start]
    while todo:
        x, y = todo.pop()
        here = heights[y * width + x] * scale
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < width) or (nx, ny) in seen:
                continue
            there = heights[ny * width + nx] * scale
            if there < 320 or abs(there - here) > 384:
                continue
            seen.add((nx, ny))
            todo.append((nx, ny))
    return seen


def start_node(key):
    path = os.path.join(REPO, 'assets_dev', 'worlds', 'xeen', 'maps', 'xeen_%s.studio.yml' % key)
    for line in open(path):
        if '{name: "start"' in line:
            values = line.split('at: [')[1].split(']')[0].split(',')
            x, y = float(values[0]), float(values[1])
            return int(round(x / 512.0 + 64)), int(round(64 - y / 512.0))
    return None


def rim_points(sketch, terrain, seas, spacing=6, inward=3, reach=None):
    width = terrain['width']
    scale = terrain['height_scale']
    heights = terrain['height_map']

    def node(x, y):
        x = min(max(int(x), 0), width - 1)
        y = min(max(int(y), 0), width - 1)
        return heights[y * width + x] * scale

    taken = [tuple(t['at']) for t in sketch.get('structures') or []
             if isinstance(t.get('at'), list) and len(t['at']) == 2 and all(isinstance(v, (int, float)) for v in t['at'])]
    points = []
    for sea in seas:
        for index, a in enumerate(sea):
            b = sea[(index + 1) % len(sea)]
            length = math.dist(a, b)
            steps = max(1, int(length // spacing))
            for step in range(steps):
                share = (step + 0.5) / steps
                px, py = a[0] + (b[0] - a[0]) * share, a[1] + (b[1] - a[1]) * share
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cx, cy = round(px + dx * (inward + 1)), round(py + dy * (inward + 1))
                    if not (4 <= cx <= 123 and 4 <= cy <= 123):
                        continue
                    if any(_inside(s, cx, cy) for s in seas):
                        continue
                    around = [node(cx + i, cy + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
                    if min(around) < 320 or max(around) - min(around) > 192:
                        continue
                    if reach is not None and (cx, cy) not in reach:
                        continue
                    if any(math.dist((cx, cy), t) < 2.0 for t in taken):
                        continue
                    if any(math.dist((cx, cy), (q[4], q[5])) < spacing - 1 for q in points):
                        continue
                    x, y = W(cx, cy)
                    yaw = {(1, 0): 0, (-1, 0): 1024, (0, 1): 1536, (0, -1): 512}[(dx, dy)]
                    points.append([int(x), int(y), int(node(cx, cy)), yaw, cx, cy])
                    break
    return points


def rim_fall(sketch, key):
    seas = rim_seas(sketch)
    if not seas:
        return []
    stem = 'xeen_' + key
    terrain = _export(stem)
    if terrain is None:
        return ['rim fall: %s is not installed; no return points' % stem]
    start = start_node(key)
    points = rim_points(sketch, terrain, seas, reach=reachable_nodes(terrain, start) if start else None)
    if not points:
        return ['rim fall: no return point found on %s' % stem]
    lua_seas = '{' + ', '.join('{' + ', '.join('{%d, %d}' % W(x, y) for x, y in sea) + '}' for sea in seas) + '}'
    lua_points = '{' + ', '.join('{%d, %d, %d, %d}' % tuple(p[:4]) for p in points) + '}'
    event = {'id': 'evt:rim_fall', 'trigger': 'timer', 'every': 1,
             'lua': 'Xeen.rimFall(%s, %s)' % (lua_seas, lua_points),
             'notes': ('F29 (P2 pins p7, p12; 2026-11-23): a party in the sea below the world rim, or in the rim\'s '
                       'foot below Xeen.RimFallDepth, is lifted back onto the rim at the nearest return point and '
                       'falls the last Xeen.SkyFallHeight (common/wild.py, xeen_common.lua Xeen.rimFall). Return '
                       'points (cells): %s.' % ', '.join('[%d, %d]' % (p[4], p[5]) for p in points))}
    events = [e for e in sketch.get('events') or [] if e.get('id') != 'evt:rim_fall']
    sketch['events'] = events + [event]
    return ['rim fall: %d return points %s' % (len(points), [(p[4], p[5]) for p in points])]


# ---- F47, F50: house tents, free-standing mouths ----

def house_tents(sketch):
    notes = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'tent' or not thing.get('house') or (thing.get('textures') or {}).get('door'):
            continue
        thing['open'] = False
        thing.pop('awning', None)
        thing.setdefault('wall_height', TENT_DOOR['wall_height'])
        thing.setdefault('door_width', TENT_DOOR['door_width'])
        thing.setdefault('door_height', TENT_DOOR['door_height'])
        thing.setdefault('textures', {})['door'] = TENT_DOOR['door']
        if float(thing.get('height', 320)) < thing['wall_height'] + 32:
            thing['height'] = thing['wall_height'] + 128
        notes.append('house tent %s: a door on its front' % thing['id'])
    return notes


def free_mouths(sketch):
    notes = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'cave_mouth' or not thing.get('free'):
            continue
        textures = thing.setdefault('textures', {})
        if str(textures.get('shell', '')).lower() in GROUND_SHELLS | {''}:
            textures['shell'] = FREE_SHELL
            notes.append('free mouth %s: a stone shell' % thing['id'])
    return notes


# ---- F50: no windows in a ruin's walls ----
# X2 p9 (2026-11-24, "missing texture"): a ruined cottage's `windows: alternate` drew the kit's glazed window as a black
# slot in a broken 32-thick wall, and its low broken course as a strip of the kit's trim. A ruin's walls are
# broken by its `gaps`; they carry no windows (the ruins of D1, D2, D4-D6, X5, X7 never had any).

# The studio's MM7 kits' wall textures (openyamm-studio/core/OutdoorBuildings.cpp): a ruin's broken tops and low
# courses take the wall's stone, not the kit's timber trim (trim2_32a read as a smeared strip, X2 p9)
KIT_WALLS = {'stone': 'chb1', 'grey': 'hhm3b', 'poor': 'hhp1b', 'timber': 'hhm1b1', 'plaster': 'hhm2b2',
             'rich': '7hhr1b', 'castle': 'ch1b1'}


def ruin_windows(sketch):
    notes = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'building' or not thing.get('ruin'):
            continue
        textures = thing.setdefault('textures', {})
        wall = textures.get('wall') or KIT_WALLS.get(thing.get('kit'))
        if wall and 'trim' not in textures:
            textures['trim'] = wall
            notes.append('ruin %s: trim in its wall (%s)' % (thing['id'], wall))
        for part in thing.get('parts') or []:
            if part.get('windows', 'none') != 'none':
                part['windows'] = 'none'
                notes.append('ruin %s/%s: no windows' % (thing['id'], part.get('id')))
    return notes


# ---- F48: the bridge ends ----

def _wet(sketch, x, y):
    water = sketch.get('water') or {}
    for body in water.get('bodies') or []:
        if body.get('polygon') and _inside(body['polygon'], x, y):
            return True
    for river in water.get('rivers') or []:
        line, half = river.get('line') or [], (river.get('width_cells') or 1) * 0.5
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            dx, dy = x2 - x1, y2 - y1
            t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / max(dx * dx + dy * dy, 1e-9)))
            if math.hypot(x1 + t * dx - x, y1 + t * dy - y) <= half:
                return True
    return False


def _water_levels(sketch):
    water = sketch.get('water') or {}
    return [w['level'] for w in (water.get('bodies') or []) + (water.get('rivers') or []) if 'level' in w]


def bridge_ends(sketch, key):
    """F48: a pad of land at each land end of every level bridge, at its deck's height."""
    terrain = None
    notes = []
    pads = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'bridge' or 'height' not in thing or len(thing.get('line') or []) < 2:
            continue
        if thing.get('piers') == 0:
            continue        # a hull afloat (D4's ferry, its skiff): no land end (P3: the ferry was drawn up the shore)
        if terrain is None:
            terrain = _export('xeen_%s' % key) or {}
        if not terrain:
            return []
        deck = float(thing['height'])
        half = float(thing.get('width', 384)) / 1024.0 + 0.75
        line = thing['line']
        for index in (0, len(line) - 1):
            end, before = line[index], line[1 if index == 0 else -2]
            ux, uy = end[0] - before[0], end[1] - before[1]
            length = math.hypot(ux, uy)
            ux, uy = ux / length, uy / length
            levels = _water_levels(sketch)

            def wet(px, py):
                # the studio levels land under water to its surface (an islet's terrace inside a lake stays dry)
                return any(abs(_terrain_at(terrain, px, py) - level) <= 8 for level in levels)
            # The land beyond the end: the first dry point within a cell and a half (an islet's shore a little past
            # a causeway's end counts); none, and the end is a pier's head over the water.
            if all(wet(end[0] + ux * k, end[1] + uy * k) for k in (0.5, 1.0, 1.5)):
                continue
            # The studio levels water to its surface, so a pad's nodes under the deck inside the water stay low and
            # the land still falls away under the deck's end: on a straight bridge along a cell axis the end goes on
            # to the first node line out of the water, where the pad's land is.
            new_end = list(end)
            if abs(ux) < 1e-6 or abs(uy) < 1e-6:
                axis = 0 if abs(ux) > abs(uy) else 1
                sign = 1 if (ux if axis == 0 else uy) > 0 else -1
                target = math.ceil(end[axis]) if sign > 0 else math.floor(end[axis])
                # P3 (2026-11-24): every node across the deck's width out of the water, not only the centre line's
                # (Island jetty's centre lay between a dry node row and a wet one: the studio levelled the wet row's
                # nodes and its end stood 48 over the land)
                across = 1 - axis
                span = range(math.floor(end[across] - half + 0.75), math.ceil(end[across] + half - 0.75) + 1)
                for _ in range(3):
                    probe = list(end)
                    probe[axis] = target
                    nodes = [(target, j) if axis == 0 else (j, target) for j in span]
                    if not any(wet(px, py) for px, py in nodes):
                        break
                    target += sign
                # 16 past the node line: walls stand on node lines, and an end face in a wall's face drew in one plane
                # with it (X2's quay walls, P3 2026-11-24)
                new_end[axis] = target + sign / 32.0
            # P3 (2026-11-24): a buried end is no longer pulled back to where the installed land met it (that land was
            # the old deck's cut: the next build's bank stood 64 over the shortened deck, Medin's jetty, X2 p10); it
            # keeps its end and takes the pad below, which cuts its bank down to the deck.
            lands = [_terrain_at(terrain, new_end[0] + ux * d, new_end[1] + uy * d) for d in (0.05, 0.12, 0.25)]
            land = max(lands, key=lambda z: abs(deck - z))
            if deck - land > BRIDGE_DESIGN:
                continue        # a deck ending in the air by design (a buried end is always cut down to: its pad)
            if new_end != list(end):
                notes.append('bridge end %s: on to the node line (%.2f, %.2f)' % (thing['id'], *new_end))
                end = new_end
                line[index] = end
            # Every land end takes its pad, whatever the installed land shows: these rules read the installed map, so a
            # pad left out once its land had come up to the deck was gone again at the next build (the step back,
            # X2's island jetty +36 after a rebuild). Only land already at the deck's own height (a town square the
            # bridge starts from) is left as it is.
            if abs(deck - land) <= 4:
                continue
            vx, vy = -uy * half, ux * half
            a = (end[0] - ux * 0.25, end[1] - uy * 0.25)
            b = (end[0] + ux * 1.5, end[1] + uy * 1.5)
            polygon = [[round(a[0] + vx, 3), round(a[1] + vy, 3)], [round(b[0] + vx, 3), round(b[1] + vy, 3)],
                       [round(b[0] - vx, 3), round(b[1] - vy, 3)], [round(a[0] - vx, 3), round(a[1] - vy, 3)]]
            pads.append({'polygon': polygon, 'height': int(deck - BRIDGE_SINK), 'slope': BRIDGE_SLOPE,
                         'notes': 'F48: the land meets %s\'s deck at its end (common/wild.py bridge_ends)'
                                  % thing.get('title', thing['id'])})
            notes.append('bridge end %s (%.1f, %.1f): land %d -> %d' % (thing['id'], end[0], end[1], land,
                                                                       deck - BRIDGE_SINK))
    if pads:
        sketch.setdefault('heights', {}).setdefault('terraces', []).extend(pads)
    return notes


def _terrain_at(terrain, cx, cy):
    """The installed map's land at a cell point (bilinear over its nodes)."""
    width, scale, heights = terrain['width'], terrain['height_scale'], terrain['height_map']
    x0, y0 = int(math.floor(cx)), int(math.floor(cy))
    fx, fy = cx - x0, cy - y0

    def h(x, y):
        x, y = max(0, min(width - 1, x)), max(0, min(width - 1, y))
        return heights[y * width + x] * scale
    return (h(x0, y0) * (1 - fx) * (1 - fy) + h(x0 + 1, y0) * fx * (1 - fy) + h(x0, y0 + 1) * (1 - fx) * fy
            + h(x0 + 1, y0 + 1) * fx * fy)


def apply(sketch, key):
    """All the rules on a finished outdoor sketch, then the rim's void and hull (common/rim.py, U-12); returns notes
    to print."""
    if not isinstance(sketch, dict) or 'structures' not in sketch:
        return []
    import rim  # noqa: E402 (beside this file)
    notes = rim.apply(sketch, key)
    return (shrine_altars(sketch) + campfires(sketch) + notes + rim_fall(sketch, key) + bridge_ends(sketch, key)
            + house_tents(sketch) + free_mouths(sketch) + ruin_windows(sketch))
