# First objects.yml of the Goblinwatch rebuild (MM6 6d01.blv), written once from the original's records (export and
# scene), measured, not invented. Doors, movers, switches and chests are tables read from the export's door records
# and faces (numbers in their notes); spawns, lights and decorations are copied record by record, each into the room
# whose outline holds it (the floor under it read off the original's floor faces). Once objects.yml has hand edits,
# it is the source and this is not run again.
# Usage: python3 gen_objects.py <export.json> <scene.yml> <rooms.yml> > objects.yml
import json, sys, struct, math, yaml

exp = json.load(open(sys.argv[1]))['map']
scene = yaml.safe_load(open(sys.argv[2]))
rooms = yaml.safe_load(open(sys.argv[3]))['rooms']
V = exp['vertices']; F = exp['faces']; S = exp['sectors']


def inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i][:2]; x2, y2 = poly[(i + 1) % len(poly)][:2]
        if (y1 > y) != (y2 > y):
            if x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x:
                c = not c
    return c


def floor_under(pt, z):
    # the original's highest floor at the point that is not above z + 8
    best = None
    for s in S[1:]:
        for fi in s['floor_faces']:
            f = F[fi]
            n = f['plane_normal']
            if n[2] <= 0:
                continue
            vs = [V[v] for v in f['vertices']]
            if not inside(pt, [v[:2] for v in vs]):
                continue
            a = vs[0]
            fz = a[2] - (n[0] * (pt[0] - a[0]) + n[1] * (pt[1] - a[1])) / n[2]
            if fz <= z + 8 and (best is None or fz > best):
                best = fz
    if best is None:
        # a thing on a wall just outside the floor's edge: the nearest floor vertex under it
        near = [(math.hypot(v[0] - pt[0], v[1] - pt[1]), v[2]) for s in S[1:] for fi in s['floor_faces']
                for v in (V[k] for k in F[fi]['vertices']) if v[2] <= z + 8]
        d, bz = min(near)
        if d < 300:
            best = bz
    return best


def room_of(pt, z):
    cands = []
    for r in rooms:
        if inside(pt, r['outline']):
            lo = min([r['floor']] + [p[2] for p in r.get('floor_points', [])] + ([r['slope']['to']] if 'slope' in r else []))
            hi = max([r['ceiling']] + [p[2] for p in r.get('ceiling_points', [])])
            d = 0 if lo - 8 <= z <= hi else min(abs(z - lo), abs(z - hi))
            cands.append((d, r['id']))
    return min(cands)[1] if cands else None


def room_near(pt, z, reach=64):
    # the room whose outline passes within `reach` of a point (a torch on a cave's wall just outside the floor's edge)
    best = None
    for r in rooms:
        o = r['outline']
        lo = min([r['floor']] + [p[2] for p in r.get('floor_points', [])] + ([r['slope']['to']] if 'slope' in r else []))
        hi = max([r['ceiling']] + [p[2] for p in r.get('ceiling_points', [])])
        if not (lo - 64 <= z <= hi + 64):
            continue
        for i in range(len(o)):
            a, b = o[i], o[(i + 1) % len(o)]
            L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
            t = max(0, min(1, ((pt[0] - a[0]) * (b[0] - a[0]) + (pt[1] - a[1]) * (b[1] - a[1])) / L2))
            d = math.hypot(pt[0] - a[0] - t * (b[0] - a[0]), pt[1] - a[1] - t * (b[1] - a[1]))
            if d < reach and (best is None or d < best[0]):
                best = (d, r['id'])
    return best[1] if best else None


def surf(t, w, h):
    return {'texture': t, 'size': [w, h]}


out = {'format': 0}
out['start'] = {'room': 'room:s1', 'at': [576, 6912], 'floor_height': 192, 'facing': 's',
                'notes': "The original's Party Start (576, 6912, 192) on the landing at the way out; the outdoor door's arrival faces south-west (1400 of 2048), into the hall."}
out['exits'] = [{'id': 'exit:way_out', 'room': 'room:s1', 'at': [576, 6944], 'floor_height': 192, 'size': [256, 256],
                 'surface': surf('t1d1', 256, 256), 'to': 'exit:new_sorpigal',
                 'notes': "Face 16 (event 51, 'Exit Door'): the double door t1d1, 256 by 256, in the hall's north wall over the landing."}]

D = []


def door(did, op, kind, s, back, speed, travel, notes, thickness=16, secret=False, leaves=None):
    d = {'id': did, 'opening': op, 'kind': kind, 'fold': True, 'state': 'closed', 'thickness': thickness,
         'speed': speed, 'travel': travel, 'surface': s}
    if back and back != s:
        d['back_surface'] = back
    if secret:
        d['secret'] = True
    if leaves:
        d['leaves'] = leaves
    d['notes'] = notes
    D.append(d)


