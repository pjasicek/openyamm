# objects.yml and wiring.yml of the mm6_scifi rebuild (exec'd by gen.py).
import re

DOOR_NOTE = ("The original's leaf slides sideways into the wall; no sideways kind exists, so it lifts instead.")
DOUBLE_NOTE = ("The original has two leaves that slide apart sideways (two door records); one lifting leaf here.")
# id, opening id, kind, thickness, texture, note, the original's door records
DOORS = [
    ('east_porch', 'open:hall_s6_porch', 'slide_up', 64, 'swor2', DOUBLE_NOTE, [2, 3]),
    ('west_porch', 'open:hall_s9_porch', 'slide_up', 64, 'swpnl', DOUBLE_NOTE, [15, 16]),
    ('east_lobby', 'open:s49_s50_east_lobby', 'slide_up', 64, 'swor2', DOOR_NOTE, [4]),
    ('east_store', 'open:s50_s51_east_store', 'slide_up', 64, 'swor', DOOR_NOTE, [5]),
    ('hatch', 'open:s52_s53_ramp_down', 'slide_down', 63, 'swtrpnl',
     "The original's door 13 sinks 255 into the floor.", [13]),
    ('vault', 'open:s53_s54_vault', 'slide_up', 32, 'swor2', DOOR_NOTE, [14]),
    ('junction_south', 'open:s22_s33_storage_corridor', 'slide_up', 64, 'swor2', DOOR_NOTE, [6]),
    ('storage_1', 'open:s33_s69_storage_1', 'slide_up', 64, 'swdoora', DOOR_NOTE, [7]),
    ('storage_2', 'open:s33_s70_storage_2', 'slide_up', 64, 'swdoora', DOOR_NOTE, [8]),
    ('storage_3', 'open:s33_s71_storage_3', 'slide_up', 64, 'swdoora', DOOR_NOTE, [9]),
    ('tube_exit', 'open:s22_s72_tube', 'slide_up', 64, 'swdoorc', DOUBLE_NOTE, [10, 11]),
    ('repair_bay', 'open:s32_s34_repair_bay', 'slide_up', 64, 'swdoorb', DOOR_NOTE, [12]),
    ('plug', 'open:plug', 'slide_down', 255, 'swdoorc',
     "The original's door 17: a block 255 long that fills the passage's end and sinks 245 into the floor.", [17]),
    ('wedge_room', 'open:s38_s40_wedge_room', 'slide_up', 64, 'swdoora', DOOR_NOTE, [18]),
    ('meeting_hall', 'open:s38_s39_meeting_hall', 'slide_up', 64, 'swor', DOOR_NOTE, [19]),
    ('locked_room', 'open:s39_s43_locked_room', 'slide_up', 64, 'swdoorb', DOOR_NOTE, [1]),
    ('h_room', 'open:s42_s41_h_room', 'slide_up', 64, 'swdoorb', DOOR_NOTE, [20]),
    ('panel_room', 'open:s42_s48_panel_room', 'slide_up', 64, 'swor2', DOOR_NOTE, [21]),
    ('gate_slab', 'open:gate_slab', 'slide_up', 197, 'swankdk',
     "The original's door 23: a slab 197 thick that hangs in the corridor 32 above a 16-high sill and lifts 200.",
     [23]),
    ('plate_store', 'open:s55_s68_plate_store', 'slide_up', 64, 'swdoorb', DOOR_NOTE, [25]),
    ('airlock', 'open:s58_s91_airlock', 'slide_up', 64, 'swdoorb', DOUBLE_NOTE, [27, 28]),
]

