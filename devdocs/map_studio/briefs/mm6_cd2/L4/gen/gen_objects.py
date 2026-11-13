#!/usr/bin/env python3
"""Writes the L4 objects.yml from the original's spawn points, decorations, lights and door records, placed in the
rooms gen.py wrote (gen_rooms.json). Wiring lives in wiring_src.py."""
import json, math, collections
from lib import *
from shapely.geometry import Polygon, Point
from shapely.ops import nearest_points
import overrides as OV
L4 = '/home/pjasicek/github/OpenYAMM/devdocs/map_studio/briefs/mm6_cd2/L4/'
G = json.load(open(D + 'gen_rooms.json'))
ROOMS = G['rooms']
for r in ROOMS:
    r['poly'] = Polygon(r['pts'])
    r['inner'] = r['poly'].buffer(-6)
log = []


def place(x, y, z, slack=96):
    """The room a point stands in: (room, x, y) with the point pulled inside when it sits on a wall."""
    best = None
    P = Point(x, y)
    for r in ROOMS:
        lo = min(r['floor'], r['slope']['to']) if r['slope'] else r['floor']
        if z < lo - 80 or z > r['ceiling'] + 8:
            continue
        d = r['poly'].distance(P)
        if d > slack:
            continue
        hi = r['floor_high']
        zd = 0 if lo - 8 <= z <= r['ceiling'] else 50
        key = (d > 0.01, round(d), zd + abs(z - lo) * 0.01)
        if best is None or key < best[0]:
            best = (key, r)
    if best is None:
        return None
    r = best[1]
    if r['inner'].is_empty:
        c = r['poly'].representative_point()
        return r, int(c.x), int(c.y)
    if not r['inner'].contains(P):
        q = nearest_points(r['inner'], P)[0]
        x, y = q.x, q.y
        # rounding must not leave the room
        for cx, cy in ((round(x), round(y)), (math.floor(x), math.floor(y)), (math.ceil(x), math.ceil(y)),
                       (math.floor(x), math.ceil(y)), (math.ceil(x), math.floor(y))):
            if r['poly'].buffer(-2).contains(Point(cx, cy)):
                return r, int(cx), int(cy)
        c = r['inner'].representative_point()
        return r, int(c.x), int(c.y)
    return r, int(round(x)), int(round(y))


def floor_of(r, x, y):
    if not r['slope']:
        return r['floor']
    return (r['floor'] + r['slope']['to']) / 2


out = ['format: 0']
st = place(21169, 1920, -689)
out.append('start: {room: "%s", at: [21169, 1920], facing: w}' % st[0]['id'])

# ---- lights
out.append('lights:')
for i, l in enumerate(m['lights']):
    p = place(*l['position'])
    if not p:
        log.append('light %d at %s is in no room' % (i, l['position']))
        continue
    r, x, y = p
    out.append('  - id: light:l%02d' % i)
    out.append('    room: %s' % r['id'])
    out.append('    at: [%d, %d]' % (x, y))
    out.append('    height: %d' % max(8, l['position'][2] - floor_of(r, x, y)))
    out.append('    radius: %d' % max(64, l['radius']))
    out.append('    brightness: %d' % l['brightness'])
    out.append('    notes: "Original light record %d (radius %d, type %d)."' % (i, l['radius'], l['type']))

# ---- spawns
out.append('spawns:')
ns = 0
tiers = collections.Counter()
for i, s in enumerate(m['spawns']):
    p = place(*s['position'])
    if not p:
        log.append('spawn %d at %s (type %d index %d) is in no drawn room' % (i, s['position'], s['type_id'], s['index']))
        continue
    r, x, y = p
    idx = s['index']
    if s['type_id'] != 3:
        log.append('spawn %d at %s is an item spawn (type %d, treasure level %d): objects.yml has no items on the floor' % (i, s['position'], s['type_id'], idx))
        continue
    slot = idx if idx <= 3 else (idx - 4) // 3 + 1
    note = 'Original spawn %d, index %d' % (i, idx)
    if idx > 3:
        note += ' (slot %d, fixed tier %s: a spawn here cannot name its tier)' % (slot, 'ABC'[(idx - 4) % 3])
        tiers[idx] += 1
    out.append('  - id: spawn:p%03d' % i)
    out.append('    room: %s' % r['id'])
    out.append('    at: [%d, %d]' % (x, y))
    out.append('    slot: %d' % slot)
    if s['radius'] != 32:
        out.append('    radius: %d' % s['radius'])
    out.append('    notes: "%s."' % note)
    ns += 1

