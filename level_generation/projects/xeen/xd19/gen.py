#!/usr/bin/env python3
"""XD-19 Castle Xeen: writes the project files of devdocs/xeen/briefs/xd19/L1..L4 (lane A7 phase 5, thirteenth
session, sub-agent agent:xeen-a7-xd19). Route after level_generation/projects/xeen/dd07/gen.py (two-storey stair halls,
breakable pylons) and the D-47 answer (devdocs/xeen/mockups/act5_a7_decisions.md).

    python3 level_generation/projects/xeen/xd19/gen.py            all four levels
    python3 level_generation/projects/xeen/xd19/gen.py L4         one level

Rerun after every change here (level_generation/projects/xeen/xd19/cycle.sh); never hand-edit the written files. The playtests
are written by tools/gen_tests.py from the built ids.lock.yml.

Frame: x east, y north, z up. Four floors 640 apart (F0 0, F1 640, F2 1280, F3 1920). The plan is drawn on a base
grid (columns C1 outer 640, C2 640, C3 896, C4 centre 3,072; bands S, M, N, NN) and scaled by 5/4 (walls 160
thick). Vertical ways are two-storey stair halls (a flight of 20 steps of 32 over 800 to a gallery 640 deep at the
next floor), as DD-07's: the two corner towers (two halls each, the second over the first's neighbour), the grand
stair (stair hall -> grand landing), the keep stair (foundry -> upper landing) and the crown stair (behind the field
-> crown landing).
"""
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / 'devdocs/xeen/briefs/xd19'
LOCK = BRIEFS / 'L4/ids.lock.yml'


class Flow(list):
    pass


class FlowDict(dict):
    pass


yaml.add_representer(Flow, lambda d, v: d.represent_sequence('tag:yaml.org,2002:seq', v, flow_style=True))
yaml.add_representer(FlowDict, lambda d, v: d.represent_mapping('tag:yaml.org,2002:map', v, flow_style=True))


def F(*v):
    return Flow(v)


def S(texture, w, h, **kw):
    d = FlowDict(texture=texture, size=Flow([w, h]))
    d.update(kw)
    return d


def lock():
    if LOCK.is_file():
        return yaml.safe_load(LOCK.read_text()) or {}
    return {}


LOCKED = lock()


def lock_no(kind, key):
    return (LOCKED.get(kind) or {}).get(key, 0)


# ---------------------------------------------------------------------------------------------------------------------
# Numbers
MAP_STATS_ID = 9144
MUSIC = 22
DEMON, DEVIL, SCREAMER, GUARD = 11630, 11631, 11632, 11603
FIRE_EL, AIR_EL, WATER_EL, EARTH_EL, GREATER = 11620, 11624, 11625, 11626, 11622
PET, LORD = 11644, 11634
NAMES = {DEMON: 'Demon', DEVIL: 'Devil', SCREAMER: 'Screamer', GUARD: "Xeen's Guard", FIRE_EL: 'Lesser Elemental',
         AIR_EL: 'Lesser Air Elemental', WATER_EL: 'Lesser Water Elemental', EARTH_EL: 'Lesser Earth Elemental',
         GREATER: 'Greater Elemental', PET: "Xeen's Pet", LORD: 'Lord Xeen'}
LEVEL = {DEMON: 42, DEVIL: 50, SCREAMER: 58, GUARD: 60, FIRE_EL: 55, AIR_EL: 55, WATER_EL: 55, EARTH_EL: 55,
         GREATER: 70, PET: 75, LORD: 85}
SLAYER_SWORD = 12500
LORD_SEEN_QBIT = 111709     # A3's m35.lord_xeen_sight once bit (lord_xeen_seen)
# A3's M35 bits (quests/m35.yml) and the map's own block 118060-118079 (phase5_maps.md).
QBITS = {
    'started': 111700, 'gen_fire': 111701, 'gen_air': 111702, 'gen_earth': 111703, 'gen_water': 111704,
    'pet_slain': 111705, 'lord_xeen_slain': 111706, 'done': 111707, 'lord_xeen_seen': 111709,
    'machine_w_down': 118060, 'machine_e_down': 118061, 'barrier_down': 118062, 'bays_open': 118063,
}
X9_ENTRANCE = 'entrance:x9_gate'
Z = {0: 0, 1: 640, 2: 1280, 3: 1920}
SC = 1.25          # the base grid's scale


def R(x0, y0, x1, y1):
    return tuple(int(round(v * SC)) for v in (x0, y0, x1, y1))


