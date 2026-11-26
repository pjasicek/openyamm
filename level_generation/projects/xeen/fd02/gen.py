#!/usr/bin/env python3
"""FD-02 Southern Sphinx: writes the L1-L4 project folders of devdocs/xeen/briefs/fd02 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here; never hand-edit the written files (diff L4 against L4/.oymap/last first).
Written by lane A7's sub-agent for FD-02 (seventeenth session, 2026-11-21) after DD-24's gen.py, on D-57
(devdocs/xeen/mockups/act6_a7_decisions.md), which wins over act6_graphs/fd02.graph.yml.

Frame: x east, y north, z up. The half-buried sphinx faces east on X6's west rim: the two leaves in its breast (east
wall of the breast steps, z 0) open on eight steps down west into the body (z -256): the hall of embalming, the two death
runs west of it, the two Preservation Rooms and the canopic chamber at the far west end. The stair of the name climbs
north from the hall's east end to the head (z 768): the landing, the door of the name, the Home of the Aged (its east
wall the face, two eyes) and the two lappet galleries. Under the sand (z -1,280) the crypt of the dragons, entered from
the canopic chamber under a 288-high arch onto a gallery and down a flight, and the stalls west of it. Rooms stand 128
apart (the walls' thickness)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/fd02'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Tomb of VARN (pyramid.blv), the set's other half (D-57 Q11): no striped columns (egycol64), no egywle/egywlc
# (XD-15's marks). Two new textures (Codex, output/studio_cal/fd02/tex): xsshelf (Picard's shelves), xsrunes (the rune
# stones and the two rune plaques).
WALLJ = S('egywlj', 256, 256)
FOOT = S('egywla', 256, 256)
BRICK = S('egywalg1', 256, 256)
PLAIN = S('egywalgm', 128, 128)
PANEL = S('egywlh', 256, 256)
GLYPHS = S('egywld', 256, 256)
FLOOR = S('egyflorf', 256, 256)
SAND = S('egyflord', 256, 256)
CEIL = S('egyceild', 128, 128)
STARS = S('egyceila', 128, 128)
DOOR = S('egydrsmd', 128, 256, fit=True)
TRIM = S('egytrmas', 32, 32)
GLYPHTILE = S('egytrmc', 64, 64)
MASK = S('egywlspb', 256, 256, fit=True)
EYE = S('egyswbon', 32, 32, fit=True)
SHELF = S('xsshelf', 256, 256)
RUNES = S('xsrunes', 128, 256, fit=True)
COINS = S('xncoins', 128, 128)
LEAF_L = S('egydrlgl', 256, 256, fit=True)
LEAF_R = S('egydrlgr', 256, 256, fit=True)

themes = [
    {'id': 'theme:body', 'wall': WALLJ, 'bands': [{'height': 64, 'surface': FOOT}], 'floor': FLOOR, 'ceiling': CEIL,
     'reveal': BRICK, 'door': DOOR,
     'notes': "The body: the Tomb of VARN's fine golden blocks (egywlj) over a footing of rough blocks (egywla), pale sand flags (egyflorf), framed ceilings (egyceild)."},
    {'id': 'theme:run', 'wall': BRICK, 'bands': [{'height': 64, 'surface': FOOT}], 'floor': SAND, 'ceiling': CEIL,
     'reveal': BRICK, 'door': DOOR,
     'notes': "The two death runs: plain brick (egywalg1), drifted sand underfoot (egyflord)."},
    {'id': 'theme:pres', 'wall': PANEL, 'bands': [{'height': 64, 'surface': FOOT}], 'floor': FLOOR, 'ceiling': CEIL,
     'reveal': BRICK, 'door': DOOR,
     'notes': "The Preservation Rooms and the canopic chamber: plaster panels framed in hieroglyph borders (egywlh)."},
    {'id': 'theme:head', 'wall': PLAIN, 'bands': [{'height': 64, 'surface': FOOT}], 'floor': FLOOR, 'ceiling': STARS,
     'reveal': BRICK, 'door': DOOR,
     'notes': "The head: smooth sandstone (egywalgm), the inlaid star ceiling (egyceila)."},
    {'id': 'theme:crypt', 'wall': GLYPHS, 'bands': [{'height': 64, 'surface': FOOT}], 'floor': SAND, 'ceiling': BRICK,
     'reveal': BRICK, 'door': DOOR,
     'notes': "The crypt under the sand: carved hieroglyph walls (egywld), drifted sand, a brick vault."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


BODY = -256     # the body's halls
HEAD = 768      # the head
CRYPT = -1280   # under the sand
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
    d = {'offset': offset, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    if pid:
        d['id'] = pid
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ floor 0 (the body)
room('room:breast', 'Breast steps', outline=rect(-896, -320, 0, 320), floor=BODY, ceiling=448, theme='theme:body',
     levels=[{'id': 'level:breast_top', 'outline': rect(-320, -320, 0, 320), 'floor': 0, 'surface': SAND,
              'notes': "The top step inside the leaves: sand blown in under the doors."}],
     flights=[{'from': [-800, 0], 'to': [-320, 0], 'width': 512, 'steps': 8, 'tread': FLOOR, 'riser': FOOT,
               'notes': "Eight broad steps down into the body."}],
     ambient=16, notes="The arrival (entrance:x6_door) on the top step inside the two leaves; eight broad steps down west into the body.")
room('room:hall', 'Hall of embalming', outline=rect(-3200, -448, -1024, 448), floor=BODY, ceiling=384,
     theme='theme:body',
     platforms=[
         {'id': 'platform:table_n', 'at': [-2112, 352], 'size': [512, 128], 'rise': 96, 'surface': GLYPHTILE,
          'top_surface': PLAIN, 'notes': "An embalming table by the north wall."},
         {'id': 'platform:table_s', 'at': [-2112, -352], 'size': [512, 128], 'rise': 96, 'surface': GLYPHTILE,
          'top_surface': PLAIN, 'notes': "The embalmer's table by the south wall: the two flasks (118119)."},
     ],
     ambient=14, notes="The body's long hall, 2,176 by 896 and 640 high: embalming tables by the walls, jars on them; the hub. West the two death runs, east the breast steps, the stair of the name north from its east end.")
room('room:swinging', 'The Swinging Death', outline=rect(-4608, 64, -3328, 448), floor=BODY, ceiling=256,
     theme='theme:run',
     walls=[{'wall': 'n', 'panels': [panel('panel:mask_swing', 64, 256, 64, 256, MASK,
                                           notes="The toll-keeper's carved figures (egywlspb): the mask that sells protection.")]}],
     ambient=12, notes="A run 1,280 by 384 west from the hall: four blades sweep out of slots in its north wall over the walk (the tell, in plain sight); a plate under each. The toll-keeper at its mouth.")
room('room:chopping', 'The Chopping Death', outline=rect(-4608, -448, -3328, -64), floor=BODY, ceiling=256,
     theme='theme:run',
     walls=[{'wall': 's', 'panels': [panel('panel:mask_chop', 64, 256, 64, 256, MASK, from_='end',
                                           notes="The toll-keeper's carved figures (egywlspb).")]}],
     ambient=12, notes="The southern run, the same length: three blades drop from slots in the ceiling; a plate under each; its own toll-keeper.")

STELA = {'size': [96, 32], 'rise': 192, 'surface': RUNES, 'end_surface': dict(PLAIN, fit=False), 'top_surface': PLAIN}
room('room:pres_n', 'Preservation Room (north)', outline=rect(-5376, 64, -4736, 704), floor=BODY, ceiling=320,
     theme='theme:pres',
     platforms=[dict(STELA, id=f'platform:rune_{c}', at=[x, 656], notes=f"A rune stone: the lesson of the letter {c.upper()}.")
                for c, x in (('p', -5216), ('i', -5056), ('c', -4896))],
     ambient=14, notes="Three rune stones by the north wall (P, I, C); the great sarcophagus by the south wall (Might 60).")
room('room:pres_s', 'Preservation Room (south)', outline=rect(-5376, -704, -4736, -64), floor=BODY, ceiling=320,
     theme='theme:pres',
     platforms=[dict(STELA, id=f'platform:rune_{c}', at=[x, -656], notes=f"A rune stone: the lesson of the letter {c.upper()}.")
                for c, x in (('a', -4896), ('r', -5056), ('d', -5216))],
     ambient=14, notes="Three rune stones by the south wall (A, R, D, read east to west on the way round); the second great sarcophagus.")
room('room:canopic', 'Canopic chamber', outline=rect(-6144, -576, -5504, 576), floor=BODY, ceiling=320,
     theme='theme:pres',
     platforms=[
         {'at': [-5824, 528], 'size': [448, 64], 'rise': 128, 'surface': GLYPHTILE, 'top_surface': PLAIN,
          'notes': "A shelf of sealed jars."},
         {'at': [-5824, -528], 'size': [448, 64], 'rise': 128, 'surface': GLYPHTILE, 'top_surface': PLAIN,
          'notes': "A shelf of sealed jars."},
     ],
     walls=[{'wall': 'w', 'panels': [panel('panel:plaque_dragons', 272, 128, 64, 192, RUNES,
                                           notes="A rune plaque by the crypt arch: 'Don't feed the dragons.'")]}],
     ambient=12, notes="Where the two Preservation Rooms meet: shelves of sealed jars; the crypt's low arch (288) in its west wall.")
# ------------------------------------------------------------------------------------------------ the stair of the name
room('room:name_stair', 'Stair of the name', outline=rect(-1536, 576, -1152, 2560), floor=BODY, ceiling=448,
     ceiling_slope={'to': HEAD + 512, 'toward': 'north'}, theme='theme:body',
     levels=[{'id': 'level:landing', 'outline': rect(-1536, 2048, -1152, 2560), 'floor': HEAD, 'surface': FLOOR,
              'notes': "The top landing: the voice asks the name here (every climb until named)."}],
     flights=[{'from': [-1344, 640], 'to': [-1344, 2048], 'width': 352, 'steps': 32, 'tread': FLOOR, 'riser': FOOT,
               'notes': "32 steps of 32 up into the head."}],
     walls=[{'wall': 'w', 'panels': [panel('panel:plaque_name', 64, 128, 64, 192, RUNES, from_='end',
                                           notes="A rune plaque at the stair's foot: 'Study the lessons to learn my name.'")]},
            {'wall': 'n', 'panels': [panel(None, 0, 384, 1360, 160, S('egymedb', 256, 256),
                                           notes="Fine brick over the door of the name's lintel.")]}],
     ambient=14, notes="From the hall's north-east corner a straight flight of 32 steps of 32, 352 wide, climbs 1,024 north into the head; on the top landing the door of the name.")
# ------------------------------------------------------------------------------------------------ the head (z 768)
room('room:home', 'Home of the Aged', outline=rect(-1792, 2688, -512, 3712), floor=HEAD, ceiling=HEAD + 640,
     theme='theme:head',
     bands=[{'height': 64, 'surface': FOOT}, {'height': 320, 'surface': SHELF}, {'height': 640, 'surface': PANEL}],
     walls=[{'wall': 'e',
             'panels': [panel('panel:eye_n', 656, 96, 400, 96, EYE, notes="The sphinx's north eye: daylight."),
                        panel('panel:eye_s', 272, 96, 400, 96, EYE, notes="The south eye.")]}],
     ambient=18, notes="Set piece: 1,280 by 1,024 under the carved face, shelves round the walls (xsshelf), two bars of light through the eyes in the east wall, four books on lecterns by the walls; at the far (west) end Picard the Aged by his very good chair.")
room('room:gallery_n', 'North sarcophagus gallery', outline=rect(-1536, 3840, -768, 4352), floor=HEAD,
     ceiling=HEAD + 512, theme='theme:pres',
     platforms=[{'at': [x, 4256], 'size': [192, 96], 'rise': 96, 'surface': GLYPHTILE, 'top_surface': PLAIN,
                 'notes': "An open sarcophagus, its lid gone."} for x in (-1344, -1088)]
     + [{'id': 'platform:find_n', 'at': [-864, 4288], 'size': [96, 64], 'rise': 64, 'surface': PLAIN,
         'top_surface': PLAIN, 'notes': "The third, empty niche's ledge: a fixed find."}],
     ambient=12, notes="A dead end in the nemes' north lappet: two empty sarcophagi, the Phase Mummies out of them; a find on the third niche's ledge.")
room('room:gallery_s', 'South sarcophagus gallery', outline=rect(-1024, 2048, -512, 2560), floor=HEAD,
     ceiling=HEAD + 512, theme='theme:pres',
     platforms=[{'at': [-576, y], 'size': [96, 192], 'rise': 96, 'surface': GLYPHTILE, 'top_surface': PLAIN,
                 'notes': "An open sarcophagus, its lid gone."} for y in (2176, 2432)]
     + [{'id': 'platform:find_s', 'at': [-960, 2112], 'size': [64, 64], 'rise': 64, 'surface': PLAIN,
         'top_surface': PLAIN, 'notes': "The empty niche's ledge: a fixed find."}],
     ambient=12, notes="The south lappet, the same: two Phase Mummies and a find.")
# ------------------------------------------------------------------------------------------------ under the sand
CRYPT_TOP = -256
room('room:crypt', 'Crypt of the dragons', outline=rect(-8448, -768, -6272, 768), floor=CRYPT, ceiling=64,
     theme='theme:crypt',
     levels=[{'id': 'level:crypt_gallery', 'outline': rect(-6656, -768, -6272, 768), 'floor': CRYPT_TOP,
              'edge': GLYPHS, 'notes': "The gallery inside the arch, level with the canopic chamber."}],
     flights=[{'from': [-7936, 0], 'to': [-6656, 0], 'width': 320, 'steps': 32, 'tread': SAND, 'riser': FOOT,
               'sides': {'height': 64, 'thickness': 16, 'surface': FOOT},
               'notes': "The crypt steps: 32 down from the gallery to the crypt floor."}],
     parapets=[{'path': [[-6640, 752], [-6640, 176]], 'height': 96, 'surface': FOOT},
               {'path': [[-6640, -176], [-6640, -752]], 'height': 96, 'surface': FOOT}],
     beams=[{'path': [[x, -752], [x, 752]], 'width': 64, 'depth': 96, 'bottom': -32, 'surface': BRICK}
            for x in (-7936, -7424, -6912)],
     ambient=10, notes="Set piece: a vault 2,176 by 1,536 and 1,344 high under brick ribs; the gallery inside the 288-high arch, the crypt steps down from it; four dragon mummies. The arch keeps them in (450 high, D-32). West the stalls.")
room('room:stalls', 'The dragon stalls', outline=rect(-9984, -640, -8576, 640), floor=CRYPT, ceiling=CRYPT_TOP,
     theme='theme:crypt',
     pillars=[{'at': [-9216, 0], 'size': [896, 96], 'surface': GLYPHS,
               'notes': "The wall between the two stalls."}],
     platforms=[{'at': [-9856, 0], 'size': [256, 1280], 'base': 256, 'rise': 768, 'surface': GLYPHS,
                 'bottom_surface': BRICK,
                 'notes': "The alcoves' low roof: 256 high under it, too low for a dragon."}],
     ambient=8, notes="Two stalls off the crypt through a wide, high opening, a dragon mummy in each; at their far end two alcoves 256 high: the illusion heap (north) and the embalmer's chest (south).")

# 'from_' is a Python-safe spelling, fixed below.
for r in rooms:
    for w in r.get('walls', []):
        for p in w.get('panels', []):
            if 'from_' in p:
                p['from'] = p.pop('from_')

op('open:breast_hall', 'room:breast', 'room:hall', link='link:breast_hall', width=384, height=320, threshold=SAND,
   notes="The body's doors at the breast steps' foot: a pair, so that no mummy of the hall sees or reaches the arrival (D-11.3).")
op('open:hall_name', 'room:hall', 'room:name_stair', link='link:hall_name', width='full', height=448)
op('open:hall_swing', 'room:hall', 'room:swinging', link='link:hall_swing', width='full', height=448)
op('open:hall_chop', 'room:hall', 'room:chopping', link='link:hall_chop', width='full', height=448)
op('open:swing_presn', 'room:swinging', 'room:pres_n', link='link:swing_presn', width=160, height=320)
op('open:chop_press', 'room:chopping', 'room:pres_s', link='link:chop_press', width=160, height=320)
op('open:presn_canopic', 'room:pres_n', 'room:canopic', link='link:presn_canopic', width=320, height=384)
op('open:press_canopic', 'room:pres_s', 'room:canopic', link='link:press_canopic', width=320, height=384)
op('open:name_home', 'room:name_stair', 'room:home', link='link:name_home', width=160, height=320)
op('open:home_galn', 'room:home', 'room:gallery_n', link='link:home_galn', width=160, height=320)
op('open:home_gals', 'room:home', 'room:gallery_s', link='link:home_gals', width=160, height=320)
op('open:canopic_crypt', 'room:canopic', 'room:crypt', link='link:canopic_crypt', width=320, height=288,
   notes="The crypt steps' low arch: 288 high (D-57), so the 450-high dragon mummies stay below.")
op('open:crypt_stalls', 'room:crypt', 'room:stalls', link='link:crypt_stalls', width=768, height=640)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:body', 'ambient': 12}, 'rooms': rooms,
             'openings': openings,
             'notes': "FD-02 Southern Sphinx: x east, y north; the breast (X6) east, the body's halls at -256 west of it, the head at 768 up the stair of the name, the crypt at -1,280 under the canopic chamber. Written by output/studio_cal/fd02/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:breast': 0, 'room:hall': BODY, 'room:swinging': BODY, 'room:chopping': BODY, 'room:pres_n': BODY,
          'room:pres_s': BODY, 'room:canopic': BODY, 'room:name_stair': BODY, 'room:home': HEAD,
          'room:gallery_n': HEAD, 'room:gallery_s': HEAD, 'room:crypt': CRYPT, 'room:stalls': CRYPT}
GH, PH, DM, PICARD = 11273, 11274, 11672, 11922
PLACED = [  # room, group, [(row, at, facing)]
    ('hall', 10, [(GH, (-2700, 250), 0), (GH, (-2850, -250), 0), (GH, (-3000, 150), 0), (GH, (-2950, -120), 0)]),
    ('swinging', 11, [(GH, (-4300, 256), 0), (GH, (-4460, 330), 0)]),
    ('chopping', 12, [(GH, (-4300, -256), 0), (GH, (-4460, -330), 0)]),
    ('pres_n', 13, [(GH, (-5050, 420), 0), (GH, (-5220, 300), 0), (GH, (-4950, 300), 0)]),
    ('pres_s', 14, [(GH, (-5050, -420), 0), (GH, (-5220, -300), 0), (GH, (-4950, -300), 0)]),
    ('canopic', 15, [(GH, (-5824, 250), 0), (GH, (-5824, -250), 0)]),
    ('gallery_n', 16, [(PH, (-1344, 4050), 270), (PH, (-1088, 4050), 270)]),
    ('gallery_s', 17, [(PH, (-850, 2200), 90), (PH, (-700, 2250), 90)]),
    ('crypt', 18, [(DM, (-7600, 420), 0), (DM, (-7600, -420), 0), (DM, (-8150, 380), 0), (DM, (-8150, -380), 0)]),
    ('stalls', 19, [(DM, (-9200, 380), 0), (DM, (-9200, -380), 0)]),
]
NAMES = {GH: 'Ghost Mummy', PH: 'Phase Mummy', DM: 'Dragon Mummy'}
LEVELS = {GH: 62, PH: 72, DM: 65}
PLAN_SPACES = [
    ('room:breast', 'Breast steps', 'room', 'S', "The arrival (entrance:x6_door) on the top step inside the two leaves; eight steps down into the body. Quiet (D-11.3)."),
    ('room:hall', 'Hall of embalming', 'room', 'L', "Embalming tables, jars; the two Might Boosts on the embalmer's table (118119). The hub."),
    ('room:swinging', 'The Swinging Death', 'corridor', 'M', "Four blades out of the north wall, a plate under each (D-57: about 6 % each); the mask's protection for 2,000 (118116)."),
    ('room:chopping', 'The Chopping Death', 'corridor', 'M', "Three blades from the ceiling, a plate under each (about 8 % each); the mask (118117)."),
    ('room:pres_n', 'Preservation Room (north)', 'room', 'M', "Rune stones P, I, C; the great sarcophagus (Might 60, T6)."),
    ('room:pres_s', 'Preservation Room (south)', 'room', 'M', "Rune stones A, R, D (the sixth read calls m40.runes); the second great sarcophagus."),
    ('room:canopic', 'Canopic chamber', 'room', 'M', "Shelves of jars; the crypt's 288-high arch; 'Don't feed the dragons.'"),
    ('room:name_stair', 'Stair of the name', 'corridor', 'S', "32 steps up 1,024; the voice on the top landing and at the door (m40.name_right / name_wrong)."),
    ('room:home', 'Home of the Aged', 'room', 'M', "Set piece: Picard the Aged (npc 5704, m40's topic: the Chime for the widget), his chair 'Throne of Legends', four books, the eyes."),
    ('room:gallery_n', 'North sarcophagus gallery', 'room', 'S', "Two Phase Mummies, a find."),
    ('room:gallery_s', 'South sarcophagus gallery', 'room', 'S', "Two Phase Mummies, a find."),
    ('room:crypt', 'Crypt of the dragons', 'room', 'L', "Set piece: the vault under the sand; four Dragon Mummies kept in by the arch."),
    ('room:stalls', 'The dragon stalls', 'room', 'M', "Two Dragon Mummies; the illusion heap (118118), the embalmer's chest (T6)."),
]
LINKS = [
    ('link:breast_hall', 'room:breast', 'room:hall', 'double_door'),
    ('link:hall_name', 'room:hall', 'room:name_stair', 'open'),
    ('link:hall_swing', 'room:hall', 'room:swinging', 'open'),
    ('link:hall_chop', 'room:hall', 'room:chopping', 'open'),
    ('link:swing_presn', 'room:swinging', 'room:pres_n', 'door'),
    ('link:chop_press', 'room:chopping', 'room:pres_s', 'door'),
    ('link:presn_canopic', 'room:pres_n', 'room:canopic', 'open'),
    ('link:press_canopic', 'room:pres_s', 'room:canopic', 'open'),
    ('link:name_home', 'room:name_stair', 'room:home', 'door'),
    ('link:home_galn', 'room:home', 'room:gallery_n', 'door'),
    ('link:home_gals', 'room:home', 'room:gallery_s', 'door'),
    ('link:canopic_crypt', 'room:canopic', 'room:crypt', 'stairs'),
    ('link:crypt_stalls', 'room:crypt', 'room:stalls', 'open'),
]


def plan_doc(level):
    pops = {}
    for rid, _, ms in PLACED:
        for mon, _, _ in ms:
            pops.setdefault(f'room:{rid}', {}).setdefault(mon, 0)
            pops[f'room:{rid}'][mon] += 1
    spaces = []
    for sid, name, kind, size, purpose in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if sid in pops:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [LEVELS[m], LEVELS[m]],
                                'notes': f"{n} {NAMES[m]} {LEVELS[m]} (placed)."} for m, n in pops[sid].items()]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [{'id': i, 'from': f, 'to': t, 'kind': k} for i, f, t, k in LINKS]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Picard the Aged's home in the half-buried Southern Sphinx: a hall of embalming, two death runs whose toll-keepers sell protection, rune stones that spell a name, a stair that asks it, the old man's library in the head, and under the sand a crypt of dragon mummies.",
        'purpose': "M40 The Southern Sphinx: the runes (m40.runes) spell PICARD; the stair's voice (m40.name_right, name_said 111800) opens the door of the name; Picard (npc 5704) trades the Chime of Opening for Halon's widget (m40.done 111801). Party 58 to 61, monsters 62-72 (26 placed, D-57 Q7), treasure 6.",
        'mood': "Dry and still: sand on the steps, resin and old linen, blades whispering in the dark runs; above, an old man's books in the light of two stone eyes; below, things too large for the arch.",
        'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:body', 'spaces': ['room:hall', 'room:swinging', 'room:pres_n', 'room:canopic',
                                                 'room:pres_s', 'room:chopping'],
                   'notes': "Round the body: out by one death run, through both Preservation Rooms and the canopic chamber, back by the other."}],
        'entrances': [{'id': 'entrance:x6_door', 'space': 'room:breast', 'kind': 'both', 'facing': 'w',
                       'how': "From X6's door in the sphinx's breast (A5's door:fd02): on the top step 256 inside the leaves, facing west down into the body."}],
        'critical_path': ['room:breast', 'room:hall', 'room:swinging', 'room:pres_n', 'room:canopic', 'room:pres_s',
                          'room:chopping', 'room:hall', 'room:name_stair', 'room:home'],
        'return_path': ['room:home', 'room:name_stair', 'room:hall', 'room:breast'],
        'goals': [{'id': 'goal:picard', 'space': 'room:home', 'kind': 'use', 'story': 'M40',
                   'what': "Picard's topic: the widget for the Chime of Opening (m40.done)."}],
        'set_pieces': [{'id': 'set:home', 'kind': 'scripted', 'spaces': ['room:home'],
                        'rule': "Behind the door of the name, opened by the name: the library under the face, Picard in his chair."},
                       {'id': 'set:crypt', 'kind': 'scripted', 'spaces': ['room:crypt', 'room:stalls'],
                        'rule': "The dragon mummies' vault, kept in by the 288-high arch (D-57)."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 13, 'sectors': 13, 'monsters_about': 26, 'chests': 3, 'doors': 6, 'loops': 1,
                   'floor_area_munits2': 12},
        'notes': "Size S (at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From act6_graphs/fd02.graph.yml and D-57 (FD-02 APPROVAL, Q7-Q13).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """FD-02 Southern Sphinx (not to scale; plan, north up; the sphinx faces east)
  z 768     [N GALLERY]
                |door
            [HOME OF THE AGED: Picard, chair, books; eyes east]--door--[S GALLERY]
                |door of the name (the name asked on the landing)
  z -256    [STAIR OF THE NAME, 32 steps]
                |
  [CANOPIC]--[PRES N]--door--[SWINGING DEATH]--[HALL OF EMBALMING]--8 steps--[BREAST] =exit= X6 (entrance:fd02_door)
      |    \\--[PRES S]--door--[CHOPPING DEATH]--/
      | arch 288, crypt steps
  z -1280   [STALLS: heap, chest]--[CRYPT OF THE DRAGONS]
