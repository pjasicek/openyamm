#!/usr/bin/env python3
"""DD-22 Sheltem's Pod, L4: objects.yml and wiring.yml (written by gen.py L4)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

import geo

PATROL, ANNIHILATOR = 11610, 11611
NAME = {PATROL: 'patrol', ANNIHILATOR: 'annihilator'}
ROBOTS = 1          # one group: the guard machines

COLD = [150, 175, 200]
RED = [235, 60, 50]
DIMRED = [200, 70, 55]
TEAL = [110, 190, 190]

ARRIVAL_AT = [0, -832]
L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/dd22/L4')


def R(r):
    return 'room:' + r


def door_number(did, fallback):
    """A door's number in ids.lock.yml (evt.SetDoorState); before the first build, the fallback."""
    p = L4 / 'ids.lock.yml'
    if p.exists():
        ids = yaml.safe_load(p.read_text()) or {}
        n = (ids.get('doors') or {}).get(did)
        if n:
            return n
    return fallback


def sound_number(sid, fallback):
    """The placed sound's number in ids.lock.yml (AmbientSound<number>); before the first build, the fallback."""
    p = L4 / 'ids.lock.yml'
    if p.exists():
        ids = yaml.safe_load(p.read_text()) or {}
        n = (ids.get('sounds') or {}).get(sid)
        if n:
            return n
    return fallback


# ------------------------------------------------------------------------------------------------ objects
def doors():
    return [
        {'id': 'door:airlock', 'opening': 'open:airlock_ring', 'kind': 'slide_left', 'surface': dict(geo.DOOR, fit=True),
         'notes': "The airlock's inner door, north into the lower ring."},
        {'id': 'door:stores', 'opening': 'open:shaft_stores', 'kind': 'slide_right', 'surface': dict(geo.DOOR, fit=True),
         'notes': "The stores' door off the shaft's foot."},
        {'id': 'door:maint', 'opening': 'open:ring_ladder', 'kind': 'slide_left', 'surface': dict(geo.MAINT, fit=True),
         'notes': "The maintenance hatch in the lower ring's east arm (swtrpnl, DD-17's maintenance doors)."},
        {'id': 'door:gun', 'opening': 'open:ring_gun', 'kind': 'slide_left', 'surface': dict(geo.DOOR, fit=True),
         'notes': "The gun deck's door."},
        {'id': 'door:brig', 'opening': 'open:ring_brig', 'kind': 'slide_left', 'surface': dict(geo.DOOR, fit=True),
         'notes': "The brig's door."},
        {'id': 'door:security', 'opening': 'open:brig_security', 'kind': 'slide_left',
         'surface': dict(geo.DOOR, fit=True), 'notes': "The security post's door off the brig."},
        {'id': 'door:blast', 'opening': 'open:blast', 'kind': 'slide_left', 'leaves': 2,
         'pictures': [[dict(geo.HATCH)]], 'back_pictures': [[dict(geo.HATCH)]],
         'notes': "The bridge's blast door: one riveted blast door (swdoora) over both leaves, parting in the middle (DD-17's Command Central pattern); sealed by the lockdown, opened for good by the security console (D-43)."},
    ]


def lifts():
    return [
        {'id': 'lift:a', 'room': R('shaft0'), 'at': geo.LIFT_A, 'size': geo.LIFT_SIZE, 'travel': geo.LIFT_TRAVEL,
         'thickness': 16, 'speed': 224, 'surface': dict(geo.REDFLOOR),
         'notes': "Lift A: a red-gridded pad from the shaft's foot (deck 1, down) up through the middle ring's floor (deck 2, up, 448); 2 s."},
        {'id': 'lift:b', 'room': R('ring1'), 'at': geo.LIFT_B, 'size': geo.LIFT_SIZE, 'travel': geo.LIFT_TRAVEL,
         'thickness': 16, 'speed': 224, 'surface': dict(geo.REDFLOOR),
         'notes': "Lift B: from the middle ring (deck 2, down) up through the bridge landing's floor (deck 3, up, 896)."},
    ]


