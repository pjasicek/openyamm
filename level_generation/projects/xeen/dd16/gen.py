#!/usr/bin/env python3
"""DD-16 Corak's Pod: writes the L1-L4 project folders of devdocs/xeen/briefs/dd16 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, atmosphere.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here; never hand-edit the written files (diff L4 against L4/.oymap/last first).
Written by the lane lead of A7 (thirteenth session, 2026-11-21) after DD-23's gen.py, on D-47 (act5_a7_decisions.md).

Frame: x east, y north, z up. Escape Pod 1 lies nose-up, half sunk in D6's lava: the hatch midship on the west side
(floor 0), the bow raised to the north (the couch row climbs to the bridge at 256), the stern sunk to the south (the
slope falls to the engine room at -384, breached onto the lava). Rooms stand 128 apart (the walls' thickness)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/dd16'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM7 The Lincoln (7d23, A6's family for the pods): a3b hull walls, a1b ribs, a2b/a2d/a2c panels, sfw7a deck plates on
# floors and ceilings, sfw1b trim; sfpnloff/sfpnlon consoles (dark until the main power, D-47); the ancient kit's
# xahullbn (the hatch, the breach's torn plates), xafield (the stasis field), xaenergy (the alien devices); MM8's lava
# (lavtyl) in the breach.
HULL = S('a3b', 128, 256)
RIB = S('a1b', 128, 256)
PANEL = S('a2b', 128, 256)
DECK = S('sfw7a', 128, 256)
TRIM = S('sfw1b', 128, 256)
DOOR = S('a2c', 128, 256, fit=True)
BLAST = S('a2d', 128, 256, fit=True)
CON_OFF = S('sfpnloff', 128, 64, fit=True)
BURNT = S('xahullbn', 256, 256, fit=True)
BURNT_T = S('xahullbn', 256, 256)
# D-51 (1): the field at half opacity, so Corak reads as a figure inside it (A7's capture, fourteenth session).
FIELD_OPACITY = 0.5
FIELD = S('xafield', 128, 256, translucent=FIELD_OPACITY)
ENERGY = S('xaenergy', 128, 256)
LAVA = {'texture': 'lavtyl', 'liquid': 'lava'}
COUCH = S('sfw1b', 128, 256)

themes = [
    {'id': 'theme:hull', 'wall': HULL, 'floor': DECK, 'ceiling': DECK, 'reveal': TRIM, 'door': DOOR,
     'notes': "The pod's decks: MM7 The Lincoln's grey hull (a3b), deck plates (sfw7a) underfoot and overhead, sfw1b trim in the doorways."},
    {'id': 'theme:engine', 'wall': S('a3bs', 128, 256), 'floor': DECK, 'ceiling': DECK, 'reveal': TRIM, 'door': DOOR,
     'notes': "The stern: the hull's ribs (a1b) bare."},
]


def octo(cx, cy, r):
    c = int(r * 0.41)
    return [[cx - c, cy - r], [cx + c, cy - r], [cx + r, cy - c], [cx + r, cy + c], [cx + c, cy + r], [cx - c, cy + r],
            [cx - r, cy + c], [cx - r, cy - c]]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


BOW, MID, STERN = 256, 0, -384
rooms = []
openings = []


def room(id, name, **kw):
    d = {'id': id, 'name': name}
    d.update(kw)
    rooms.append(d)
    return d


def op(id, frm, to, **kw):
    d = {'id': id, 'from': frm, 'to': to}
    d.update(kw)
    openings.append(d)


def panel(pid, offset, length, bottom, height, surface, **kw):
    d = {'id': pid, 'offset': offset, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ midship (0)
room('room:airlock', 'Hatch airlock', outline=rect(-1024, -192, -640, 192), floor=MID, ceiling=320,
     ambient=14, notes="The arrival from D6's crust: the hatch's inner face in the west wall, the inner door east.")
room('room:main_deck', 'Main deck', outline=octo(0, 0, 512), floor=MID, ceiling=448,
     platforms=[{'id': 'platform:scanner', 'at': [256, -256], 'size': [128, 64], 'rise': 112, 'surface': PANEL,
                 'top_surface': CON_OFF, 'notes': "The scanning console (aaze0087:22)."}],
     ambient=14, notes="The round main hull, 1,024 across: the hub. The couch row climbs north to the bow, the slope falls south to the stern, the gun deck opens east.")
room('room:gun_deck', 'Gun deck', outline=rect(640, -256, 1152, 256), floor=MID, ceiling=320,
     walls=[{'wall': 'e', 'panels': [panel('panel:phaser', 96, 128, 96, 64, CON_OFF),
                                     panel('panel:photon', 288, 128, 96, 64, CON_OFF)]}],
     ambient=14, notes="The phaser and photon controls on the east wall; the weapons locker; the service hatch in the floor.")
room('room:couches', 'Couch row', outline=rect(-192, 640, 192, 1920), floor=MID,
     slope={'to': BOW, 'toward': 'north'}, ceiling=352, ceiling_slope={'to': BOW + 352, 'toward': 'north'},
     platforms=[{'id': f'platform:couch_{s}{i}', 'at': [x, y], 'size': [80, 160], 'rise': 64, 'surface': COUCH,
                 'top_surface': COUCH, 'notes': "An empty acceleration couch, its harness hanging."}
                for i, y in enumerate((928, 1248, 1568), 1) for s, x in (('w', -148), ('e', 148))],
     ambient=14, notes="The midship corridor tilted up to the bow: six empty acceleration couches along its walls, the blast door at its top.")
room('room:bridge', 'The bridge', outline=rect(-640, 2048, 640, 2816), floor=BOW, ceiling=BOW + 512,
     walls=[{'wall': 'n', 'panels': [panel('panel:console', 192, 192, 96, 64, CON_OFF,
                                           notes="The main console beside the stasis field (m29.console; Corak's after m29.done).")]},
            {'wall': 'w', 'panels': [panel('panel:log1', 192, 128, 96, 64, CON_OFF),
                                     panel('panel:log2', 448, 128, 96, 64, CON_OFF)]},
            {'wall': 'e', 'panels': [panel('panel:log3', 320, 128, 96, 64, CON_OFF,
                                           notes="The third log computer: the source's entries in five pages (D-47 Q19).")]}],
     ambient=16, notes="A tilted cockpit of dark hull steel: the stasis alcove in the north wall behind its field, the main console beside it, the log computers on the side walls.")
room('room:stasis', 'Stasis alcove', outline=rect(-192, 2944, 192, 3328), floor=BOW, ceiling=BOW + 448,
     ambient=24, notes="Behind the field: where Corak hangs in stasis.")

# ------------------------------------------------------------------------------------------------ the sunk stern (-384)
room('room:stern_slope', 'Stern slope', outline=rect(-192, -1664, 192, -640), floor=MID,
     slope={'to': STERN, 'toward': 'south'}, ceiling=352, ceiling_slope={'to': STERN + 352, 'toward': 'south'},
     theme='theme:engine', ambient=14, notes="A corridor sloping down into the heat, the deck plates warm.")
BREACH = rect(256, -2560, 640, -2240)
room('room:engine_room', 'Engine room', outline=rect(-768, -2688, 768, -1792), floor=STERN, ceiling=STERN + 544,
     theme='theme:engine',
     levels=[{'id': 'level:breach', 'outline': BREACH, 'floor': STERN - 128, 'edge': BURNT_T, 'surface': LAVA,
              'notes': "The breach: the hull torn open onto D6's lava, 128 below the deck (floors: lava; behind the torn plates, off every walking line, D-47)."}],
     parapets=[{'path': [[232, -2584], [664, -2584], [664, -2216], [232, -2216], [232, -2584]], 'height': 112,
                'thickness': 16, 'surface': BURNT_T, 'notes': "Torn hull plates bent up round the breach."}],
     walls=[{'wall': 'n', 'panels': [panel('panel:power', 1088, 192, 96, 64, CON_OFF,
                                           notes="The Main Power Console (aaze0087:7).")]},
            {'wall': 's', 'panels': [panel('panel:breach', 1024, 448, 0, 448, BURNT,
                                           notes="The torn hull over the breach.")]}],
     ambient=20, notes="The breached stern: the hull torn open onto the lava in its south-east corner, the Main Power Console on the north wall, the stores locker by the west wall.")
room('room:device_bay', 'Device bay', outline=rect(-1408, -2432, -896, -2048), floor=STERN, ceiling=STERN + 320,
     theme='theme:engine',
     platforms=[{'id': 'platform:device_1', 'at': [-1280, -2368], 'size': [128, 64], 'rise': 128, 'surface': ENERGY,
                 'top_surface': ENERGY, 'notes': "A strange energy device (aaze0087:8)."},
                {'id': 'platform:device_2', 'at': [-1024, -2368], 'size': [128, 64], 'rise': 128, 'surface': ENERGY,
                 'top_surface': ENERGY, 'notes': "The second strange energy device."}],
     ambient=16, notes="A dead end with the two alien devices against its south wall.")
room('room:crawlway', 'Service crawlway', outline=rect(896, -2304, 1152, -64), floor=STERN, ceiling=MID,
     theme='theme:engine', ambient=12,
     notes="A service crawlway from the engine room north under the gun deck, to a ladder up through the gun deck's floor hatch.")

op('open:airlock_deck', 'room:airlock', 'room:main_deck', link='link:airlock_deck', width=256, height=256)
op('open:deck_couches', 'room:main_deck', 'room:couches', link='link:deck_couches', width=256, height=288)
op('open:couches_bridge', 'room:couches', 'room:bridge', link='link:couches_bridge', width=256, height=288)
op('open:bridge_stasis', 'room:bridge', 'room:stasis', link='link:bridge_stasis', width=256, height=320)
op('open:deck_gun', 'room:main_deck', 'room:gun_deck', link='link:deck_gun', width=256, height=256)
op('open:deck_slope', 'room:main_deck', 'room:stern_slope', link='link:deck_slope', width=256, height=288)
op('open:slope_engine', 'room:stern_slope', 'room:engine_room', link='link:slope_engine', width=256, height=288)
op('open:engine_device', 'room:engine_room', 'room:device_bay', link='link:engine_device', width=256, height=256)
op('open:engine_crawl', 'room:engine_room', 'room:crawlway', link='link:engine_crawl', width=224, height=288)
op('open:gun_hatch', 'room:gun_deck', 'room:crawlway', link='link:crawl_gun', **{'in': 'floor'}, at=[1024, -144],
   size=[192, 128], notes="The service hatch in the gun deck's floor.")

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:hull', 'ambient': 14}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-16 Corak's Pod: x east, y north; the bridge (256) north, the hatch midship (0) west, the sunk stern (-384) south. Written by output/studio_cal/dd16/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:airlock': MID, 'room:main_deck': MID, 'room:gun_deck': MID, 'room:couches': MID, 'room:bridge': BOW,
          'room:stasis': BOW, 'room:stern_slope': MID, 'room:engine_room': STERN, 'room:device_bay': STERN,
          'room:crawlway': STERN}
PLAN_SPACES = [
    ('room:airlock', 'Hatch airlock', 'room', 'S', "The arrival (entrance:d6_hatch): the hatch's inner face, the inner door ahead. Quiet (D-11.3).", []),
    ('room:main_deck', 'Main deck', 'room', 'M', "The round main hull, the hub; the scanning console's X.E.E.N. readout.", [('Floating Eye', 40, 2)]),
    ('room:gun_deck', 'Gun deck', 'room', 'S', "Phaser and photon controls, both disarmed; the weapons locker (chest); the service hatch.", []),
    ('room:couches', 'Couch row', 'corridor', 'M', "The corridor tilted up to the bow; the blast door to the bridge at its top.", [('Terrible Eye', 50, 1), ('Floating Eye', 40, 1)]),
    ('room:bridge', 'The bridge', 'room', 'M', "The stasis field (m29.stasis), the main console (m29.console), three log computers; Corak after m29.done.", []),
    ('room:stasis', 'Stasis alcove', 'room', 'S', "Behind the field: Corak in stasis.", []),
    ('room:stern_slope', 'Stern slope', 'corridor', 'S', "A corridor sloping down into the heat.", [('Terrible Eye', 50, 1)]),
    ('room:engine_room', 'Engine room', 'room', 'M', "The breach onto the lava; the Main Power Console opens the bridge; the stores locker (chest).", [('Lesser Elemental', 55, 2)]),
    ('room:device_bay', 'Device bay', 'room', 'S', "The two strange energy devices (m29.alien_device, once per character).", []),
    ('room:crawlway', 'Service crawlway', 'corridor', 'S', "From the engine room up a ladder to the gun deck's floor hatch: the loop.", []),
]


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if pop:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [lv, lv],
                                'notes': f"{n} {row} {lv} (placed)."} for row, lv, n in pop]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:airlock_deck', 'from': 'room:airlock', 'to': 'room:main_deck', 'kind': 'door'},
        {'id': 'link:deck_couches', 'from': 'room:main_deck', 'to': 'room:couches', 'kind': 'ramp'},
        {'id': 'link:couches_bridge', 'from': 'room:couches', 'to': 'room:bridge', 'kind': 'door',
         'notes': "The blast door: opened by the Main Power Console (power_on 118080)."},
        {'id': 'link:bridge_stasis', 'from': 'room:bridge', 'to': 'room:stasis', 'kind': 'door',
         'notes': "The stasis field: down with m29.done."},
        {'id': 'link:deck_gun', 'from': 'room:main_deck', 'to': 'room:gun_deck', 'kind': 'door'},
        {'id': 'link:deck_slope', 'from': 'room:main_deck', 'to': 'room:stern_slope', 'kind': 'ramp'},
        {'id': 'link:slope_engine', 'from': 'room:stern_slope', 'to': 'room:engine_room', 'kind': 'door'},
        {'id': 'link:engine_device', 'from': 'room:engine_room', 'to': 'room:device_bay', 'kind': 'door'},
        {'id': 'link:engine_crawl', 'from': 'room:engine_room', 'to': 'room:crawlway', 'kind': 'open'},
        {'id': 'link:crawl_gun', 'from': 'room:crawlway', 'to': 'room:gun_deck', 'kind': 'ladder',
         'notes': "A ladder up through the gun deck's floor hatch."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Escape Pod 1, a starship's lifeboat, lies nose-up and half sunk in the lava of the Forbidden Zone. Inside, red emergency lamps, decks that slope, and the heat of the lava through the breached stern. The Main Power Console in the engine room wakes the pod and unseals the bridge, where a figure hangs in a stasis field that answers only an Ancient phrase.",
        'purpose': "M29 (the logs, the console, the stasis field: 'where no man has gone before' wakes Corak) and M32 (Corak takes the Soul Box). Party 45 to 47, 7 monsters 40-55 (D-47 Q17), treasure 5.",
        'mood': "Dead machinery coming back to life: red lamps, then white; the hum of the field; lava ticking against the hull.",
        'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:crawl', 'spaces': ['room:main_deck', 'room:stern_slope', 'room:engine_room',
                                                 'room:crawlway', 'room:gun_deck'],
                   'notes': "Down the slope to the engines, up the service crawlway's ladder to the gun deck and back to the main deck (the ladder is one way up for monsters: they do not climb)."}],
        'entrances': [{'id': 'entrance:d6_hatch', 'space': 'room:airlock', 'kind': 'both',
                       'facing': 'e', 'how': "From D6's crust through the hatch (A6's m29.pod_door): 192 inside the hatch, facing east into the pod."}],
        'critical_path': ['room:airlock', 'room:main_deck', 'room:stern_slope', 'room:engine_room',
                          'room:stern_slope', 'room:main_deck', 'room:couches', 'room:bridge'],
        'return_path': ['room:bridge', 'room:couches', 'room:main_deck', 'room:airlock'],
        'goals': [
            {'id': 'goal:power', 'space': 'room:engine_room', 'kind': 'use', 'story': 'M29',
             'what': "The Main Power Console: lights up, consoles on, the blast door unseals (power_on 118080, m29.power_console)."},
            {'id': 'goal:stasis', 'space': 'room:bridge', 'kind': 'use', 'story': 'M29',
             'what': "The stasis field's prompt 'To boldly go...': 'where no man has gone before' (m29.stasis, m29.done 111582).",
             'gives': {'qbit': 'stasis_done'}},
        ],
        'set_pieces': [
            {'id': 'set:bridge', 'kind': 'scripted', 'spaces': ['room:bridge', 'room:stasis'],
             'rule': "The field (xafield, translucent) stands across the stasis alcove with Corak inside until m29.done, then is down on every load; Corak by his console until m32.done, then gone."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 10, 'sectors': 10, 'monsters_about': 7, 'chests': 2, 'doors': 6, 'loops': 1,
                   'floor_area_munits2': 6},
        'notes': "Size S (at most 15 sectors and 20 M units², 15-30 monsters: D-47 Q17's 7, one NOTES exception line). From act5_graphs/dd16.graph.yml and D-47 (act5_a7_decisions.md, DD-16); the stasis alcove is its own room.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-16 Corak's Pod (not to scale; plan, north up; the pod lies nose-up)
  floor 256                 [STASIS ALCOVE: Corak]
                                  | field (m29.done)
                     [THE BRIDGE: console, 3 logs]
                                  | blast door (power)
                     [COUCH ROW: ramp up 256]
  floor 0  [AIRLOCK]--door--[MAIN DECK: scanner]--door--[GUN DECK: phaser, photon, locker]
          (hatch to D6)          |                          | floor hatch, ladder
                     [STERN SLOPE: ramp down 384]            |
  floor -384 [DEVICE BAY]--door--[ENGINE ROOM: power, breach, locker]--[SERVICE CRAWLWAY]
"""

