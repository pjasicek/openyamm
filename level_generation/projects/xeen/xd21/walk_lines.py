#!/usr/bin/env python3
"""XD-21 dressing check against the walking lines (devdocs/xeen/formats/DRESSING.md: a floor prop at least its radius
+ 64 from the straight line between two openings of its room; containers also against the walls, clear of door faces
and portals). After level_generation/projects/xeen/xd27/walk_lines.py, with XD-21's own lines: the rooms' openings (the
portal centres of the built blv, `oymap export`), the start and the quay door, and what the party walks to (the worn
block, the bridge's landings, the winch, the catwalk's ends, the boss's desk and catch, the chests, the dues box).
Lines across the race are left out (the bridge and the catwalk are the ways over). Furniture platforms are rectangles
(their nearest edge at least 64 from the line); decorations are circles of decoration_data's radius (+ 64).
Architecture (sills, pier buttresses, the catwalk and its rails, the plinth under the strongbox, the winch post the
lines end at) is not dressing and is skipped. Usage: walk_lines.py <L4 folder>"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
DD = {}
for line in open(_REPO_ROOT + '/assets_dev/engine/data_tables/decoration_data.txt', encoding='latin-1'):
    c = line.rstrip('\n').split('\t')
    if len(c) > 5 and c[0].isdigit():
        DD[c[1].lower()] = int(c[4] or 0)
# Openings (portal centres from the export), start, targets.
QUAY, START, SECRET = (-2560, 0), (-2560, 320), (-2560, 1152)
DEN, DICE_E, BUNKS, DUES = (-2560, 3584), (-1408, 4224), (-2432, 4864), (-3120, 4480)
BUNKS_S, SLUICE_W = (-2432, 5120), (-1408, 5632)
UNDER_N, STAIR, BRIDGE_W, BRIDGE_E, WINCH = (442, 4864), (1664, 3968), (-300, 3968), (300, 3968), (500, 3712)
CAT_W, CAT_E, FENCE = (-300, 5760), (300, 5760), (1024, 5632)
FENCE_CHEST, COUNT = (1856, 5380), (1856, 5800)
BOSS_W, PASSAGE, DESK = (3200, 3968), (3904, 4736), (4250, 3968)
VAULT_S, BOX = (3904, 6144), (3904, 6520)
L = lambda *pts: [(pts[i], pts[j]) for i in range(len(pts)) for j in range(i + 1, len(pts))]
LINES = {
    'room:quay_cellar': [(QUAY, START), (START, SECRET)],
    'room:crawl': [(SECRET, DEN)],
    'room:dicing_room': L(DEN, DICE_E, BUNKS) + [(BUNKS, DUES), (DICE_E, DUES)],  # the box from the room's free north half
    'room:bunk_room': [(BUNKS_S, SLUICE_W)],
    'room:undercroft': [(DICE_E, BRIDGE_W)] + L(UNDER_N, STAIR, BRIDGE_E, WINCH),
    'room:sluice': [(SLUICE_W, CAT_W), (CAT_E, UNDER_N), (CAT_E, FENCE), (UNDER_N, FENCE)],
    'room:fence_store': [(FENCE, FENCE_CHEST), (FENCE, COUNT)],
    'room:boss_stair': [(STAIR, BOSS_W)],
    'room:strongroom_walk': [(PASSAGE, VAULT_S)],
}
SKIP_PLATFORM = ('sill', 'buttress', 'catwalk', 'plinth', 'winch', 'dart')


def dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; n = dx * dx + dy * dy
    t = 0 if n == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / n))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def seg_seg(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    if (ccw(a, c, d) > 0) != (ccw(b, c, d) > 0) and (ccw(a, b, c) > 0) != (ccw(a, b, d) > 0):
        return 0.0
    return min(dist(a, c, d), dist(b, c, d), dist(c, a, b), dist(d, a, b))


def own(at, size, a, b):
    """A line that ends at this prop (the party walks up to it): not checked against it."""
    reach = max(size[:2]) / 2 + 128
    return any(math.hypot(e[0] - at[0], e[1] - at[1]) <= reach for e in (a, b) if tuple(e) in TARGETS)


def rect_line(at, size, a, b):
    if own(at, size, a, b):
        return 1e9
    x0, y0, x1, y1 = at[0] - size[0] / 2, at[1] - size[1] / 2, at[0] + size[0] / 2, at[1] + size[1] / 2
    if x0 <= a[0] <= x1 and y0 <= a[1] <= y1:
        return 0.0
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    return min(seg_seg(a, b, c, d) for c, d in edges)


L4 = sys.argv[1]
rooms = yaml.safe_load(open(L4 + '/rooms.yml'))['rooms']
objs = yaml.safe_load(open(L4 + '/objects.yml'))
bad = n = 0
# The boss's quarters: the door, the passage, the desk, the catch (wall position from objects.yml), the boss's chest.
catch = next(s for s in objs['switches'] if s['id'] == 'switch:catch')['at']
CATCH = (catch[0], catch[1] - 96)
bchest = next(c for c in objs['chests'] if c['id'] == 'chest:boss')['at']
LINES['room:boss_quarters'] = L(BOSS_W, PASSAGE, DESK, CATCH) + [(BOSS_W, tuple(bchest))]
LINES['room:vault'] = [(VAULT_S, BOX)]
TARGETS = {DUES, WINCH, FENCE_CHEST, COUNT, DESK, CATCH, tuple(bchest), BOX}
out = []
for r in rooms:
    for p in r.get('platforms', []):
        name = p.get('id') or p.get('notes', '')
        if any(k in name.lower() for k in SKIP_PLATFORM) or 'base' in p:
            continue
        n += 1
        lines = LINES.get(r['id'], [])
        g = min((rect_line(p['at'], p['size'], a, b) for a, b in lines), default=1e9)
        flag = g < 64
        bad += flag
        out.append(f"{'!!' if flag else '  '} {r['id']:20s} {name[:34]:34s} at {str(p['at']):14s} edge to line {g:6.0f} (need 64)")
for o in objs.get('decorations', []):
    if o.get('wall') or o.get('floor_height') or o.get('hangs'):
        continue
    n += 1
    rad = DD.get(o['decoration'].lower(), 32)
    lines = LINES.get(o['room'], [])
    g = min((dist(o['at'], a, b) for a, b in lines), default=1e9)
    flag = g < rad + 64
    bad += flag
    out.append(f"{'!!' if flag else '  '} {o['room']:20s} {o['id'] + ' ' + o['decoration']:34s} at {str(o['at']):14s} centre to line {g:6.0f} (need {rad + 64})")
for c in objs.get('chests', []):
    n += 1
    lines = LINES.get(c['room'], [])
    g = min((rect_line(c['at'], [96, 96], a, b) for a, b in lines), default=1e9)
    flag = g < 64
    bad += flag
    out.append(f"{'!!' if flag else '  '} {c['room']:20s} {c['id']:34s} at {str(c['at']):14s} edge to line {g:6.0f} (need 64)")
print('\n'.join(out))
print('offenders', bad, 'of', n)