door('door:d1', 'open:s1_s2', 'slide_up', surf('T1spclA', 128, 256), None, 80, 250,
     "Door record 1 (event 1): the leaf T1spclA, 32 thick, rises 250 from 6 over the floor (faces 5, 1444, 1441).", thickness=28)
door('door:d2', 'open:s1w_s5r', 'slide_right', surf('t1d2', 256, 256), surf('t1d1', 256, 256), 85, 250,
     "Door record 2 (event 2): t1d2 toward the hall, t1d1 toward the ramp (faces 1432, 1431); its east edge moves 250 west.", thickness=28)
door('door:d3', 'open:s6_s7', 'slide_left', surf('T1spclA', 128, 256), surf('d6DorA', 256, 256), 50, 250,
     "Door record 3 (event 3): T1spclA toward the approach, d6DorA toward the prison (faces 1436, 1435); its north edge moves 250 south.", thickness=28)
door('door:d16', 'open:s1_s20', 'slide_up', surf('t1w11a', 128, 256), surf('d6dorD', 128, 256), 85, 250,
     "Door record 16 (event 16): the hall's wall t1w11a on its west face, d6dorD on its east (faces 17, 1447); rises 250.", thickness=28)
door('door:d17', 'open:s3_s45', 'slide_right', surf('t1d2', 256, 256), None, 90, 250,
     "Door record 17 (event 17): t1d2 on both faces (1976, 1977); its north edge moves 250 south.", thickness=28)
door('door:d18', 'open:s21t_s48a', 'slide_up', surf('t1w11a', 128, 256), surf('T3D3', 128, 256), 85, 250,
     "Door record 18 (event 18): the stair's wall t1w11a on its west face, T3D3 on its east (faces 332, 1426); rises 250.", thickness=28)
door('door:d23', 'open:s3g_s3', 'slide_left', surf('T3WSBP', 128, 256), surf('t1d2', 256, 256), 85, 250,
     "Door record 23 (event 61): T3WSBP toward the gate passage, t1d2 toward the cross passage (faces 1623, 1622); its east edge moves 253 west.", thickness=28)
CELLS = {4: 16, 5: 15, 6: 14, 7: 11, 8: 12, 9: 13, 10: 10, 11: 9, 12: 8, 13: 17, 14: 18, 15: 19}
for rec, cell in sorted(CELLS.items()):
    door(f'door:d{rec}', f'open:s7_c{cell}', 'slide_up', surf('SWFloor5a', 128, 128), surf('OrCeil', 128, 128), 90, 120,
         f"Door record {rec} (event {rec}): locker {cell}'s door, SWFloor5a toward the corridor, OrCeil inside; rises 120 of its 127.")
door('door:d30w', 'open:s4_s52', 'slide_up', surf('T3T6', 32, 32), surf('T3WSBTD', 256, 256), 85, 250,
     "Door record 30, west leaf (event 63; face 1626, secret by the scene's face override): the back wall of the west tower, rising 250.", secret=True)
door('door:d30e', 'open:s4_s53', 'slide_up', surf('T3T6', 32, 32), surf('T3WSBTD', 256, 256), 85, 250,
     "Door record 30, east leaf (event 63; face 1627, secret): the back wall of the east tower.", secret=True)
door('door:d60', 'open:s51_s44', 'slide_left', surf('T3D2B', 256, 256), surf('T3D2A', 256, 256), 150, 250,
     "Door records 45 and 46 (event 60, from the corridor's side only): two leaves of T3D2A/T3D2B parting from the middle, each 250.", thickness=28, leaves=2)
out['doors'] = D

M = []
M.append({'id': 'mover:towers', 'room': 'room:s4', 'at': [-704, 4232], 'size': [256, 16], 'height': 510,
          'travel': [0, 0, -504], 'speed': 80, 'surface': surf('T3WSBP', 128, 256), 'top_surface': surf('OrErt32', 32, 32),
          'parts': [{'at': [-584, 4360], 'size': [16, 240], 'height': 510, 'bottom': 0},
                    {'at': [320, 4232], 'size': [256, 16], 'height': 510, 'bottom': 0},
                    {'at': [200, 4360], 'size': [16, 240], 'height': 510, 'bottom': 0}],
          'notes': "Door record 32 (the switch, event 62): the two towers' walls, 16 thick and 510 high, that close off the hall's north corners; they sink 504 into the floor (faces 107 to 114, 1578, 1579 and their tops)."})
SIDES12 = surf('T3T5', 64, 64)
SIDES36 = surf('SWFloor6a', 128, 128)
TOP = surf('SWhz2', 32, 32)
END = surf('SWhz4', 32, 32)