def rect(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------------------------------------------------------------------------------------------------------------
# Textures: MM8 Escaton's Palace d35 (black stone, gold friezes, the gnecdr door pairs) with the Ancient kit's machine
# panels (MM6 swll4dk/swpnl/swtrpnl, Xeen's xaenergy and xafield) inset (graph `textures`, dungeon_families castles).
STONE = S('gnecwal1', 256, 256)          # black stone
FRIEZE = S('gnecwalt', 256, 256)         # black stone under the gold frieze (the top row of each wall)
FLOOR = S('gnecflr', 128, 128)           # gold-veined flags: halls
FLOOR2 = S('gtrlflr', 128, 128)          # black diamond flags: wards, galleries, stairs
CEIL = S('gnecclg2', 128, 256)           # pale vault
GOLD_H = S('gnectr2h', 128, 32)          # gold rail (a band along)
GOLD_V = S('gnectr2v', 32, 128)          # gold rail (a post up)
BLOCK = S('gnecstpv', 64, 128)           # rough stone: plinths, the dais's sides
STEPTOP = S('gnecstpf', 128, 32)         # a stone tread's top
MACH = S('swll4dk', 128, 256)            # Ancient panels: machine sides
MACH2 = S('swll5dk', 128, 256)           # Ancient panels with a red eye
PANEL = S('swpnl', 128, 256, fit=True)   # Ancient control panel (a band: laid once up a face)
SKULLP = S('swtrpnl', 128, 256, fit=True)
ENERGY = S('xaenergy', 128, 256)         # the conduits' energy panel: the generator cores, the pylons lit
FIELD = S('xafield', 128, 256, translucent=0.5)   # the barrier's field (D-51: half opacity, the crown stair behind)
HULL = S('xahullbn', 256, 256)           # riveted plate: the foundry's floor and the machines' tops
SHUTTER = S('swdoorc', 128, 256)         # Ancient shutter (door: tile)
DOOR1 = S('gnecdr2', 128, 256)           # the castle's single doors (a robed figure: door: tile)
SIGIL_DOOR = S('gnecdr3', 256, 256)      # the treasury's sigil door
WING_L, WING_R = S('gnecdr1l', 128, 256), S('gnecdr1r', 128, 256)     # the gate's and the great hall's leaves
THRONE_L, THRONE_R = S('gnecdr4l', 128, 256), S('gnecdr4r', 128, 256)  # the throne doors' studded leaves
GRAVEL = S('gtrlrf3', 128, 128)          # the earth generator's gravel bed
FROST = S('tws1h', 128, 128)             # (not used)
SKY = dict(CEIL, sky=True)
# D-51 3(c): the seven new textures (output/studio_cal/xd19/tex, xtex.py): the four generator cores (each core's
# faces, the picture once per face), Lord Xeen's sigil banner (the nave, over the gatehall's inner arch), the Sixth
# Mirror and its shattered frame (the dais's north wall; m35.done and the cinematic swap them).
CORES = {g: S(f'xcore{g}', 128, 256, fit=True) for g in ('fire', 'air', 'water', 'earth')}
BANNER = S('xsigilban', 128, 256, fit=True)
MIRROR6 = S('xmirror6', 256, 256, fit=True)
MIRROR6_GONE = 'xmirror6x'
DARK = S('gnecwal1', 256, 256)           # a pylon put out
WOOD = S('7trimd', 128, 256)             # beds' frames, the war table
SHEET = S('t2bedsht', 128, 256)

THEMES = [
    dict(id='theme:castle', wall=STONE, floor=FLOOR, ceiling=CEIL, reveal=STONE, door=DOOR1,
         notes="Castle Xeen's halls: black stone (MM8 gnecwal1) under a gold frieze (gnecwalt, the top row of every "
               "wall), gold-veined flags (gnecflr), a pale vault (gnecclg2); the robed-figure doors (gnecdr2)."),
    dict(id='theme:ward', wall=STONE, floor=FLOOR2, ceiling=CEIL, reveal=STONE, door=DOOR1,
         notes="Wards, galleries and stairs: the same black stone and frieze over black diamond flags (gtrlflr)."),
    dict(id='theme:works', wall=STONE, floor=HULL, ceiling=CEIL, reveal=STONE, door=DOOR1,
         notes="The machine rooms (the foundry, the generator vaults, the barrier hall): the castle's stone over "
               "riveted Ancient plate (xahullbn) underfoot."),
    dict(id='theme:sky', wall=STONE, floor=FLOOR2, ceiling=SKY, reveal=STONE, door=DOOR1,
         notes="Open to the sky (atmosphere.yml open_sky, X9's xeen_cloud_sea): the wall walks and the aviary."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms. Base-grid rectangles (scaled by R), the floor (0..3), the ceiling above the floor, the theme.
ROOMS = {}


def room(rid, name, base, floor, height, theme, lift=0, **extra):
    r = R(*base)
    ROOMS[rid] = dict(name=name, rect=r, outline=rect(r), floor=Z[floor] + lift, ceiling=Z[floor] + lift + height,
                      theme=theme, fl=floor, **extra)


def mirror_x(base):
    x0, y0, x1, y1 = base
    return (-x1, y0, -x0, y1)


TOWER_A = (-3328, -3840, -2688, -2304)    # C2 S: F0 stair hall, under the generator top
TOWER_B = (-4096, -3840, -3456, -2304)    # C1 S: F1 stair hall
# F0 (z 0)
room('gate', 'Gatehall', (-512, -3456, 512, -2304), 0, 768, 'castle')
room('nave', 'Hall of Xeendom', (-896, -2176, 896, -640), 0, 1152, 'castle')
room('aisle_w', 'Hall of Xeendom, west aisle', (-1536, -2176, -1024, -640), 0, 512, 'castle')
room('aisle_e', 'Hall of Xeendom, east aisle', mirror_x((-1536, -2176, -1024, -640)), 0, 512, 'castle')
room('ward_w', 'West ward', (-2560, -1664, -1664, -1152), 0, 512, 'ward')
room('ward_e', 'East ward', mirror_x((-2560, -1664, -1664, -1152)), 0, 512, 'ward')
room('barracks', 'Guard barracks', (-2560, -3328, -1664, -1792), 0, 512, 'ward')
room('armoury', 'Armoury', mirror_x((-2560, -3328, -1664, -1792)), 0, 512, 'ward')
room('gallery_w', 'West gallery', (-3328, -2176, -2688, -640), 0, 512, 'ward')
room('gallery_e', 'East gallery', mirror_x((-3328, -2176, -2688, -640)), 0, 512, 'ward')
room('tower0_w', 'South-west tower', TOWER_A, 0, 1152, 'ward', stair=('n', 'tower0_w'))
room('tower0_e', 'South-east tower', mirror_x(TOWER_A), 0, 1152, 'ward', stair=('n', 'tower0_e'))
room('vault_w', 'Cold vault', (-3328, -512, -1664, 1536), 0, 512, 'works')
room('vault_e', 'Gravel vault', mirror_x((-3328, -512, -1664, 1536)), 0, 512, 'works')
room('stair_hall', 'Stair hall', (-1536, -512, 1536, 1536), 0, 1152, 'castle', stair=('n', 'grand'))
# F1 (z 640)
room('tower1_w', 'South-west tower, upper stair', TOWER_B, 1, 1152, 'ward', stair=('s', 'tower1_w'))
room('tower1_e', 'South-east tower, upper stair', mirror_x(TOWER_B), 1, 1152, 'ward', stair=('s', 'tower1_e'))
room('wall_ws', 'West wall walk', (-4096, -2176, -3456, 256), 1, 768, 'sky')
room('turret_w', 'West turret', (-4096, 384, -3456, 1152), 1, 512, 'ward')
room('wall_wn', 'West wall walk, north', (-4096, 1280, -3456, 3584), 1, 768, 'sky')
room('wall_es', 'East wall walk', mirror_x((-4096, -2176, -3456, 256)), 1, 768, 'sky')
room('turret_e', 'East turret', mirror_x((-4096, 384, -3456, 1152)), 1, 512, 'ward')
room('wall_en', 'East wall walk, north', mirror_x((-4096, 1280, -3456, 3584)), 1, 768, 'sky')
room('grand_landing', 'Grand landing', (-1024, 1664, 1024, 2176), 1, 512, 'castle')
room('foundry', 'Guard foundry', (-1536, 2304, 1536, 3584), 1, 1152, 'works')
room('foundry_w', 'Guard foundry, west machine', (-3328, 1664, -1664, 3584), 1, 768, 'works')
room('foundry_e', 'Guard foundry, east machine', mirror_x((-3328, 1664, -1664, 3584)), 1, 768, 'works')
room('store', 'Parts store', (-2560, 640, -1664, 1536), 1, 512, 'ward', store=True)
room('keep_stair', 'Keep stair', mirror_x((-2560, -512, -1664, 1536)), 1, 1152, 'ward', stair=('s', 'keep'))
room('bays', 'Guard bays', (-1024, 3712, 1024, 4224), 1, 448, 'works')
# F2 (z 1280)
room('gen_fire', 'Fire generator', TOWER_A, 2, 704, 'works')
room('gen_air', 'Air generator', mirror_x(TOWER_A), 2, 704, 'works')
room('upper_w', 'Upper west gallery', (-2560, -3328, -1664, -640), 2, 512, 'ward')
room('upper_e', 'Upper east gallery', mirror_x((-2560, -3328, -1664, -640)), 2, 512, 'ward')
room('war_room', 'War room', (-2560, -512, -1664, 768), 2, 512, 'castle')
room('quarters', "Demons' quarters", mirror_x((-3328, -2176, -2688, -640)), 2, 512, 'castle')
room('barrier', 'Barrier hall', (-896, -2176, 896, -640), 2, 512, 'works')
room('barrier_w', 'Barrier hall, west bay', (-1536, -2176, -1024, -640), 2, 512, 'works')
room('barrier_e', 'Barrier hall, east bay', mirror_x((-1536, -2176, -1024, -640)), 2, 512, 'works')
room('upper_landing', 'Keep stair top', (-1536, -512, 1536, 512), 2, 512, 'castle')
room('crown_stair', 'Crown stair', (-512, -3840, 512, -2304), 2, 1152, 'castle', stair=('s', 'crown'))
# F3 (z 1920)
room('crown_landing', 'Crown landing', (-1536, -3840, -640, -2304), 3, 512, 'castle')
room('aviary_s', "Xeen's Aviary", (-1536, -2176, 1536, -1472), 3, 1536, 'sky')
room('aviary_n', "Xeen's Aviary, roost", (-1536, -1344, 1536, -640), 3, 1536, 'sky')
room('walk_s', "Keeper's walk", (-2560, -3840, -1664, -1536), 3, 384, 'ward')
room('walk_n', "Keeper's walk, north", (-2560, -1408, -1664, 128), 3, 384, 'ward')
room('loft', "Keeper's loft", mirror_x((-2560, -2176, -1664, -640)), 3, 576, 'ward')
room('threshold', 'Throne doors', (-1536, -512, 1536, 128), 3, 512, 'castle')
room('throne', 'Throne room', (-1536, 256, 1536, 2560), 3, 896, 'castle')
room('apse', "Lord Xeen's dais", (-1024, 2688, 1024, 3328), 3, 896, 'castle')
room('treasury', 'Treasury', (-768, 3456, 768, 4096), 3, 448, 'castle')

STAIR = {}   # rid -> dict(low side, gallery rect, flight)
RUN, GAL, FW = 800, 640, 320


def stair_layout(rid):
    """A two-storey stair hall: from its low end the floor, then a flight of 20 steps over RUN to a gallery GAL deep at
    the high end hanging 608 over the floor (its top one storey up)."""
    side, _ = ROOMS[rid]['stair']
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    cx = (x0 + x1) // 2
    w = FW if rid != 'stair_hall' else 512
    if side == 'n':     # high end north
        g = (x0, y1 - GAL, x1, y1)
        f_from, f_to = (cx, y1 - GAL - RUN), (cx, y1 - GAL)
    else:
        g = (x0, y0, x1, y0 + GAL)
        f_from, f_to = (cx, y0 + GAL + RUN), (cx, y0 + GAL)
    if rid == 'stair_hall':     # the grand stair's gallery: the stair's width and margins, the room's middle third
        g = (-640, g[1], 640, g[3])
    STAIR[rid] = dict(side=side, gallery=g, f_from=f_from, f_to=f_to, width=w,
                      top=ROOMS[rid]['floor'] + 640)


for _rid in [k for k, v in ROOMS.items() if 'stair' in v]:
    stair_layout(_rid)

# ---------------------------------------------------------------------------------------------------------------------
# Openings: by the facing walls of two rectangles (compass sides), `at` along the wall.
SIDE = {'south': 0, 'east': 1, 'north': 2, 'west': 3}
OPEN_AT = {}


def edges(rid):
    o = ROOMS[rid]['outline']
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def opening(oid, a, wa, b, wb, at=None, width=256, height=320, link=None, **kw):
    ia, ib = SIDE[wa], SIDE[wb]
    p0, p1 = edges(a)[ia]
    q0, q1 = edges(b)[ib]
    L = math.dist(p0, p1)
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    t = sorted([(q0[0] - p0[0]) * d[0] + (q0[1] - p0[1]) * d[1], (q1[0] - p0[0]) * d[0] + (q1[1] - p0[1]) * d[1]])
    lo, hi = max(0.0, t[0]), min(L, t[1])
    if hi - lo <= 0:
        raise SystemExit(f'{oid}: walls {wa}/{wb} of {a}/{b} share no stretch')
    tc = (lo + hi) / 2 if at is None else (((at - p0[0]) / d[0]) if abs(d[0]) > 0.5 else ((at - p0[1]) / d[1]))
    if tc - width / 2 < lo - 0.01 or tc + width / 2 > hi + 0.01:
        raise SystemExit(f'opening {oid} ({width} at {at}) does not fit the shared stretch {lo:.0f}..{hi:.0f}')
    gap = abs((q0[0] - p0[0]) * d[1] - (q0[1] - p0[1]) * d[0])
    if gap > 200:
        raise SystemExit(f'opening {oid}: walls {gap:.0f} apart')
    along = (tc - lo) / (hi - lo)
    o = {'id': f'open:{oid}', 'from': f'room:{a}', 'to': f'room:{b}', 'from_wall': ia, 'to_wall': ib}
    if link:
        o['link'] = link
    if round(along, 4) != 0.5:
        o['along'] = round(along, 4)
    o['width'] = width
    o['height'] = height
    o.update(kw)
    pt = (p0[0] + d[0] * tc, p0[1] + d[1] * tc)
    OPEN_AT[oid] = (pt, width, a, b, max(ROOMS[a]['floor'], ROOMS[b]['floor']) + kw.get('sill', 0))
    return o


OPENINGS = []


def add(*a, **kw):
    OPENINGS.append(opening(*a, **kw))


def mx(v):
    return -v


SC_ = lambda v: int(round(v * SC))   # noqa: E731

# F0
add('gate_nave', 'gate', 'north', 'nave', 'south', width=640, height=512, link='link:gate_hall',
    notes="The inner arch from the gatehall into the Hall of Xeendom, Lord Xeen's sigil over it.")
for s, k in (('w', 1), ('e', -1)):
    ais, wrd, gal, bar = f'aisle_{s}', f'ward_{s}', f'gallery_{s}', ('barracks' if s == 'w' else 'armoury')
    inner, outer = ('west', 'east') if s == 'w' else ('east', 'west')
    for i, y in enumerate((-2400, -1760, -1120), 1):
        add(f'arcade0_{s}{i}', 'nave', inner, ais, outer, at=y, width=320, height=448,
            notes="An arch of the arcade between the nave and its aisle.")
    add(f'{ais}_{wrd}', ais, inner, wrd, outer, at=-1760, width=320, height=384, link=f'link:hall_{s}w',
        notes="The aisle opens on the ward.")
    add(f'{wrd}_{bar}', wrd, 'south', bar, 'north', at=k * -2640, width=192, height=320, link=f'link:{wrd}_{bar}')
    add(f'{wrd}_{gal}', wrd, inner, gal, outer, at=-1760, width=320, height=384, link=f'link:{wrd}_{gal}')
    add(f'{gal}_tower0', gal, 'south', f'tower0_{s}', 'north', width=384, height=384, link=f'link:{gal}_tower0',
        notes="The gallery runs into the tower's foot, under its gallery.")
    add(f'{gal}_vault', gal, 'north', f'vault_{s}', 'south', width=192, height=320, link=f'link:{gal}_vault')
    add(f'vault_{s}_stair', f'vault_{s}', outer, 'stair_hall', inner, at=0, width=192, height=320,
        link=f'link:vault_{s}_stair')
add('nave_stair', 'nave', 'north', 'stair_hall', 'south', width=512, height=448, link='link:hall_stair',
    notes="The great hall's north doors (two leaves) into the stair hall.")
add('stair_top', 'stair_hall', 'north', 'grand_landing', 'south', width=512, height=384, link='link:grand_up',
    notes="The head of the grand stair: its gallery opens north onto the grand landing.")
# The towers: tower0 (F0) gallery -> tower1 (F1) foot; tower1 gallery -> the generator top (F2); tower1 foot -> walk.
for s in ('w', 'e'):
    inner, outer = ('east', 'west') if s == 'w' else ('west', 'east')
    t0, t1 = f'tower0_{s}', f'tower1_{s}'
    add(f'{t0}_top', t0, outer, t1, inner, at=-3120, width=256, height=384, link=f'link:{s}_tower_up',
        notes="The head of the tower's first stair: its gallery opens on the upper stair's foot.")
    gen = 'gen_fire' if s == 'w' else 'gen_air'
    add(f'{t1}_top', t1, inner, gen, outer, at=-4480, width=256, height=384, link=f'link:{s}_tower_top',
        notes="The head of the upper stair: its gallery opens on the tower top.")
    add(f'{t1}_walk', t1, 'north', f'wall_{s}s', 'south', width=320, height=384, link=f'link:{s}_tower_walk')
    add(f'wall_{s}s_turret', f'wall_{s}s', 'north', f'turret_{s}', 'south', width=320, height=384)
    add(f'turret_{s}_wall', f'turret_{s}', 'north', f'wall_{s}n', 'south', width=320, height=384)
    fd = f'foundry_{s}'
    add(f'wall_{s}n_{fd}', f'wall_{s}n', inner, fd, outer, at=3200, width=256, height=384,
        link=f'link:{s}_wall_foundry', notes="The keep's door from the wall walk.")
    add(f'{fd}_arcade', fd, inner, 'foundry', outer, at=3680, width=640, height=640,
        notes="The wide arch between the machine bay and the foundry's floor.")
add('landing_foundry', 'grand_landing', 'north', 'foundry', 'south', width=640, height=448, link='link:foundry_landing')
add('store_door', 'store', 'north', 'foundry_w', 'south', width=192, height=320, link='link:foundry_store')
add('bays_shutter', 'foundry', 'north', 'bays', 'south', width=512, height=320, link='link:foundry_bays',
    notes="The guard bays' shutters.")
add('keep_foot', 'keep_stair', 'north', 'foundry_e', 'south', width=320, height=384, link='link:keep_up',
    notes="The keep stair's foot off the east machine bay.")
add('keep_top', 'keep_stair', 'west', 'upper_landing', 'east', at=-320, width=320, height=384, link='link:keep_up_top',
    notes="The head of the keep stair: its gallery opens west onto the keep stair top.")
# F2
for s in ('w', 'e'):
    inner, outer = ('east', 'west') if s == 'w' else ('west', 'east')
    gen = 'gen_fire' if s == 'w' else 'gen_air'
    add(f'upper_{s}_{gen}', f'upper_{s}', outer, gen, inner, at=-3520, width=192, height=320,
        link=f'link:upper_{s}_gen')
    add(f'upper_{s}_barrier', f'upper_{s}', inner, f'barrier_{s}', outer, at=-1760, width=320, height=384,
        link=f'link:barrier_{s}u')
    for i, y in enumerate((-2400, -1760, -1120), 1):
        add(f'arcade2_{s}{i}', 'barrier', 'west' if s == 'w' else 'east', f'barrier_{s}', 'east' if s == 'w' else 'west',
            at=y, width=320, height=448, notes="An arch between the barrier hall and its bay.")
add('upper_w_war', 'upper_w', 'north', 'war_room', 'south', width=192, height=320, link='link:upper_w_war')
add('upper_e_quarters', 'upper_e', 'east', 'quarters', 'west', at=-1760, width=192, height=320,
    link='link:upper_e_quarters')
add('landing_barrier', 'upper_landing', 'south', 'barrier', 'north', width=640, height=448, link='link:landing_barrier')
add('field', 'barrier', 'south', 'crown_stair', 'north', width=384, height=448, link='link:barrier_crown',
    notes="The field across the crown stair's foot (xafield), held by the four pylons.")
add('crown_top', 'crown_stair', 'west', 'crown_landing', 'east', at=-4480, width=256, height=384, link='link:crown_up',
    notes="The head of the crown stair: its gallery opens west onto the crown landing.")
# F3
add('arch_s', 'crown_landing', 'north', 'aviary_s', 'south', at=-1360, width=320, height=256, link='link:landing_aviary',
    notes="The low arch (256 high, D-32) into the aviary: Xeen's Pet cannot pass it.")
add('aviary_mid', 'aviary_s', 'north', 'aviary_n', 'south', width=2560, height=1280,
    notes="The aviary's middle: the roost's ledge line, open to the sky above.")
add('arch_n', 'aviary_n', 'north', 'threshold', 'south', width=320, height=256, link='link:aviary_threshold',
    notes="The second low arch (256 high, D-32), onto the throne doors.")
add('landing_walk', 'crown_landing', 'west', 'walk_s', 'east', at=-4000, width=192, height=320, link='link:landing_kw')
add('walk_mid', 'walk_s', 'north', 'walk_n', 'south', width=320, height=320)
add('walk_threshold', 'walk_n', 'east', 'threshold', 'west', at=-240, width=192, height=320, link='link:kw_threshold')
add('aviary_loft', 'aviary_s', 'east', 'loft', 'west', at=-2280, width=256, height=320, link='link:aviary_loft',
    notes="The keeper's way up to the loft: a low door (Xeen's Pet cannot pass it).")
add('throne_doors', 'threshold', 'north', 'throne', 'south', width=512, height=448, link='link:threshold_throne',
    notes="The throne doors: two studded leaves (gnecdr4l/gnecdr4r).")
add('throne_apse', 'throne', 'north', 'apse', 'south', width=1600, height=704,
    notes="The arch over the dais at the throne room's end.")
add('apse_treasury', 'apse', 'north', 'treasury', 'south', at=768, width=256, height=320, link='link:throne_treasury',
    notes="The hoard door behind the dais (Lord Xeen's sigil, gnecdr3).")

# ---------------------------------------------------------------------------------------------------------------------
# Platforms, levels, flights


def block(at, size, rise, surface, top=None, notes=None, pid=None, base=None, end=None, bottom=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d['at'] = F(*at)
    d['size'] = F(*size)
    d['rise'] = rise
    d['surface'] = surface
    if end:
        d['end_surface'] = end
    if top:
        d['top_surface'] = top
    if bottom:
        d['bottom_surface'] = bottom
    if base is not None:
        d['base'] = base
    if notes:
        d['notes'] = notes
    return d


PLATFORMS = {}
FLIGHTS = {}
LEVELS = {}
for rid, st in STAIR.items():
    gx0, gy0, gx1, gy1 = st['gallery']
    PLATFORMS.setdefault(rid, Flow()).append(FlowDict(
        id=f'platform:head_{rid}', outline=Flow([F(gx0, gy0), F(gx1, gy0), F(gx1, gy1), F(gx0, gy1)]), rise=32,
        surface=STONE, top_surface=FLOOR2, bottom_surface=CEIL, base=608,
        notes=f"The head of the stair at {st['top']}: a gallery {gy1 - gy0} deep across the {st['side']} end."))
    FLIGHTS[rid] = Flow([FlowDict(**{'from': F(*st['f_from']), 'to': F(*st['f_to']), 'to_height': st['top'],
                                     'width': st['width'], 'steps': 20,
                                     'notes': f"Twenty steps of 32 over {RUN}, rising {st['side']}."})])


def cen(rid):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return ((x0 + x1) // 2, (y0 + y1) // 2)


def P(rid, *items):
    PLATFORMS.setdefault(rid, Flow()).extend(items)


# Generators: a core column (the destructible, clicked) between two Ancient housings, against the room's far wall.
GENS = {
    'fire': dict(room='gen_fire', where='the south-west tower', title='Fire Generator', color=(255, 120, 40),
                 line='Fire Generator.  Destroy?', ref='aaze0075:1', el=FIRE_EL),
    'air': dict(room='gen_air', where='the south-east tower', title='Air Generator', color=(190, 170, 255),
                line='Air Generator.  Destroy?', ref='aaze0075:2 (Electricity)', el=AIR_EL),
    'water': dict(room='vault_w', where='the cold vault', title='Water Generator', color=(110, 200, 255),
                  line='Water Generator.  Destroy?', ref='aaze0075:3 (Cold)', el=WATER_EL),
    'earth': dict(room='vault_e', where='the gravel vault', title='Earth Generator', color=(130, 220, 90),
                  line='Earth Generator.  Destroy?', ref='aaze0075:4 (Poison)', el=EARTH_EL),
}
for g, d in GENS.items():
    rid = d['room']
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    if rid.startswith('gen_'):      # tower tops: the core at the south end, the doors are north/west/east
        cx, cy = (x0 + x1) // 2, y0 + 224
        hx = ((cx - 224, cy), (cx + 224, cy))
        hs = (128, 192)
    else:                          # the vaults: the core against the north wall
        cx, cy = (x0 + x1) // 2, y1 - 224
        hx = ((cx - 256, cy), (cx + 256, cy))
        hs = (160, 192)
    d['core'] = (cx, cy)
    d['front'] = 1 if rid.startswith('gen_') else -1
    P(rid,
      block((cx, cy), (192, 192), 448, CORES[g], HULL, f"The {d['title']}'s core: an Ancient column round the "
            f"{g} core (xcore{g}; the destructible: its click asks '{d['line']}').", pid=f'platform:gen_{g}'),
      block(hx[0], hs, 384, PANEL, HULL, "An Ancient housing beside the core: dials, a red lamp.", end=MACH),
      block(hx[1], hs, 384, PANEL, HULL, "An Ancient housing beside the core.", end=MACH))
    if g == 'earth':
        LEVELS.setdefault(rid, Flow()).append(FlowDict(
            id='level:gravel', outline=Flow([F(cx - 480, cy - 448), F(cx + 480, cy - 448), F(cx + 480, cy - 208),
                                             F(cx - 480, cy - 208)]),
            floor=ROOMS[rid]['floor'] + 16, surface=GRAVEL, notes="The gravel bed the core grinds."))

# Pylons in the barrier hall: four pillars along the field's wall, two each side of it (fire/air south-west and
# south-east, water/earth north-west and north-east: each nearest its generator).
bx0, by0, bx1, by1 = ROOMS['barrier']['rect']
PYLONS = {'fire': (bx0 + 224, by0 + 400), 'air': (bx1 - 224, by0 + 400),
          'water': (bx0 + 224, by1 - 400), 'earth': (bx1 - 224, by1 - 400)}
for g, at in PYLONS.items():
    P('barrier', block(at, (128, 128), 448, ENERGY, HULL,
                       f"The {g} pylon: its conduit runs to {GENS[g]['where']} (dark when its generator falls).",
                       pid=f'platform:pylon_{g}'))

# The guard-making machines: one against the outer wall of each machine bay, its output chute beside it.
MACHINES = {}
for s in ('w', 'e'):
    rid = f'foundry_{s}'
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    wx = x0 + 208 if s == 'w' else x1 - 208
    MACHINES[s] = dict(room=rid, at=(wx, 3360), chute=(wx + (288 if s == 'w' else -288), 3360 - 352))
    P(rid,
      block((wx, 3360), (320, 704), 512, MACH2, HULL, "A guard-making machine: Ancient panels round a press that "
            "stamps out Xeen's Guards (the destructible: 'Guard Making Machine.  Destroy?', aaze0075:0).",
            pid=f'platform:machine_{s}', end=SKULLP),
      block((wx + (240 if s == 'w' else -240), 3360 + 192), (160, 192), 96, HULL, HULL,
            "The machine's output chute: a low plate where the finished guards step off."))
# The foundry's slow line: a long low bench of chrome plates down the middle.
P('foundry', block((0, 3360), (1600, 192), 64, HULL, HULL, "The slow line: chrome plates waiting to be stamped."))
# The guard bays: racks along the back wall, the gem tray.
bx0, by0, bx1, by1 = ROOMS['bays']['rect']
P('bays', block((-640, by1 - 64), (448, 96), 256, MACH, HULL, "An empty rack where finished guards stood."),
  block((640, by1 - 64), (448, 96), 256, MACH, HULL, "An empty rack."),
  block((0, by1 - 64), (256, 96), 96, MACH, HULL, "The tray of spare gem eyes.", pid='platform:gems'))
# The war room's table; the demons' quarters' beds; the loft's raised back and buckets.
wx0, wy0, wx1, wy1 = ROOMS['war_room']['rect']
P('war_room', block(((wx0 + wx1) // 2, (wy0 + wy1) // 2 + 160), (448, 320), 80, WOOD, WOOD,
                    "The war table: a map of both faces of Xeen, armies marked in Lord Xeen's hand.",
                    pid='platform:war_table'))
qx0, qy0, qx1, qy1 = ROOMS['quarters']['rect']
P('quarters', *[block((qx1 - 120, y), (192, 384), 48, WOOD, SHEET, "An iron bed (for a demon).",
                      pid=f'platform:bed_{i}') for i, y in enumerate((-2400, -1920, -1440, -1200), 1)][:3])
lx0, ly0, lx1, ly1 = ROOMS['loft']['rect']
LEVELS['loft'] = Flow([FlowDict(id='level:loft_back', outline=Flow([F(lx1 - 448, ly0 + 64), F(lx1 - 64, ly0 + 64),
                                                                    F(lx1 - 64, ly1 - 64), F(lx1 - 448, ly1 - 64)]),
                                floor=Z[3] + 192, surface=FLOOR2,
                                notes="The keeper's loft proper, up six steps off the aviary's level.")])
FLIGHTS['loft'] = Flow([FlowDict(**{'from': F(lx1 - 448 - 256, (ly0 + ly1) // 2), 'to': F(lx1 - 448, (ly0 + ly1) // 2),
                                    'width': 256, 'steps': 6, 'notes': "Six steps up to the loft."})])
# The throne room: the dais in the apse (the throne on it, the Sixth Mirror behind against the north wall).
ax0, ay0, ax1, ay1 = ROOMS['apse']['rect']
LEVELS['apse'] = Flow([FlowDict(id='level:dais', outline=Flow([F(ax0 + 128, ay0 + 256), F(ax1 - 128, ay0 + 256),
                                                               F(ax1 - 128, ay1 - 160), F(ax0 + 128, ay1 - 160)]),
                                floor=Z[3] + 64, surface=FLOOR,
                                notes="The black dais (two steps up).")])
FLIGHTS['apse'] = Flow([FlowDict(**{'from': F(0, ay0 + 160), 'to': F(0, ay0 + 256), 'width': 768, 'steps': 2,
                                    'notes': "Two broad steps up the dais."})])
THRONE_AT = (0, ay1 - 288)
MIRROR_AT = (0, ay1 - 112)
P('apse',
  block(THRONE_AT, (256, 192), 192, BLOCK, STEPTOP, "Lord Xeen's throne of black stone; the Scepter of Temporal "
        "Distortion across its arms.", pid='platform:throne'))

# The nave's columns (pillars stand clear of the arcade's arches).
PILLARS = {'nave': Flow([FlowDict(at=F(x, y), size=F(128, 128), surface=S('gnecwal2', 128, 256))
                         for x in (-736, 736) for y in (-2080, -1440)]),
           'throne': Flow([FlowDict(at=F(x, y), size=F(128, 128), surface=STONE)
                           for x in (-1280, 1280) for y in (1120, 2240)])}

# The wall walks' outer sides (D-97): sky above a parapet this high.
WALK_OUTER = {'wall_ws': 'west', 'wall_wn': 'west', 'wall_es': 'east', 'wall_en': 'east'}
WALK_PARAPET = 160

AMBIENT = {'nave': 22, 'stair_hall': 20, 'aviary_s': 28, 'aviary_n': 28, 'wall_ws': 28, 'wall_wn': 28,
           'wall_es': 28, 'wall_en': 28, 'throne': 14, 'apse': 14, 'treasury': 12, 'bays': 12}

ROOM_NOTES = {
    'gate': "Behind the gate's two leaves (the way out to X9): the arrival entrance:x9_gate, quiet; the inner "
            "arch north into the great hall.",
    'nave': "The Hall of Xeendom: black pillars under the gold frieze, the arcades to its two aisles, the two-leaf "
            "north doors to the stair hall.",
    'aisle_w': "The west aisle behind the arcade; the west ward opens off it.",
    'aisle_e': "The east aisle behind the arcade; the east ward opens off it.",
    'ward_w': "A vaulted passage from the hall to the west gallery and the barracks.",
    'ward_e': "A vaulted passage from the hall to the east gallery and the armoury.",
    'barracks': "A dead end: racks where finished guards stand powered down; the chest.",
    'armoury': "A dead end: weapon racks, the guards' spare gem eyes in a case; the chest.",
    'gallery_w': "Along the west wall from the south-west tower to the cold vault.",
    'gallery_e': "Along the east wall from the south-east tower to the gravel vault.",
    'tower0_w': "The south-west tower's first stair: twenty steps north to its gallery, which opens west on the upper "
                "stair.",
    'tower0_e': "The south-east tower's first stair.",
    'vault_w': "The cold vault: the Water Generator (the source's Cold Generator) against the north wall, its two "
               "elementals; doors to the west gallery and the stair hall.",
    'vault_e': "The gravel vault: the Earth Generator (the source's Poison Generator) over its gravel bed, its two "
               "elementals.",
    'stair_hall': "Behind the great hall's north doors: the grand stair up to the grand landing; doors west and east "
                  "into the two generator vaults.",
    'tower1_w': "The south-west tower's upper stair: from the west wall walk's door south up to the tower top.",
    'tower1_e': "The south-east tower's upper stair.",
    'wall_ws': "The west wall walk under open sky, from the tower to the turret: the outer parapet over X9's cloud sea.",
    'turret_w': "A roofed turret on the west wall.",
    'wall_wn': "The west wall walk's north stretch, to the keep's west door; open sky over the outer parapet.",
    'wall_es': "The east wall walk under open sky, the outer parapet over X9's cloud sea.",
    'turret_e': "A roofed turret on the east wall.",
    'wall_en': "The east wall walk's north stretch, to the keep's east door; open sky over the outer parapet.",
    'grand_landing': "The grand stair's top, opening on the foundry floor.",
    'foundry': "The guard foundry's floor: the slow line of chrome plates, the shutters of the guard bays in the north "
               "wall; the machine bays west and east through wide arches.",
    'foundry_w': "The west machine bay: a guard-making machine against the outer wall stamping, its chute, the "
                 "keep's west door; the parts store's door.",
    'foundry_e': "The east machine bay: the second machine, the keep's east door, the keep stair's foot.",
    'store': "A dead end with a chest: crates of plates and gems, a storeroom.",
    'keep_stair': "From the east machine bay the keep stair climbs south to the keep stair top.",
    'bays': "Behind the shutters: empty racks and the tray of spare gem eyes.",
    'gen_fire': "The south-west tower top: the Fire Generator roaring, two fire elementals.",
    'gen_air': "The south-east tower top: the Air Generator, arcs between its coils, two air elementals.",
    'upper_w': "From the barrier hall to the fire tower and the war room.",
    'upper_e': "From the barrier hall to the air tower and the demons' quarters.",
    'war_room': "A dead end with a chest: the war table, Lord Xeen's orders.",
    'quarters': "A dead end with a chest: iron beds, braziers.",
    'barrier': "The barrier hall: four pylons along its south wall feed the field across the crown stair; two Greater "
               "Elementals ward it.",
    'barrier_w': "The barrier hall's west bay behind its arcade.",
    'barrier_e': "The barrier hall's east bay behind its arcade.",
    'upper_landing': "The keep stair arrives here, before the barrier hall.",
    'crown_stair': "Behind the field: twenty steps south up to the crown.",
    'crown_landing': "The quiet first room past the barrier: the low arch into the aviary, the door to the keeper's "
                     "walk.",
    'aviary_s': "Xeen's Aviary under the open sky: black stone ledges, gnawed bones; the loft's low door.",
    'aviary_n': "The aviary's roost: Xeen's Pet; the second low arch to the throne doors.",
    'walk_s': "A low gallery round the aviary's west side: the way round the Pet.",
    'walk_n': "The keeper's walk's north stretch, to the throne doors.",
    'loft': "Up six steps off the aviary: feed buckets, chains, the keeper's strongbox.",
    'threshold': "The antechamber before the two-leaf throne doors. Quiet.",
    'throne': "The throne room: black columns, braziers, the dais at the far end lit; the step plate inside the doors.",
    'apse': "Lord Xeen's dais: the throne, the Sixth Mirror behind it in its force field, the hoard door in the "
            "north wall.",
    'treasury': "The hoard, behind the dais (opened by Lord Xeen's death).",
}


def wall_bands(rid):
    h = ROOMS[rid]['ceiling'] - ROOMS[rid]['floor']
    if h < 384:
        return None
    return Flow([FlowDict(height=h - 256, surface=STONE)])


def rooms_yml():
    rooms = []
    for rid, r in ROOMS.items():
        d = {'id': f'room:{rid}', 'name': r['name'], 'outline': Flow([F(*p) for p in r['outline']]),
             'floor': r['floor'], 'ceiling': r['ceiling'], 'theme': f"theme:{r['theme']}"}
        if r.get('store'):
            d['store'] = True
        b = wall_bands(rid)
        if b and r['theme'] != 'sky':
            d['bands'] = b
            d['walls'] = [{'wall': w, 'surface': FRIEZE} for w in ('north', 'east', 'south', 'west')]
        if rid in WALK_OUTER:
            # D-97 (F21, the user 2026-11-22: "I don't see the roof"): a wall walk opens on its outer side, sky over a
            # parapet (the outer wall stays solid and draws as sky, XD-22's moon gallery); walls 768 high on both sides
            # read as a corridor with its roof missing.
            side = WALK_OUTER[rid]
            x0, y0, x1, y1 = r['rect']
            x = x0 + 32 if side == 'west' else x1 - 32
            d['walls'] = [FlowDict(wall=side, surface=dict(STONE, sky=True), bands=False)]
            # F60 (the player's pins 2026-11-25, XD-14's slots): the parapet runs from end wall to end wall; 32
            # short of each it left a slot of sky from the floor up (tools/xeen/check_parapet_gaps.py).
            d['parapets'] = [FlowDict(path=Flow([F(x, y0), F(x, y1)]), height=WALK_PARAPET, thickness=32,
                                      surface=STONE,
                                      notes="The outer parapet: the cloud sea and X9's sky beyond it (D-97).")]
        if rid in PILLARS:
            d['pillars'] = PILLARS[rid]
        if rid in PLATFORMS:
            d['platforms'] = PLATFORMS[rid]
        if rid in LEVELS:
            d['levels'] = LEVELS[rid]
        if rid in FLIGHTS:
            d['flights'] = FLIGHTS[rid]
        d['ambient'] = AMBIENT.get(rid, 18)
        d['notes'] = ROOM_NOTES[rid]
        rooms.append(d)
    return {'format': 0, 'themes': THEMES, 'defaults': FlowDict(theme='theme:castle', ambient=18), 'rooms': rooms,
            'openings': OPENINGS,
            'notes': "XD-19 Castle Xeen at L4: four floors 640 apart (x east, y north). F0 the lower castle (gatehall, "
                     "great hall and aisles, wards, barracks, armoury, galleries, the cold and gravel vaults, the "
                     "stair hall, the towers' first stairs); F1 the wall walks under open sky, the guard foundry, the "
                     "parts store, the guard bays, the keep stair; F2 the tower tops (fire and air generators), the "
                     "upper galleries, the war room, the demons' quarters, the barrier hall, the crown stair; F3 the "
                     "crown: the crown landing, the aviary (open sky), the keeper's walk and loft, the throne doors, "
                     "the throne room and dais, the treasury. Written by output/studio_cal/xd19/tools/gen.py."}


# ---------------------------------------------------------------------------------------------------------------------
# objects.yml
# Placed monsters: room -> group, [(row, (x, y), facing)]; 96 (D-47 Q16's 70, D-98's +26) + Xeen's Pet + Lord Xeen.
# Lord Xeen and his six guards come first: their actor indices 0-6 (the scene keeps this order).
# D-98 (the user 2026-11-22: more monsters, at least 4-6 throne guards): about a third more, the same mix and band,
# in the rooms that stood empty (aisles, north wall walks, keep stair, barrier bays, landings, crown stair).


def at_in(rid, fx, fy):
    """A point at fractions (0..1) of a rectangle room."""
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return (int(x0 + (x1 - x0) * fx), int(y0 + (y1 - y0) * fy))


LORD_AT = (0, ay0 + 128 + 576)
PLACED = [
    ('apse', 60, [(LORD, (THRONE_AT[0], THRONE_AT[1] - 176), 270)], True),
    # D-98: six royal guards in two ranks flanking the way up to the dais, freed with Lord Xeen (evt:sight_clock).
    ('throne', 61, [(GUARD, (x, y), 270) for y in (2880, 2496, 2112) for x in (-480, 480)], True),
    ('aviary_n', 62, [(PET, (0, -1280), 270)], False),
    # F0 (27 + 7)
    # D-130 (2026-11-24): out of sight of the gate's landing (0, -4064) (hide.py's spots, the same nave).
    ('nave', 10, [(DEMON, (-608, -1760), 270), (DEMON, (544, -1824), 270), (DEMON, (-704, -1280), 270),
                  (DEVIL, (-448, -2240), 90), (DEVIL, (-512, -1952), 270)], False),
    ('aisle_w', 70, [(DEMON, at_in('aisle_w', 0.5, 0.3), 0), (DEMON, at_in('aisle_w', 0.5, 0.7), 0)], False),
    ('aisle_e', 71, [(DEMON, at_in('aisle_e', 0.5, 0.3), 180), (DEMON, at_in('aisle_e', 0.5, 0.7), 180)], False),
    ('ward_w', 11, [(DEMON, at_in('ward_w', 0.3, 0.5), 0), (DEMON, at_in('ward_w', 0.6, 0.5), 0)], False),
    ('ward_e', 12, [(DEMON, at_in('ward_e', 0.4, 0.5), 180), (DEMON, at_in('ward_e', 0.7, 0.5), 180)], False),
    ('barracks', 13, [(GUARD, at_in('barracks', 0.3, 0.3), 90), (GUARD, at_in('barracks', 0.7, 0.3), 90),
                      (GUARD, at_in('barracks', 0.5, 0.6), 90)], False),
    ('armoury', 14, [(GUARD, at_in('armoury', 0.3, 0.35), 90), (GUARD, at_in('armoury', 0.7, 0.35), 90),
                     (DEVIL, at_in('armoury', 0.5, 0.6), 90)], False),
    ('gallery_w', 15, [(DEMON, at_in('gallery_w', 0.5, 0.25), 90), (DEMON, at_in('gallery_w', 0.5, 0.75), 270),
                       (DEVIL, at_in('gallery_w', 0.5, 0.5), 90)], False),
    ('gallery_e', 16, [(DEMON, at_in('gallery_e', 0.5, 0.25), 90), (DEMON, at_in('gallery_e', 0.5, 0.75), 270),
                       (DEVIL, at_in('gallery_e', 0.5, 0.5), 90)], False),
    ('vault_w', 17, [(WATER_EL, at_in('vault_w', 0.35, 0.45), 270), (WATER_EL, at_in('vault_w', 0.65, 0.45), 270)],
     False),
    ('vault_e', 18, [(EARTH_EL, at_in('vault_e', 0.35, 0.45), 270), (EARTH_EL, at_in('vault_e', 0.65, 0.45), 270)],
     False),
    ('stair_hall', 19, [(DEMON, (-1280, 0), 270), (DEMON, (1280, 0), 270), (SCREAMER, (-1280, 800), 270),
                        (GUARD, (1280, 800), 270), (DEVIL, (0, -320), 270)], False),
    # F1 (16 + 6)
    ('wall_ws', 20, [(DEMON, at_in('wall_ws', 0.5, 0.3), 90), (DEMON, at_in('wall_ws', 0.5, 0.6), 90),
                     (DEVIL, at_in('wall_ws', 0.5, 0.85), 270)], False),
    ('foundry', 21, [(GUARD, (-960, 3040), 270), (GUARD, (960, 3040), 270), (GUARD, (0, 3840), 270),
                     (DEVIL, (0, 2960), 270)], False),
    ('store', 22, [(DEMON, at_in('store', 0.35, 0.4), 270), (DEMON, at_in('store', 0.65, 0.4), 270)], False),
    ('wall_es', 23, [(DEMON, at_in('wall_es', 0.5, 0.3), 90), (DEMON, at_in('wall_es', 0.5, 0.6), 90),
                     (DEVIL, at_in('wall_es', 0.5, 0.85), 270)], False),
    ('wall_wn', 72, [(DEMON, at_in('wall_wn', 0.5, 0.35), 270), (DEVIL, at_in('wall_wn', 0.5, 0.7), 270)], False),
    ('wall_en', 73, [(DEMON, at_in('wall_en', 0.5, 0.35), 270), (DEVIL, at_in('wall_en', 0.5, 0.7), 270)], False),
    ('keep_stair', 74, [(DEMON, at_in('keep_stair', 0.3, 0.85), 270), (DEMON, at_in('keep_stair', 0.7, 0.85), 270)],
     False),
    # F2 (19 + 8)
    ('gen_fire', 30, [(FIRE_EL, at_in('gen_fire', 0.3, 0.6), 270), (FIRE_EL, at_in('gen_fire', 0.7, 0.6), 270)],
     False),
    ('gen_air', 31, [(AIR_EL, at_in('gen_air', 0.3, 0.6), 270), (AIR_EL, at_in('gen_air', 0.7, 0.6), 270)], False),
    ('upper_w', 32, [(DEMON, at_in('upper_w', 0.5, 0.3), 90), (DEMON, at_in('upper_w', 0.5, 0.75), 90),
                     (DEVIL, at_in('upper_w', 0.5, 0.5), 90)], False),
    ('upper_e', 33, [(DEMON, at_in('upper_e', 0.5, 0.3), 90), (DEMON, at_in('upper_e', 0.5, 0.75), 90),
                     (DEVIL, at_in('upper_e', 0.5, 0.5), 90)], False),
    ('war_room', 34, [(DEVIL, at_in('war_room', 0.3, 0.3), 90), (DEVIL, at_in('war_room', 0.7, 0.3), 90),
                      (SCREAMER, at_in('war_room', 0.5, 0.85), 270)], False),
    ('quarters', 35, [(DEMON, at_in('quarters', 0.3, 0.2), 90), (DEMON, at_in('quarters', 0.3, 0.5), 90),
                      (DEMON, at_in('quarters', 0.3, 0.8), 90), (SCREAMER, at_in('quarters', 0.5, 0.95), 270)], False),
    ('barrier', 36, [(GREATER, (-480, -1600), 270), (GREATER, (480, -1600), 270)], False),
    ('barrier_w', 75, [(DEVIL, at_in('barrier_w', 0.5, 0.5), 0)], False),
    ('barrier_e', 76, [(DEVIL, at_in('barrier_e', 0.5, 0.5), 180)], False),
    ('upper_landing', 77, [(DEMON, at_in('upper_landing', 0.2, 0.5), 270),
                           (DEMON, at_in('upper_landing', 0.8, 0.5), 270)], False),
    ('crown_stair', 78, [(SCREAMER, at_in('crown_stair', 0.25, 0.9), 270), (DEVIL, at_in('crown_stair', 0.75, 0.9), 270)],
     False),
    # F3 (8 + 1 + 2; the throne's 6 above)
    ('walk_s', 50, [(DEVIL, at_in('walk_s', 0.5, 0.4), 90), (DEVIL, at_in('walk_s', 0.5, 0.8), 90)], False),
    ('walk_n', 51, [(SCREAMER, at_in('walk_n', 0.5, 0.5), 270), (DEVIL, at_in('walk_n', 0.5, 0.2), 90)], False),
    ('crown_landing', 79, [(GUARD, at_in('crown_landing', 0.5, 0.35), 90), (GUARD, at_in('crown_landing', 0.5, 0.65), 90)],
     False),
    ('loft', 52, [(DEMON, at_in('loft', 0.82, 0.3), 180), (DEMON, at_in('loft', 0.82, 0.7), 180),
                  (DEVIL, at_in('loft', 0.82, 0.5), 180)], False),
]
# The foundry's hidden pool (D-47 Q7): four guards at the two machines' output chutes, one group each (41-44), shown
# one by one by the 45 s timer while a machine stands, the rest at once when both have fallen.
POOL = []
for i, (s, dy) in enumerate((('w', 0), ('e', 0), ('w', -288), ('e', -288)), 1):
    cx, cy = MACHINES[s]['chute']
    POOL.append((f'pool_{i}', f'foundry_{s}', 40 + i, (cx, cy + dy)))

START = (0, -4064)


def on_wall(rid, at, inset=12):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    x, y = at
    side = min((x - x0, 'w'), (x1 - x, 'e'), (y - y0, 's'), (y1 - y, 'n'))[1]
    return {'w': (x0 + inset, y), 'e': (x1 - inset, y), 's': (x, y0 + inset), 'n': (x, y1 - inset)}[side], side


def sconce_spots(rid, count):
    """Wall points of a rectangle room clear of its openings (their half width + 160) and of stair flights/galleries
    (the sconce sits at 176 over the room's own floor)."""
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    cands = []
    for f in (0.25, 0.75, 0.5):
        cands += [((x0, int(y0 + (y1 - y0) * f)), 'w'), ((x1, int(y0 + (y1 - y0) * f)), 'e'),
                  ((int(x0 + (x1 - x0) * f), y0), 's'), ((int(x0 + (x1 - x0) * f), y1), 'n')]
    out = []
    for (x, y), side in cands:
        ok = True
        for oid, (pt, width, a, b, z) in OPEN_AT.items():
            if rid not in (a, b):
                continue
            if math.dist((x, y), pt) < width / 2 + 192:
                ok = False
        st = STAIR.get(rid)
        if st:
            gx0, gy0, gx1, gy1 = st['gallery']
            if gy0 - 64 <= y <= gy1 + 64 and gx0 - 64 <= x <= gx1 + 64:
                ok = False
            fx, fy0 = st['f_from']
            fy1 = st['f_to'][1]
            if abs(x - fx) < st['width'] / 2 + 64 and min(fy0, fy1) - 64 <= y <= max(fy0, fy1) + 64:
                ok = False
        for p in PLATFORMS.get(rid, []):
            if 'at' in p:
                px, py = p['at']
                sx, sy = p['size']
                if abs(x - px) < sx / 2 + 96 and abs(y - py) < sy / 2 + 96:
                    ok = False
        if ok:
            out.append(((x, y), side))
        if len(out) >= count:
            break
    return out


SCONCE_COUNT = {'gate': 2, 'nave': 4, 'aisle_w': 2, 'aisle_e': 2, 'ward_w': 2, 'ward_e': 2, 'barracks': 2,
                'armoury': 2, 'gallery_w': 3, 'gallery_e': 3, 'tower0_w': 2, 'tower0_e': 2, 'vault_w': 3,
                'vault_e': 3, 'stair_hall': 4, 'tower1_w': 2, 'tower1_e': 2, 'turret_w': 2, 'turret_e': 2,
                'grand_landing': 2, 'foundry': 3, 'foundry_w': 3, 'foundry_e': 3, 'store': 1, 'keep_stair': 2,
                'bays': 1, 'gen_fire': 2, 'gen_air': 2, 'upper_w': 3, 'upper_e': 3, 'war_room': 2, 'quarters': 2,
                'barrier': 2, 'barrier_w': 2, 'barrier_e': 2, 'upper_landing': 3, 'crown_stair': 2,
                'crown_landing': 2, 'walk_s': 3, 'walk_n': 2, 'loft': 2, 'threshold': 3, 'throne': 4, 'apse': 2,
                'treasury': 1}


def objects_yml():
    doors = []

    def door(did, op, notes, **kw):
        d = {'id': did, 'opening': op, 'kind': 'slide_up', 'thickness': 24, 'surface': dict(DOOR1, fit=True),
             'back_surface': dict(DOOR1, fit=True), 'speed': 192, 'notes': notes}
        d.update(kw)
        doors.append(d)

    def pair(did, op, left, right, notes):
        doors.append({'id': did, 'opening': op, 'kind': 'hinged', 'leaves': 2, 'thickness': 32, 'speed': 128,
                      'pictures': [[left, right]], 'back_pictures': [[left, right]],
                      'edge_surface': S('gnecstpv', 64, 128), 'notes': notes})

    pair('door:hall_north', 'open:nave_stair', WING_L, WING_R,
         "The great hall's north doors: two leaves (MM8 gnecdr1l/gnecdr1r, the robed figures), swinging apart.")
    pair('door:throne', 'open:throne_doors', THRONE_L, THRONE_R,
         "The throne doors: two studded black leaves (gnecdr4l/gnecdr4r), swinging apart.")
    for s in ('w', 'e'):
        bar = 'barracks' if s == 'w' else 'armoury'
        door(f'door:{bar}', f'open:ward_{s}_{bar}', f"The {bar}' door.")
        door(f'door:vault_{s}', f'open:gallery_{s}_vault', "The vault's door from the gallery.")
        door(f'door:vault_{s}_stair', f'open:vault_{s}_stair', "The vault's door to the stair hall.")
        door(f'door:keep_{s}', f'open:wall_{s}n_foundry_{s}', "The keep's door off the wall walk.")
        gen = 'gen_fire' if s == 'w' else 'gen_air'
        door(f'door:{gen}', f'open:upper_{s}_{gen}', "The tower top's door.")
    door('door:store', 'open:store_door', "The parts store's door.")
    door('door:war_room', 'open:upper_w_war', "The war room's door (it slides aside: the keeper's walk lies over it).", kind='slide_left')
    door('door:quarters', 'open:upper_e_quarters', "The demons' quarters' door.")
    door('door:walk', 'open:landing_walk', "The keeper's walk's door off the crown landing.")
    door('door:walk_threshold', 'open:walk_threshold', "The keeper's walk's door onto the throne doors.")
    doors.append({'id': 'door:bays', 'opening': 'open:bays_shutter', 'kind': 'slide_up', 'thickness': 24, 'speed': 96,
                  'surface': dict(SHUTTER), 'back_surface': dict(SHUTTER), 'tile': True,
                  'notes': "The guard bays' Ancient shutters (swdoorc, a shutter that tiles): they roll up when both "
                           "machines are destroyed (map qbit 118063)."})
    doors.append({'id': 'door:field', 'opening': 'open:field', 'kind': 'slide_down', 'fold': True,
                  'surface': FIELD, 'tile': True, 'speed': 256,
                  'notes': "The field across the crown stair (xafield, translucent): it sinks away when the four "
                           "pylons are dark (m35.barrier, map qbit 118062) and stays down."})
    doors.append({'id': 'door:treasury', 'opening': 'open:apse_treasury', 'kind': 'slide_up', 'thickness': 32,
                  'speed': 128, 'surface': dict(SIGIL_DOOR, fit=True), 'back_surface': dict(SIGIL_DOOR, fit=True),
                  'notes': "The hoard door behind the dais, Lord Xeen's sigil on it (gnecdr3): it opens at his death."})

    plates = [{'id': 'plate:sight', 'room': 'room:throne', 'at': F(0, ROOMS['throne']['rect'][1] + 96),
               'size': F(1024, 96),
               'notes': "The step plate across the throne doors' sill, inside the leaves: the throne straight ahead "
                        "and lit (D-47 Q13)."}]

    chests = []

    def chest(cid, rid, at, facing, notes, level=5, items=3, gold=3000, kind='gt002'):
        # D-99: facing None lets the studio turn the chest (its back to the wall by it); a word overrides.
        chests.append({'id': f'chest:{cid}', 'room': f'room:{rid}', 'at': F(*at), 'kind': kind,
                       **({'facing': facing} if facing else {}),
                       'treasure_level': level, 'random_items': items, 'gold': gold, 'notes': notes})

    chest('barracks', 'barracks', at_in('barracks', 0.2, 0.08), None, "The barracks' chest by the south wall.")
    chest('armoury', 'armoury', at_in('armoury', 0.8, 0.08), 'n', "The armoury's chest.")
    chest('store', 'store', at_in('store', 0.88, 0.85), None, "The parts store's chest.")
    chest('war_room', 'war_room', at_in('war_room', 0.12, 0.88), None, "The war room's chest.")
    chest('quarters', 'quarters', at_in('quarters', 0.12, 0.08), 'n', "The demons' quarters' chest.")
    chest('loft', 'loft', at_in('loft', 0.9, 0.12), None, "The keeper's strongbox, up in the loft.")
    chest('hoard', 'treasury', (0, ROOMS['treasury']['rect'][3] - 128), 's', "Lord Xeen's hoard (T6).", level=6,
          items=5, gold=12000, kind='7gt002')

    monsters = []
    for rid, group, ms, immobile in PLACED:
        for n, (mon, at, facing) in enumerate(ms, 1):
            key = {LORD: 'lord_xeen', PET: 'pet'}.get(mon, f'{rid}_{n}')
            m = {'id': f'monster:{key}', 'room': f'room:{rid}', 'monster': mon, 'at': F(*at), 'facing': facing,
                 'hostile': True, 'group': group}
            if immobile:
                m['immobile'] = True
            if mon == LORD:
                m['notes'] = ("Lord Xeen on his dais: immobile until 4 s after the first-sight line (evt:sight_clock frees him by "
                              "ActorIndex); only melee with the Xeen Slayer Sword harms him (evt:lord_damage).")
            monsters.append(m)
    for pid, rid, group, at in POOL:
        monsters.append({'id': f'monster:{pid}', 'room': f'room:{rid}', 'monster': GUARD, 'at': F(*at),
                         'facing': 270, 'hostile': True, 'group': group, 'hidden': True,
                         'notes': "One of the foundry's four hidden guards at a machine's output chute (D-47 Q7)."})

    decos = []

    def deco(name, rid, d, at, **kw):
        e = {'id': f'deco:{name}', 'room': f'room:{rid}', 'decoration': d, 'at': F(*at)}
        e.update(kw)
        decos.append(e)

    n = 0
    for rid, cnt in SCONCE_COUNT.items():
        for (x, y), side in sconce_spots(rid, cnt):
            n += 1
            p, _ = on_wall(rid, (x, y))
            deco(f'sconce_{n:02d}', rid, 'scon100', p, height=176)
    # The throne room's floor braziers either side of the dais's arch, the quarters' braziers.
    for x in (-960, 960):
        deco(f'throne_brazier_{"w" if x < 0 else "e"}', 'throne', 'flamb00', (x, 3008))
    qx0, qy0, qx1, qy1 = ROOMS['quarters']['rect']
    deco('quarters_brazier', 'quarters', 'flamb00', (qx0 + 96, (qy0 + qy1) // 2))
    # The aviary's gnawed bones, by the ledges (off the walking line between the arches).
    for i, (d, at) in enumerate([('dec19', (-1600, -2400)), ('dec29', (1600, -2560)), ('dec29', (-1600, -1040)),
                                 ('dec19', (1560, -1120)), ('7dec18', (1680, -960))], 1):
        deco(f'bones_{i}', 'aviary_s' if at[1] < -1760 else 'aviary_n', d, at)
    # The parts store (store: true): crates of plates, sacks of gems, barrels, in clumps along the walls.
    sx0, sy0, sx1, sy1 = ROOMS['store']['rect']
    for i, (d, at) in enumerate([('bigbarel', (sx0 + 96, sy1 - 96)), ('bigbarel', (sx0 + 200, sy1 - 96)),
                                 ('smlbarel', (sx0 + 96, sy1 - 200)), ('bag01', (sx0 + 96, sy0 + 96)),
                                 ('bag_A', (sx0 + 200, sy0 + 96)), ('floursac', (sx0 + 96, sy0 + 200)),
                                 ('bigbarel', (sx1 - 96, sy0 + 96)), ('smlbarel', (sx1 - 200, sy0 + 96))], 1):
        deco(f'store_{i}', 'store', d, at)
    # A pair of barrels by the barracks' wall.
    bx0, by0, bx1, by1 = ROOMS['barracks']['rect']
    deco('barracks_barrel_1', 'barracks', 'bigbarel', (bx1 - 96, by0 + 96))
    deco('barracks_barrel_2', 'barracks', 'bigbarel', (bx1 - 200, by0 + 96))

    lights = []

    def light(name, rid, at, height, radius, color, **kw):
        d = {'id': f'light:{name}', 'room': f'room:{rid}', 'at': F(*at), 'height': height, 'radius': radius,
             'color': F(*color)}
        d.update(kw)
        lights.append(d)

    warm = (230, 190, 140)
    cool = (175, 185, 215)
    for rid, r in ROOMS.items():
        x0, y0, x1, y1 = r['rect']
        w, dd = x1 - x0, y1 - y0
        # Half the room's height (at most 420): hung 96 under the pale vault (gnecclg2) the fill lights burned the
        # ceilings near white after the bake (review G3 row 72); at half height the vault falls off into shadow.
        h = min((r['ceiling'] - r['floor']) // 2, 420)
        if rid in STAIR:
            g = STAIR[rid]['gallery']
            pts = [((x0 + x1) // 2, (y0 + y1) // 2)]
            h = 520
        elif max(w, dd) > 1800:
            pts = ([(x0 + w // 4, (y0 + y1) // 2), (x1 - w // 4, (y0 + y1) // 2)] if w >= dd else
                   [((x0 + x1) // 2, y0 + dd // 4), ((x0 + x1) // 2, y1 - dd // 4)])
        else:
            pts = [((x0 + x1) // 2, (y0 + y1) // 2)]
        col = cool if r['theme'] in ('sky', 'works') else warm
        if rid == 'apse':
            pts = [(0, THRONE_AT[1] - 320)]
        for i, at in enumerate(pts, 1):
            light(f'{rid}_{i}' if len(pts) > 1 else rid, rid, at, h, 1600 if max(w, dd) > 1800 else 1100, col)
    # The generators' glows and the pylons' (each put out with its generator); the field's.
    for g, d in GENS.items():
        cx, cy = d['core']
        light(f'core_{g}', d['room'], (cx, cy + 288 * d['front']), 240, 1000, d['color'], brightness=30,
              notes=f"The {g} generator's glow: out when it falls.")
    for g, at in PYLONS.items():
        light(f'pylon_{g}', 'barrier', (at[0], at[1] + (160 if at[1] < -1600 else -160)), 300, 700, GENS[g]['color'],
              brightness=26, pulse={'intensity': F(0.6, 1), 'frequency': 0.7},
              notes=f"The {g} pylon's light: out when its generator falls.")
    light('field', 'barrier', (0, ROOMS['barrier']['rect'][1] + 160), 240, 900, (110, 160, 255), brightness=26,
          pulse={'intensity': F(0.5, 1), 'frequency': 1.6}, notes="The field's crackle of light: out when it falls.")
    light('throne_lit', 'apse', (0, THRONE_AT[1] - 96), 360, 1400, (255, 210, 150), brightness=31,
          notes="The throne lit, straight ahead of the doors (D-47 Q13).")
    light('mirror', 'apse', (0, MIRROR_AT[1] - 160), 300, 800, (200, 220, 255), brightness=28,
          notes="The Sixth Mirror's silver light: out when it shatters.")

    sounds = []
    for g, d in GENS.items():
        cx, cy = d['core']
        sounds.append({'id': f'sound:gen_{g}', 'room': f"room:{d['room']}", 'at': F(cx, cy + 256 * d['front']), 'sound': 'humming',
                       'radius': 1500, 'inner_radius': 400, 'volume': 0.5,
                       'notes': f"The {g} generator's hum (AU session 3: the engine's humming); off when it falls."})
    for s, m in MACHINES.items():
        sounds.append({'id': f'sound:machine_{s}', 'room': f"room:{m['room']}", 'at': F(m['at'][0], m['at'][1] - 512),
                       'sound': 'xeen_machine_stamp_loop', 'radius': 3200, 'inner_radius': 900, 'volume': 0.45,
                       'notes': "The guard-making machine's stamping (AU's xeen_machine_stamp_loop); off when it "
                                "falls."})
    sounds.append({'id': 'sound:barrier', 'room': 'room:barrier', 'at': F(0, ROOMS['barrier']['rect'][1] + 256),
                   'sound': 'xeen_barrier_loop', 'radius': 2000, 'inner_radius': 600, 'volume': 0.5,
                   'notes': "The field's crackle (AU's xeen_barrier_loop); off when it falls."})

    destructibles = []
    for g, d in GENS.items():
        destructibles.append({'id': f'destructible:gen_{g}', 'of': f'platform:gen_{g}', 'hp': 300, 'material': 'metal',
                              'on_destroyed': f'evt:gen_{g}_down',
                              'notes': f"The {d['title']}'s core: the question breaks it, and blows and spells too "
                                       "(D-47 Q8); its faces vanish, the housings stay."})
    for s in ('w', 'e'):
        destructibles.append({'id': f'destructible:machine_{s}', 'of': f'platform:machine_{s}', 'hp': 400,
                              'material': 'metal', 'on_destroyed': f'evt:machine_{s}_down',
                              'notes': "A guard-making machine: the question breaks it, blows and spells too (D-47 "
                                       "Q7/Q8); no experience (Q15)."})

    return {'format': 0,
            'start': {'room': 'room:gate', 'at': F(*START), 'facing': 'n',
                      'notes': "In the gatehall about 256 inside the gate's two leaves, facing north into the great "
                               "hall (the arrival from X9)."},
            'arrivals': [FlowDict(entrance=X9_ENTRANCE, room='room:gate', at=F(*START), facing='n',
                                  notes="X9's castle gate (A5's thing:castle_xeen_gate, m34.gate) arrives here: about "
                                        "256 inside the leaves, facing north, the great hall ahead.")],
            'doors': doors, 'plates': plates, 'sounds': sounds, 'lights': lights, 'chests': chests,
            'monsters': monsters, 'decorations': decos, 'destructibles': destructibles, 'exits': gate_exits(),
            'relations': []}


# ---------------------------------------------------------------------------------------------------------------------
# wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def amb(sound_key, state):
    n = lock_no('sounds', f'sound:{sound_key}')
    return {'lua': f"evt.SetMapVar('AmbientSound{n}', {state})"}


def snd(name, x, y, z):
    return {'lua': f'evt.PlaySoundName("{name}", {x}, {y}, {z})'}


YES = ['Yes', 'Y', 'yes', 'y']


def wiring_yml():
    ev = []

    def e(**kw):
        ev.append(kw)

    e(id='evt:arrive', preset='script', trigger='timer', every=1, once=True, effects=[hook('m35.arrival')],
      notes="A3's m35.arrival (started 111700, once): its line at the first arrival.")
    # The gate: each leaf the exit preset to X9 (an indoor map: no leave window; 'Exit Castle Xeen?', aaze0075:6, is
    # its meaning).
    for s in ('l', 'r'):
        e(id=f'evt:gate_{s}', preset='exit', source=f'exit:gate_{s}', title='Exit Castle Xeen',
          notes="Out to X9 (installed, A5) at its named arrival entrance:xd19_gate (0, 11264, 768) facing south, "
                "before the castle's gate.")
    for did, title in (('barracks', 'Door'), ('armoury', 'Door'), ('vault_w', 'Door'), ('vault_e', 'Door'),
                       ('vault_w_stair', 'Door'), ('vault_e_stair', 'Door'), ('keep_w', 'Door'), ('keep_e', 'Door'),
                       ('gen_fire', 'Door'), ('gen_air', 'Door'), ('store', 'Door'), ('war_room', 'Door'),
                       ('quarters', 'Door'), ('walk', 'Door'), ('walk_threshold', 'Door'),
                       ('hall_north', 'Great doors'), ('throne', 'Throne doors')):
        e(id=f'evt:door_{did}', preset='door', source=f'door:{did}', title=title)
    # --- The four generators (D-47 Q8): a click breaks the core (F47: no question); its on_destroyed is the rest.
    for g, d in GENS.items():
        e(id=f'evt:gen_{g}', preset='script', source=f'platform:gen_{g}', title=d['title'],
          condition={'not': {'destroyed': f'destructible:gen_{g}'}},
          effects=[{'destroy': f'destructible:gen_{g}'}],
          else_effects=[hook(f'm35.gen_{g}')],
          notes=f"The {d['title']} ({d['ref']}): a click breaks the core (F47 2026-11-24: no Yes/No; its on_destroyed, "
                f"evt:gen_{g}_down, does the rest); blows and spells break it too. Broken: A3's else line.")
        e(id=f'evt:gen_{g}_down', preset='script', trigger='call',
          effects=[hook(f'm35.gen_{g}'), amb(f'gen_{g}', 2), {'lights_off': [f'light:core_{g}', f'light:pylon_{g}']},
                   {'set_texture': {'of': f'platform:pylon_{g}', 'to': DARK['texture']}}],
          notes=f"The {g} generator's core broken (by the question, a blow or a spell): A3's m35.gen_{g} "
                f"({QBITS['gen_' + g]}), its hum stops, its glow and its pylon's light go out, the pylon goes dark.")
        e(id=f'evt:gen_{g}_load', preset='script', trigger='load', condition={'destroyed': f'destructible:gen_{g}'},
          effects=[amb(f'gen_{g}', 2), {'lights_off': [f'light:core_{g}', f'light:pylon_{g}']},
                   {'set_texture': {'of': f'platform:pylon_{g}', 'to': DARK['texture']}}],
          notes=f"On every later load the {g} generator stays dead and its pylon dark.")
        e(id=f'evt:pylon_{g}', preset='text', source=f'platform:pylon_{g}',
          title=f"{g.capitalize()} pylon: to {d['where']}",
          text=f"The {g} pylon. Its conduit runs to {d['where']}.", seconds=4,
          notes=f"D-47 Q9: each pylon's hover names its generator's {('tower' if 'tower' in d['where'] else 'vault')}.")
    # --- The barrier (D-47 Q9).
    e(id='evt:barrier_falls', preset='script', trigger='timer', every=1, once=True,
      condition={'all': [{'lua': 'XeenQuests.can("m35.barrier")'}, {'not': {'qbit': QBITS['barrier_down']}}]},
      opens=['door:field'],
      effects=[{'qbit': QBITS['barrier_down']}, hook('m35.barrier'), amb('barrier', 2), {'lights_off': 'light:field'},
               {'shake': {'strength': 1, 'seconds': 1.5}}],
      notes="All four pylons dark (A3's m35.barrier reads the four generator bits): the field sinks, the crackle "
            "stops, the hook's line once (barrier_down 118062).")
    e(id='evt:barrier_load', preset='script', trigger='load', condition={'qbit': QBITS['barrier_down']},
      opens=['door:field'], effects=[amb('barrier', 2), {'lights_off': 'light:field'}],
      notes="On every later load the field stays down.")
    e(id='evt:field', preset='door', source='door:field', title='Barrier', action='open',
      condition={'qbit': QBITS['barrier_down']}, else_effects=[hook('m35.barrier')],
      notes="The field's click while it stands: A3's m35.barrier fail line (four pylons, while one burns).")
    # --- The guard foundry (D-47 Q7).
    for s in ('w', 'e'):
        e(id=f'evt:machine_{s}', preset='script', source=f'platform:machine_{s}', title='Guard Making Machine',
          condition={'not': {'destroyed': f'destructible:machine_{s}'}},
          effects=[{'destroy': f'destructible:machine_{s}'}],
          else_effects=[{'text': "A broken press. Nothing comes out of it any more."}],
          notes="aaze0075:0: a click breaks it (F47 2026-11-24: no Yes/No; blows and spells too); no experience (D-47 Q15).")
        e(id=f'evt:machine_{s}_down', preset='script', trigger='call',
          effects=[{'qbit': QBITS[f'machine_{s}_down']}, amb(f'machine_{s}', 2),
                   {'text': "The machine shudders, jams, and stops stamping."}],
          notes=f"The machine broken: machine_{s}_down {QBITS[f'machine_{s}_down']}, its stamping stops.")
        e(id=f'evt:machine_{s}_load', preset='script', trigger='load',
          condition={'destroyed': f'destructible:machine_{s}'}, effects=[amb(f'machine_{s}', 2)],
          notes="On every later load the broken machine stays silent.")
    e(id='evt:foundry_step', preset='script', trigger='step', source='room:foundry_w',
      sources=['room:foundry', 'room:foundry_e', 'room:grand_landing'], once=True,
      effects=[{'set': {'var': {'map_var': 'pool_on'}, 'value': 1}}],
      notes="The party's first step into the foundry (by the grand landing, either keep door or the keep stair) "
            "starts the pool's clock.")
    both = {'all': [{'destroyed': 'destructible:machine_w'}, {'destroyed': 'destructible:machine_e'}]}
    rel = ' '.join(
        f"{'if' if i == 1 else 'elseif'} not IsAtLeast(MapVar(pool), {i}) then evt.SetMonGroupBit({40 + i}, "
        f"MonsterBits.Invisible, 0) SetValue(MapVar(pool), {i})" for i in range(1, 5)) + ' end'
    e(id='evt:pool_clock', preset='script', trigger='timer', every=1,
      condition={'all': [{'map_var': 'pool_on'}, {'not': both}, {'map_var': {'name': 'pool', 'below': 4}}]},
      effects=[{'add': {'var': {'map_var': 'pool_clock'}, 'value': 1}}],
      lua=f"if IsAtLeast(MapVar(pool_clock), 45) then SetValue(MapVar(pool_clock), 0) {rel} "
          "evt.StatusText(\"A press thumps. A new guard steps off the line.\", 3) end",
      notes="While either machine stands, every 45 s from the first step into the foundry one of the four hidden "
            "guards at the chutes is shown (D-18's word for showing a hidden actor: its group's Invisible bit "
            "cleared) and, hostile, takes the party on; pool counts them (at most 4).")
    e(id='evt:machines_down', preset='script', trigger='timer', every=1, once=True, condition=both,
      opens=['door:bays'],
      effects=[{'show_actors': 40 + i} for i in range(1, 5)]
      + [{'qbit': QBITS['bays_open']}, {'set': {'var': {'map_var': 'pool'}, 'value': 4}},
         {'text': "Both machines are still. The bays' shutters roll up, and the last guards step off the line."}],
      notes="Both machines destroyed: every guard still hidden is shown, the bays open on the gem find "
            "(bays_open 118063); the count stays 70 (D-47 Q7).")
    e(id='evt:bays_load', preset='switch', trigger='load', condition={'qbit': QBITS['bays_open']},
      opens=['door:bays'], notes="On every later load the shutters stay up.")
    e(id='evt:gems', preset='script', source='platform:gems', title='Tray', condition={'not': {'map_var': 'gems'}},
      effects=[{'set': {'var': {'map_var': 'gems'}, 'value': 1}}, {'give_item': 183}, {'give_item': 183},
               {'give_item': 183}, {'text': "Green gem eyes, a whole tray of spares. You take three emeralds."}],
      else_effects=[{'text': "An empty tray."}],
      notes="The guard bays' gem find (graph: 'Green gem eyes'): three Emeralds (183), once.")
    # --- The crown: Xeen's Pet, the first sight, Lord Xeen, the scepter.
    e(id='evt:pet_dead', preset='script', trigger='timer', every=2, once=True,
      condition={'kills': {'monster': 'monster:pet'}}, effects=[hook('m35.pet')],
      notes="Xeen's Pet's death: A3's m35.pet (pet_slain 111705). Opens nothing (D-47).")
    e(id='evt:sight', preset='script', trigger='step', source='plate:sight', once=True,
      condition={'not': {'qbit': LORD_SEEN_QBIT}},
      effects=[hook('m35.lord_xeen_sight'), {'set': {'var': {'map_var': 'sight'}, 'value': 1}}],
      notes="The plate inside the throne doors (D-47 Q13): A3's m35.lord_xeen_sight (lord_xeen_seen 111709, D-38's "
            "voiced line, once per save); the clock frees Lord Xeen and his guards 4 s after.")
    who = ['monster:lord_xeen'] + [f'monster:throne_{i}' for i in range(1, 7)]
    free = ' '.join(['evt.SetActorImmobile(ActorIndex("%s"), false)' % m for m in who]
                    + ['evt.SetActorTarget(ActorIndex("%s"), "party")' % m for m in who])
    e(id='evt:sight_clock', preset='script', trigger='timer', every=1,
      condition={'all': [{'map_var': 'sight'}, {'not': {'map_var': 'freed'}}]},
      effects=[{'add': {'var': {'map_var': 'sight'}, 'value': 1}}],
      lua=f"if IsAtLeast(MapVar(sight), 5) then SetValue(MapVar(freed), 1) {free} end",
      notes="4 s after the line, Lord Xeen and his six guards (monster:throne_1 to throne_6, D-98; ActorIndex, merge "
            "point 22) leave their places and go for the party (evt.SetActorImmobile, evt.SetActorTarget).")
    # D-47 Q12/Q13 on merge point 21's monster_damage trigger: only melee with the Xeen Slayer Sword harms Lord Xeen;
    # the first zeroed hit of a visit gives A3's m35.untouchable line; a hit before the plate also runs the first sight.
    e(id='evt:lord_damage', preset='script', trigger='monster_damage', actors=['monster:lord_xeen'],
      lua=("if not (hook.attack == 'melee' and hook.weaponItemId == %d) then\n"
           "    evt.SetHookDamage(0)\n"
           "    if not IsAtLeast(MapVar(untouched), 1) then\n"
           "        SetValue(MapVar(untouched), 1)\n"
           "        XeenQuests.hook(\"m35.untouchable\")\n"
           "    end\n"
           "end\n"
           "if not IsQBitSet(QBit(%d)) then\n"
           "    XeenQuests.hook(\"m35.lord_xeen_sight\")\n"
           "    SetValue(MapVar(sight), 1)\n"
           "end") % (SLAYER_SWORD, LORD_SEEN_QBIT),
      notes="D-47 Q12: every hit on Lord Xeen but melee with the Xeen Slayer Sword (12500) is zeroed; the first "
            "zeroed hit of a visit shows A3's m35.untouchable. Q13: a hit before the throne doors' plate runs "
            "m35.lord_xeen_sight (its own once bit) and starts the 4 s clock that frees him.")
    e(id='evt:lord_untouched_leave', preset='script', trigger='leave',
      effects=[{'set': {'var': {'map_var': 'untouched'}, 'value': 0}}],
      notes="m35.untouchable's line once per visit: cleared when the party leaves.")
    e(id='evt:lord_dead', preset='script', trigger='timer', every=1, once=True,
      condition={'kills': {'monster': 'monster:lord_xeen'}}, opens=['door:treasury'],
      effects=[hook('m35.lord_xeen')],
      notes="Lord Xeen's death: A3's m35.lord_xeen (lord_xeen_slain 111706, D-38's voiced line); the treasury opens.")
    e(id='evt:treasury_load', preset='switch', trigger='load', condition={'qbit': QBITS['lord_xeen_slain']},
      opens=['door:treasury'], notes="On every later load the hoard stays open.")
    e(id='evt:throne', preset='script', source='platform:throne', title='Throne',
      condition={'all': [{'not': {'qbit': QBITS['done']}}, {'lua': 'XeenQuests.hook("m35.scepter_ask")'}]},
      question={'ask': 'Take (Yes/No)?', 'answers': YES},
      effects=[hook('m35.scepter'), {'cinematic': {'id': 'cinematic:mirror', 'then': 'evt:after_mirror'}}],
      else_effects=[hook('m35.scepter')],
      notes="D-47 Q14: after Lord Xeen's death the throne asks first (A3's m35.scepter_ask shows its text, then the "
            "question). Yes: A3's m35.scepter (done 111707, award 411, 35,000, the Scepter), then the cinematic. No: "
            "nothing. Before his death and after the scepter: m35.scepter's fail and else lines.")
    e(id='evt:mirror', preset='script', source='panel:mirror', title='Mirror',
      condition={'not': {'qbit': QBITS['done']}}, effects=[hook('m35.mirror')],
      else_effects=[{'text': "An empty frame. Silver dust and shards of glass."}],
      notes="aaze0078:5 by A3's m35.mirror while the mirror stands; after it shatters, a map-local line.")
    e(id='evt:mirror_shatters', preset='script', trigger='call',
      effects=[{'lights_off': 'light:mirror'}, {'set_texture': {'of': 'panel:mirror', 'to': MIRROR6_GONE}},
               {'shake': {'strength': 2, 'seconds': 3}}],
      notes="The cinematic's cue: the mirror's light goes out and the mirror becomes its shattered frame (xmirror6x).")
    e(id='evt:after_mirror', preset='script', trigger='call', effects=[{'leave': 'exit:x9_gate'}],
      notes="D-47 Q14: the cinematic's done event: 'proceed to the nearest exit' - the party is out on X9 before the "
            "gate at once (the studio's leave: evt.MoveToMap(..., {direct = true}), merge point 21's confirmation).")
    e(id='evt:mirror_load', preset='script', trigger='load', condition={'qbit': QBITS['done']},
      effects=[{'lights_off': 'light:mirror'}, {'set_texture': {'of': 'panel:mirror', 'to': MIRROR6_GONE}}],
      notes="After the scepter the mirror stays dark and shattered.")
    # --- Chests and lines.
    for c in ('barracks', 'armoury', 'store', 'war_room', 'quarters', 'loft', 'hoard'):
        e(id=f'evt:chest_{c}', preset='chest', source=f'chest:{c}', title='Chest')
    e(id='evt:war_table', preset='text', source='platform:war_table', title='War table',
      text="A map of both faces of Xeen. Darkside armies are pinned along the edge, ready to cross.", seconds=5,
      notes="Map-local line (Crodo's warning, M21).")
    for i in (1, 2, 3):
        e(id=f'evt:bed_{i}', preset='text', source=f'platform:bed_{i}', title='Bed',
          text="An iron bed. It smells of sulphur.", notes="Map-local line.")
    ev.sort(key=lambda x: x['id'])
    return {'format': 0, 'variables': ['pool_on', 'pool', 'pool_clock', 'gems', 'sight', 'freed', 'untouched'],
            'events': ev,
            'cinematics': [cinematic()]}


SUBS = [
    "Xeen's scepter gives a high whine, like a blade drawn across a whetstone. The mirror takes up the sound and "
    "throws it back, louder and louder.",
    "Just as you realize that the mirror and the scepter are not compatible, the mirror shatters in a spectacular "
    "display of light, noise and violence.",
    "The castle gives an awful shudder and groans like a beast mortally wounded.",
    "With masonry falling and dust filling the air, you all decide to remain calm and proceed to the nearest exit in "
    "an orderly fashion.",
]


def cinematic():
    mx_, my_ = MIRROR_AT
    return {'id': 'cinematic:mirror',
            'notes': "D-47 Q14: the Sixth Mirror shatters after the scepter is taken. Subtitles are A3's "
                     "m35.scepter cinematic_subtitles (aaze0078:4, shortened), in order; sounds AU's "
                     "xeen_mirror_shatter then xeen_castle_groan.",
            'shots': [FlowDict(seconds=5, at=F(0, my_ - 1400, Z[3] + 260), look_at=F(mx_, my_, Z[3] + 260)),
                      FlowDict(seconds=5, at=F(-700, my_ - 900, Z[3] + 360), look_at=F(mx_, my_, Z[3] + 200)),
                      FlowDict(seconds=6, at=F(0, my_ - 2600, Z[3] + 480), look_at=F(mx_, my_, Z[3] + 160))],
            'cues': [FlowDict(at=0, fade='in', seconds=1),
                     FlowDict(at=0.5, subtitle=SUBS[0], seconds=4.5),
                     FlowDict(at=5, sound='xeen_mirror_shatter'),
                     FlowDict(at=5.2, event='evt:mirror_shatters'),
                     FlowDict(at=5.2, subtitle=SUBS[1], seconds=4.5),
                     FlowDict(at=5.2, shake=0.8, seconds=2),
                     FlowDict(at=10, sound='xeen_castle_groan'),
                     FlowDict(at=10, shake=1, seconds=3),
                     FlowDict(at=10, subtitle=SUBS[2], seconds=3),
                     FlowDict(at=13, subtitle=SUBS[3], seconds=3),
                     FlowDict(at=15, fade='out', seconds=1)]}


# ---------------------------------------------------------------------------------------------------------------------
# The gatehall's south wall: the frieze; the gate's two leaves are exits (gate_exits).
def gate_walls():
    gx0, gy0, gx1, gy1 = ROOMS['gate']['rect']
    half = (gx1 - gx0) // 2
    # The south wall runs west to east (its start corner the west end, the right hand seen from inside): the right
    # leaf seen from inside (west) shows the right wing, the left leaf (east) the left wing.
    return [{'wall': 'south', 'surface': FRIEZE}]


def gate_exits():
    """The gate's two leaves seen from inside, each the exit to X9 (merge point 22: a named arrival keeps its facing
    on every exit that names it). West of the middle the right wing, east of it the left wing."""
    gx0, gy0, gx1, gy1 = ROOMS['gate']['rect']
    mid = (gx0 + gx1) // 2
    return [{'id': 'exit:gate_r', 'room': 'room:gate', 'at': F(mid - 128, gy0), 'size': F(256, 512),
             'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x9_gate',
             'notes': "The gate's west leaf (the right wing seen from inside): out to X9's causeway."},
            {'id': 'exit:gate_l', 'room': 'room:gate', 'at': F(mid + 128, gy0), 'size': F(256, 512),
             'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x9_gate',
             'notes': "The gate's east leaf (the left wing seen from inside): out to X9's causeway."}]


# The new textures on the walls (D-51 3(c)). A wall's offsets run from its start corner (the right-hand end seen from
# inside); every pair here is symmetric about the wall's middle.
NAVE_W = ROOMS['nave']['rect'][2] - ROOMS['nave']['rect'][0]          # 1792: the arch (640) and the great doors (512)
BAN_L, BAN_H, BAN_B = 192, 384, 256                                    # a nave banner: 192 x 384, from 256 to 640
BAN_OFF = NAVE_W // 2 - 608 - BAN_L // 2                               # centred 608 either side of the middle


def nave_banners(tag):
    return [FlowDict(id=f'panel:banner_{tag}{i}', offset=o, length=BAN_L, bottom=BAN_B, height=BAN_H, surface=BANNER)
            for i, o in ((1, BAN_OFF), (2, NAVE_W - BAN_OFF - BAN_L))]


WALL_PANELS = {
    # The gatehall's inner arch (640 x 512 in a wall 768 high): Lord Xeen's sigil banner hangs over it from the roof;
    # this wall is black stone to the top (no gold frieze row) so the banner hangs on the stone it was painted on.
    ('gate', 'north'): {'surface': STONE,
                        'panels': [FlowDict(id='panel:sigil', at='centre', length=112, bottom=528, height=224,
                                            surface=BANNER)]},
    # The Hall of Xeendom: two sigil banners either side of the inner arch (south) and of the great doors (north).
    ('nave', 'south'): {'panels': nave_banners('s')},
    ('nave', 'north'): {'panels': nave_banners('n')},
    # The Sixth Mirror on the dais's north wall behind the throne (512 x 448 from 64): xmirror6, then the shattered
    # frame xmirror6x once the scepter is taken (the cinematic's cue and every later load).
    ('apse', 'north'): {'panels': [FlowDict(id='panel:mirror', at='centre', length=512, bottom=64, height=448,
                                            surface=MIRROR6)]},
}


# ---------------------------------------------------------------------------------------------------------------------
# project.yml


def project_yml(level):
    return {
        'format': 0, 'id': 'xeen_xd19', 'name': 'Castle Xeen', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-19', 'units': FlowDict(plan_grid=512),
        'extent': FlowDict(footprint_cells=F(21, 20), climbs='n'),
        'map_stats': {
            'id': MAP_STATS_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5,
            'trap_dice': 8, 'perception_difficulty': 15, 'refill_days': 672, 'music': MUSIC,
            'environment': 'stoneroom', 'lock_difficulty': 15,
            'slots': [FlowDict(monster='Xeen Demon', tier=5, per_marker=F(1, 2), weight=100)],
        },
        'neighbours': [{
            'id': 'exit:x9_gate', 'to': 'xeen_x9.blv', 'kind': 'door', 'arrival': 'entrance:xd19_gate',
            'arrival_hint': "On X9's causeway before Castle Xeen's gate, facing south away from it (A5's "
                            "entrance:xd19_gate, (0, 11264, 768) facing 1536).",
            'notes': "X9 installed (A5, 01:29). X9's gate (leaves at x -256..256, y 11768) names this map's arrival "
                     "entrance:x9_gate: in the gatehall about 256 inside the leaves, facing north."}],
        'qbits': dict(sorted(QBITS.items())),
        'items': {'xeen_slayer_sword': SLAYER_SWORD, 'emerald': 183},
        'notes': f"Xeen design brief, level {level}: XD-19 Castle Xeen, on X9 (the Clouds of Xeen), Act V, class L "
                 "(MU-6 graph devdocs/xeen/mockups/act5_graphs/xd19.graph.yml, decider D-47 in "
                 "mockups/act5_a7_decisions.md). M35: the four generators (m35.gen_*), the barrier (m35.barrier), "
                 "Xeen's Pet (m35.pet), Lord Xeen's first sight and death (m35.lord_xeen_sight, m35.lord_xeen), the "
                 "scepter (m35.scepter_ask, m35.scepter) and the Sixth Mirror's cinematic. 96 monsters (D-98: Demon 11630 "
                 "x 38, Devil 11631 x 22, Screamer 11632 x 5, Xeen's Guard 11603 x 21 of which 6 the throne room's and 4 the foundry's hidden "
                 "pool, Lesser Elementals 11620/11624/11625/11626 x 2 each, Greater Elemental 11622 x 2) + Xeen's Pet "
                 "11644 + Lord Xeen 11634. Rest encounters 10 % from the demons at Dif 5 (D-47). Map card 9144, "
                 "music 22, treasure 5 (six T5 chests and the T6 hoard). Map qbits 118060-118063. The gate leads to X9's "
                 "entrance:xd19_gate, and so does the scepter's cinematic; X9's gate arrives at entrance:x9_gate.",
    }


# ---------------------------------------------------------------------------------------------------------------------
# plan.yml
PLAN_SPACES = [
    ('gate', 'room', 'S', "The arrival (entrance:x9_gate): behind the two gate leaves, the sigil over the inner arch; "
                          "m35.arrival. Quiet (D-11.3).", None),
    ('nave', 'hall', 'L', "Black pillared hall under gold friezes; two-leaf doors north to the stair hall.", None),
    ('aisle_w', 'corridor', 'M', "The great hall's west aisle.", None),
    ('aisle_e', 'corridor', 'M', "The great hall's east aisle.", None),
    ('ward_w', 'corridor', 'M', "Vaulted passage to the west gallery and the barracks.", None),
    ('ward_e', 'corridor', 'M', "The same on the east: to the east gallery and the armoury.", None),
    ('barracks', 'room', 'M', "Dead end with a chest: racks of powered-down guards.", 5),
    ('armoury', 'room', 'M', "Dead end with a chest: weapon racks, spare gem eyes.", 5),
    ('gallery_w', 'corridor', 'M', "From the south-west tower to the cold vault.", None),
    ('gallery_e', 'corridor', 'M', "From the south-east tower to the gravel vault.", None),
    ('tower0_w', 'stair', 'S', "The south-west tower's first stair.", None),
    ('tower0_e', 'stair', 'S', "The south-east tower's first stair.", None),
    ('vault_w', 'room', 'M', "The Water Generator (m35.gen_water).", None),
    ('vault_e', 'room', 'M', "The Earth Generator (m35.gen_earth).", None),
    ('stair_hall', 'stair', 'M', "The grand stair up to the foundry; doors into the two vaults.", None),
    ('tower1_w', 'stair', 'S', "The south-west tower's upper stair to the tower top.", None),
    ('tower1_e', 'stair', 'S', "The south-east tower's upper stair.", None),
    ('wall_ws', 'corridor', 'M', "Battlements under open sky.", None),
    ('turret_w', 'room', 'S', "A roofed turret on the west wall.", None),
    ('wall_wn', 'corridor', 'M', "The wall walk's north stretch; the keep's west door.", None),
    ('wall_es', 'corridor', 'M', "The east battlements under open sky.", None),
    ('turret_e', 'room', 'S', "A roofed turret on the east wall.", None),
    ('wall_en', 'corridor', 'M', "The keep's east door.", None),
    ('grand_landing', 'stair', 'S', "The grand stair's top, opening on the foundry.", None),
    ('foundry', 'hall', 'L', "The guard foundry: the slow line, the bays' shutters.", None),
    ('foundry_w', 'hall', 'M', "The west guard-making machine (destructible), its chute, two hidden guards.", None),
    ('foundry_e', 'hall', 'M', "The east machine, its chute, two hidden guards; the keep stair's foot.", None),
    ('store', 'room', 'S', "Dead end with a chest: crates of plates and gems.", 5),
    ('keep_stair', 'stair', 'M', "The keep stair from the foundry to the keep stair top.", None),
    ('bays', 'room', 'M', "Behind the shutters: empty racks and the gem find.", None),
    ('gen_fire', 'room', 'M', "The south-west tower top: the Fire Generator (m35.gen_fire).", None),
    ('gen_air', 'room', 'M', "The south-east tower top: the Air Generator (m35.gen_air).", None),
    ('upper_w', 'corridor', 'M', "From the barrier hall to the fire tower and the war room.", None),
    ('upper_e', 'corridor', 'M', "From the barrier hall to the air tower and the demons' quarters.", None),
    ('war_room', 'room', 'M', "Dead end with a chest: the war table.", 5),
    ('quarters', 'room', 'M', "Dead end with a chest: beds, braziers.", 5),
    ('barrier', 'hall', 'L', "Four pylons hold the field across the crown stair (m35.barrier).", None),
    ('barrier_w', 'hall', 'M', "The barrier hall's west bay.", None),
    ('barrier_e', 'hall', 'M', "The barrier hall's east bay.", None),
    ('upper_landing', 'stair', 'M', "The keep stair arrives here.", None),
    ('crown_stair', 'stair', 'S', "Behind the field: the stair to the crown.", None),
    ('crown_landing', 'room', 'S', "Quiet; the low arch into the aviary, the keeper's walk.", None),
    ('aviary_s', 'hall', 'L', "Open sky: ledges and bones.", None),
    ('aviary_n', 'hall', 'L', "The roost: Xeen's Pet (m35.pet), held by the two low arches (D-32).", None),
    ('walk_s', 'corridor', 'M', "The way round the Pet.", None),
    ('walk_n', 'corridor', 'M', "The way round the Pet, to the throne doors.", None),
    ('loft', 'room', 'S', "Dead end with the keeper's strongbox.", 5),
    ('threshold', 'room', 'S', "Before the throne doors. Quiet.", None),
    ('throne', 'hall', 'L', "The throne room; the sight plate inside the doors (m35.lord_xeen_sight).", None),
    ('apse', 'room', 'M', "Lord Xeen on his dais (m35.lord_xeen), the Sixth Mirror, the scepter (m35.scepter).", None),
    ('treasury', 'room', 'S', "The hoard (T6), opened by Lord Xeen's death.", 6),
]


def polygon_area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                   for i in range(len(pts)))) / 2


AREA = sum(polygon_area(r['outline']) for r in ROOMS.values())


def plan_yml(level):
    pop = {}
    for rid, group, ms, _ in PLACED:
        for mon, _, _ in ms:
            pop.setdefault(rid, {}).setdefault(mon, 0)
            pop[rid][mon] += 1
    for _, rid, _, _ in POOL:
        pop.setdefault(rid, {}).setdefault(GUARD, 0)
        pop[rid][GUARD] += 1
    spaces = []
    for sid, kind, size, purpose, chest in PLAN_SPACES:
        r = ROOMS[sid]
        x0, y0, x1, y1 = r['rect']
        s = {'id': f'room:{sid}', 'name': r['name'], 'kind': kind if kind in ('room', 'corridor') else 'room', 'size': size, 'extent': F(x1 - x0, y1 - y0),
             'floor': r['floor'], 'purpose': purpose}
        if sid in pop:
            s['population'] = [{'actor': m, 'groups': 1, 'levels': F(LEVEL[m], LEVEL[m]),
                                'notes': f"{n} placed {NAMES[m]}."} for m, n in pop[sid].items()]
        else:
            s['empty'] = True
        if chest:
            s['treasure'] = [FlowDict(kind='chest', count=1, tier=chest)]
        spaces.append(s)

    def L(lid, a, b, kind, **kw):
        return {'id': f'link:{lid}', 'from': f'room:{a}', 'to': f'room:{b}', 'kind': kind, **kw}

    links = [L('gate_hall', 'gate', 'nave', 'open'), L('hall_stair', 'nave', 'stair_hall', 'door')]
    for s in ('w', 'e'):
        bar = 'barracks' if s == 'w' else 'armoury'
        gen = 'gen_fire' if s == 'w' else 'gen_air'
        links += [L(f'nave_aisle_{s}', 'nave', f'aisle_{s}', 'open'),
                  L(f'hall_{s}w', f'aisle_{s}', f'ward_{s}', 'open'),
                  L(f'ward_{s}_{bar}', f'ward_{s}', bar, 'door'),
                  L(f'ward_{s}_gallery_{s}', f'ward_{s}', f'gallery_{s}', 'open'),
                  L(f'gallery_{s}_tower0', f'gallery_{s}', f'tower0_{s}', 'open'),
                  L(f'gallery_{s}_vault', f'gallery_{s}', f'vault_{s}', 'door'),
                  L(f'vault_{s}_stair', f'vault_{s}', 'stair_hall', 'door'),
                  L(f'{s}_tower_up', f'tower0_{s}', f'tower1_{s}', 'stairs', rise=640),
                  L(f'{s}_tower_top', f'tower1_{s}', gen, 'stairs', rise=640),
                  L(f'{s}_tower_walk', f'tower1_{s}', f'wall_{s}s', 'open'),
                  L(f'wall_{s}_turret', f'wall_{s}s', f'turret_{s}', 'open'),
                  L(f'turret_{s}_wall', f'turret_{s}', f'wall_{s}n', 'open'),
                  L(f'{s}_wall_foundry', f'wall_{s}n', f'foundry_{s}', 'door'),
                  L(f'foundry_{s}_arcade', f'foundry_{s}', 'foundry', 'open'),
                  L(f'upper_{s}_gen', f'upper_{s}', gen, 'door'),
                  L(f'barrier_{s}u', f'upper_{s}', f'barrier_{s}', 'open'),
                  L(f'barrier_bay_{s}', 'barrier', f'barrier_{s}', 'open')]
    links += [
        L('grand_up', 'stair_hall', 'grand_landing', 'stairs', rise=640),
        L('foundry_landing', 'grand_landing', 'foundry', 'open'),
        L('foundry_store', 'foundry_w', 'store', 'door'),
        L('foundry_bays', 'foundry', 'bays', 'door', condition={'qbit': QBITS['bays_open']},
          notes="The shutters roll up when both machines are destroyed (state:machines)."),
        L('keep_up', 'foundry_e', 'keep_stair', 'open'),
        L('keep_up_top', 'keep_stair', 'upper_landing', 'stairs', rise=640),
        L('landing_barrier', 'upper_landing', 'barrier', 'open'),
        L('upper_w_war', 'upper_w', 'war_room', 'door'),
        L('upper_e_quarters', 'upper_e', 'quarters', 'door'),
        L('barrier_crown', 'barrier', 'crown_stair', 'door', condition={'qbit': QBITS['barrier_down']},
          notes="The field falls when the four pylons are dark (m35.barrier)."),
        L('crown_up', 'crown_stair', 'crown_landing', 'stairs', rise=640),
        L('landing_aviary', 'crown_landing', 'aviary_s', 'open', notes="Low arch, 256 high (D-32)."),
        L('aviary_mid', 'aviary_s', 'aviary_n', 'open'),
        L('aviary_threshold', 'aviary_n', 'threshold', 'open', notes="Low arch, 256 high (D-32)."),
        L('landing_kw', 'crown_landing', 'walk_s', 'door'),
        L('walk_mid', 'walk_s', 'walk_n', 'open'),
        L('kw_threshold', 'walk_n', 'threshold', 'door'),
        L('aviary_loft', 'aviary_s', 'loft', 'door'),
        L('threshold_throne', 'threshold', 'throne', 'door'),
        L('throne_apse', 'throne', 'apse', 'open'),
        L('throne_treasury', 'apse', 'treasury', 'door', condition={'qbit': QBITS['lord_xeen_slain']},
          notes="Opened by Lord Xeen's death."),
    ]
    plan = {
        'format': 0, 'level': min(level, 'L3'),
        'pitch': "Lord Xeen's castle on the clouds: black stone and gold with the Ancients' machines set into it. Four "
                 "elemental generators, two in the lower vaults and two at the tower tops, feed one field before the "
                 "crown stair; in the keep the guard-making machines keep stamping out Xeen's Guards. Above the "
                 "field, the aviary under open sky where Xeen's Pet roosts, then the throne room: Lord Xeen on his "
                 "dais and the Sixth Mirror behind him.",
        'purpose': "M35 Castle Xeen: m35.gen_* (four generators), m35.barrier, m35.pet, m35.lord_xeen_sight, "
                   "m35.lord_xeen, m35.scepter_ask/m35.scepter and the mirror's cinematic. 96 monsters at 42-70 (D-98) "
                   "plus Xeen's Pet 75 and Lord Xeen 85; treasure 5 and the hoard 6.",
        'mood': "Black stone under gold friezes, cold green-blue machine light, the crackle of the field, open sky over "
                "the battlements and the aviary.",
        'datum': 'arrival',
        'spaces': spaces,
        'links': links,
        'loops': [
            {'id': 'loop:west_ring', 'spaces': [f'room:{x}' for x in ('nave', 'aisle_w', 'ward_w', 'gallery_w',
                                                                      'vault_w', 'stair_hall')]},
            {'id': 'loop:east_ring', 'spaces': [f'room:{x}' for x in ('nave', 'aisle_e', 'ward_e', 'gallery_e',
                                                                      'vault_e', 'stair_hall')]},
            {'id': 'loop:west_climb', 'spaces': [f'room:{x}' for x in ('stair_hall', 'grand_landing', 'foundry',
                                                                       'foundry_w', 'wall_wn', 'turret_w', 'wall_ws',
                                                                       'tower1_w', 'tower0_w', 'gallery_w',
                                                                       'vault_w')]},
            {'id': 'loop:east_climb', 'spaces': [f'room:{x}' for x in ('stair_hall', 'grand_landing', 'foundry',
                                                                       'foundry_e', 'wall_en', 'turret_e', 'wall_es',
                                                                       'tower1_e', 'tower0_e', 'gallery_e',
                                                                       'vault_e')]},
            {'id': 'loop:towers', 'spaces': [f'room:{x}' for x in ('barrier', 'barrier_w', 'upper_w', 'gen_fire',
                                                                   'tower1_w', 'wall_ws', 'turret_w', 'wall_wn',
                                                                   'foundry_w', 'foundry', 'foundry_e', 'keep_stair',
                                                                   'upper_landing')]},
            {'id': 'loop:crown', 'spaces': [f'room:{x}' for x in ('crown_landing', 'aviary_s', 'aviary_n',
                                                                  'threshold', 'walk_n', 'walk_s')],
             'notes': "Round the Pet by the keeper's walk."},
        ],
        'entrances': [
            {'id': X9_ENTRANCE, 'space': 'room:gate', 'kind': 'both', 'facing': 'n',
             'how': "From X9's castle gate (m34.gate, the Lord Xeen doll): in the gatehall about 256 inside the leaves "
                    "facing north. The way out: the gate's two leaves (exit preset) to X9's entrance:xd19_gate."},
        ],
        'critical_path': [f'room:{x}' for x in (
            'gate', 'nave', 'aisle_w', 'ward_w', 'gallery_w', 'vault_w', 'stair_hall', 'vault_e', 'gallery_e',
            'tower0_e', 'tower1_e', 'gen_air', 'upper_e', 'barrier_e', 'barrier', 'barrier_w', 'upper_w', 'gen_fire',
            'tower1_w', 'wall_ws', 'turret_w', 'wall_wn', 'foundry_w', 'foundry', 'foundry_e', 'keep_stair',
            'upper_landing', 'barrier', 'crown_stair', 'crown_landing', 'aviary_s', 'aviary_n', 'threshold',
            'throne', 'apse')],
        'return_path': [f'room:{x}' for x in ('apse', 'treasury', 'apse', 'throne', 'threshold', 'walk_n', 'walk_s',
                                              'crown_landing', 'crown_stair', 'barrier', 'upper_landing',
                                              'keep_stair', 'foundry_e', 'foundry', 'grand_landing', 'stair_hall',
                                              'nave', 'gate')],
        'goals': [
            {'id': f'goal:gen_{g}', 'space': f"room:{d['room']}", 'kind': 'use', 'story': 'M35',
             'what': f"The {d['title']} destroyed (m35.gen_{g}).", 'gives': {'qbit': QBITS['gen_' + g]}}
            for g, d in GENS.items()] + [
            {'id': 'goal:lord_xeen', 'space': 'room:apse', 'kind': 'kill', 'story': 'M35',
             'what': "Lord Xeen slain (m35.lord_xeen).", 'gives': {'qbit': QBITS['lord_xeen_slain']}},
            {'id': 'goal:scepter', 'space': 'room:apse', 'kind': 'take', 'story': 'M35',
             'what': "The Scepter of Temporal Distortion (m35.scepter): the Sixth Mirror shatters.",
             'gives': {'qbit': QBITS['done']}}],
        'set_pieces': [
            {'id': 'set:foundry', 'kind': 'scripted', 'spaces': ['room:foundry', 'room:foundry_w', 'room:foundry_e'],
             'rule': "Two guard-making machines: while either stands a 45 s clock shows one of four hidden guards at a "
                     "chute; both destroyed show the rest and open the bays (D-47 Q7)."},
            {'id': 'set:barrier', 'kind': 'scripted', 'spaces': ['room:barrier'],
             'rule': "Four pylons, each named for its generator, go dark one by one; all dark, the field falls."},
            {'id': 'set:aviary', 'kind': 'scripted', 'spaces': ['room:aviary_s', 'room:aviary_n'],
             'rule': "Xeen's Pet under open sky, held in by two 256-high arches (D-32); the keeper's walk goes round."},
            {'id': 'set:throne', 'kind': 'scripted', 'spaces': ['room:throne', 'room:apse'],
             'rule': "First sight at the doors' plate; Lord Xeen harmed only by the Slayer Sword (E11); the scepter's "
                     "question and the mirror's cinematic."},
        ],
        'diagram': FlowDict(file='diagram.txt'),
        'totals': {'rooms': len(ROOMS), 'sectors': len(ROOMS), 'monsters_about': 98, 'chests': 7, 'loops': 6,
                   'doors': 25, 'fixed_actors': 0, 'floor_area_munits2': round(AREA / 1e6, 1)},
        'notes': "Class L (ROADMAP §5.1: 50-75 sectors, 120-200 M units², four set pieces, doors up to 25). From the "
                 "MU-6 graph devdocs/xeen/mockups/act5_graphs/xd19.graph.yml with D-47 (the guard pool at the "
                 "chutes, the generators' questions, one field and four pylons, the new elemental tiers, Lord Xeen "
                 "and E11, the scepter's question and its fallback). The graph's great hall, foundry, barrier hall, "
                 "aviary and throne room are split into rooms of their own (nave and aisles, machine bays, bays of "
                 "the barrier hall, the roost, the dais); its gatehall's 'two leaves' are the castle gate's.",
    }
    if level in ('L3', 'L4'):
        plan['sketch'] = FlowDict(file='rooms.yml', grid=512)
    return plan


DIAGRAM = r"""XD-19 Castle Xeen (x east, y north; four floors 640 apart)

 F3 1920  [TREASURY: hoard T6]  (opens at Lord Xeen's death)
               | sigil door
          [DAIS: LORD XEEN, throne + scepter, Sixth Mirror]
               | arch
          [THRONE ROOM]  <- sight plate inside the doors
               | two leaves
 [KEEPER'S WALK n]--door--[THRONE DOORS]--low arch--[AVIARY roost: XEEN'S PET] (open sky)
        |                                               |
 [KEEPER'S WALK s]--door--[CROWN LANDING]--low arch--[AVIARY]--door--[LOFT: chest]
                               ^ crown stair (behind the FIELD)
 F2 1280  [FIRE GEN (SW top)]-door-[UPPER W]-[BARRIER w bay]=[BARRIER HALL: 4 pylons, FIELD]=[e bay]-[UPPER E]-door-[AIR GEN (SE top)]
                                    | door        | open                                   | door
                               [WAR ROOM: chest] [KEEP STAIR TOP]<-keep stair      [DEMONS' QUARTERS: chest]
 F1  640  [WALL WALK W (sky)]-[turret]-[wall n]=door=[FOUNDRY W: machine]=[FOUNDRY]=[FOUNDRY E: machine]=door=[wall n]...[WALL WALK E]
          ^ SW tower upper stair         | door        | shutters      | keep stair foot
                                      [PARTS STORE]  [GUARD BAYS: gems]
                                               ^ grand landing <- grand stair
 F0    0  [SW tower]-[W GALLERY]-[W WARD]-[W AISLE]=[HALL OF XEENDOM]=[E AISLE]-[E WARD]-[E GALLERY]-[SE tower]
                         | door    | door               | two leaves            | door      | door
                   [COLD VAULT: water gen]-door-[STAIR HALL]-door-[GRAVEL VAULT: earth gen]
                             [BARRACKS]          [GATEHALL: arrival, gate to X9]       [ARMOURY]
"""


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def write(level):
    d = BRIEFS / level
    d.mkdir(parents=True, exist_ok=True)
    dump(d / 'project.yml', project_yml(level))
    dump(d / 'plan.yml', plan_yml(level))
    (d / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        rooms = rooms_yml()
        for r in rooms['rooms']:
            if r['id'] == 'room:gate':
                r['walls'] = gate_walls() + [w for w in r.get('walls', []) if w['wall'] != 'south']
            for w in r.get('walls', []):
                extra = WALL_PANELS.get((r['id'][5:], w['wall']))
                if extra:
                    w.update(extra)
        dump(d / 'rooms.yml', rooms)
    if level == 'L4':
        dump(d / 'objects.yml', objects_yml())
        dump(d / 'wiring.yml', wiring_yml())
        dump(d / 'atmosphere.yml', {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_cloud_sea'},
                                    'notes': "The wall walks and the aviary open to X9's sky (xeen_cloud_sea, D-47), "
                                             "the preset by its own name."})


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
    print('written', sys.argv[1:] or 'L1-L4', f'area {AREA / 1e6:.1f} M units², rooms {len(ROOMS)}, '
          f'monsters {sum(len(m) for _, _, m, _ in PLACED) + len(POOL)}')