def switches():
    def button(sid, room, at, notes):
        return {'id': sid, 'room': R(room), 'kind': 'button', 'at': at, 'height': 112, 'notes': notes}
    return [
        button('switch:lift_a1', 'shaft0', [geo.LIFT_A[0], geo.SHAFT[3]], "Lift A's button on the shaft's north wall, over the pad (deck 1)."),
        button('switch:lift_a2', 'ring1', [geo.LIFT_A[0], geo.RING1[3]], "Lift A's button on the middle ring's north wall, over its well (deck 2)."),
        button('switch:lift_b2', 'ring1', [geo.LIFT_B[0], geo.RING1[3]], "Lift B's button on the middle ring's north wall, over the pad (deck 2)."),
        button('switch:lift_b3', 'bridge_ante', [geo.LIFT_B[0], geo.ANTE[3]], "Lift B's button on the bridge landing's north wall, over its well (deck 3)."),
    ]


def ladders():
    return [{'id': 'ladder:maint', 'room': R('ladder'), 'at': geo.LADDER_AT, 'facing': 'n', 'height': geo.LIFT_TRAVEL,
             'exit': geo.LADDER_EXIT, 'surface': dict(geo.LADDERTEX),
             'notes': "The maintenance ladder up through the gun deck's floor hatch (the loop)."}]


# F6 feedback fix (2026-11-21): every Xeen chest is the shipped chest; MM8's (gt002) suits the pod's metal decks. A
# chest's `facing` is its long axis: the front (the lock) faces 90 degrees anticlockwise of it (e -> north, w -> south).
LOCKER = {'kind': 'gt002'}


def chests():
    return [dict(c, **LOCKER) for c in [
        {'id': 'chest:stores', 'room': R('stores'), 'at': [-640, 400], 'facing': 'w', 'treasure_level': 6,
         'random_items': 3, 'gold': 4000, 'notes': "The pod's stores locker (T6), against the north wall."},
        {'id': 'chest:brig', 'room': R('brig'), 'at': [-832, -464], 'facing': 'e', 'treasure_level': 6,
         'random_items': 3, 'gold': 4000, 'notes': "The guards' locker (T6), against the south wall."},
        {'id': 'chest:couch', 'room': R('bridge'), 'at': [0, 880], 'facing': 'w', 'treasure_level': 6,
         'random_items': 3, 'gold': 6000, 'notes': "Sheltem's locker (T6), on the couch's dais under its high back."},
    ]]


PLACED = {
    'ring0': [(PATROL, [-384, -384]), (PATROL, [256, -400])],
    'drive': [(PATROL, [-640, 896]), (PATROL, [512, 704]), (ANNIHILATOR, [0, 1184])],
    'stores': [(PATROL, [-640, 64]), (PATROL, [-704, 256])],
    'gun_deck': [(PATROL, [768, -320]), (PATROL, [768, 576]), (ANNIHILATOR, [1024, -192])],
    'brig': [(PATROL, [-896, -256]), (PATROL, [-768, 256]), (ANNIHILATOR, [-960, 64])],
    'security': [(ANNIHILATOR, [-1024, 704]), (ANNIHILATOR, [-704, 768]), (PATROL, [-896, 864])],
    'bridge_ante': [(PATROL, [-384, 0]), (PATROL, [-160, -64])],
    'bridge': [(PATROL, [-640, 896]), (ANNIHILATOR, [640, 896])],
}


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 270, 'group': ROBOTS})
    return out


def decorations():
    return [
        {'id': 'deco:stores_barrel_1', 'room': R('stores'), 'decoration': 'bigbarel', 'at': [-784, -80],
         'notes': "A pair of barrels in the stores' south-west corner."},
        {'id': 'deco:stores_barrel_2', 'room': R('stores'), 'decoration': 'bigbarel', 'at': [-784, 16]},
        {'id': 'deco:stores_keg_1', 'room': R('stores'), 'decoration': 'smlbarel', 'at': [-784, 400],
         'notes': "Two small kegs in the north-west corner."},
        {'id': 'deco:stores_keg_2', 'room': R('stores'), 'decoration': 'smlbarel', 'at': [-784, 320]},
    ]