TERMINALS = {
    53: 'Hello and welcome to this self-guided tour of the Varn Planetary Control Facility.  We gladly welcome all visitors.  As you arrive at each key area, be sure to check any of our display screens for more information.  Enjoy your tour!',
    54: 'This is the main equipment storage and repair facility.  By now, you may have noticed several floating Drone-bots.  They are responsible both for maintaining the key systems of this facility as well as sanitation.  If a unit becomes damaged, it is brought here to be repaired.',
    55: "The room to your left is the main meeting hall.  Visiting dignitaries from around the world have feasted at banquets held in their honor.  In fact, it is said that at his 21st birthday party King Sheridan nearly choked to death on a piece of mogred, but was saved by a serving girl who he later married and made his Queen.  Ahh, l'amour.",
    56: "Chief Engineer Wilson's Personal Log.  I have locked myself in Storage Room #6 but currently have no means of escape.  The drone-bots have gone mad and have started killing everyone in sight.  I was able to access the main control terminal on Level Four despite warnings of a hazardous leak, and I sent a distress signal, but since we have not had contact with any of the colonies for several weeks, I do not believe that a rescue is possible.  I have also managed to seal this facility so that the drones can not escape.  It is my hope that the colonists will be able to mount some sort of defense by the time my encryption codes are broken.  Tell Emma I love her.  Wilson out.",
    57: 'We apologize for any inconvenience, but we ask that all personnel evacuate the facility at this time.  Please do not be alarmed.  Thank you.',
    58: 'Before entering the Planetary Reaction Chamber, please request a pair of Safety Goggles from one of our Drones.  During peak hours of operation, this facility can generate enough power to produce a light bright enough to be seen from space.  Please avoid looking directly into the light.',
    59: 'Alert, environmental controls are offline on Level Four, Sections 18 through 96.  Access restricted to drones until further notice.',
    60: 'Warning, intruder alert, Level Four, Section.  All drones proceed to Level Four to intercept intruders.  Reactor is offline.  Encryption integrity at 2.064%.  Warning, intruder alert, Level Four',
    61: 'Blaster weapons provide an effective, accurate ranged attack.  To operate the blaster, hold the grip comfortably in your hand, point the barrel at your target, and gently squeeze the trigger.  Should the weapon misfire, do not look into the barrel- give the weapon to an instructor and let them fix the problem.  Never point a blaster at something you do not want to vaporize.',
}


def wall_of(r, x, y):
    best = None
    o = r['outline']
    for i in range(len(o)):
        p, al, ow, L = frame(o, i)
        t = (x - p[0]) * al[0] + (y - p[1]) * al[1]
        dist = abs((x - p[0]) * ow[0] + (y - p[1]) * ow[1])
        if -1 <= t <= L + 1 and (best is None or dist < best[0]):
            best = (dist, i, max(0, min(1, t / L)))
    return best[1], round(best[2], 3)


def wall_fit(r, x, y, width):
    w, al = wall_of(r, x, y)
    p, a2, ow, L = frame(r['outline'], w)
    c = max(width / 2 + 9, min(L - width / 2 - 9, al * L))
    return w, round(c / L, 4)


def clear(o, x, y, m):
    if not inside(o, x, y):
        return False
    for i in range(len(o)):
        p, al, ow, L = frame(o, i)
        t = (x - p[0]) * al[0] + (y - p[1]) * al[1]
        t = max(0, min(L, t))
        if math.hypot(x - p[0] - al[0] * t, y - p[1] - al[1] * t) < m:
            return False
    return True


SEC_ROOMS = collections.defaultdict(list)


def snap(x, y, z, sec=None, m=8, slack=40):
    """The room a point of the original belongs to, and the point moved inside it when it stands in a wall."""
    r = room_at(x, y, z, slack)
    if r is not None and clear(r['outline'], x, y, m):
        return r, x, y
    cands = [r] if r is not None else []
    if not SEC_ROOMS:
        for rr in ROOMS:
            SEC_ROOMS[rr['sec']].append(rr)
    if sec is not None:
        cands += SEC_ROOMS.get(sec, [])
    if not cands:
        cands = ROOMS
    best = None
    for rr in cands:
        lo = min(rr['floor'], rr.get('slope', {}).get('to', rr['floor']))
        if not cands is ROOMS or (lo - 80 <= z <= rr['ceiling'] + 80):
            for rad in range(8, 400, 8):
                found = False
                for k in range(16):
                    nx = x + rad * math.cos(k * math.pi / 8)
                    ny = y + rad * math.sin(k * math.pi / 8)
                    if clear(rr['outline'], nx, ny, m):
                        if best is None or rad < best[0]:
                            best = (rad, rr, int(round(nx)), int(round(ny)))
                        found = True
                        break
                if found:
                    break
    if best is None:
        return None, x, y
    return best[1], best[2], best[3]


LIGHT_SEC = {}
for _si, _s in enumerate(S):
    for _l in _s['lights']:
        LIGHT_SEC[_l] = _si


def floor_of(r):
    return r['floor']