"""

# ================================================================================================ objects
ARRIVAL = [-256, 0]
objects = {'format': 0}
objects['start'] = {'room': 'room:breast', 'at': ARRIVAL, 'facing': 'w',
                    'notes': "entrance:x6_door: on the top step 256 inside the leaves, facing west down into the body."}
objects['arrivals'] = [{'entrance': 'entrance:x6_door', 'room': 'room:breast', 'at': ARRIVAL, 'facing': 'w',
                        'notes': "On the top step 256 inside the two leaves, facing west (X6's door:fd02, A5)."}]
PAIR = {'pictures': [[S('egydrsml', 128, 256), S('egydrsmr', 128, 256)]],
        'back_pictures': [[S('egydrsml', 128, 256), S('egydrsmr', 128, 256)]]}
objects['doors'] = [
    dict({'id': 'door:body', 'opening': 'open:breast_hall', 'kind': 'hinged', 'leaves': 2, 'thickness': 24,
          'edge_surface': TRIM,
          'notes': "The body's doors at the foot of the breast steps (egydrsml/egydrsmr, Horus on each leaf): shut, the hall's mummies neither see nor reach the arrival (D-11.3, as D-57 made FD-03's east way a door)."},
         **PAIR),
    {'id': 'door:swing', 'opening': 'open:swing_presn', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR,
     'back_surface': DOOR, 'edge_surface': TRIM, 'notes': "The Swinging Death's end: a carved slab door."},
    {'id': 'door:chop', 'opening': 'open:chop_press', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR,
     'back_surface': DOOR, 'edge_surface': TRIM, 'notes': "The Chopping Death's end."},
    {'id': 'door:name', 'opening': 'open:name_home', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR,
     'back_surface': DOOR, 'edge_surface': TRIM,
     'notes': "The door of the name: opened by PICARD (m40.name_right) in the same visit, and on every load (name_said 111800)."},
    {'id': 'door:gal_n', 'opening': 'open:home_galn', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR,
     'back_surface': DOOR, 'edge_surface': TRIM, 'notes': "The north lappet's door."},
    {'id': 'door:gal_s', 'opening': 'open:home_gals', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR,
     'back_surface': DOOR, 'edge_surface': TRIM, 'notes': "The south lappet's door."},
]
SARC = S('egytrmc', 64, 64)
objects['chests'] = [
    {'id': 'chest:sarc_n', 'room': 'room:pres_n', 'at': [-5056, 128], 'facing': 'e', 'size': [192, 96, 96],
     'surface': SARC, 'top_surface': PLAIN, 'treasure_level': 6, 'random_items': 3, 'gold': 4000,
     'notes': "The north great sarcophagus: opens for a clicking member with Might 60 (D-57 Q10)."},
    {'id': 'chest:sarc_s', 'room': 'room:pres_s', 'at': [-5056, -128], 'facing': 'e', 'size': [192, 96, 96],
     'surface': SARC, 'top_surface': PLAIN, 'treasure_level': 6, 'random_items': 3, 'gold': 4000,
     'notes': "The south great sarcophagus (Might 60)."},
    # F6 feedback fix (2026-11-21): the shipped MM8 chest (gt002) in place of a sandstone box, on the alcove's floor
    # (it stood on the alcoves' hanging roof, the highest floor there), its back to the west wall: a chest's `facing`
    # is its long axis, its front 90 degrees anticlockwise (s -> east)
    {'id': 'chest:embalmer', 'room': 'room:stalls', 'at': [-9936, -384], 'facing': 's', 'kind': 'gt002',
     'floor_height': CRYPT, 'treasure_level': 6,
     'random_items': 4, 'gold': 5000, 'notes': "The embalmer's chest in the south alcove."},
]
objects['monsters'] = []
for rid, group, ms in PLACED:
    for n, (mon, at, facing) in enumerate(ms, 1):
        m = {'id': f'monster:{rid}_{n}', 'room': f'room:{rid}', 'monster': mon, 'at': list(at), 'facing': facing,
             'group': group}
        if mon == DM:
            # F75 (reviews/PLAYER_FEEDBACK_20261126.md, "dragon gets stuck", 2026-11-26): a Dragon Mummy (450 high,
            # radius 120) stops at the crypt's 288-high arch with its body in the frame; leashed so it stays 64 clear
            # of it (the largest such leash, at most 1,536; tools/xeen/check_monster_fit.py).
            m['leash'] = {(-7600, 420): 1152, (-7600, -420): 1152}.get(tuple(at), 1536)
        objects['monsters'].append(m)
objects['monsters'].append({'id': 'monster:picard', 'room': 'room:home', 'monster': PICARD, 'at': [-1520, 3200],
                            'facing': 0, 'hostile': False, 'group': 40, 'immobile': True, 'npc': 5704,
                            'notes': "Picard the Aged (11922, A2's peaceful placed-only row; S's look to come): by his chair, talks as npc 5704 (m40), takes no damage (evt:picard_load, D-51/D-52)."})

# Movers: the blades (review G3 row 54: real blades, not slabs). Each is a long steel blade 4 thick and 28 high (MM7's
# brushed steel `ch004i`, one picture along its 352) over a bevelled edge 2 thick and 8 high in the paler `gn_mtl01`
# along its whole length: 36 high in all (the old slab was 16 x 112). Swinging: out of slots
# in the north wall, sweeping 360 south over the walk (the edge's underside 216 above the floor, over the party's 192).
# Chopping: down out of ceiling slots to the same height.
SWING_X = (-3840, -4032, -4224, -4416)
CHOP_X = (-3904, -4160, -4416)
BLADE = S('ch004i', 64, 64, scale=5.5, offset=[0, 30])  # D-63 14's steel: one picture 352 along the blade, a band of it up
EDGE = S('gn_mtl01', 128, 128)                         # the honed edge, paler than the blade; seamless along the 352
BLADE_LEN, BODY_T, BODY_H, EDGE_T, EDGE_H = 352, 4, 28, 2, 8


def blade(mid_id, room, x, y, edge_bottom, travel, state, notes):
    return {'id': mid_id, 'room': room, 'at': [x, y], 'size': [BODY_T, BLADE_LEN], 'bottom': edge_bottom + EDGE_H,
            'height': BODY_H, 'travel': travel, 'speed': 900, 'state': state, 'surface': BLADE, 'top_surface': BLADE,
            'end_surface': BLADE,
            'parts': [{'at': [x, y], 'size': [EDGE_T, BLADE_LEN], 'bottom': edge_bottom, 'height': EDGE_H,
                       'surface': EDGE, 'notes': "The bevelled edge."}],
            'notes': notes}


objects['movers'] = []
for i, x in enumerate(SWING_X, 1):
    objects['movers'].append(blade(f'mover:swing_{i}', 'room:swinging', x, 272, 216, [0, 360, 0],
                                   'end' if i % 2 else 'start',
                                   "A swinging blade: drawn at its start swept out over the walk, at its end back in its slot in the north wall."))
for i, x in enumerate(CHOP_X, 1):
    objects['movers'].append(blade(f'mover:chop_{i}', 'room:chopping', x, -256, 520, [0, 0, -304],
                                   'end' if i % 2 else 'start', "A chopping blade: down out of its ceiling slot and back."))
objects['plates'] = (
    [{'id': f'plate:swing_{i}', 'room': 'room:swinging', 'at': [x, 256], 'size': [64, 352], 'surface': SAND,
      'notes': "Under the blade's sweep."} for i, x in enumerate(SWING_X, 1)]
    + [{'id': f'plate:chop_{i}', 'room': 'room:chopping', 'at': [x, -256], 'size': [64, 352], 'surface': SAND,
        'notes': "Under the blade's drop."} for i, x in enumerate(CHOP_X, 1)])


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [235, 170, 100]
DAY = [255, 236, 200]
objects['lights'] = [
    light('light:eye_n', 'room:home', [-600, 3392], 480, 1400, DAY, brightness=30, notes="Daylight through the north eye."),
    light('light:eye_s', 'room:home', [-600, 3008], 480, 1400, DAY, brightness=30, notes="Daylight through the south eye."),
    light('light:doors', 'room:breast', [-120, 0], 300, 900, DAY, brightness=18, notes="Daylight round the leaves."),
]
# Torches on the walls (12 out from the wall, as DD-24's).
TORCHES = [('breast', (-500, 308), 0), ('breast', (-500, -308), 0),
           ('hall', (-1700, 436), 0), ('hall', (-1700, -436), 0), ('hall', (-2700, 436), 0), ('hall', (-2700, -436), 0),
           ('swinging', (-3400, 76), 0), ('chopping', (-3400, -76), 0),
           ('pres_n', (-4748, 600), 0), ('pres_s', (-4748, -600), 0),
           ('canopic', (-6132, 450), 0), ('canopic', (-6132, -450), 0),
           ('name_stair', (-1524, 800), 0), ('name_stair', (-1164, 2300), HEAD),
           ('home', (-1780, 2900), HEAD), ('home', (-1780, 3500), HEAD),
           ('gallery_n', (-780, 4000), HEAD), ('gallery_s', (-1012, 2400), HEAD),
           ('crypt', (-8436, 600), 0), ('crypt', (-6284, 600), CRYPT_TOP), ('crypt', (-6284, -600), CRYPT_TOP),
           ('stalls', (-8588, 500), 0), ('stalls', (-8588, -500), 0)]
objects['decorations'] = []
for i, (rid, at, fh) in enumerate(TORCHES, 1):
    d = {'id': f'deco:torch_{i:02d}', 'room': f'room:{rid}', 'decoration': 'torch01', 'at': list(at), 'height': 224}
    if fh:
        d['floor_height'] = fh
    objects['decorations'].append(d)
    lt = light(f'light:torch_{i:02d}', f'room:{rid}', list(at), 256, 800, FIRE)
    if fh:
        lt['floor_height'] = fh
    objects['lights'].append(lt)
objects['decorations'] += [
    {'id': 'deco:jar_1', 'room': 'room:hall', 'decoration': 'dec97', 'at': [-2240, 352], 'floor_height': BODY + 96},
    {'id': 'deco:jar_2', 'room': 'room:hall', 'decoration': 'dec97', 'at': [-1984, 352], 'floor_height': BODY + 96},
    {'id': 'deco:jar_3', 'room': 'room:hall', 'decoration': 'dec97', 'at': [-2240, -352], 'floor_height': BODY + 96},
    {'id': 'deco:jar_4', 'room': 'room:canopic', 'decoration': 'dec97', 'at': [-6016, 528], 'floor_height': BODY + 128},
    {'id': 'deco:jar_6', 'room': 'room:canopic', 'decoration': 'dec97', 'at': [-5632, 528], 'floor_height': BODY + 128},
    {'id': 'deco:jar_7', 'room': 'room:canopic', 'decoration': 'dec97', 'at': [-6016, -528], 'floor_height': BODY + 128},
    {'id': 'deco:vase_1', 'room': 'room:home', 'decoration': 'dec97', 'at': [-576, 2752]},
    {'id': 'deco:vase_2', 'room': 'room:home', 'decoration': 'dec97', 'at': [-576, 3648]},
    # Picard's very good chair, the Throne of Legends: lane S's carved throne (D-66, row 4043), its back to the west
    # wall, looking east down the room; origin at its foot's centre, where D-63's block seat stood.
    {'id': 'deco:throne', 'room': 'room:home', 'decoration': 'xeen_throne', 'at': [-1696, 3200], 'facing': 0,
     'notes': "Picard's very good chair, the Throne of Legends (clicked: evt:throne)."},
    # The four books: lane S's carved lecterns (row 4050, 41 deep at the desk), backs 24 off the north and south
    # walls (centres 45 in), facing into the room; where the block lecterns stood.
] + [
    {'id': f'deco:book_{i}', 'room': 'room:home', 'decoration': 'xeen_lectern', 'at': at, 'facing': f,
     'floor_height': HEAD, 'notes': "A lectern with a book (clicked: evt:book_%d)." % i}
    for i, (at, f) in enumerate((([-1600, 3667], 270), ([-704, 3667], 270), ([-1664, 2733], 90),
                                 ([-1088, 2733], 90)), 1)
] + [
    {'id': 'deco:bones_1', 'room': 'room:crypt', 'decoration': 'dec29', 'at': [-8380, 650]},
    {'id': 'deco:bones_2', 'room': 'room:crypt', 'decoration': '7dec18', 'at': [-8380, -650]},
    {'id': 'deco:skulls_1', 'room': 'room:stalls', 'decoration': 'sklplrev', 'at': [-8700, 560]},
    {'id': 'deco:bones_3', 'room': 'room:stalls', 'decoration': 'dec19', 'at': [-8700, -560]},
]
objects['exits'] = [
    {'id': 'exit:leaf_l', 'room': 'room:breast', 'at': [0, 120], 'floor_height': 0, 'size': [224, 256],
     'surface': S('7solid01', 256, 256, fit=True), 'to': 'exit:x6_door', 'notes': "The north leaf of the breast's doors (seen from inside, the left)."},
    {'id': 'exit:leaf_r', 'room': 'room:breast', 'at': [0, -120], 'floor_height': 0, 'size': [224, 256],
     'surface': S('7solid01', 256, 256, fit=True), 'to': 'exit:x6_door', 'notes': "The south leaf."},
]
objects['sounds'] = [
    {'id': 'sound:bed', 'room': 'room:hall', 'at': [-2112, 0], 'sound': 'humming', 'radius': 9000,
     'inner_radius': 4000, 'volume': 0.35, 'pan': False, 'notes': "The dungeon hum under the whole body (D-48)."},
    {'id': 'sound:crypt', 'room': 'room:crypt', 'at': [-7600, 0], 'sound': 'humming', 'radius': 3200,
     'inner_radius': 1200, 'volume': 0.5, 'pan': False, 'notes': "The crypt's deeper hum."},
]

# ================================================================================================ wiring
QB = {'rune_p': 118110, 'rune_i': 118111, 'rune_c': 118112, 'rune_a': 118113, 'rune_r': 118114, 'rune_d': 118115,
      'swing_paid': 118116, 'chop_paid': 118117, 'illusion_gone': 118118, 'boosts_taken': 118119,
      'name_said': 111800, 'm40_done': 111801}
RUNE_ORDER = ['p', 'i', 'c', 'a', 'r', 'd']


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def runes_all_lua():
    return ' and '.join(f'IsQBitSet(QBit({QB["rune_" + c]}))' for c in RUNE_ORDER)


def mask_lua(qbit, death, hook_name):
    # D-57 Q9 (aazex125:9-14, sums rescaled): the map asks; A3's hooks pay, set the qbit and say the lines.
    offer = f'"For 2,000 gold I can protect you from the {death}. Will you pay?"'
    clue = '"For another 500 I\'ll give you a clue. Will you pay?"'
    ask_clue = f'AskChoiceWithAnswerSteps(eventId, 6, {yaml_lua_str(clue)}, {{{{Answer = "Yes", Step = 3}}, {{Answer = "No", Step = 4}}}})'
    return (
        'if continueStep == 1 then\n'
        f'    if XeenQuests.hook("m40.{hook_name}") then evt.PlaySoundName("gold01") end\n'
        '    return\n'
        'end\n'
        'if continueStep == 3 then XeenQuests.hook("m40.mask_clue") return end\n'
        'if continueStep == 2 or continueStep == 4 then XeenQuests.hook("m40.mask_no") return end\n'
        'if continueStep ~= nil then return end\n'
        f'if IsQBitSet(QBit({qbit})) then\n'
        f'    {ask_clue}\n'
        '    return\n'
        'end\n'
        f'AskChoiceWithAnswerSteps(eventId, 5, {yaml_lua_str(offer)}, {{{{Answer = "Yes", Step = 1}}, {{Answer = "No", Step = 2}}}})')


def yaml_lua_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


# D-57 APPROVAL: one unprotected crossing deals at most about 25 % of a level-59 member's HP in all (about 6 % per
# Swinging blade, about 8 % per Chopping blade), Physical. Sized on the weakest member of the playtest party (a
# level-59 sorcerer, measured in playtest_traps.yml; NOTES "Measurements").
SWING_DMG = 8
CHOP_DMG = 11
BOOKS = [
    ("The book seems to be an account of one of Picard's favorite adventurers. You open it to a random page: "
     "...Encoplius loosened his short sword in its scabbard. It looked like yet another fight with the hated mad fools. "
     "Bargus, the party's sorcerer, began to tremble with fright..."),
    ("The book seems to be an account of one of Picard's favorite adventurers. You open it to a random page: "
     "...Bruno cut through yet another insane beggar with his massive broadsword. \"As I was saying, this town is great! "
     "Just look at this place! An excellent trainer, a bank, a... excuse me...\""),
    ("The book seems to be an account of one of Picard's favorite adventurers. You open it to a random page: "
     "And then princess Shiela... EDITOR'S NOTE: THE FOLLOWING TEXT HAS BEEN EXCISED FOR THE MORAL HEALTH OF OUR "
     "LOYAL PLAYERS."),
    "This book has been hollowed out and used to store old cigars.",
]
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 7,
     'text': "Sand on the steps, cool air from below, and a smell of resin and old linen."},
    {'id': 'evt:exit_l', 'preset': 'exit', 'source': 'exit:leaf_l', 'title': 'Exit the Southern Sphinx',
     'notes': "Out to X6 (installed, A5) before the breast's leaves: the game's own leave window (D-24); 'Exit the "
              "Southern Sphinx?' (aazex125:3) is its meaning."},
    {'id': 'evt:exit_r', 'preset': 'exit', 'source': 'exit:leaf_r', 'title': 'Exit the Southern Sphinx'},
    {'id': 'evt:door_body', 'preset': 'door', 'source': 'door:body', 'title': 'Doors'},
    {'id': 'evt:door_swing', 'preset': 'door', 'source': 'door:swing', 'title': 'Door'},
    {'id': 'evt:door_chop', 'preset': 'door', 'source': 'door:chop', 'title': 'Door'},
    {'id': 'evt:door_gal_n', 'preset': 'door', 'source': 'door:gal_n', 'title': 'Door'},
    {'id': 'evt:door_gal_s', 'preset': 'door', 'source': 'door:gal_s', 'title': 'Door'},
    # ---- the name (m40)
    {'id': 'evt:name_landing', 'preset': 'script', 'trigger': 'step', 'source': 'level:landing',
     'condition': {'not': {'qbit': QB['name_said']}},
     'question': {'ask': 'What is my name?', 'answers': ['picard'], 'wrong_effects': [hook('m40.name_wrong')]},
     'opens': ['door:name'], 'effects': [hook('m40.name_right')],
     'else_effects': [{'text': "Home of the Aged"}],
     'notes': "Once named, the landing shows the door's sign 'Home of the Aged' (aazex125:2). The top landing, on every climb until named: \"What is my name?\" (aazex125:16). PICARD (any case): A3's m40.name_right (\"Correct, come on up!\", name_said 111800) and the door of the name opens in the same visit; anything else m40.name_wrong (\"Wrong.\")."},
    {'id': 'evt:name_door', 'preset': 'script', 'source': 'door:name', 'side': 'room:name_stair',
     'title': 'Door of the name', 'condition': {'not': {'qbit': QB['name_said']}},
     'question': {'ask': 'What is my name?', 'answers': ['picard'], 'wrong_effects': [hook('m40.name_wrong')]},
     'opens': ['door:name'], 'effects': [hook('m40.name_right')],
     'else_effects': [{'text': "The door of the name stands open."}],
     'notes': "The door's click from the landing asks as the landing does (the same hooks)."},
    {'id': 'evt:name_door_back', 'preset': 'door', 'source': 'door:name', 'side': 'room:home', 'title': 'Door',
     'action': 'open', 'notes': "From inside the Home the door opens."},
    {'id': 'evt:name_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': QB['name_said']},
     'opens': ['door:name'], 'notes': "With name_said the door of the name stands open on every load (m40.stair true)."},
    {'id': 'evt:home_enter', 'preset': 'script', 'trigger': 'step', 'source': 'room:home', 'once': True,
     'effects': [hook('m40.stair')],
     'notes': "The first step into the Home: A3's m40.stair (\"The door at the top of the stair opens on a room full of books, and an old man in a very good chair.\")."},
    {'id': 'evt:plaque_name', 'preset': 'script', 'source': 'panel:plaque_name', 'title': 'Inscription',
     'effects': [hook('m40.stair_plaque')], 'notes': "aazex127:8 (A3's m40.stair_plaque)."},
    {'id': 'evt:plaque_dragons', 'preset': 'script', 'source': 'panel:plaque_dragons', 'title': 'Inscription',
     'effects': [hook('m40.crypt_sign')], 'notes': "aazex127:9 by the crypt's arch (A3's m40.crypt_sign)."},
    {'id': 'evt:sign_pres_n', 'preset': 'text', 'trigger': 'step', 'source': 'room:pres_n', 'text': 'Preservation Room',
     'seconds': 3, 'notes': "aazex125:0."},
    {'id': 'evt:sign_pres_s', 'preset': 'text', 'trigger': 'step', 'source': 'room:pres_s', 'text': 'Preservation Room',
     'seconds': 3, 'notes': "aazex125:1."},
    # ---- Picard
    {'id': 'evt:picard_load', 'preset': 'script', 'trigger': 'load',
     'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:picard"), false)',
     'notes': "Picard cannot be killed: every hit on him is zeroed, on every load (D-51, D-52)."},
    {'id': 'evt:throne', 'preset': 'script', 'source': 'deco:throne', 'title': 'Throne of Legends', 'effects': [hook('m40.chair')], 'notes': "aazex126:11 as the hover, A3's m40.chair (D-57 Q12): no reward."},
]
for i, text in enumerate(BOOKS, 1):
    events.append({'id': f'evt:book_{i}', 'preset': 'text', 'source': f'deco:book_{i}', 'title': 'Book',
                   'text': text, 'window': True, 'notes': f"aazex126:{14 + 2 * i - 1}{'-' + str(14 + 2 * i) if i < 4 else ''}."})
for c in RUNE_ORDER:
    q = QB['rune_' + c]
    events.append({
        'id': f'evt:rune_{c}', 'preset': 'script', 'source': f'platform:rune_{c}', 'title': 'Runes',
        'lua': (f'XeenQuests.hook("m40.rune_{c}")\n'
                'if XeenQuests.can("m40.runes") then XeenQuests.hook("m40.runes") end'),
        'notes': f"aazex127:{2 + RUNE_ORDER.index(c)}: the lesson of the letter {c.upper()}, map qbit {q}; once all six are read, any stone calls A3's m40.runes (the six letters in the order of the halls)."})
events += [
    # ---- the two death runs (D-57 APPROVAL, Q9)
    {'id': 'evt:mask_swing', 'preset': 'script', 'source': 'panel:mask_swing', 'title': 'Toll-keeper',
     'lua': mask_lua(QB['swing_paid'], 'Swinging Death', 'mask_swinging'),
     'notes': "aazex125:9, 11-14 (sums rescaled, D-57 Q9): the map asks; Yes calls A3's m40.mask_swinging (2,000 gold, swinging_paid 118116: evt:swing_still puts the blades in their slots for good), the hook's line; every later click offers the clue (m40.mask_clue, 500); No m40.mask_no (\"Begone, then!\"), no throw. "},
    {'id': 'evt:mask_chop', 'preset': 'script', 'source': 'panel:mask_chop', 'title': 'Toll-keeper',
     'lua': mask_lua(QB['chop_paid'], 'Chopping Death', 'mask_chopping'),
     'notes': "aazex125:10-14: the same for the Chopping Death (118117)."},
    {'id': 'evt:swing_tick', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'qbit': QB['swing_paid']}},
     'toggles': [f'mover:swing_{i}' for i in range(1, len(SWING_X) + 1)],
     'notes': "The Swinging Death's blades sweep out and back, alternate ones together, until protection is paid."},
    {'id': 'evt:chop_tick', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'qbit': QB['chop_paid']}},
     'toggles': [f'mover:chop_{i}' for i in range(1, len(CHOP_X) + 1)],
     'notes': "The Chopping Death's blades drop and rise until protection is paid."},
    {'id': 'evt:swing_still', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'qbit': QB['swing_paid']},
     'opens': [f'mover:swing_{i}' for i in range(1, len(SWING_X) + 1)],
     'notes': "Paid (118116): the blades go back into their slots and stay there, in the same visit and on every load."},
    {'id': 'evt:chop_still', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'qbit': QB['chop_paid']},
     'closes': [f'mover:chop_{i}' for i in range(1, len(CHOP_X) + 1)],
     'notes': "Paid (118117): the blades back in the ceiling for good."},
]
for i, x in enumerate(SWING_X, 1):
    events.append({'id': f'evt:plate_swing_{i}', 'preset': 'script', 'trigger': 'step', 'source': f'plate:swing_{i}',
                   'condition': {'not': {'qbit': QB['swing_paid']}},
                   'effects': [{'lua': f'evt.PlaySoundName("swing with sword01", {x}, 256, {BODY + 300})'},
                               {'damage': {'amount': SWING_DMG, 'kind': 'physical', 'who': 'all'}}],
                   'notes': f"A swinging blade catches the party: {SWING_DMG} Physical to each (D-57: about 6 % of a level-59 member), once per crossing."})
for i, x in enumerate(CHOP_X, 1):
    events.append({'id': f'evt:plate_chop_{i}', 'preset': 'script', 'trigger': 'step', 'source': f'plate:chop_{i}',
                   'condition': {'not': {'qbit': QB['chop_paid']}},
                   'effects': [{'lua': f'evt.PlaySoundName("swing with axe01", {x}, -256, {BODY + 300})'},
                               {'damage': {'amount': CHOP_DMG, 'kind': 'physical', 'who': 'all'}}],
                   'notes': f"A chopping blade: {CHOP_DMG} Physical to each (about 8 %), once per crossing."})
events += [
    # ---- the great sarcophagi (D-57 Q10) and the embalmer's table
    {'id': 'evt:chest_sarc_n', 'preset': 'chest', 'source': 'chest:sarc_n', 'title': 'Sarcophagus',
     'condition': {'stat': {'name': 'ActualMight', 'at_least': 60}},
     'else_effects': [{'message': 'You are too weak to open the sarcophagus.'}],
     'notes': "aazex125:4-5, D-57 Q10: Might 60 on the clicking member, potions and spells counting (ActualMight)."},
    {'id': 'evt:chest_sarc_s', 'preset': 'chest', 'source': 'chest:sarc_s', 'title': 'Sarcophagus',
     'condition': {'stat': {'name': 'ActualMight', 'at_least': 60}},
     'else_effects': [{'message': 'You are too weak to open the sarcophagus.'}]},
    {'id': 'evt:chest_embalmer', 'preset': 'chest', 'source': 'chest:embalmer', 'title': 'Chest',
     'notes': "The source's Super Dragon Embalmer (aazex127:12-13, +5 levels) to the ledger only; a T6 chest."},
    {'id': 'evt:table_boosts', 'preset': 'script', 'source': 'platform:table_s', 'title': "Embalmer's table",
     'lua': ('if XeenQuests.hook("m40.embalming_table") then\n'
             '    evt.SetHeldItem(240, {bonus = 10}) evt.SetHeldItem(240, {bonus = 10})\n'
             'end'),
     'notes': "D-57 Q10, D-22's pattern (XD-15): two Might Boosts of a fixed power 10, once per game (A3's m40.embalming_table sets embalming_boosts 118119 and says the line)."},
    {'id': 'evt:table_n', 'preset': 'text', 'source': 'platform:table_n', 'title': 'Embalming table',
     'text': "Jars of resin and natron, hooks and linen. Nothing you want."},
    # ---- the galleries' finds (the graph's fixed finds; a T6 item of any kind until A2 names them)
    {'id': 'evt:find_n', 'preset': 'script', 'source': 'platform:find_n', 'title': 'Niche',
     'condition': {'not': {'map_var': 'find_n'}},
     'effects': [{'set': {'var': {'map_var': 'find_n'}, 'value': 1}}, {'give_item': {'level': 6}},
                 {'text': "Grave goods left in the empty niche. You take them."}],
     'else_effects': [{'text': "Nothing here."}], 'notes': "aazex126:13 'Nothing here.' once taken."},
    {'id': 'evt:find_s', 'preset': 'script', 'source': 'platform:find_s', 'title': 'Niche',
     'condition': {'not': {'map_var': 'find_s'}},
     'effects': [{'set': {'var': {'map_var': 'find_s'}, 'value': 1}}, {'give_item': {'level': 6}},
                 {'text': "Grave goods left in the empty niche. You take them."}],
     'else_effects': [{'text': "Nothing here."}]},
    # ---- the illusion heap
    {'id': 'evt:heap', 'preset': 'script', 'source': 'platform:heap', 'title': 'Alcove',
     'condition': {'not': {'qbit': QB['illusion_gone']}},
     'locked_text': 'Nothing here.',
     'effects': [hook('m40.illusion'), {'hide': 'platform:heap'}, {'passable': 'platform:heap'}],
     'notes': "aazex127:11, 14: the heap of gold is an illusion, gone at the click (118118), no harm."},
    {'id': 'evt:heap_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': QB['illusion_gone']},
     'effects': [{'hide': 'platform:heap'}, {'passable': 'platform:heap'}],
     'notes': "The heap stays gone on every load."},
]
# The illusion heap: a low mound of coins in the north alcove.
for r in rooms:
    if r['id'] == 'room:stalls':
        r['platforms'].append({'id': 'platform:heap', 'at': [-9888, 384], 'size': [160, 192], 'rise': 40,
                               'top_heights': [8, 8, 40, 40], 'surface': COINS, 'top_surface': COINS,
                               'notes': "A heap of gold: an illusion (aazex127:14)."})
wiring = {'format': 0, 'variables': ['find_n', 'find_s'], 'events': events}

project = {
    'format': 0, 'id': 'xeen_fd02', 'name': 'Southern Sphinx', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'FD-02', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [20, 10], 'climbs': 'n'},
    'map_stats': {'id': 9180, 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 10,
                  'perception_difficulty': 20, 'refill_days': 672, 'music': 46, 'environment': 'stoneroom',
                  'lock_difficulty': 20, 'bolster': 'LowerToEqual', 'slots': []},
    'neighbours': [{
        'id': 'exit:x6_door', 'to': 'xeen_x6.odm', 'kind': 'door', 'arrival': 'entrance:fd02_door',
        'arrival_hint': "On X6 256 before the Southern Sphinx's breast leaves, facing east (A5's entrance:fd02_door).",
        'direction': 0,
        'notes': "X6 installed (A5). The way out names X6's named arrival entrance:fd02_door, moved by A5 (seventeenth "
                 "session, 03:43) to the whole cell (-12288, -10240, 1536) facing east, out of the sphinx (D-57's "
                 "-12144 is not on a cell). X6's door:fd02 names this map's "
                 "arrival entrance:x6_door: (-256, 0, 0) facing west."}],
    'qbits': QB,
    'notes': "Xeen design brief, level L4: FD-02 Southern Sphinx on X6 (M40, Act VI). D-57: Ghost Mummy 11273 x 16, Phase Mummy 11274 x 4, Dragon Mummy 11672 x 6 (26, 31.07k per member); Picard the Aged 11922 (npc 5704) peaceful, placed-only, unkillable. Rest encounters 0 (Q13). Hooks m40.runes, name_right, name_wrong, stair; Picard's topic (m40.done). Map qbits 118110-118119. Music 46.",
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
        p['notes'] = f"Xeen design brief, level {lv}: FD-02 Southern Sphinx (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: FD-02 Southern Sphinx, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM)])
print('written L4')