# ---- decorations
out.append('decorations:')
nd = 0
for i, e in enumerate(m['entities']):
    if e['name'] == 'Party Start':
        continue
    p = place(*e['position'])
    if not p:
        log.append('decoration %d %s at %s is in no drawn room' % (i, e['name'], e['position']))
        continue
    r, x, y = p
    out.append('  - id: deco:d%03d' % i)
    out.append('    room: %s' % r['id'])
    out.append('    decoration: %s' % e['name'].lower())
    out.append('    at: [%d, %d]' % (x, y))
    h = e['position'][2] - floor_of(r, x, y)
    if h > 1:
        out.append('    height: %d' % h)
    if e['facing']:
        out.append('    facing: %d' % (e['facing'] * 360 // 2048))
    nd += 1
# ---- doors
ops = {o['id']: o for o in G['openings']}
out.append('doors:')
wir = ['format: 0', 'variables: [east_way_cleared, west_way_cleared, fires_sign_read]', 'events:']
EXTRA_DOORS = [
    ('d10', 'open:s066_s058', 'slide_down', 150, None, 'Door record 10: the portcullis between the north passage and the north cavern; it sinks 180 into the floor. In the original it is lowered by touching the great hall teleporter cube after the lever in the lever closet has been pulled (events 54 and 28 to 32); here the lever lowers it.'),
    ('forcefield', 'open:s094_c_s144_a', 'slide_up', 600, {'texture': 'lavatyl', 'size': [128, 128]}, 'The forcefield in the doorway to the west court (face 4522, lava texture, event 59: Your way is blocked). In the original it is not a door: the faces are made passable by the throne hall cube once the west lever is pulled. Here the west lever opens it.'),
]
for did, oid, kind, speed, surf, note in EXTRA_DOORS:
    if oid not in ops:
        log.append('door %s: its opening %s is not drawn' % (did, oid))
        continue
    out.append('  - id: door:%s' % did)
    out.append('    opening: %s' % oid)
    out.append('    kind: %s' % kind)
    out.append('    state: closed')
    out.append('    speed: %d' % speed)
    th = min(32, ops[oid]['_gap'])
    if th >= 8:
        out.append('    thickness: %d' % th)
    if surf:
        out.append('    surface: {texture: %s, size: %s}' % (surf['texture'], surf['size']))
    out.append('    notes: "%s"' % note)
for did, (oid, title, note) in sorted(OV.DOOR_OPENINGS.items()):
    if oid not in ops:
        log.append('door %d: its opening %s is not drawn' % (did, oid))
        continue
    rec = [d for d in DOORS if d['door_id'] == did][0]
    out.append('  - id: door:d%02d' % did)
    out.append('    opening: %s' % oid)
    out.append('    kind: slide_up')
    out.append('    state: closed')
    out.append('    speed: %d' % rec['open_speed'])
    th = min(32, ops[oid]['_gap'])
    if th >= 8:
        out.append('    thickness: %d' % th)
    out.append('    notes: "%s It slides sideways in the original; the vocabulary has slide_up, slide_down and hinged."' % note)
    wir.append('  - id: evt:door%02d' % did)
    wir.append('    preset: door')
    wir.append('    source: door:d%02d' % did)
    wir.append('    title: %s' % title)
    wir.append('    action: open')

def wall_of(r, x, y):
    """The wall of a room nearest a point: (edge index, along 0..1)."""
    best = None
    n = len(r['pts'])
    for i in range(n):
        a, b = r['pts'][i], r['pts'][(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (ln * ln)))
        d = math.hypot(x - (a[0] + dx * t), y - (a[1] + dy * t))
        if best is None or d < best[0]:
            best = (d, i, t)
    return best[1], round(best[2], 4)


def face_box(ev):
    fs = [f for f in F if f['cog_triggered'] == ev]
    ps = [q for f in fs for q in fpts(f)]
    mn = [min(q[k] for q in ps) for k in range(3)]
    mx = [max(q[k] for q in ps) for k in range(3)]
    return mn, mx


# ---- the way out (event 60: the big door in the entry hall's east wall)
mn, mx = face_box(60)
r, x, y = place((mn[0] + mx[0]) / 2 - 16, (mn[1] + mx[1]) / 2, mn[2])
w, al = wall_of(r, (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2)
out.append('exits:')
out.append('  - id: exit:gate')
out.append('    room: %s' % r['id'])
out.append('    wall: %d' % w)
out.append('    along: %s' % al)
out.append('    size: [256, 256]')
out.append('    surface: {texture: d2lgdor, size: [256, 256]}')
out.append('    to: exit:darkmoor_region')
out.append('    notes: "The original\'s event 60 on the d2lgdor door face behind the party\'s arrival."')
wir.append('  - id: evt:leave')
wir.append('    preset: exit')
wir.append('    source: exit:gate')
wir.append('    title: "Leave Castle Darkmoor"')

# ---- the chest (event 10, in the lich's study)
mn, mx = face_box(10)
p = place((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2])
if p:
    r, x, y = p
    out.append('chests:')
    out.append('  - id: chest:study')
    out.append('    room: %s' % r['id'])
    out.append('    at: [%d, %d]' % (x, y))
    out.append('    size: [96, 64, 64]')
    out.append('    treasure_level: 6')
    out.append('    random_items: 3')
    out.append('    notes: "Chest record 0 of the original (event 10): three random item slots (two of class 6, one of class 7)."')
    wir.append('  - id: evt:chest')
    wir.append('    preset: chest')
    wir.append('    source: chest:study')
    wir.append('    title: Chest')

# ---- signs and levers on walls
sw = ['switches:']
SIGNS = [(53, 'sign_embers_e', 'Sign', 'The crimson embers will lead the way', None),
         (55, 'sign_embers_w', 'Sign', 'The crimson embers will lead the way', None),
         (45, 'sign_fires', 'Sign', 'The fires of the dead shall burn forever', 'fires_sign_read'),
         (54, 'lever_east', 'Lever', None, 'east_way_cleared'),
         (56, 'lever_west', 'Lever', None, 'west_way_cleared')]
for ev, name, title, text, var in SIGNS:
    mn, mx = face_box(ev)
    cx, cy, cz = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2
    p = place(cx, cy, cz)
    if not p:
        log.append('event %d (%s) is in no drawn room' % (ev, name))
        continue
    r, x, y = p
    w, al = wall_of(r, cx, cy)
    sw.append('  - id: switch:%s' % name)
    sw.append('    room: %s' % r['id'])
    sw.append('    wall: %d' % w)
    sw.append('    along: %s' % al)
    sw.append('    height: %d' % max(16, cz - floor_of(r, x, y)))
    if title == 'Sign':
        tex, size = (('bigsign', [128, 64]) if ev == 45 else ('sign7', [64, 32]))
        sw.append('    size: %s' % size)
        sw.append('    off: {texture: %s, size: %s}' % (tex, size))
        sw.append('    on: %s' % tex)
    sw.append('    notes: "Original event %d."' % ev)
    wir.append('  - id: evt:%s' % name)
    wir.append('    preset: %s' % ('text' if text and not var else 'switch'))
    wir.append('    source: switch:%s' % name)
    wir.append('    title: %s' % title)
    if ev == 54:
        wir.append('    opens: [door:d10]')
        wir.append('    text: "The way has been cleared"')
    if ev == 56:
        wir.append('    opens: [door:forcefield]')
        wir.append('    text: "The way has been cleared"')
    if var:
        wir.append('    sets: {map_var: %s}' % var)
    if text:
        wir.append('    text: "%s"' % text)
out += sw

# ---- what objects.yml cannot say
out.append('placeholders:')
def ph(pid, x, y, z, what, size, note):
    p = place(x, y, z)
    if not p:
        log.append('placeholder %s is in no drawn room' % pid)
        return
    r, px_, py_ = p
    out.append('  - id: ph:%s' % pid)
    out.append('    room: %s' % r['id'])
    out.append('    at: [%d, %d]' % (px_, py_))
    out.append('    stands_for: "%s"' % what)
    out.append('    size: %s' % size)
    out.append('    notes: "%s"' % note)
FLOW = {e['event']: e for e in (json.loads(l.rstrip(',\n').lstrip('[').rstrip(']')) for l in open(D + 'flow.txt') if l.strip().startswith(('{', '[{')))}
for ev in sorted(set(f['cog_triggered'] for f in F if f['cog_triggered'])):
    if ev in (1, 4, 5, 6, 7, 8, 9, 10, 60, 53, 55, 45, 54, 56):
        continue
    mn, mx = face_box(ev)
    fl = FLOW.get(ev, {})
    effs = []
    for pth in fl.get('paths', []):
        for e in pth['effects']:
            if e not in effs:
                effs.append(e)
    plate = abs(nrm([f for f in F if f['cog_triggered'] == ev][0])[2]) > 0.7
    what = ('Pressure plate' if plate else 'Touch or click face') + ' of event %d%s: %s' % (
        ev, (' (' + fl.get('title') + ')') if fl.get('title') else '', '; '.join(effs)[:300].replace('"', "'"))
    ph('event%02d' % ev, (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2], what,
       [max(16, mx[0] - mn[0]), max(16, mx[1] - mn[1]), max(16, mx[2] - mn[2])],
       'A wiring event needs a door, switch, chest or exit as its source; a floor the party steps on or a block it touches cannot start one.')
ph('lich_guardian', -14016, 14880, -240, 'Fixed actor: monster 2000 (monster info 570, 600 hit points, unique name 134) carrying item 1761.', [80, 80, 180], 'objects.yml has no fixed actors.')
ph('floor_items', -15488, 17024, 600, 'Items lying on the floor: the original has 72 sprite objects (the secret treasure room and the study) and 5 item spawn points of treasure class 6.', [64, 64, 32], 'objects.yml has no items on the floor.')
open(D + 'wiring_auto.yml', 'w').write('\n'.join(wir) + '\n')
open(D + 'objects_auto.yml', 'w').write('\n'.join(out) + '\n')
open(D + 'objects_log.txt', 'w').write('\n'.join(log) + '\n')
print('%d spawns, %d decorations, %d log lines; fixed tiers %s' % (ns, nd, len(log), dict(tiers)))