# ================================================================================================ objects
ARRIVAL = [-832, 0]
objects = {'format': 0}
objects['start'] = {'room': 'room:airlock', 'at': ARRIVAL, 'facing': 'e',
                    'notes': "entrance:d6_hatch: 192 inside the hatch, facing east toward the inner door."}
objects['arrivals'] = [{'entrance': 'entrance:d6_hatch', 'room': 'room:airlock', 'at': ARRIVAL, 'facing': 'e',
                        'notes': "192 inside the hatch, facing east into the pod (D6's hatch, A6)."}]


def light(id, rm, at, h, r, col, **kw):
    floor = FLOORS[rm]
    d = {'id': id, 'room': rm, 'at': at, 'height': h - floor, 'radius': r, 'color': col}
    d.update(kw)
    return d


RED = [150, 40, 30]       # emergency lamps (on at load)
WHITE = [170, 190, 180]   # the pod's lights once the main power is on (D-47)
LAVA_GLOW = [220, 110, 40]
FIELD_GLOW = [150, 200, 230]
POWERED = []


def lamp_pair(name, rm, at, h, r):
    """A red emergency lamp lit at load and a white one lit by the main power, at one ceiling point."""
    POWERED.append(f'light:{name}')
    return [light(f'light:{name}_red', rm, at, h, int(r * 0.7), RED, brightness=10),
            light(f'light:{name}', rm, at, h, r, WHITE, on=False)]


