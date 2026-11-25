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
- **Bridge ends (F48, agent xeen-fb3-outdoor, 2026-11-24; D-170, 2026-11-25).** A bridge or pier whose deck is level
  at `height` meets the land at each end that stands on land: the land under its last cell and a cell and a half
  beyond it, the deck's width and half a cell each side, is set to the highest of the land's 32 steps at least
  BRIDGE_UNDER under the deck (a `heights.terraces` pad, its edge running back over BRIDGE_SLOPE cells), so the party
  walks on and off it without a step; an end that meets a terrace at the deck's own height takes no pad and stops 16
  short of the terrace's edge on the water side. A deck that follows the land (no `height`) gets a flat pad beyond and
  beside each end at the lowest land across it, and the studio stands the end 16 over it. Under every deck, each node
  of a cell it covers that stands at or over the step under the deck there is cut to that step (The Great Bridge, the causeway and the jetties stood 56-87 over the land at
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

- **Things on slopes (F59, agent xeen-fb4-outdoor, 2026-11-25).** Every set piece with a foot of its own (tents,
  fountains, wells, crates, stone rings, titled or clicked decorations, piles) on uneven land gets a level pad, and a
  plain rock, stump or bone heap sinks to its rim's lowest land (common/level_pads.py `auto`).

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
BRIDGE_UNDER = 4         # D-170: the land under a deck stands at least this far under it, on the land's 32 steps
BRIDGE_SLOPE = 2         # cells the land takes to run back from the pad
BRIDGE_STEP = 32         # D-174: tools/xeen/town_fit_check.py BRIDGE_STEP: a terrace this far over a deck is not its land
BRIDGE_DESIGN = 200      # an end this far off the land is meant to stand off it
# F58 (2026-11-25): a level deck on a land step standing DECK_LIFT over it, so it no longer lies on the land; off (0)
# for now: lifting X2's decks by 4 broke their ends' fit (bridges.step +36/-42, the quay terraces win over the pads)
DECK_LIFT = 0
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


def _wet_node(sketch, x, y):
    """D-170: a node the studio keeps as water: in a body, or within a river's half width, a river narrower than two
    cells being laid two wide (the studio's warning), and a little over (its node rounding)."""
    water = sketch.get('water') or {}
    for body in water.get('bodies') or []:
        if body.get('polygon') and _inside(body['polygon'], x, y):
            return True
    for river in water.get('rivers') or []:
        line, half = river.get('line') or [], max(river.get('width_cells') or 1, 2) * 0.5 + 0.25
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            dx, dy = x2 - x1, y2 - y1
            t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / max(dx * dx + dy * dy, 1e-9)))
            if math.hypot(x1 + t * dx - x, y1 + t * dy - y) <= half:
                return True
    return False


def _water_levels(sketch):
    water = sketch.get('water') or {}
    return [w['level'] for w in (water.get('bodies') or []) + (water.get('rivers') or []) if 'level' in w]


def _step_under(z):
    """D-170: the highest of the land's 32 steps at least BRIDGE_UNDER under z."""
    return int(math.floor((z - BRIDGE_UNDER) / 32.0)) * 32


def _square(cx, cy, half_x, half_y):
    return [[round(cx - half_x, 3), round(cy - half_y, 3)], [round(cx + half_x, 3), round(cy - half_y, 3)],
            [round(cx + half_x, 3), round(cy + half_y, 3)], [round(cx - half_x, 3), round(cy + half_y, 3)]]


def _node(terrain, x, y):
    width = terrain['width']
    x, y = max(0, min(width - 1, x)), max(0, min(width - 1, y))
    return terrain['height_map'][y * width + x] * terrain['height_scale']