def band(mid, x, y0, y1, bottom, height, travel, speed, sides, notes, parts=None):
    m = {'id': mid, 'room': 'room:s51', 'at': [x, (y0 + y1) / 2], 'size': [32, y1 - y0], 'bottom': bottom, 'height': height,
         'travel': travel, 'speed': speed, 'surface': sides, 'end_surface': END, 'top_surface': TOP, 'notes': notes}
    if parts:
        m['parts'] = parts
    M.append(m)


band('mover:g52', 2544, 4608, 5119, 0, 64, [0, -500, 0], 100, SIDES12, "Door record 52: gate 1's lowest band (128 to 192), slides 500 south.")
band('mover:g40', 2544, 4609, 5120, 65, 126, [0, 500, 0], 85, SIDES12, "Door record 40: gate 1's middle band (193 to 319), slides 500 north.")
band('mover:g51', 2544, 4608, 5119, 192, 64, [0, -500, 0], 100, SIDES12, "Door record 51: gate 1's top band (320 to 384), slides 500 south.")
band('mover:g36', 2704, 4608, 5120, 0, 128, [0, 0, -120], 85, SIDES12, "Door record 36: gate 2's low block (128 to 256), sinks 120.")
band('mover:g47', 2704, 4864, 5120, 129, 127, [0, 250, 0], 85, SIDES12, "Door record 47: gate 2's upper north half (257 to 384), slides 250 north.")
band('mover:g48', 2704, 4608, 4863, 129, 127, [0, -250, 0], 85, SIDES12, "Door record 48: gate 2's upper south half, slides 250 south.")
for (lo_hi, mid_rec, x) in [(38, 44, 2864), (55, 56, 3024), (57, 58, 3184), (60, 59, 3344)]:
    band(f'mover:g{lo_hi}', x, 4608, 5119, 0, 64, [0, -500, 0], 85, SIDES36,
         f"Door record {lo_hi}: the gate's lowest band (128 to 192) and its top band (257 to 384), sliding 500 south together.",
         parts=[{'at': [x, 4863.5], 'size': [32, 511], 'bottom': 129, 'height': 127}])
    band(f'mover:g{mid_rec}', x, 4609, 5120, 65, 63, [0, 500, 0], 85, SIDES36,
         f"Door record {mid_rec}: the gate's middle band (193 to 256), sliding 500 north.")
out['movers'] = M

SW = []
SW.append({'id': 'switch:dais', 'room': 'room:s4', 'kind': 'button', 'at': [-192, 2944], 'floor_height': 120,
           'height': 104, 'size': [64, 64], 'depth': 16, 'off': surf('T3T5', 64, 64), 'sides': surf('T3T7', 32, 32),
           'notes': "Door record 31 (event 62, 'Switch'): a block 64 square of T3T5 standing 16 out of the south wall over the dais's top (faces 89 to 93), pushed in 8."})
cols = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
for i, name in enumerate('ABCDEFGHIJKLMNOP'):
    row = i // 4; col = i % 4
    SW.append({'id': f'switch:{name.lower()}', 'room': 'room:s45', 'kind': 'plate', 'block': 'platform:console', 'side': 'w',
               'along': 0.125 + 0.25 * col, 'height': 72 - 16 * row, 'size': [16, 16],
               'off': surf('T1swDd', 16, 16), 'on': 'T1swDu',
               'notes': f"Event {19 + i} ('{name}'): face {[2010, 2011, 2012, 2013, 2009, 2008, 2007, 2006, 2002, 2003, 2004, 2005, 2001, 2000, 1999, 1998][i]} of the console, row {row + 1} from the top, column {col + 1} from the north."})
out['switches'] = SW

records = {c['chest_index']: c for c in scene['initial_state']['chests']}