objects['lights'] = (
    lamp_pair('airlock', 'room:airlock', [-832, 0], 300, 700)
    + lamp_pair('deck', 'room:main_deck', [0, 0], 428, 1200)
    + lamp_pair('gun', 'room:gun_deck', [896, 0], 300, 800)
    + lamp_pair('couches_s', 'room:couches', [0, 960], 300, 800)
    + lamp_pair('couches_n', 'room:couches', [0, 1600], 300, 800)
    + lamp_pair('slope', 'room:stern_slope', [0, -1152], 300, 800)
    + lamp_pair('engine', 'room:engine_room', [-256, -2240], STERN + 520, 1200)
    + lamp_pair('device', 'room:device_bay', [-1152, -2240], STERN + 300, 700)
    + lamp_pair('crawl_s', 'room:crawlway', [1024, -1728], -20, 700)
    + lamp_pair('crawl_n', 'room:crawlway', [1024, -640], -20, 700)
    + lamp_pair('bridge', 'room:bridge', [0, 2432], BOW + 492, 1300)
    + [light('light:breach', 'room:engine_room', [448, -2400], STERN + 40, 900, LAVA_GLOW, brightness=24,
             pulse={'intensity': [0.6, 1.0], 'frequency': 0.4},
             notes="The lava's glow through the breach."),
       light('light:field', 'room:stasis', [0, 3136], BOW + 220, 800, FIELD_GLOW, brightness=26,
             pulse={'intensity': [0.5, 1.0], 'frequency': 0.7},
             notes="The stasis field's pale light (off once Corak is woken)."),
       light('light:blast_red', 'room:couches', [0, 1856], 270, 280, [220, 30, 20], brightness=20,
             notes="The blast door's lamp: red while the power is off (D-47)."),
       light('light:blast_green', 'room:couches', [0, 1856], 270, 280, [40, 220, 60], brightness=20, on=False,
             notes="The blast door's lamp: green once the power is on.")])