def lights():
    L = []

    def add(room, at, radius, color, height=None, notes=None, **kw):
        d = {'id': f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height is not None:
            d['height'] = height
        d.update(kw)
        if notes:
            d['notes'] = notes
        L.append(d)
    # deck 1
    add('airlock', [0, -832], 700, DIMRED, height=288, notes="The airlock's red emergency lamp.")
    add('ring0', [-352, -384], 800, COLD, height=288)
    add('ring0', [576, 0], 800, COLD, height=288)
    add('shaft0', [0, 160], 900, COLD, height=288)
    add('stores', [-640, 160], 700, COLD, height=288)
    add('drive', [-384, 896], 900, COLD, height=288)
    add('drive', [384, 896], 900, COLD, height=288)
    add('drive', [0, 896], 800, RED, height=24, notes="The drive's red glow under the grilles.",
        pulse={'intensity': [0.6, 1], 'frequency': 0.25})
    add('ladder', [960, 64], 600, COLD, height=288)
    # deck 2
    add('ring1', [0, -128], 1000, COLD, height=288)
    add('gun_deck', [832, -192], 900, COLD, height=288)
    add('gun_deck', [832, 448], 900, COLD, height=288)
    add('brig', [-896, -128], 1000, TEAL, height=288)
    add('brig', [-1120, 0], 500, DIMRED, height=128, notes="The dark cells' faint red.")
    add('security', [-896, 832], 900, RED, height=288, notes="The security post's alarm light.",
        pulse={'intensity': [0.35, 1], 'frequency': 1.0})
    # deck 3
    add('bridge_ante', [-64, 160], 1000, COLD, height=400)
    add('bridge', [0, 1056], 1500, RED, height=700, notes="The bridge's red light under the dome.")
    add('bridge', [-640, 1088], 900, DIMRED, height=320)
    add('bridge', [640, 1088], 900, DIMRED, height=320)
    add('bridge', [-320, 1472], 600, RED, height=160, notes="The main console flickering red.",
        pulse={'intensity': [0.3, 1], 'frequency': 2.3})
    add('bridge', [320, 1472], 600, RED, height=160, notes="The scanning console flickering red.",
        pulse={'intensity': [0.3, 1], 'frequency': 1.7, 'phase': 0.4})
    add('bridge', [896, 1088], 500, TEAL, height=160, notes="The log computer's screen.")
    return L


ALARM_AT = [-896, 960]


def sounds():
    return [
        {'id': 'sound:bed_deck1', 'room': R('shaft0'), 'at': [0, 160], 'sound': 'humming', 'radius': 2200,
         'inner_radius': 1100, 'volume': 0.22, 'pan': False,
         'notes': "The pod's cold hum over deck 1 (D-48: a bed, not panned)."},
        {'id': 'sound:bed_deck2', 'room': R('ring1'), 'at': [0, 0], 'sound': 'humming', 'radius': 2200,
         'inner_radius': 1100, 'volume': 0.2, 'pan': False, 'notes': "The hum over deck 2, not panned."},
        {'id': 'sound:bed_bridge', 'room': R('bridge'), 'at': [0, 1088], 'sound': 'humming', 'radius': 2000,
         'inner_radius': 1000, 'volume': 0.2, 'pan': False, 'notes': "The hum over deck 3, not panned."},
        {'id': 'sound:alarm', 'room': R('security'), 'at': ALARM_AT, 'sound': 'xeen_pod_alarm', 'radius': 1300,
         'inner_radius': 400, 'volume': 0.35,
         'notes': "The security console's alarm (AU's two-tone beep, a loop): it stops when the lockdown is released (AmbientSound map variable)."},
    ]


def exits():
    return [{'id': 'exit:hatch', 'room': R('airlock'), 'at': [0, geo.AIRLOCK[1]], 'size': [256, 256],
             'surface': geo.S_('7solid01', 256, 256, fit=True), 'to': 'exit:d6_hatch',
             'notes': "The round hatch's inner face (the riveted swdoora with its boss): out to D6."}]


def objects():
    return {
        'format': 0,
        'start': {'room': R('airlock'), 'at': ARRIVAL_AT, 'facing': 'n',
                  'notes': "In the airlock 192 inside the hatch, facing north."},
        'arrivals': [
            {'entrance': 'entrance:d6_hatch', 'room': R('airlock'), 'at': ARRIVAL_AT, 'facing': 'n',
             'notes': "From D6's hatch (door:dd22, A6; A3's d6.sheltem_hatch once m33.done)."},
        ],
        'doors': doors(), 'lifts': lifts(), 'switches': switches(), 'ladders': ladders(), 'chests': chests(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': exits(),
        'notes': "DD-22's contents, written by output/studio_cal/dd22/tools/dress.py: 7 doors (the blast door a two-leaf pair) and the hatch's exit face, two lifts (A deck 1 to 2, B deck 2 to 3) with four call buttons, the maintenance ladder, 3 chests (T6), 20 placed robots (Patrol 11610 x14, Annihilator 11611 x6), the stores' barrels.",
    }


# ------------------------------------------------------------------------------------------------- wiring
LOG_LUA = "\n".join([
    'local page = 1',
    'for n = 1, 5 do',
    '    if IsAtLeast(MapVar(log_page), n) then page = n + 1 end',
    'end',
    f'evt.PlaySoundName("xeen_log_chirp", 896, 1088, {geo.D3 + 160})',
] + [f'{"if" if n == 1 else "elseif"} page == {n} then\n    XeenQuests.hook("dd22.log_page_{n}")' for n in range(1, 7)] + [
    'end',
    'SetValue(MapVar(log_page), page % 6)',
])

ARRIVE_TEXT = "Escape Pod 2. Cold air, red light, and somewhere above, machines still on guard."


def lift_event(eid, source, lift, text):
    return {'id': eid, 'preset': 'switch', 'source': source, 'title': 'Lift', 'toggles': [lift],
            'effects': [{'lua': f'evt.PlaySoundName("xeen_lift", {geo.LIFT_A[0] if lift == "lift:a" else geo.LIFT_B[0]}, '
                                f'{geo.LIFT_A[1]}, {geo.D2 if lift == "lift:a" else geo.D3})'}],
            'notes': text}


def events():
    alarm = sound_number('sound:alarm', 1)
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'dd22_arrived_once'}},
              'effects': [{'qbit': 'dd22_arrived_once'}, {'text': ARRIVE_TEXT}],
              'notes': "The first arrival (dd22_arrived_once 117760): one status line (map-local, for A3; A3 has no hook text for it); the airlock is quiet (D-11.3)."})
    E.append({'id': 'evt:hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Exit Escape Pod 2',
              'notes': "Out to D6 at its named arrival entrance:dd22_hatch (7168, 12288, 1952) facing 1536: the game's own leave window (D-24); 'Exit Escape Pod 2?' (aaze0088:1) is its meaning, as DD-16's 'Exit Escape Pod 1'."})
    for d, title in (('airlock', 'Airlock door'), ('stores', 'Stores'), ('maint', 'Maintenance hatch'),
                     ('gun', 'Gun deck'), ('brig', 'Brig'), ('security', 'Security post')):
        E.append({'id': f'evt:door_{d}', 'preset': 'door', 'source': f'door:{d}', 'title': title})
    # the lockdown
    blast = door_number('door:blast', 4)
    blast2 = door_number('door:blast.leaf2', 5)
    console_lua = "\n".join([
        'if continueStep == 1 then',
        f'    evt.SetDoorState({blast}, DoorAction.Open)',
        f'    evt.SetDoorState({blast2}, DoorAction.Open)',
        '    XeenQuests.hook("dd22.security_console")',
        f'    evt.SetMapVar("AmbientSound{alarm}", 2)',
        '    return',
        'end',
        'if continueStep ~= nil then',
        '    return',
        'end',
        'if IsQBitSet(QBit(117761)) then',
        '    XeenQuests.hook("dd22.security_console")',
        '    return',
        'end',
        'AskChoiceWithAnswerSteps(eventId, 3, "Security lockdown: bridge sealed. Release?", '
        '{{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})',
    ])
    E.append({'id': 'evt:security_console', 'preset': 'script', 'source': 'platform:sec_console',
              'title': 'Security Console', 'lua': console_lua,
              'notes': "goal:lockdown (D-62; D-67 change 7: Yes/No buttons; D-65 B1: no message before the prompt, so the prompt keeps its own text): Yes calls A3's dd22.security_console (lockdown_released 117761, once), opens the bridge's blast door for good (both leaves, one way, D-43) and stops the alarm. Later clicks: the hook's else text."})
    E.append({'id': 'evt:lockdown_load', 'preset': 'script', 'trigger': 'load',
              'condition': {'qbit': 'lockdown_released'}, 'opens': ['door:blast'],
              'effects': [{'lua': f'evt.SetMapVar("AmbientSound{alarm}", 2)'}],
              'notes': "Every load after the release: the blast door open, the alarm silent."})
    E.append({'id': 'evt:blast', 'preset': 'script', 'source': 'door:blast', 'title': 'Blast door',
              'condition': {'not': {'qbit': 'lockdown_released'}},
              'effects': [{'lua': 'XeenQuests.hook("dd22.blast_door")'}],
              'else_effects': [{'text': "The blast door stands open."}],
              'notes': "While the lockdown holds: A3's dd22.blast_door (its fail text 'The bridge door is sealed. Security lockdown.')."})
    # the lifts
    E.append(lift_event('evt:lift_a1', 'switch:lift_a1', 'lift:a', "Lift A from deck 1: up or called down."))
    E.append(lift_event('evt:lift_a2', 'switch:lift_a2', 'lift:a', "Lift A from deck 2: down or called up."))
    E.append(lift_event('evt:lift_b2', 'switch:lift_b2', 'lift:b', "Lift B from deck 2: up or called down."))
    E.append(lift_event('evt:lift_b3', 'switch:lift_b3', 'lift:b', "Lift B from deck 3: down or called up."))
    # the gun deck
    for k, name, ref in (('phaser', 'Phaser Control', 2), ('photon', 'Photon Control', 3)):
        lua = "\n".join([
            'if continueStep == 1 then',
            '    XeenQuests.hook("dd22.weapons")',
            '    return',
            'end',
            'if continueStep ~= nil then',
            '    return',
            'end',
            f'evt.SetMessage("{name}. A status indicator on the weapon shows it to be disarmed. Fire anyway?")',
            'AskChoiceWithAnswerSteps(eventId, 3, "Fire anyway?", {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})',
        ])
        E.append({'id': f'evt:{k}', 'preset': 'script', 'source': f'platform:{k}', 'title': name, 'lua': lua,
                  'notes': f"dark/aaze0088:{ref}: the message ends on the request (D-65 B1) over Yes/No buttons (D-67 change 7); Yes calls A3's dd22.weapons ('Nothing happens.'), as DD-16 (D-47)."})
    # the bridge
    E.append({'id': 'evt:log', 'preset': 'script', 'source': 'panel:log', 'title': 'Log Computer', 'lua': LOG_LUA,
              'notes': "D-62 Q54 (D-47 Q19's pattern): each click shows A3's next page (dd22.log_page_1..6) with a computer chirp, wrapping round after the sixth; the map variable log_page holds the page shown last. Page 6's hook adds autonote 4139 sheltem_log."})
    for k, name, ref in (('main_console', 'Main Console', 5), ('scan_console', 'Scanning Console', 6)):
        E.append({'id': f'evt:{k}', 'preset': 'text', 'source': f'platform:{k}', 'title': name, 'window': False,
                  'text': f"{name}. The computer seems to be malfunctioning.", 'notes': f"dark/aaze0088:{ref} (map-local)."})
    E.append({'id': 'evt:couch', 'preset': 'text', 'source': 'platform:couch', 'title': 'Command couch',
              'window': False, 'text': "Sheltem's command couch, empty. The harness hangs open.",
              'notes': "Map-local (Lines for A3)."})
    for i in (1, 2):
        E.append({'id': f'evt:cell_{i}', 'preset': 'text', 'source': f'panel:cell_{i}', 'title': 'Stasis cell',
                  'window': False, 'text': "An empty stasis cell. Its field is dark.",
                  'notes': "The brig's cells (log XL70I's), map-local (Lines for A3)."})
    # the drive room
    for i in (1, 2):
        E.append({'id': f'evt:device_{i}', 'preset': 'text', 'source': f'platform:device_{i}',
                  'title': 'Strange Alien Device', 'window': False,
                  'text': "The strange alien device seems to be dormant.",
                  'notes': "dark/aaze0088:0 (D-62 Q53: dressing, no reward)."})
    E.append({'id': 'evt:generator', 'preset': 'text', 'source': 'platform:generator', 'title': 'Stasis generator',
              'window': False, 'text': "The stasis generator that carried Sheltem through the crash. It is cold.",
              'notes': "Map-local (Lines for A3); log XLDBA."})
    E.append({'id': 'evt:drive_rack', 'preset': 'script', 'source': 'platform:rack', 'title': 'Tool rack',
              'condition': {'not': {'qbit': 'drive_find'}},
              'effects': [{'give_item': {'level': 6}}, {'lua': 'XeenQuests.hook("dd22.drive_rack")'}],
              'else_effects': [{'text': 'Nothing here.'}],
              'notes': "D-62 APPROVAL: the first search gives one random T6 item (the map) and calls A3's dd22.drive_rack (drive_find 117762, its line); afterwards 'Nothing here.' (the map's)."})
    for c in ('stores', 'brig', 'couch'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}',
                  'title': 'Chest',
                  'notes': {'stores': "The stores locker.", 'brig': "The guards' locker.", 'couch': "Sheltem's locker."}[c]})
    return E


def wiring():
    return {'format': 0, 'variables': ['log_page'], 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-22's events, written by output/studio_cal/dd22/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
