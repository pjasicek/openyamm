"""Shared wild-land rules for Xeen's outdoor generators (P2 feedback F29, F32, F33; agent xeen-fb2-wild, 2026-11-23).

Each outdoor map's gen.py calls `apply(sketch, '<key>')` on its finished sketch just before writing it:

- **Shrine altars (F32).** A shrine pavilion (a `building` part on `posts` whose click gives something) gets an altar
  block under its roof, and the click moves onto the altar: the pavilion keeps only its title. As MM6's prefab shrines
  (OUTE1 event 261 on the altar faces of `shrineE` only) and MM7's "Shrine" (hint) / "Altar" (the click) pairs.
- **Campfires (F33).** Every campfire decoration without an event of its own feeds the party once (MM8 Global 285/286
  "Camp Fire": food, then the event is gone) and a character with Perception finds a small ring on the cursor (MM7's
  campfire, Global 1162/1163 here); the status line says what was found (F13).
- **The rim fall (F29).** The sea under the world rim (`water:sky` / `water:rim_sea`, level 0) gets a timer event: a
  party in it or in the rim's foot below Xeen.RimFallDepth (not flying) is lifted back onto the rim at the nearest of
  a few return points and falls the last Xeen.SkyFallHeight (xeen_common.lua `Xeen.rimFall`). The return points
  stand on the built map's land (the installed ODM's heights, read through `oymap export`), at least three cells in
  from the sea, on level ground, away from structures.

`tools/xeen/check_rim.py` and `tools/xeen/check_wild.py` check the built maps.
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
                'else evt.StatusText("You find food by the fire (+" .. food .. ").") end '
                'evt.ChangeEvent(0)')
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


def apply(sketch, key):
    """All three rules on a finished outdoor sketch, then the rim's void and hull (common/rim.py, U-12); returns notes
    to print."""
    if not isinstance(sketch, dict) or 'structures' not in sketch:
        return []
    import rim  # noqa: E402 (beside this file)
    notes = rim.apply(sketch, key)
    return shrine_altars(sketch) + campfires(sketch) + notes + rim_fall(sketch, key)