objects['exits'] = [
    {'id': 'exit:hatch', 'room': 'room:airlock', 'wall': 'w', 'size': [256, 256], 'surface': S('7solid01', 256, 256, fit=True),
     'to': 'exit:d6_hatch', 'notes': "The hatch's inner face, burnt plates: out onto D6's crust."},
]
objects['sounds'] = [
    {'id': 'sound:stasis', 'room': 'room:stasis', 'at': [0, 3136], 'sound': 'humming', 'radius': 1500,
     'inner_radius': 400, 'volume': 0.5, 'notes': "The stasis field's hum (AU session 3), off when Corak is woken."},
    {'id': 'sound:lava', 'room': 'room:engine_room', 'at': [448, -2400], 'sound': 'lava loop', 'radius': 1600,
     'inner_radius': 500, 'volume': 0.5, 'notes': "Lava against the hull at the breach."},
]
objects['doors'] = [
    {'id': 'door:inner', 'opening': 'open:airlock_deck', 'kind': 'slide_left', 'fold': True, 'thickness': 16,
     'speed': 256, 'surface': DOOR, 'tile': True, 'notes': "The airlock's inner door."},
    {'id': 'door:blast', 'opening': 'open:couches_bridge', 'kind': 'slide_up', 'fold': True, 'thickness': 24,
     'speed': 192, 'surface': BLAST, 'tile': True, 'notes': "The bridge's blast door: sealed until the main power is on (power_on 118080)."},
    {'id': 'door:field', 'opening': 'open:bridge_stasis', 'kind': 'slide_down', 'fold': True, 'thickness': 8,
     'speed': 160, 'surface': FIELD, 'tile': True,
     'notes': "The stasis field across the alcove (xafield, translucent): down with m29.done."},
    {'id': 'door:gun', 'opening': 'open:deck_gun', 'kind': 'slide_left', 'fold': True, 'thickness': 16,
     'speed': 256, 'surface': DOOR, 'tile': True, 'notes': "The gun deck's door."},
    {'id': 'door:engine', 'opening': 'open:slope_engine', 'kind': 'slide_left', 'fold': True, 'thickness': 16,
     'speed': 256, 'surface': DOOR, 'tile': True, 'notes': "The engine room's door at the slope's foot."},
    {'id': 'door:device', 'opening': 'open:engine_device', 'kind': 'slide_left', 'fold': True, 'thickness': 16,
     'speed': 256, 'surface': DOOR, 'tile': True, 'notes': "The device bay's door."},
]
objects['ladders'] = [
    {'id': 'ladder:hatch', 'room': 'room:crawlway', 'at': [1024, -90], 'facing': 'n', 'height': 384,
     'exit': [1024, 16], 'surface': S('trim11_32', 32, 64, uneven=True), 'notes': "The crawlway's ladder up through the gun deck's floor hatch."},
]
objects['floors'] = [{'id': 'floor:breach', 'of': 'level:breach', 'kind': 'lava',
                      'notes': "The breach's lava burns (D-47: off every walking line, behind the torn plates)."}]