def write_objects():
    ev = collections.defaultdict(list)
    for i, f in enumerate(F):
        if f['cog_triggered']:
            ev[f['cog_triggered']].append(i)
    obj = {'format': 0}
    obj['start'] = {'room': 'room:s65_entry', 'at': [-9280, 4160], 'facing': 's',
                    'notes': "The original's Party Start (-9280, 4160, 196), facing south down the entrance corridor."}
    openings = {o.get('oid'): o for o in OPEN}
    doors = []
    for did, oid, kind, th, tex, note, recs in DOORS:
        assert oid in openings, oid
        assert openings[oid]['gap'] >= th - 1e-6, (oid, openings[oid]['gap'])
        doors.append({'id': 'door:' + did, 'opening': oid, 'kind': kind, 'state': 'closed', 'thickness': th,
                      'speed': 150, 'surface': surf(tex, fit=True),
                      'notes': note + " Original door record%s %s." % ('s' if len(recs) > 1 else '',
                                                                      ' and '.join(str(x) for x in recs))})
    obj['doors'] = doors
    # lights: the original's, where they stand
    lights = []
    lost = 0
    for i, l in enumerate(d['lights']):
        x, y, z = l['position']
        r, x, y = snap(x, y, z, LIGHT_SEC.get(i))
        if r is None:
            lost += 1
            print('  light', i, l['position'], 'sector', LIGHT_SEC.get(i))
            continue
        fl = r['floor']
        if 'slope' in r:
            fl = min(r['floor'], r['slope']['to'])
        h = max(8, min(z - fl, r['ceiling'] - fl - 8))
        lights.append({'id': 'light:l%03d' % i, 'room': 'room:' + r['id'], 'at': [x, y], 'height': h,
                       'radius': l['radius'], 'brightness': l['brightness']})
    obj['lights'] = lights
    print('lights', len(lights), 'outside every room', lost)
    # switches: the button and the nine terminals
    sw = []
    r = RB['s39_meeting_hall']
    w, al = wall_of(r, -2976, 4480)
    sw.append({'id': 'switch:meeting_hall_button', 'room': 'room:s39_meeting_hall', 'wall': w, 'along': al,
               'height': 167, 'size': [32, 32], 'off': surf('swr4'), 'on': 'swr4dk',
               'notes': "The original's door 26: a 32-square button in the north wall that sinks 13 when pressed "
                        "and opens the door to the room behind (door 1)."})
    term = []
    for n in sorted(TERMINALS):
        fi = ev[n][0]
        lo, hi = bb(F[fi])
        cx, cy, cz = [(lo[k] + hi[k]) / 2 for k in range(3)]
        r = room_at(cx, cy, cz, 60)
        if r is None:  # the screen is in the wall plane: look a little inside
            nrm = F[fi]['plane_normal']
            r = room_at(cx + nrm[0] / 65536 * 40, cy + nrm[1] / 65536 * 40, cz, 60)
        w, al = wall_fit(r, cx, cy, 128)
        sw.append({'id': 'switch:terminal_%d' % n, 'room': 'room:' + r['id'], 'wall': w, 'along': al,
                   'height': int(cz - r['floor']), 'size': [128, 64], 'off': surf('trekscrn'), 'on': 'trekscon',
                   'notes': "Computer terminal: the original's event %d (a wall screen 128 by 64)." % n})
        term.append(n)
    obj['switches'] = sw
    # chests: every box of the original that opens a chest
    chests = []
    chest_events = []
    CH = {29: 0, 30: 1, 31: 2, 32: 3, 33: 4, 34: 5, 35: 6, 36: 7, 37: 8, 65: 9, 66: 10, 67: 11, 68: 12, 69: 13}
    for e in sorted(CH):
        bysec = collections.defaultdict(list)
        for fi in ev[e]:
            if F[fi]['texture'].lower().startswith('ch5'):
                bysec[F[fi]['room']].append(fi)
        for k, (sec, fs) in enumerate(sorted(bysec.items())):
            los = [bb(F[i])[0] for i in fs]
            his = [bb(F[i])[1] for i in fs]
            lo = [min(l[k2] for l in los) for k2 in range(3)]
            hi = [max(h[k2] for h in his) for k2 in range(3)]
            cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
            if hi[2] - lo[2] < 8:
                continue  # one stray face of a neighbouring box bound to this event
            m = min(sx_ := hi[0] - lo[0], hi[1] - lo[1]) / 2 + 6
            m = math.hypot(hi[0] - lo[0], hi[1] - lo[1]) / 2 + 4
            r, cx, cy = snap(cx, cy, lo[2] + 10, sec, m, 60)
            if r is None:
                print('chest outside rooms', e, sec, lo, hi)
                continue
            # keep the box 4 clear of the room's walls
            cid = 'chest:c%d%s' % (CH[e], '' if len(bysec) == 1 else 'ab'[k])
            sx, sy, sz = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
            c = {'id': cid, 'room': 'room:' + r['id'], 'at': [int(cx), int(cy)],
                 'size': [int(max(sx, sy)), int(min(sx, sy)), int(sz)], 'facing': 0 if sx >= sy else 90,
                 'surface': surf('ch5frnt', fit=True), 'end_surface': surf('ch5side', fit=True),
                 'treasure_level': 5, 'random_items': 3,
                 'notes': "Storage container: the original's chest %d (event %d), a box in sector %d%s. Its "
                          "contents are not copied (the original's are fixed items in the map's saved state); "
                          "three random items stand in." % (
                              CH[e], e, sec, '' if len(bysec) == 1 else
                              '; in the original two boxes open this one chest, here each has its own')}
            chests.append(c)
            chest_events.append((cid, e))
    obj['chests'] = chests
    # spawns
    spawns = []
    SLOT = {1: 1, 4: 1, 5: 1, 6: 1, 2: 2, 7: 2, 8: 2, 9: 2, 3: 3, 10: 3, 11: 3, 12: 3}
    for i, s in enumerate(d['spawns']):
        x, y, z = s['position']
        r, x, y = snap(x, y, z + 20, None, 40, 80)
        if r is None:
            print('spawn outside rooms', i, s['position'])
            continue
        spawns.append({'id': 'spawn:m%02d' % i, 'room': 'room:' + r['id'], 'at': [x, y], 'slot': SLOT[s['index']],
                       'radius': s['radius'],
                       'notes': "Original spawn %d, encounter index %d." % (i, s['index'])})
    obj['spawns'] = spawns
    r = RB['s65_entry']
    w, al = wall_of(r, -9216, 4288)
    obj['exits'] = [{'id': 'exit:to_oracle', 'room': 'room:s65_entry', 'wall': w, 'along': al,
                     'size': [256, 256], 'surface': surf('swdoorb', fit=True), 'to': 'exit:oracle',
                     'notes': "The original's event 70: the door behind the party start, back to the Oracle."}]
    ph = []
    for k, (x, y) in enumerate([(-1920, -2048), (-1920, 1280), (2688, 1280), (2688, -2048)]):
        ph.append({'id': 'placeholder:shaft_%d' % (k + 1), 'room': 'room:hall_upper', 'at': [x, y],
                   'size': [448, 448, 416],
                   'stands_for': "A square shaft through the floor, 448 by 448 and 416 deep, open into the lower "
                                 "hall below (the original's sectors 86 to 89): one looks, drops and shoots through "
                                 "it. A hole in a floor onto the room below is not in the vocabulary.",
                   })
    ph.append({'id': 'placeholder:pressure_plate', 'room': 'room:s55_plate_room', 'at': [-9168, -2698],
               'size': [128, 128, 1],
               'stands_for': "A pressure plate 128 square in the floor (the original's door 24, event 24): stepping "
                             "on it toggles the store's door. Floor triggers are not in the vocabulary; the door "
                             "opens on a click instead."})
    ph.append({'id': 'placeholder:lounge_window', 'room': 'room:s62_lounge', 'at': [-4200, -382],
               'size': [16, 593, 128],
               'stands_for': "A window in the lounge's east wall, 128 above its floor, down into the west "
                             "passage's ramp (the original's portal between sectors 62 and 9)."})
    ph.append({'id': 'placeholder:balcony_window', 'room': 'room:s35_upper_room_n', 'at': [-4990, 498],
               'size': [16, 128, 98],
               'stands_for': "A slot 128 wide and 98 high in the corridor's east wall, 110 above the floor, "
                             "down into the low passage's ramp (the original's portal between sectors 35 and 60)."})
    ph.append({'id': 'placeholder:spark_trap', 'room': 'room:s70_storage_2', 'at': [-5632, -4368],
               'size': [16, 16, 16],
               'stands_for': "The original's event 71: a Sparks spell cast across storage room 2 (from -5632, "
                             "-4736 to -5632, -4000 at height 660), bound to no face in the shipped map."})
    obj['placeholders'] = ph
    obj['notes'] = ("Doors, lights, spawns, chests, the button and the terminals stand where the original's do. The "
                    "80 spawns keep their position and slot; the original's encounter index (1, 4, 7, 10: a fixed "
                    "tier of a slot) has no field. The tube's 15 floor triggers that switch its lights (events 38 "
                    "to 52) and the three short-circuit handlers (62 to 64) are not in the project.")
    yaml.safe_dump(obj, open(L4 + '/objects.yml', 'w'), default_flow_style=None, sort_keys=False, width=100000)

    evs = []

    def door_evt(did, title='Door', **kw):
        e = {'id': 'evt:' + did, 'preset': 'door', 'source': 'door:' + did, 'title': title, 'action': 'open'}
        e.update(kw)
        evs.append(e)

    for did in ('east_lobby', 'east_store', 'hatch', 'vault', 'junction_south', 'tube_exit', 'repair_bay', 'plug',
                'wedge_room', 'meeting_hall', 'h_room', 'panel_room', 'gate_slab', 'plate_store', 'airlock'):
        door_evt(did)
    lock = {}
    if os.path.exists(L4 + '/ids.lock.yml'):
        lock = (yaml.safe_load(open(L4 + '/ids.lock.yml')) or {}).get('doors', {})

    def shut(*ids):
        return '\n'.join('evt.SetDoorState(%d, DoorAction.Close)' % lock['door:' + i] for i in ids if 'door:' + i in lock)

    evs.append({'id': 'evt:east_porch', 'preset': 'door', 'source': 'door:east_porch', 'title': 'Door',
                'lua': shut('west_porch'),
                'notes': "The original's event 2: the east porch door toggles and the west one shuts, so the lower "
                         "hall is never open on both sides. A door preset moves only its own door, so the other door is shut by a Lua line that names its number in ids.lock.yml."})
    evs.append({'id': 'evt:west_porch', 'preset': 'door', 'source': 'door:west_porch', 'title': 'Door',
                'lua': shut('east_porch'),
                'notes': "The original's event 15, the mirror of evt:east_porch."})
    for a, others in (('storage_1', ['storage_2', 'storage_3']), ('storage_2', ['storage_1', 'storage_3']),
                      ('storage_3', ['storage_1', 'storage_2'])):
        evs.append({'id': 'evt:' + a, 'preset': 'door', 'source': 'door:' + a, 'title': 'Door', 'action': 'open',
                    'lua': shut(*others),
                    'notes': "The original's events 7 to 9: opening one storage room shuts the other two."})
    evs.append({'id': 'evt:locked_room', 'preset': 'text', 'source': 'door:locked_room', 'title': 'Door',
                'text': "The door won't budge.",
                'notes': "The original's event 1; the button in the meeting hall opens this door."})
    evs.append({'id': 'evt:meeting_hall_button', 'preset': 'switch', 'source': 'switch:meeting_hall_button',
                'title': 'Door', 'toggles': ['door:locked_room'], 'notes': "The original's event 26."})
    for cid, e in chest_events:
        ce = {'id': 'evt:' + cid.split(':')[1], 'preset': 'chest', 'source': cid, 'title': 'Storage Container'}
        if e == 34:
            ce['effects'] = [{'add': {'var': 'Awards', 'value': 103}}]
            ce['notes'] = "The original's event 34 also gives every member award 103."
        evs.append(ce)
    for n in term:
        e = {'id': 'evt:terminal_%d' % n, 'preset': 'switch', 'source': 'switch:terminal_%d' % n,
             'title': 'Computer Terminal', 'text': TERMINALS[n],
             'notes': "The original shows this in a message window (evt.SetMessage) and turns the screen to "
                      "trekscon; here the switch's `on` texture and the preset's text."}
        if n == 61:
            e['effects'] = [{'qbit': 1300}]
        evs.append(e)
    evs.append({'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:to_oracle', 'title': 'Exit'})
    yaml.safe_dump({'format': 0, 'events': evs}, open(L4 + '/wiring.yml', 'w'), default_flow_style=None,
                   sort_keys=False, width=100000)
    print(len(doors), 'doors', len(chests), 'chests', len(spawns), 'spawns', len(sw), 'switches', len(evs), 'events')