def contents(rec):
    r = records[rec]
    b = bytes.fromhex(r['raw_items_hex'])
    items = [x for x in (struct.unpack_from('<i', b, i * 36)[0] for i in range(len(b) // 36)) if x]
    c = {}
    rand = [-x for x in items if x < 0]
    fixed = [x for x in items if x > 0]
    if rand:
        c['random_levels'] = rand
    else:
        c['random_items'] = 0
    if fixed:
        c['items'] = fixed
    if r['flags'] & 1:
        c['trap_level'] = 1
    return c, items, r['flags']


C = []


def chest(cid, rec, place, notes):
    c = {'id': cid}
    c.update(place)
    cont, items, flags = contents(rec)
    c.update(cont)
    c['notes'] = notes + f" Chest record {rec}: {items} as the scene holds it (negative: a random item of that level)" + \
        (", trapped (flags 1; the map row's Trap column, 1)." if flags & 1 else ".")
    C.append(c)


chest('chest:c3', 3, {'room': 'room:s52', 'kind': 'ch1', 'at': [-1152, 3952], 'facing': 'e', 'floor_height': 32},
      "Event 43: the chest on the hidden room's step, front north (faces 1816 to 1823).")
chest('chest:c5', 5, {'room': 'room:s57n', 'kind': 'ch1', 'lid': 'v', 'at': [18640, 8576], 'facing': 'n'},
      "Event 45: the chest in the east cave's niche, front west (faces 1804 to 1811).")
for rec, y in [(6, 5488), (7, 5232), (8, 4976), (9, 4720)]:
    chest(f'chest:c{rec}', rec, {'room': 'room:s50', 'kind': 'ch1', 'lid': 'v', 'at': [11168, y], 'facing': 'n'},
          f"Event {40 + rec}: one of the vault's four chests against its east wall, front west.")
chest('chest:c10', 10, {'room': 'room:s56n', 'kind': 'ch1', 'at': [-20288, 8272], 'facing': 'e'},
      "Event 50: the chest in the west cave's niche, front south (faces 1793 to 1800).")
for rec in (1, 2, 4):
    c = {'id': f'chest:c{rec}', 'box_of': 'chest:c10'}
    cont, items, flags = contents(rec)
    c.update(cont)
    c['notes'] = (f"Chest record {rec} (type 7): it has no box in the original, only the picture ch2frnt on a locker's back wall "
                  f"(a wall panel with an id opens it); its contents {items}" + (", trapped." if flags & 1 else ".") +
                  " `box_of` names another chest only because the studio's box-less chest needs one.")
    C.append(c)
out['chests'] = C

SP = []
for s in scene['spawns']:
    p = s['position']
    pt = (p['x'], p['y'])
    rid = room_of(pt, p['z'])
    sp = {'id': 'spawn:p%02d' % s['spawn_index'], 'room': rid, 'at': [p['x'], p['y']]}
    if s['type_id'] == 3:
        i = s['index']
        if i <= 3:
            sp['slot'] = i
            note = 'index %d' % i
        else:
            sp['slot'] = (i - 4) % 3 + 1
            sp['tier'] = 'abc'[(i - 4) // 3]
            note = 'index %d: slot %d, tier %s' % (i, sp['slot'], sp['tier'])
        sp['notes'] = 'Original spawn %d (%s), at height %d.' % (s['spawn_index'], note, p['z'])
    else:
        sp['kind'] = 'item'
        sp['treasure_level'] = s['index']
        sp['notes'] = 'Original spawn %d: an item of treasure level %d, at height %d.' % (s['spawn_index'], s['index'], p['z'])
    if rid is None:
        print('NO ROOM spawn', s['spawn_index'], pt, file=sys.stderr)
    SP.append(sp)
out['spawns'] = SP

L = []
for i, l in enumerate(exp['lights']):
    x, y, z = l['position']
    rid = room_of((x, y), z - 64)
    fz = floor_under((x, y), z)
    if rid is None or fz is None:
        print('NO ROOM light', i, l['position'], file=sys.stderr)
        continue
    L.append({'id': 'light:l%03d' % i, 'room': rid, 'at': [x, y], 'height': max(1, round(z - fz)), 'radius': l['radius'],
              'brightness': l['brightness'], 'notes': 'Original light record %d (%d, %d, %d; radius %d).' % (i, x, y, z, l['radius'])})
out['lights'] = L

DEC = []
counts = {}
for e in exp['entities']:
    if e['name'] == 'Party Start':
        continue
    x, y, z = e['position']
    rid = room_of((x, y), z - 64)
    fz = floor_under((x, y), z)
    if rid is None:
        r2 = room_near((x, y), z - 64)
        if r2:
            print('deco just outside every outline, put in the nearest room', e['name'], e['position'], r2, file=sys.stderr)
            rid = r2
    if rid is None or fz is None:
        print('NO ROOM deco', e['name'], e['position'], file=sys.stderr)
        continue
    n = e['name'].lower()
    counts[n] = counts.get(n, 0) + 1
    d = {'id': 'deco:%s_%02d' % (n, counts[n]), 'room': rid, 'decoration': e['name'], 'at': [x, y]}
    h = round(z - fz)
    if abs(h) > 1:
        d['height'] = h
    DEC.append(d)
out['decorations'] = DEC


class Dumper(yaml.SafeDumper):
    pass


yaml.dump(out, sys.stdout, Dumper=Dumper, sort_keys=False, width=200, allow_unicode=True)
print('chests', len(C), 'spawns', len(SP), 'lights', len(L), 'decos', len(DEC), file=sys.stderr)