objects['chests'] = [
    {'id': 'chest:locker', 'room': 'room:gun_deck', 'at': [1056, 192], 'treasure_level': 5,
     'random_items': 3, 'gold': 2500, 'notes': "The weapons locker (nothing in it fires)."},
    {'id': 'chest:stores', 'room': 'room:engine_room', 'at': [-688, -2560], 'treasure_level': 5,
     'random_items': 3, 'gold': 3000, 'notes': "The engine room's stores locker."},
]
FE, TE, LE, CORAK = 11570, 11571, 11620, 11912
objects['monsters'] = []


def mon(id, rm, kind, at, group, facing=270, **kw):
    d = {'id': id, 'room': rm, 'monster': kind, 'at': at, 'facing': facing, 'hostile': True, 'group': group}
    d.update(kw)
    objects['monsters'].append(d)


mon('monster:deck_1', 'room:main_deck', FE, [-200, 250], 10, facing=180)
mon('monster:deck_2', 'room:main_deck', FE, [220, 220], 10, facing=180)
mon('monster:couches_te', 'room:couches', TE, [0, 1500], 11)
mon('monster:couches_fe', 'room:couches', FE, [0, 1100], 11)
mon('monster:slope_te', 'room:stern_slope', TE, [0, -1300], 12, facing=90)
mon('monster:engine_1', 'room:engine_room', LE, [200, -2100], 13, facing=90,
    notes="A fire elemental risen out of the lava through the breach.")