def bridge_ends(sketch, key):
    """F48, D-170: the land at each land end of every bridge and under its deck, from the installed map's land."""
    terrain = None
    notes = []
    pads = []
    ends_seen = set()
    for thing in sketch.get('structures') or []:
        if thing.get('kind') != 'bridge' or len(thing.get('line') or []) < 2:
            continue
        if thing.get('piers') == 0:
            continue        # a hull afloat (D4's ferry, its skiff) or a rope walk: no land end
        if terrain is None:
            terrain = _export('xeen_%s' % key) or {}
        if not terrain:
            return []
        level = 'height' in thing
        deck = float(thing['height']) if level else None
        line = thing['line']
        # F67 X2 p12 (2026-11-25): `head: first|last` names a pier's head over the water, never a land end, even with
        # a dry bank within a cell and a half beyond it (a river pier's far bank); the studio does not know the word
        head = thing.pop('head', None)
        # D-170: `pad_beyond: <cells>` runs a land-following end's pad that far beyond the end with BRIDGE_SLOPE (a road
        # graded through the end pulls an end-cell pad back up its bank: D2's log bridge); the studio does not know it
        pad_beyond = thing.pop('pad_beyond', None)
        heads = {0} if head == 'first' else {len(line) - 1} if head == 'last' else set()
        # F58 (2026-11-25): a level deck on a land step standing DECK_LIFT over it; off (0), D-170 replaced it
        if DECK_LIFT and level and deck % 32 == 0 and any(abs(_terrain_at(terrain, *line[i]) - deck) <= 4
                                                           for i in (0, len(line) - 1) if i not in heads):
            deck += DECK_LIFT
            thing['height'] = int(deck)
        width = float(thing.get('width', 384))
        lift = float(thing.get('raise', 16))
        # D-170: a pad spans the deck's width and half a cell each side
        half = width / 1024.0 + 0.5
        levels = _water_levels(sketch)

        def wet(px, py):
            # the studio levels land under water to its surface (an islet's terrace inside a lake stays dry). D-174
            # (xeen-fb4-fix7, 2026-11-25): and only where the sketch has water: read from the installed land alone, the
            # land a deck's own cut had lowered to the lake's level read as water, the end moved on inland and the
            # cut followed it (X2's island jetty: 36.0 -> 33.97, a trench at 640 across the island's 768 crown)
            return _wet_node(sketch, px, py) and any(abs(_terrain_at(terrain, px, py) - level_) <= 8 for level_ in levels)
        # each end: the deck's height there (None: left as the studio makes it) and whether the land beyond it is kept
        end_z = {}
        kept_beyond = set()
        end_pads = []
        for index in (0, len(line) - 1):
            if index in heads:
                kept_beyond.add(index)
                continue
            end, before = line[index], line[1 if index == 0 else -2]
            ux, uy = end[0] - before[0], end[1] - before[1]
            length = math.hypot(ux, uy)
            ux, uy = ux / length, uy / length
            # The land beyond the end: the first dry point within a cell and a half (an islet's shore a little past
            # a causeway's end counts); none, and the end is a pier's head over the water.
            # (a deck that follows the land reads only the sketch's water below: the installed land under its end is
            # what its pad made, and an end read as over water once and as on land the next flipped, X3's causeway)
            if level and all(wet(end[0] + ux * k, end[1] + uy * k) for k in (0.5, 1.0, 1.5)):
                kept_beyond.add(index)
                continue
            if not level:
                # D-170: a deck that follows the land stands `raise` (16) over the lowest land the studio reads across
                # its end, or halfway up a fall across it, so a fall across the end left one side on the land (D2's
                # log bridge, D3's Wrath Bridge). The dry nodes of the cells the end stands in (across the deck's
                # width) are levelled at their lowest 32 step, no slope and nothing further: the end stands 16 over
                # flat land, and the land round it is left (a pad running on beyond the end cut Vertigo's square
                # under X1's town bridge). Water nodes are the studio's.
                cx, cy = end[0] + ux * 1.0 / 32.0, end[1] + uy * 1.0 / 32.0
                if abs(ux) < 1e-6 or abs(uy) < 1e-6:
                    along_axis = 0 if abs(ux) > abs(uy) else 1
                    across_axis = 1 - along_axis
                    centre = end[across_axis]
                    lines = [math.floor((cx, cy)[along_axis]), math.floor((cx, cy)[along_axis]) + 1]
                    span = range(math.floor(centre - width / 1024.0), math.ceil(centre + width / 1024.0) + 1)
                    nodes = [((n, j) if along_axis == 0 else (j, n)) for n in lines for j in span]
                else:
                    nodes = [(math.floor(cx) + i, math.floor(cy) + j) for i in (0, 1) for j in (0, 1)]
                dry = [n for n in nodes if not _wet_node(sketch, *n)]
                if not dry:
                    kept_beyond.add(index)
                    continue
                lows = [_node(terrain, *n) for n in dry]
                pad_height = _end_height(key, thing['id'], index, end, int(math.floor(min(lows) / 32.0 + 1e-6)) * 32)
                ends_seen.add('%s#%d' % (thing['id'], index))
                end_z[index] = pad_height + lift
                xs, ys = [n[0] for n in dry], [n[1] for n in dry]
                polygon = _square((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0,
                                  (max(xs) - min(xs)) / 2.0 + 0.02, (max(ys) - min(ys)) / 2.0 + 0.02)
                slope = {}
                if pad_beyond:
                    vx, vy = -uy * half, ux * half
                    a = (end[0] - ux * 0.25, end[1] - uy * 0.25)
                    b = (end[0] + ux * pad_beyond, end[1] + uy * pad_beyond)
                    polygon = [[round(a[0] + vx, 3), round(a[1] + vy, 3)], [round(b[0] + vx, 3), round(b[1] + vy, 3)],
                               [round(b[0] - vx, 3), round(b[1] - vy, 3)], [round(a[0] - vx, 3), round(a[1] - vy, 3)]]
                    slope = {'slope': BRIDGE_SLOPE}
                # every build, whatever the installed land shows (the studio builds the land from the sketch)
                pads.append(dict({'polygon': polygon, 'height': pad_height,
                                  'notes': 'D-170: the land at %s\'s end, its lowest across it (common/wild.py '
                                           'bridge_ends)' % thing.get('title', thing['id'])}, **slope))
                if max(lows) > pad_height:
                    notes.append('bridge end %s (%.1f, %.1f): land %d-%d -> %d' % (
                        thing['id'], end[0], end[1], min(lows), max(lows), pad_height))
                end_pads.append(polygon)
                continue
            # The studio levels water to its surface, so a pad's nodes under the deck inside the water stay low and
            # the land still falls away under the deck's end: on a straight bridge along a cell axis the end goes on
            # to the first node line out of the water, where the pad's land is.
            new_end = list(end)
            axis = None
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
                kept_beyond.add(index)
                continue        # a deck ending in the air by design (a buried end is always cut down to: its pad)
            if axis is not None and abs(deck - land) <= 2:
                # D-170: the end meets a terrace at the deck's own height (a town square, a quay): no pad, and the
                # deck stops 16 short of the terrace's edge on the water side instead of running 16 onto it (The
                # Great Bridge's ends lay on X2's squares at 1024)
                def line_at(n):
                    return min(_node(terrain, *((n, j) if axis == 0 else (j, n))) for j in span)
                edge = target
                for _ in range(8):
                    if line_at(edge - sign) < deck - 2:
                        break
                    edge -= sign
                new_end[axis] = edge - sign / 32.0
                kept_beyond.add(index)
                end_z[index] = deck
                if new_end != list(end):
                    notes.append('bridge end %s: 16 short of the terrace at its deck (%.2f, %.2f)' % (
                        thing['id'], *new_end))
                    line[index] = new_end
                continue
            if new_end != list(end):
                notes.append('bridge end %s: on to the node line (%.2f, %.2f)' % (thing['id'], *new_end))
                end = new_end
                line[index] = end
            # Every land end takes its pad, whatever the installed land shows: these rules read the installed map, so a
            # pad left out once its land had come up to the deck was gone again at the next build (the step back,
            # X2's island jetty +36 after a rebuild).
            vx, vy = -uy * half, ux * half
            a = (end[0] - ux * 0.25, end[1] - uy * 0.25)
            b = (end[0] + ux * 1.5, end[1] + uy * 1.5)
            polygon = [[round(a[0] + vx, 3), round(a[1] + vy, 3)], [round(b[0] + vx, 3), round(b[1] + vy, 3)],
                       [round(b[0] - vx, 3), round(b[1] - vy, 3)], [round(a[0] - vx, 3), round(a[1] - vy, 3)]]
            # D-174 (xeen-fb4-fix7, 2026-11-25): an end that butts into a crown or square the sketch raises over the
            # deck (a terrace of the generator's own more than BRIDGE_STEP over it on the first node line beyond the
            # end) takes no pad and cuts nothing beyond it: it stands where the land rising from its node line to the
            # terrace's edge passes 16 under the deck. The pad running on 1.5 cells with its slope of 2 cut X2's
            # island crown (768) under Medin's landing and the X9 sky fall point down to the island jetty's 640.
            if axis is not None:
                beyond = [((target + sign, j) if axis == 0 else (j, target + sign)) for j in span]
                crown = max((_raised_terrace(sketch, deck + BRIDGE_STEP, *n) or 0) for n in beyond)
                if crown:
                    # along the deck's middle line from the end's node line towards the terrace (the studio's water
                    # can hold a corner node of that cell low: X2's 35,61)
                    # (town_fit_check bridges.step reads 24 beyond the end, on the middle and a quarter width out)
                    share = 1.0
                    for k in range(65):
                        lands = []
                        for side in (0.0, 0.25, -0.25):
                            at = [end[0], end[1]]
                            at[axis] = target + sign * (k / 64.0 + 24.0 / 512.0)
                            at[1 - axis] += side * width / 512.0
                            lands.append(_terrain_at(terrain, *at))
                        if min(lands) >= deck - lift:
                            share = k / 64.0
                            break
                    end = list(end)
                    end[axis] = round(target + sign * share, 3)
                    line[index] = end
                    end_z[index] = deck
                    kept_beyond.add(index)
                    notes.append('bridge end %s: meets the terrace at %d, ends at (%.2f, %.2f) without a pad' % (
                        thing['id'], crown, end[0], end[1]))
                    continue
            # D-170: the pad at the highest of the land's 32 steps at least 4 under the deck (8 under a deck on a step
            # rounded back up to it and lay on it: the Nystor jetties, check_faces faces.on_land); 32 or so is still
            # a step the party climbs (town_fit_check BRIDGE_STEP)
            pad_height = _step_under(deck)
            end_z[index] = deck
            pads.append({'polygon': polygon, 'height': pad_height, 'slope': BRIDGE_SLOPE,
                         'notes': 'F48: the land meets %s\'s deck at its end (common/wild.py bridge_ends)'
                                  % thing.get('title', thing['id'])})
            notes.append('bridge end %s (%.1f, %.1f): land %d -> %d' % (thing['id'], end[0], end[1], land,
                                                                       pad_height))
        # D-170: under every stretch of the deck over land, each node of a cell the deck covers whose land stands at or
        # over the highest 32 step at least 4 under the deck there is cut to that step, node by node (a pad of its own
        # with no slope, so the land round it is not touched and the next build finds the same nodes): Medin's jetty
        # ran under its bank's side, the Snow River bridge along a hillside. Nodes beyond an end that is kept (a
        # pier's head, a terrace at the deck's height, an end in the air) are left.
        (x0, y0), (x1, y1) = line[0], line[-1]
        total = math.hypot(x1 - x0, y1 - y0)
        if total < 1e-6 or len(line) != 2:
            continue        # (every Xeen bridge is one straight stretch)
        ux, uy = (x1 - x0) / total, (y1 - y0) / total
        z0 = deck if level else end_z.get(0, _terrain_at(terrain, x0, y0) + lift)
        z1 = deck if level else end_z.get(len(line) - 1, _terrain_at(terrain, x1, y1) + lift)
        rise = 0.0 if level else float(thing.get('rise', 0))

        def deck_z(t):
            share = max(0.0, min(1.0, t / total))
            return z0 + (z1 - z0) * share + rise * 4.0 * share * (1.0 - share)
        reach = 1.0 if abs(ux) < 1e-6 or abs(uy) < 1e-6 else math.sqrt(2.0)
        cut = []
        # a node once cut stays cut while the deck stays (bridge_end_heights.yml '<id>#cut'): the installed land under
        # it can stand under the step by something laid after the terraces (a road's bed), and an uncut node there
        # changed the next generation (D3's Wrath Bridge, 74,47)
        cut_name = '%s#cut' % thing['id']
        cut_kept = _cut_nodes(key, cut_name, line)
        ends_seen.add(cut_name)
        for nx in range(math.floor(min(x0, x1) - half - 1), math.ceil(max(x0, x1) + half + 1) + 1):
            for ny in range(math.floor(min(y0, y1) - half - 1), math.ceil(max(y0, y1) + half + 1) + 1):
                t = (nx - x0) * ux + (ny - y0) * uy
                off = abs(-(nx - x0) * uy + (ny - y0) * ux)
                if off >= width / 1024.0 + reach or t <= -reach or t >= total + reach:
                    continue        # no cell of this node's lies under the deck
                if (t <= 0.0 and 0 in kept_beyond) or (t >= total and len(line) - 1 in kept_beyond):
                    continue
                if _wet_node(sketch, nx, ny):
                    continue        # the studio keeps water at its level
                if any(_inside(polygon, nx, ny) for polygon in end_pads):
                    continue        # levelled with its end (the studio stands the end 16 over it)
                lowest = min(deck_z(t + k * reach / 4.0) for k in range(-4, 5))
                step = _step_under(lowest)
                if _node(terrain, nx, ny) >= step or (nx, ny) in cut_kept:
                    cut.append((nx, ny, step))
        _keep_cut_nodes(key, cut_name, line, cut_kept | {(nx, ny) for nx, ny, _ in cut})
        for nx, ny, step in cut:
            pads.append({'polygon': _square(nx, ny, 0.02, 0.02), 'height': step,
                         'notes': 'D-170: the land under %s\'s deck (common/wild.py bridge_ends)'
                                  % thing.get('title', thing['id'])})
        if cut:
            notes.append('bridge %s: %d nodes under the deck cut (%s)' % (
                thing['id'], len(cut), ', '.join('%d,%d>%d' % c for c in cut[:6]) + (' ...' if len(cut) > 6 else '')))
    if pads:
        sketch.setdefault('heights', {}).setdefault('terraces', []).extend(pads)
    _prune_end_heights(key, ends_seen)
    return notes


# D-170 (agent xeen-fb4-outdoor6, 2026-11-25): a land-following end's pad height is read once from the installed land
# and kept in bridge_end_heights.yml (map -> '<bridge id>#<end index>' -> its `at` and height) while the end stays
# there. Read again at every build, the pad met the deck's own node cuts under the end (D3's Wrath Bridge: 1024, then
# 992 at the second build: the cut nodes 74,45-47 are the end's dry nodes). Moving the end reads its land again.
END_HEIGHTS = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bridge_end_heights.yml')
END_HEIGHTS_HEAD = ('# Each land-following bridge end\'s pad height (common/wild.py bridge_ends): read once from the '
                    'installed land,\n# then kept while the end stays at `at`, so the pad does not drift from build to '
                    'build. Written by the outdoor generators.\n')


def _end_height(key, tid, index, end, read):
    import level_pads  # noqa: E402 (beside this file)
    record = level_pads._load(END_HEIGHTS).get(key) or {}
    name = '%s#%d' % (tid, index)
    at = [round(float(end[0]), 3), round(float(end[1]), 3)]
    kept = record.get(name)
    if kept and kept.get('at') == at:
        return int(kept['height'])
    record = dict(record)
    record[name] = {'at': at, 'height': int(read)}
    level_pads._store(END_HEIGHTS, END_HEIGHTS_HEAD, key, record)
    return int(read)


def _raised_terrace(sketch, over, x, y):
    """D-174: the height of the highest terrace of the generator's own (not a rule's pad) standing over `over` that
    holds the node in or on its outline, or None."""
    best = None
    for terrace in (sketch.get('heights') or {}).get('terraces') or []:
        notes = str(terrace.get('notes', ''))
        if 'common/wild.py' in notes or 'common/level_pads.py' in notes or float(terrace.get('height', 0)) <= over:
            continue
        if any(_inside(terrace['polygon'], x + dx, y + dy) for dx in (-0.01, 0.01) for dy in (-0.01, 0.01)):
            best = max(best or 0.0, float(terrace['height']))
    return best


def _line_key(line):
    return [[round(float(p[0]), 3), round(float(p[1]), 3)] for p in line]


def _cut_nodes(key, name, line):
    import level_pads  # noqa: E402
    kept = (level_pads._load(END_HEIGHTS).get(key) or {}).get(name)
    if kept and kept.get('line') == _line_key(line):
        return {tuple(n) for n in kept.get('nodes') or []}
    return set()


def _keep_cut_nodes(key, name, line, nodes):
    import level_pads  # noqa: E402
    record = level_pads._load(END_HEIGHTS).get(key) or {}
    entry = {'line': _line_key(line), 'nodes': sorted([int(x), int(y)] for x, y in nodes)}
    if record.get(name) != entry:
        record = dict(record)
        record[name] = entry
        level_pads._store(END_HEIGHTS, END_HEIGHTS_HEAD, key, record)


def _prune_end_heights(key, seen):
    import level_pads  # noqa: E402
    record = level_pads._load(END_HEIGHTS).get(key) or {}
    if set(record) - seen:
        level_pads._store(END_HEIGHTS, END_HEIGHTS_HEAD, key, {k: v for k, v in record.items() if k in seen})


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
    import level_pads  # noqa: E402 (beside this file; F59: pads and sunk rocks for things on slopes)
    return (shrine_altars(sketch) + campfires(sketch) + notes + rim_fall(sketch, key) + bridge_ends(sketch, key)
            + house_tents(sketch) + free_mouths(sketch) + ruin_windows(sketch) + level_pads.auto(sketch, key))