mon('monster:engine_2', 'room:engine_room', LE, [-160, -2400], 13, facing=90)
objects['monsters'].append({'id': 'monster:corak', 'room': 'room:stasis', 'monster': CORAK, 'at': [0, 3200],
                            'facing': 270, 'hostile': False, 'immobile': True, 'group': 30, 'npc': 5513,
                            'notes': "Corak (11912, A2's peaceful placed-only row; S's look to come): in the field until m29.done, by his console until m32.done, then hidden. Takes no damage (evt:corak_load, D-51). Talks as NPC 5513 when clicked (merge point 22's indoor npc word) once the field is down."})


objects['decorations'] = []

# ================================================================================================ wiring
QB = {'stasis_done': 111582, 'corak_boxed': 111640, 'power_on': 118080}


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


POWER_ON = ([{'lights_on': POWERED + ['light:blast_green']}, {'lights_off': 'light:blast_red'}]
            + [{'set_texture': {'of': p, 'to': 'sfpnlon'}} for p in
               ('panel:console', 'panel:log1', 'panel:log2', 'panel:log3', 'panel:phaser', 'panel:photon',
                'panel:power')]
            + [{'set_texture': {'of': 'platform:scanner', 'to': 'sfpnlon', 'face': 'top'}}])
FIRE_Q = {'answers': ['Yes', 'Y'], 'ask': 'Fire (Yes/No)?'}
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 7,
     'text': "Escape Pod 1. The deck slopes under your feet, and lava ticks against the hull. Only red emergency lamps are lit."},
    {'id': 'evt:hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Exit Escape Pod 1',
     'notes': "Out to D6 (installed, A6) at its named arrival entrance:dd16_hatch on the crust 384 before the hatch, "
              "facing south-east (1792): the game's own leave window (D-24); 'Exit Escape Pod 1?' (aaze0087:6) is its "
              "meaning."},
    {'id': 'evt:door_inner', 'preset': 'door', 'source': 'door:inner', 'title': 'Door'},
    {'id': 'evt:door_gun', 'preset': 'door', 'source': 'door:gun', 'title': 'Door'},
    {'id': 'evt:door_engine', 'preset': 'door', 'source': 'door:engine', 'title': 'Door'},
    {'id': 'evt:door_device', 'preset': 'door', 'source': 'door:device', 'title': 'Door'},
    {'id': 'evt:blast', 'preset': 'door', 'source': 'door:blast', 'title': 'Blast door', 'action': 'open',
     'condition': {'qbit': 'power_on'}, 'else_effects': [hook('m29.blast_door')],
     'notes': "Sealed until the main power is on: A3's m29.blast_door names the missing power (D-47)."},
    {'id': 'evt:scanner', 'preset': 'text', 'source': 'platform:scanner', 'title': 'Scanning Console',
     'text': "Scanning Console. A message on the screen reads: X.E.E.N. (Xylonite Experimental Expansion Nacelle) Starseed Project. Mean orbit: 1.1 AU. Surface gravity: .88. Mean surface temperature: 72.",
     'notes': "dark/aaze0087:22 (map-local)."},
    {'id': 'evt:phaser', 'preset': 'script', 'source': 'panel:phaser', 'title': 'Phaser Control',
     'question': dict(FIRE_Q, message="Phaser Control. A status indicator on the weapon shows it to be disarmed. Fire anyway?"),
     'effects': [{'text': "Nothing happens."}], 'notes': "dark/aaze0087:11, :9 (map-local)."},
    {'id': 'evt:photon', 'preset': 'script', 'source': 'panel:photon', 'title': 'Photon Control',
     'question': dict(FIRE_Q, message="Photon Control. A status indicator on the weapon shows it to be disarmed. Fire anyway?"),
     'effects': [{'text': "Nothing happens."}], 'notes': "dark/aaze0087:12, :9 (map-local)."},
    {'id': 'evt:power', 'preset': 'script', 'source': 'panel:power', 'title': 'Main Power Console',
     'condition': {'not': {'qbit': 'power_on'}},
     'question': {'message': "Main Power Console. Activate?", 'ask': 'Activate (Yes/No)?', 'answers': ['Yes', 'Y']},
     'opens': ['door:blast'],
     'effects': [{'qbit': 'power_on'}, hook('m29.power_console'),
                 {'lua': 'evt.PlaySoundName("xeen_power_up", -416, -1800, -288)'}] + POWER_ON,
     'else_effects': [{'text': "The main power is on."}],
     'notes': "goal:power (dark/aaze0087:7, the typo mended): power_on 118080; the pod's lights come up, the consoles light (sfpnloff -> sfpnlon), the blast door's lamp turns green and the door unseals (D-47); AU's xeen_power_up at the panel."},
    {'id': 'evt:power_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'power_on'},
     'opens': ['door:blast'], 'effects': list(POWER_ON),
     'notes': "Every later load with the power on: lit, consoles on, the blast door open."},
    {'id': 'evt:field', 'preset': 'script', 'source': 'door:field', 'title': 'Stasis field',
     'condition': {'not': {'qbit': 'stasis_done'}}, 'locked_text': "The stasis field is down.",
     'question': {'message': "A strange energy field surrounds a figure suspended within it.",
                  'ask': 'To boldly go...', 'answers': ['where no man has gone before', 'where no man has gone before.',
                                                        'where no man has gone before!'],
                  'wrong_effects': [hook('m29.stasis_wrong')]},
     'opens': ['door:field'],
     'effects': [hook('m29.stasis'), {'lights_off': 'light:field'},
                 {'lua': 'STASIS_HUM_OFF'}],
     'notes': "goal:stasis: the field's prompt (dark/aaze0087:0); the right answer calls A3's m29.stasis (stasis_off 111581, done 111582) and drops the field; any other A3's m29.stasis_wrong."},
    {'id': 'evt:stage_awake', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'stasis_done'},
     'opens': ['door:field'], 'effects': [{'lights_off': 'light:field'}, {'lua': 'STASIS_HUM_OFF'}],
     'notes': "From m29.done on every load: the field down, its light and hum off; Corak by his console."},
    {'id': 'evt:corak_load', 'preset': 'script', 'trigger': 'load',
     'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:corak"), false)',
     'notes': "D-51 (1): Corak cannot be killed: every hit on him is zeroed, on every load (ActorIndex, merge point 22)."},
    {'id': 'evt:stage_boxed', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'corak_boxed'},
     'effects': [{'hide_actors': 30}], 'notes': "From m32.done on every load: Corak gone (he is in the Soul Box)."},
    {'id': 'evt:boxed_now', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'qbit': 'corak_boxed'}, 'effects': [{'hide_actors': 30}],
     'notes': "The visit in which Corak goes into the box: he vanishes from the alcove."},
    {'id': 'evt:console', 'preset': 'script', 'source': 'panel:console', 'title': 'Console',
     'lua': ('if IsQBitSet(QBit(111640)) then\n'
             '    evt.SimpleMessage("Stasis field deactivated.")\n'
             'elseif IsQBitSet(QBit(111582)) then\n'
             '    evt.SimpleMessage("Stasis field deactivated.")\n'
             'else\n'
             '    XeenQuests.hook("m29.console")\n'
             'end'),
     'notes': "Before m29.done A3's m29.console (the phrase in plain words); from m29.done 'Stasis field deactivated.' (dark/aaze0087:24, map-local): Corak talks from his own body now (monster npc 5513, merge point 22)."},
    {'id': 'evt:log1', 'preset': 'script', 'source': 'panel:log1', 'title': 'Log Computer', 'effects': [hook('m29.log1')]},
    {'id': 'evt:log2', 'preset': 'script', 'source': 'panel:log2', 'title': 'Log Computer', 'effects': [hook('m29.log2')]},
    {'id': 'evt:log3', 'preset': 'script', 'source': 'panel:log3', 'title': 'Log Computer', 'lua': 'LOG3_LUA',
     'notes': "D-47 Q19: each click shows A3's next page (m29.log_page_1..5), wrapping round; the map variable log_page holds the page shown last."},
    {'id': 'evt:device_1', 'preset': 'script', 'source': 'platform:device_1', 'title': 'Strange energy device',
     'effects': [hook('m29.alien_device')], 'notes': "D-47 Q18: A3's hook decides for the clicking member (player bit 11352)."},
    {'id': 'evt:device_2', 'preset': 'script', 'source': 'platform:device_2', 'title': 'Strange energy device',
     'effects': [hook('m29.alien_device')]},
    {'id': 'evt:chest_locker', 'preset': 'chest', 'source': 'chest:locker', 'title': 'Chest'},
    {'id': 'evt:chest_stores', 'preset': 'chest', 'source': 'chest:stores', 'title': 'Chest'},
    {'id': 'evt:engine_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:engine_room', 'once': True,
     'seconds': 6, 'text': "The stern is torn open. Lava glows through the gap, a hand's breadth below the deck."},
    {'id': 'evt:bridge_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:bridge', 'once': True,
     'seconds': 6, 'text': "The bridge. Behind a curtain of pale light, a tall figure hangs in the air, quite still."},
]
LOCK = BRIEF / 'L4/ids.lock.yml'
_mv = (yaml.safe_load(LOCK.read_text()) or {}).get('map_vars', {}) if LOCK.exists() else {}
_n = _mv.get('log_page', 0)
LOG3_LUA = ('local page = 1\n'
            'for n = 1, 4 do\n'
            '    if IsAtLeast(MapVar(log_page), n) then page = n + 1 end\n'
            'end\n'
            + ''.join(f'{"if" if n == 1 else "elseif"} page == {n} then\n    XeenQuests.hook("m29.log_page_{n}")\n'
                      for n in range(1, 6)) + 'end\n'
            'SetValue(MapVar(log_page), page % 5)')
_snd = (yaml.safe_load(LOCK.read_text()) or {}).get('sounds', {}) if LOCK.exists() else {}
HUM_OFF = f"evt.SetMapVar('AmbientSound{_snd.get('sound:stasis', 1)}', 2)"
for e in events:
    if e.get('lua') == 'LOG3_LUA':
        e['lua'] = LOG3_LUA
    for f in e.get('effects', []):
        if f.get('lua') == 'STASIS_HUM_OFF':
            f['lua'] = HUM_OFF
wiring = {'format': 0, 'variables': ['log_page'], 'events': events}

atmosphere = {'format': 0, 'notes': "No open sky: the pod is closed (the breach looks onto lava, not sky)."}

project = {
    'format': 0, 'id': 'xeen_dd16', 'name': "Corak's Pod", 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'DD-16', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [6, 12], 'climbs': 'n'},
    'map_stats': {'id': 9169, 'encounter_chance': 10, 'treasure_level': 5, 'trap_dice': 4,
                  'perception_difficulty': 8, 'refill_days': 672, 'music': 46, 'environment': 'stoneroom',
                  'lock_difficulty': 8, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Eye', 'tier': 0, 'per_marker': [1, 1], 'weight': 100}]},
    'neighbours': [{
        'id': 'exit:d6_hatch', 'to': 'xeen_d6.odm', 'kind': 'door', 'arrival': 'entrance:dd16_hatch',
        'arrival_hint': "On D6's cooled crust 384 before the pod's hatch, facing south-east (A6's entrance:dd16_hatch).",
        'notes': "D6 installed (A6). The way out names D6's named arrival entrance:dd16_hatch, now on the crust at "
                 "(5120, -2560, 1466) facing 1792 (merge point 25 stands an outdoor arrival on a structure's top); "
                 "the facing comes with it. D6's door:dd16 (thing:corak_pod, A3's m29.pod_door after lava_cooled) names this "
                 "map's arrival entrance:d6_hatch: (-832, 0, 0) facing east."}],
    'qbits': QB,
    'notes': "Xeen design brief, level L4: DD-16 Corak's Pod, Escape Pod 1 in D6's lava (M29, M32). D-47: 7 monsters (Floating Eye 11570 x 3, Terrible Eye 11571 x 2, Lesser Elemental 11620 x 2; 4.79k), the peaceful placed-only Corak 11912; rest encounters eyes at Dif 0 (Floating Eye 40 only, 10 %). Hooks m29.* (A3), Corak's topics npc 5513 (m32) on his own body (merge point 22). Map qbit power_on 118080. Music 46. The hatch leads to D6's entrance:dd16_hatch (A6); D6's door arrives at entrance:d6_hatch.",
}


def write(folder, docs):
    folder.mkdir(parents=True, exist_ok=True)
    for name, doc in docs:
        if isinstance(doc, str):
            (folder / name).write_text(doc)
        else:
            (folder / name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))


if '--levels' in sys.argv:
    p = dict(project)
    for lv in ('L1', 'L2'):
        p['notes'] = f"Xeen design brief, level {lv}: DD-16 Corak's Pod (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-16 Corak's Pod, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('atmosphere.yml', atmosphere),
                     ('diagram.txt', DIAGRAM)])
print('written L4')
