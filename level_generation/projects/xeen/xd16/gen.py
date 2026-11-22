#!/usr/bin/env python3
"""XD-16 Volcano Cave: writes the project files of devdocs/xeen/briefs/xd16/L1..L4 (lane A7 phase 5, sub-agent
agent:xeen-a7-xd16). Route after level_generation/projects/xeen/xd15/gen.py.

    python3 level_generation/projects/xeen/xd16/gen.py            all four levels
    python3 level_generation/projects/xeen/xd16/gen.py L4         one level

Rerun after every change here (level_generation/projects/xeen/xd16/cycle.sh); never hand-edit the written files. The playtests are
written by tools/gen_tests.py from the built ids.lock.yml.

Frame: x east, y north, z up; z 0 is X7's sill (2,250 on X7). The mouth opens west onto X7 (the party enters facing
east). Floor 0 (the burning halls) runs east to the fire lake, its fissure north to the demon shrine and the cinder run
back south to the stair head; the rough steps go down south to floor -1 (z -640: the stair foot, the lever hall with
the four lever stones, the steam vents, the magma caves and the slag pocket, the gate run's four slabs); the deep stair
goes down south to floor -2 (z -1280: the obsidian landing, the ember pocket, the glass caves, the ash pits, the magma
heart, the last cave and the cool passage behind the way's rock). No room stands over another; walls between rooms are
128 thick.
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / 'devdocs/xeen/briefs/xd16'


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


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------------------------------------------------------------------------------------------------------------
# Numbers
MAP_STATS_ID = 9142
MUSIC = 7                        # source/maps.yml XD-16
DEMON, DEVIL, SCREAMER = 11630, 11631, 11632
NAMES = {DEMON: 'Demon', DEVIL: 'Devil', SCREAMER: 'Screamer'}
LEVEL = {DEMON: 42, DEVIL: 50, SCREAMER: 58}
QBITS = {
    'demon_skull': 112520,       # A3's q-c26.demon_skull
    'devil_skull': 112521,       # A3's q-c26.devil_skull
    'way_open': 112522,          # A3's q-c26.done (the second skull sets it)
    'slab_1': 118050,            # map: the first lever stone pulled (one-way, D-43)
    'slab_2': 118051,
    'slab_3': 118052,
    'slab_4': 118053,
    'rock_drawn': 118054,        # map: the way's rock drawn open (D-47 Q4)
    'trap_1': 118055,            # map: the five trap chests burst (D-47 Q2), one each
    'trap_2': 118056,
    'trap_3': 118057,
    'trap_4': 118058,
    'trap_5': 118059,
}
X7_ARRIVAL = 'entrance:xd16_mouth'   # X7's named arrival (512, 9728, 2240) facing west, in xeen_x7.studio.yml

# ---------------------------------------------------------------------------------------------------------------------
# Textures: MM7 Thunderfist Mountain 7d07 (dungeon_families caves, D-45)
ROCK = S('c2b', 256, 256)              # dark brown-black cave rock: walls, roofs
SEAMS = S('c2bb', 256, 256)            # the same rock with glowing seams: the fissure, the pillar, the glass caves
RFLOOR = S('cfb1', 128, 128)           # rock floor
ASH = S('dirt', 128, 128)              # grey-brown ash floor (floor 0)
ASH2 = S('7dirttyl', 128, 128)         # the ash pits and the vault's floor
LAVA = S('lava', 256, 256)             # 7d07's lava (floors: lava burns)
WORKED = S('vlcwl1', 128, 256)         # the demon shrine's worked stone: MM6 Fire Lord 6d04's (D-89, A7 s28; was cwb)
REDROCK = S('cwb1', 128, 256)          # the vault rooms' red rock
CARVED = S('ch1b1', 128, 256)          # rough-carved stone: the altars' sides, the lever stones
BLACK = S('7solid01', 16, 16)          # black: the altars' tops, the slabs' edges
IRON = S('t5d1', 128, 256)             # iron doors (one leaf)
DAYLIGHT = S('xodaylt', 256, 128, fit=True, uneven=True)   # daylight in the mouth (XD-26's)

ROUGH = FlowDict(step=256, depth=96)

THEMES = [
    dict(id='theme:cave', wall=ROCK, floor=RFLOOR, ceiling=ROCK, reveal=ROCK, door=IRON,
         notes="The caves: 7d07's dark brown-black rock (c2b) on walls and roofs, its rock floor (cfb1)."),
    dict(id='theme:ash', wall=ROCK, floor=ASH, ceiling=ROCK, reveal=ROCK, door=IRON,
         notes="The ash floors of the burning halls: the same rock over 7d07's dirt."),
    dict(id='theme:seams', wall=SEAMS, floor=RFLOOR, ceiling=ROCK, reveal=SEAMS, door=IRON,
         notes="Rock split by glowing seams (c2bb): the fissure, the glass caves, the lever hall."),
    dict(id='theme:shrine', wall=WORKED, floor=RFLOOR, ceiling=ROCK, reveal=WORKED, door=IRON,
         notes="The demon shrine: 7d07's worked stone (cwb) under the cave's roof."),
    dict(id='theme:vault', wall=REDROCK, floor=ASH2, ceiling=ROCK, reveal=REDROCK, door=IRON,
         notes="The smoking passage and the vault of chests: red rock (cwb1), ash flags (7dirttyl)."),
    dict(id='theme:pits', wall=ROCK, floor=ASH2, ceiling=ROCK, reveal=ROCK, door=IRON,
         notes="The ash pits and the slag pocket: rock over grey ash (7dirttyl)."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms: id -> dict(name, pts, floor, ceiling, theme, extra)
ROOMS = {}


def room(rid, name, pts, floor, ceiling, theme, **extra):
    if len(pts) == 4 and all(isinstance(v, int) for v in pts):
        pts = rect_pts(*pts)
    ROOMS[rid] = dict(name=name, pts=pts, floor=floor, ceiling=ceiling, theme=theme, **extra)


F0, F1, F2 = 0, -640, -1280
# Floor 0, the burning halls
room('mouth', 'Cave mouth', (0, -384, 768, 384), F0, 512, 'cave')
room('ash_gallery', 'Ash gallery', (896, -320, 2944, 320), F0, 448, 'ash', rough=True)
room('vault_ante', 'Smoking passage', (1792, -1408, 2560, -448), F0, 448, 'vault')
room('chest_vault', 'Vault of chests', (1536, -2560, 2816, -1536), F0, 512, 'vault')
room('fire_lake', 'The fire lake', (3072, -1536, 6144, 1536), F0, 1152, 'ash', rough=True)
room('fissure', 'North fissure', (5248, 1664, 5888, 3328), F0, 768, 'seams', rough=True)
room('demon_shrine', "Demon skull's shrine", (4736, 3456, 6656, 4736), F0, 704, 'shrine')
room('cinder_run', 'Cinder run', (6272, -2304, 6656, 3328), F0, 384, 'ash', rough=True)
room('stair_head', 'Stair head', (5376, -2432, 6144, -1664), F0, 512, 'cave', rough=True)
room('rough_steps', 'Rough steps', (5568, -4608, 5952, -2560), F0, 448, 'cave',
     slope={'to': F1, 'toward': 'south', 'steps': 20}, ceiling_slope={'to': F1 + 448, 'toward': 'south'})
# Floor -1, the gate stones
room('stair_foot', 'Stair foot', (5376, -5504, 6144, -4736), F1, F1 + 512, 'cave', rough=True)
room('lever_hall', 'Lever hall', (3584, -6272, 5248, -4352), F1, F1 + 896, 'seams')
room('steam_vents', 'Steam vents', (5376, -7040, 6528, -5632), F1, F1 + 576, 'cave', rough=True)
room('magma_caves', 'Magma caves', (1792, -6016, 3456, -4480), F1, F1 + 768, 'cave', rough=True)
room('slag_pocket', 'Slag pocket', (768, -5632, 1664, -4864), F1, F1 + 448, 'pits', rough=True)
GATE_X = (4224, 4608)
GATE_SEGS = [(-6912, -6400), (-7552, -7040), (-8192, -7680), (-8832, -8320), (-9472, -8960)]
for i, (ya, yb) in enumerate(GATE_SEGS, 1):
    room(f'gate_run_{i}', f'Gate run {i}', (GATE_X[0], ya, GATE_X[1], yb), F1, F1 + 448, 'cave', space='gate_run')
room('deep_stair', 'Deep stair', (4224, -11520, 4608, -9600), F1, F1 + 448, 'cave',
     slope={'to': F2, 'toward': 'south', 'steps': 20}, ceiling_slope={'to': F2 + 448, 'toward': 'south'})
# Floor -2, the heart of the mountain
room('landing', 'Obsidian landing', (4096, -12416, 5632, -11648), F2, F2 + 512, 'seams', rough=True)
room('ember_pocket', 'Ember pocket', (5120, -11520, 5888, -10752), F2, F2 + 448, 'pits', rough=True)
room('glass_caves', 'Glass caves', [(2304, -15104), (3456, -15104), (3456, -12544), (3968, -12544), (3968, -11776),
                                    (2304, -11776)], F2, F2 + 640, 'seams', rough=True)
room('ash_pits', 'Ash pits', [(6272, -15104), (7424, -15104), (7424, -11776), (5760, -11776), (5760, -12544),
                              (6272, -12544)], F2, F2 + 576, 'pits', rough=True)
room('magma_heart', 'The magma heart', (3584, -15616, 6144, -12672), F2, F2 + 1280, 'cave', rough=True)
room('last_cave', 'The last cave', (4416, -16768, 5312, -15744), F2, F2 + 512, 'cave', rough=True)
room('cool_passage', 'Cool passage', (4672, -18432, 5056, -16896), F2, F2 + 448, 'cave')


def bbox(rid):
    xs = [p[0] for p in ROOMS[rid]['pts']]
    ys = [p[1] for p in ROOMS[rid]['pts']]
    return min(xs), min(ys), max(xs), max(ys)


def cx(rid):
    x0, y0, x1, y1 = bbox(rid)
    return (x0 + x1) // 2


def cy(rid):
    x0, y0, x1, y1 = bbox(rid)
    return (y0 + y1) // 2


# ---------------------------------------------------------------------------------------------------------------------
# Openings: absolute centre on the shared wall; the helper finds the walls (outline edges) and the `along`.


def walls_of(rid):
    o = ROOMS[rid]['pts']
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


OPEN_AT = {}   # opening id -> (point, width, axis, a, b)


def opening(oid, a, b, at, width, height, link=None, **kw):
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
            if p0[0] == p1[0] and q0[0] == q1[0]:
                ax = 1
            elif p0[1] == p1[1] and q0[1] == q1[1]:
                ax = 0
            else:
                continue
            o = 1 - ax
            gap = abs(p0[o] - q0[o])
            lo = max(min(p0[ax], p1[ax]), min(q0[ax], q1[ax]))
            hi = min(max(p0[ax], p1[ax]), max(q0[ax], q1[ax]))
            if hi - lo <= 0 or gap > 256 or gap == 0 or not (lo <= at <= hi):
                continue
            if best is None or gap < best[0]:
                best = (gap, i, j, lo, hi, ax, p0, p1)
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b} at {at}')
    gap, i, j, lo, hi, ax, p0, p1 = best
    if at - width / 2 < lo or at + width / 2 > hi:
        raise SystemExit(f'opening {oid} ({width} at {at}) does not fit the shared wall {lo}..{hi}')
    forward = (p1[ax] - p0[ax]) > 0
    along = (at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo)
    d = {'id': f'open:{oid}', 'from': f'room:{a}', 'to': f'room:{b}', 'from_wall': i, 'to_wall': j}
    if link:
        d['link'] = link
    if round(along, 4) != 0.5:
        d['along'] = round(along, 4)
    d['width'] = width
    d['height'] = height
    d.update(kw)
    pt = (at, p0[1]) if ax == 0 else (p0[0], at)
    OPEN_AT[oid] = (pt, width, ax, a, b)
    return d


OPENINGS = [
    # floor 0
    opening('mouth_ash', 'mouth', 'ash_gallery', 0, 448, 384, 'link:mouth_ash'),
    opening('ash_lake', 'ash_gallery', 'fire_lake', 0, 512, 416, 'link:ash_lake'),
    opening('ash_ante', 'ash_gallery', 'vault_ante', 2176, 320, 352, 'link:ash_ante'),
    opening('ante_vault', 'vault_ante', 'chest_vault', 2176, 192, 320, 'link:ante_vault',
            notes="The vault door: an iron leaf, smoke curling from under it."),
    opening('lake_fissure', 'fire_lake', 'fissure', 5568, 448, 576, 'link:lake_fissure'),
    opening('fissure_shrine', 'fissure', 'demon_shrine', 5568, 192, 320, 'link:fissure_shrine',
            notes="The shrine's iron door."),
    opening('shrine_cinder', 'demon_shrine', 'cinder_run', 6464, 320, 352, 'link:shrine_cinder'),
    opening('cinder_stair', 'cinder_run', 'stair_head', -1984, 320, 352, 'link:cinder_stair'),
    opening('lake_stair', 'fire_lake', 'stair_head', 5760, 448, 448, 'link:lake_stair'),
    opening('head_steps', 'stair_head', 'rough_steps', 5760, 352, 416, 'link:head_steps'),
    # floor -1
    opening('steps_foot', 'rough_steps', 'stair_foot', 5760, 352, 416, 'link:steps_foot'),
    opening('foot_lever', 'stair_foot', 'lever_hall', -5120, 384, 416, 'link:foot_lever'),
    opening('foot_vents', 'stair_foot', 'steam_vents', 5760, 384, 416, 'link:foot_vents'),
    opening('vents_lever', 'steam_vents', 'lever_hall', -5952, 320, 384, 'link:vents_lever'),
    opening('lever_magma', 'lever_hall', 'magma_caves', -5248, 384, 448, 'link:lever_magma'),
    opening('magma_slag', 'magma_caves', 'slag_pocket', -5248, 320, 352, 'link:magma_slag'),
    opening('lever_gate1', 'lever_hall', 'gate_run_1', 4416, 352, 416, 'link:lever_gates'),
    opening('gate_1_2', 'gate_run_1', 'gate_run_2', 4416, 256, 352, None, notes="The first slab."),
    opening('gate_2_3', 'gate_run_2', 'gate_run_3', 4416, 256, 352, None, notes="The second slab."),
    opening('gate_3_4', 'gate_run_3', 'gate_run_4', 4416, 256, 352, None, notes="The third slab."),
    opening('gate_4_5', 'gate_run_4', 'gate_run_5', 4416, 256, 352, None, notes="The fourth slab."),
    opening('gate_deep', 'gate_run_5', 'deep_stair', 4416, 352, 416, 'link:gates_stair'),
    # floor -2
    opening('deep_landing', 'deep_stair', 'landing', 4416, 352, 416, 'link:stair_down2'),
    opening('landing_ember', 'landing', 'ember_pocket', 5376, 320, 352, 'link:landing_ember'),
    opening('landing_glass', 'landing', 'glass_caves', -12096, 384, 416, 'link:landing_glass'),
    opening('landing_ash', 'landing', 'ash_pits', -12096, 384, 416, 'link:landing_ash'),
    opening('glass_heart', 'glass_caves', 'magma_heart', -14144, 448, 512, 'link:glass_heart'),
    opening('ash_heart', 'ash_pits', 'magma_heart', -14144, 448, 512, 'link:ash_heart'),
    opening('heart_last', 'magma_heart', 'last_cave', 4864, 512, 448, 'link:heart_last'),
    opening('last_way', 'last_cave', 'cool_passage', 4864, 256, 320, 'link:last_way',
            notes="The way's rock: a slab of bare rock that grinds aside when both skulls are broken."),
]

# ---------------------------------------------------------------------------------------------------------------------
# Walls: panels


def panel(pid, offset, length, bottom, height, surface, notes=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d.update(offset=offset, length=length, bottom=bottom, height=height, surface=surface)
    if notes:
        d['notes'] = notes
    return d


def woff(rid, wall, coord):
    """Offset along a wall of a rectangle room (walls counter-clockwise from the outline's first point)."""
    x0, y0, x1, y1 = bbox(rid)
    return {'south': coord - x0, 'east': coord - y0, 'north': x1 - coord, 'west': y1 - coord}[wall]


def pan(rid, wall, centre, length, bottom, height, surface, pid=None, notes=None):
    return panel(pid, woff(rid, wall, centre) - length // 2, length, bottom, height, surface, notes)


WALLS = {
}

# Pillar of the lever hall (a block, so that the four lever stones stand on its sides)
PILLAR = (4416, -5120)
PILLAR_HALF = 160


def block(at, size, rise, surface, top=None, notes=None, pid=None, base=None, end=None):
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
    if base is not None:
        d['base'] = base
    if notes:
        d['notes'] = notes
    return d


DEMON_ALTAR = (5696, 4480)
DEVIL_ALTAR = (4736, 0)
ALTAR_RISE = 96
DAIS = (2176, -2352)            # the vault's dais, along its south wall
DAIS_SIZE = (1088, 288)
DAIS_RISE = 32
# The six chests on the dais, west to east: which one is real (D-47 Q2: one real T5 chest, five traps)
VAULT_CHESTS = ['trap_1', 'trap_2', 'real', 'trap_3', 'trap_4', 'trap_5']
VAULT_X0 = 1760
VAULT_STEP = 168
HEARTH_RISE = 8
EMBERS = S('c2bb', 256, 256, scale=0.25)   # glowing seams, small: embers in the cracks under a trap chest


def vault_chest_at(i):
    return (VAULT_X0 + i * VAULT_STEP, DAIS[1] - 24)


PLATFORMS = {
    'demon_shrine': Flow([
        block((5696, 4416), (768, 384), 32, CARVED, RFLOOR, "The shrine's dais."),
        block(DEMON_ALTAR, (320, 160), ALTAR_RISE, SEAMS, ROCK,
              "The black altar: the skull of a demon on it (clicked: 'Destroy?', aaze0046:0).",
              pid='platform:demon_altar'),
    ]),
    'fire_lake': Flow([
        block(DEVIL_ALTAR, (320, 160), ALTAR_RISE, SEAMS, ROCK,
              "The black altar on the island: the skull of a devil on it (clicked: 'Destroy?', aaze0046:1).",
              pid='platform:devil_altar'),
    ]),
    'chest_vault': Flow([
        block(DAIS, DAIS_SIZE, DAIS_RISE, CARVED, ASH2, "The dais of the six chests along the vault's south wall.",
              pid='platform:dais'),
    ] + [block(vault_chest_at(i), (144, 112), HEARTH_RISE, SEAMS, EMBERS,
               "A trap chest's hearth stone: embers glowing in its cracks (the tell, D-47 Q2; the real chest stands "
               "on the bare ash of the dais).", base=DAIS_RISE)
         for i, which in enumerate(VAULT_CHESTS) if which != 'real']),
    'lever_hall': Flow([
        block(PILLAR, (2 * PILLAR_HALF, 2 * PILLAR_HALF), 640, SEAMS, BLACK,
              "The black pillar: four lever stones on its sides, one for each slab of the gate run.",
              pid='platform:pillar'),
    ]),
}

# Lava: sunken levels 128 deep, banks on the sides a party walks out by (D-47 Q5)
LAKE_PTS = [(3584, -1024), (5632, -1024), (5632, 1024), (3584, 1024), (3584, 128), (4352, 128), (4352, 384),
            (5120, 384), (5120, -384), (4352, -384), (4352, -128), (3584, -128)]
LAKE_BANK = [192, 192, 192, 192, 0, 0, 0, 0, 0, 0, 0, 192]
HEART_C = (4864, -14144)
HEART_R = 704


def octagon(c, r):
    k = int(r * 0.414)
    x, y = c
    return [(x - k, y - r), (x + k, y - r), (x + r, y - k), (x + r, y + k), (x + k, y + r), (x - k, y + r),
            (x - r, y + k), (x - r, y - k)]


CRUST = S('c2b', 256, 256)
LEVELS = {
    'fire_lake': Flow([
        FlowDict(id='level:lake', outline=Flow([F(*p) for p in LAKE_PTS]), floor=F0 - 128, bank=Flow(LAKE_BANK),
                 edge=CRUST, surface=LAVA,
                 notes="The lake of lava round the island, 128 below the shore: banks on its four outer sides (a "
                       "party that falls in walks out burning), crust edges along the causeway and the island."),
    ]),
    'magma_caves': Flow([
        FlowDict(id='level:river_n', outline=Flow([F(*p) for p in rect_pts(2304, -5088, 2688, -4608)]),
                 floor=F1 - 128, bank=F(0, 160, 0, 160), edge=CRUST, surface=LAVA,
                 notes="The lava river north of the stepping crust: banks on both long sides."),
        FlowDict(id='level:river_s', outline=Flow([F(*p) for p in rect_pts(2304, -5888, 2688, -5408)]),
                 floor=F1 - 128, bank=F(0, 160, 0, 160), edge=CRUST, surface=LAVA,
                 notes="The lava river south of the stepping crust: banks on both long sides."),
    ]),
    'magma_heart': Flow([
        FlowDict(id='level:heart', outline=Flow([F(*p) for p in octagon(HEART_C, HEART_R)]), floor=F2 - 128,
                 bank=192, edge=CRUST, surface=LAVA,
                 notes="The heart's pool of lava, 128 below the ring ledge, banked on every side."),
    ]),
}

STORE = set()
AMBIENT = {'mouth': 20, 'fire_lake': 16, 'magma_heart': 16, 'demon_shrine': 12, 'cool_passage': 10}

ROOM_NOTES = {
    'mouth': "The arrival (entrance:x7_mouth): daylight behind between the idols, heat ahead; the way out west.",
    'ash_gallery': "A wide passage floored with ash, red light ahead; the smoking passage south.",
    'vault_ante': "Smoke curls from under the vault's iron door; a lone chest by the wall.",
    'chest_vault': "Six chests on a dais: five burst in flame (the ones with embers glowing under them), one is real.",
    'fire_lake': "Set piece: a tall cavern round a lake of lava, the island with the devil skull's black altar in the "
                 "middle reached by a causeway of crust; the fissure north, the stair head south.",
    'fissure': "A crack running north from the lake's shore, glowing seams in its walls; the shrine's iron door.",
    'demon_shrine': "A worked chamber behind its iron door: braziers, the black altar with the demon skull on its dais; "
                    "the cinder run's mouth in the south-east corner.",
    'cinder_run': "A low burnt passage from the shrine back south along the lake's east side to the stair head.",
    'stair_head': "On the lake's south shore: the rough steps go down south into the dark.",
    'rough_steps': "Twenty rough steps down to the gate stones (640).",
    'stair_foot': "The steps' foot: the lever hall west, the steam vents south.",
    'lever_hall': "The black pillar with four lever stones on its sides; the gate run opens south, its slabs in sight.",
    'steam_vents': "Vents hissing out of the floor between heaps of rock; a chest in a dry corner.",
    'magma_caves': "A river of lava across the cave, the stepping crust over it; the slag pocket west.",
    'slag_pocket': "A dead end: an old pick and pack by a cooled slag heap, a chest.",
    'gate_run_1': "The gate run's mouth off the lever hall: the first slab ahead.",
    'gate_run_2': "Between the first and the second slab.",
    'gate_run_3': "Between the second and the third slab.",
    'gate_run_4': "Between the third and the fourth slab.",
    'gate_run_5': "Beyond the last slab: the deep stair down.",
    'deep_stair': "Twenty steps down to the heart of the mountain (640).",
    'landing': "The deep stair's foot: black glass underfoot, heat rising; the glass caves west, the ash pits east, the "
               "ember pocket north.",
    'ember_pocket': "A dead end with a chest, embers drifting from a vent in the roof.",
    'glass_caves': "Caves of black volcanic glass, the lava's light in every face; to the heart's west ledge.",
    'ash_pits': "Pits of grey ash; to the heart's east ledge.",
    'magma_heart': "Set piece: a pool of lava at the root of the mountain, a ring ledge round it, the roof lost in "
                   "smoke; the last cave south.",
    'last_cave': "A short cave ending in a slab of bare rock, hot to the touch: the way to Shangri-La.",
    'cool_passage': "Behind the rock: cool air and the smell of grass; its end leads to XD-17. "
                    "XD-17's way back arrives here (entrance:xd17_way).",
}


def rooms_yml():
    rooms = []
    for rid, r in ROOMS.items():
        d = {'id': f'room:{rid}', 'name': r['name']}
        if 'space' in r:
            d['space'] = f"room:{r['space']}"
        d['outline'] = Flow([F(*p) for p in r['pts']])
        d['floor'] = r['floor']
        if 'slope' in r:
            d['slope'] = FlowDict(r['slope'])
        d['ceiling'] = r['ceiling']
        if 'ceiling_slope' in r:
            d['ceiling_slope'] = FlowDict(r['ceiling_slope'])
        d['theme'] = f"theme:{r['theme']}"
        if r.get('rough'):
            d['rough'] = ROUGH
        if rid in STORE:
            d['store'] = True
        if rid in WALLS:
            d['walls'] = WALLS[rid]
        if rid in PLATFORMS:
            d['platforms'] = PLATFORMS[rid]
        if rid in LEVELS:
            d['levels'] = LEVELS[rid]
        d['ambient'] = AMBIENT.get(rid, 12)
        d['notes'] = ROOM_NOTES[rid]
        rooms.append(d)
    return {'format': 0, 'themes': THEMES, 'defaults': FlowDict(theme='theme:cave', ambient=12), 'rooms': rooms,
            'openings': OPENINGS,
            'notes': "XD-16 Volcano Cave at L4: floor 0 (the mouth, the ash gallery, the smoking passage and the vault of "
                     "chests, the fire lake with the devil skull's island, the fissure, the demon shrine, the cinder "
                     "run, the stair head), the rough steps down to floor -640 (the stair foot, the lever hall, the "
                     "steam vents, the magma caves and the slag pocket, the gate run's four slabs), the deep stair down "
                     "to floor -1280 (the obsidian landing, the ember pocket, the glass caves, the ash pits, the magma "
                     "heart, the last cave, the cool passage). x east, y north; the mouth opens west onto X7. Written "
                     "by output/studio_cal/xd16/tools/gen.py."}


# ---------------------------------------------------------------------------------------------------------------------
# objects.yml

# Placed monsters: room -> group, [(row, (x, y), facing)]
PLACED = [
    ('ash_gallery', 10, [(DEMON, (1664, -128), 180), (DEMON, (2048, 128), 180), (DEMON, (2560, -96), 180)]),
    ('fire_lake', 11, [(DEMON, (3328, 1344), 180), (DEMON, (3328, -1344), 180), (DEVIL, (5920, 1344), 180)]),
    ('fire_lake', 12, [(DEVIL, (4544, 192), 180), (DEVIL, (4928, 192), 180), (DEVIL, (4928, -192), 180)]),
    ('fissure', 13, [(DEMON, (5440, 2368), 270), (DEMON, (5696, 2880), 270)]),
    ('demon_shrine', 14, [(DEMON, (5248, 4096), 270), (DEMON, (6144, 4096), 270), (DEMON, (5696, 3840), 270)]),
    ('cinder_run', 15, [(DEMON, (6464, 1792), 90), (DEMON, (6464, -512), 90)]),
    ('vault_ante', 16, [(DEVIL, (2048, -960), 90), (DEVIL, (2368, -1152), 90)]),
    ('lever_hall', 20, [(DEMON, (3904, -4672), 0), (DEMON, (3904, -5888), 0), (DEVIL, (4928, -5888), 0)]),
    ('steam_vents', 21, [(DEMON, (5760, -6272), 90), (DEMON, (6208, -6656), 90), (DEVIL, (5952, -6784), 90)]),
    ('magma_caves', 22, [(DEMON, (3136, -4800), 0), (DEMON, (3136, -5696), 0), (DEVIL, (2048, -5248), 0)]),
    ('gate_run_5', 23, [(DEVIL, (4320, -9216), 90), (DEVIL, (4512, -9216), 90)]),
    ('gate_run_4', 23, [(SCREAMER, (4416, -8576), 90)]),
    ('ember_pocket', 30, [(DEVIL, (5376, -11008), 270), (SCREAMER, (5696, -11136), 270)]),
    ('glass_caves', 31, [(DEMON, (2880, -14336), 90), (DEMON, (2880, -13248), 90), (DEVIL, (3456, -12160), 90)]),
    ('ash_pits', 32, [(DEVIL, (6848, -13248), 90), (SCREAMER, (6848, -14336), 90)]),
    ('magma_heart', 33, [(SCREAMER, (4864, -12928), 270), (SCREAMER, (3744, -14144), 270),
                         (SCREAMER, (5984, -14144), 270)]),
]

START = (256, 0)
XD17_ARRIVAL = (4864, -18176)
SLAB_NAMES = ['First slab', 'Second slab', 'Third slab', 'Fourth slab']
LEVER_SIDES = ['n', 'e', 's', 'w']


def objects_yml():
    slab = dict(kind='slide_down', thickness=48, speed=96, surface=SEAMS, tile=True,
                edge_surface=BLACK, top_surface=BLACK)
    doors = [
        {'id': 'door:vault', 'opening': 'open:ante_vault', 'kind': 'slide_up', 'thickness': 24,
         'speed': 192, 'surface': S('t5d1', 128, 256, fit=True),
         'notes': "The vault's iron door (one leaf); smoke curls from under it."},
        {'id': 'door:shrine', 'opening': 'open:fissure_shrine', 'kind': 'slide_up', 'thickness': 24,
         'speed': 192, 'surface': S('t5d1', 128, 256, fit=True), 'notes': "The demon shrine's iron door."},
    ]
    for n, oid in enumerate(('gate_1_2', 'gate_2_3', 'gate_3_4', 'gate_4_5'), 1):
        doors.append({'id': f'door:slab_{n}', 'opening': f'open:{oid}', **slab,
                      'notes': f"The {SLAB_NAMES[n - 1].lower()} of black rock across the gate run: its lever stone "
                               f"on the pillar grinds it down into the floor (one-way, D-43)."})
    doors.append({'id': 'door:way', 'opening': 'open:last_way', 'kind': 'slide_left', 'thickness': 48, 'speed': 64,
                  'surface': SEAMS, 'tile': True, 'edge_surface': ROCK,
                  'notes': "The way's rock: bare rock, hot to the touch; it grinds aside into the wall when the second "
                           "skull breaks (q-c26.done) and stands open on every later load (D-47 Q4)."})
    switches = []
    for n in range(1, 5):
        switches.append({'id': f'switch:lever_{n}', 'room': 'room:lever_hall', 'kind': 'lever',
                         'block': 'platform:pillar', 'side': LEVER_SIDES[n - 1], 'height': 128,
                         'size': F(24, 72), 'reach': 64, 'off': S('ch1b1', 128, 256), 'base': S('cwb', 128, 256),
                         'notes': f"The {SLAB_NAMES[n - 1].lower()}'s lever stone on the pillar's "
                                  f"{ {'n': 'north', 'e': 'east', 's': 'south', 'w': 'west'}[LEVER_SIDES[n - 1]]} side."})
    chests = [
        {'id': 'chest:ante', 'room': 'room:vault_ante', 'at': F(1904, -1280), 'kind': 'ch1', 'treasure_level': 5, 'random_items': 3, 'gold': 2500, 'notes': "A lone chest by the wall (the source's (15,11))."},
        {'id': 'chest:vents', 'room': 'room:steam_vents', 'at': F(6400, -6912), 'kind': 'ch1', 'facing': 'w',
         'treasure_level': 5, 'random_items': 3, 'gold': 2500, 'notes': "A chest wedged in a dry corner."},
        {'id': 'chest:slag', 'room': 'room:slag_pocket', 'at': F(896, -5504), 'kind': 'ch1', 'facing': 'e',
         'treasure_level': 5, 'random_items': 3, 'gold': 2500, 'notes': "An old dwarf's chest by his pick and pack."},
        {'id': 'chest:ember', 'room': 'room:ember_pocket', 'at': F(5760, -10880), 'kind': 'ch1', 'facing': 'w',
         'treasure_level': 5, 'random_items': 3, 'gold': 2500, 'notes': "A chest at the pocket's end."},
    ]
    for i, which in enumerate(VAULT_CHESTS):
        at = vault_chest_at(i)
        if which == 'real':
            chests.append({'id': 'chest:vault_real', 'room': 'room:chest_vault', 'at': F(*at), 'kind': 'ch1',
                           'facing': 'n', 'treasure_level': 5, 'random_items': 4, 'gold': 4000,
                           'notes': "The vault's one real chest (the third from the west): no embers under it."})
        else:
            chests.append({'id': f'chest:{which}', 'room': 'room:chest_vault', 'at': F(*at), 'kind': 'ch1',
                           'facing': 'n', 'random_items': 0,
                           'notes': "A trap chest (D-47 Q2): embers glow under it; it bursts in flame on the first "
                                    "opening and holds nothing."})
    monsters = []
    for rid, group, ms in PLACED:
        n0 = sum(1 for m in monsters if m['room'] == f'room:{rid}')
        for n, (mon, at, facing) in enumerate(ms, n0 + 1):
            monsters.append({'id': f'monster:{rid}_{n}', 'room': f'room:{rid}', 'monster': mon, 'at': F(*at),
                             'facing': facing, 'hostile': True, 'group': group})

    decos = []

    def deco(name, rid, d, at, **kw):
        e = {'id': f'deco:{name}', 'room': f'room:{rid}', 'decoration': d, 'at': F(*at)}
        e.update(kw)
        decos.append(e)

    # The skulls on the altars (they break: destructibles)
    deco('demon_skull', 'demon_shrine', '7dec20', DEMON_ALTAR, floor_height=F0 + ALTAR_RISE,
         notes="The skull of a demon on the black altar.")
    deco('devil_skull', 'fire_lake', '7dec20', DEVIL_ALTAR, floor_height=F0 + ALTAR_RISE,
         notes="The skull of a devil on the island's black altar.")
    # Wall torches in the worked rooms; floor braziers in the shrine
    for i, (rid, at) in enumerate(TORCHES, 1):
        deco(f'torch_{i:02d}', rid, 'torch01', on_wall(rid, at), height=176)
    for i, at in enumerate([(5248, 4480), (6144, 4480), (5248, 3712), (6144, 3712)], 1):
        deco(f'brazier_{i}', 'demon_shrine', 'flamb00', at)
    # Bones and rock about the caves (cave rubble, off the walking lines, by the walls)
    for i, (rid, d, at) in enumerate([
            ('mouth', 'dec29', (128, 320)), ('mouth', '7dec18', (640, -320)),
            ('ash_gallery', '7dec18', (1216, 240)), ('ash_gallery', 'dec29', (2752, -256)),
            ('fire_lake', 'dec29', (3200, 1440)), ('fire_lake', '7dec18', (6048, -1440)),
            ('fire_lake', 'dec19', (3168, -1440)),
            ('fissure', 'dec29', (5344, 3200)),
            ('cinder_run', 'dec29', (6560, 2560)), ('cinder_run', 'dec29', (6368, 448)),
            ('stair_head', '7dec18', (5472, -2336)),
            ('steam_vents', 'dec29', (5504, -6912)), ('steam_vents', '7dec18', (6400, -5760)),
            ('magma_caves', 'dec29', (1920, -4608)), ('magma_caves', 'dec29', (3328, -5888)),
            ('slag_pocket', '7rock03', (1536, -4992)),
            ('glass_caves', '7dec18', (2432, -11904)), ('glass_caves', 'dec29', (3328, -14976)),
            ('ash_pits', 'dec29', (7296, -11904)), ('ash_pits', '7dec18', (6400, -14976)),
            ('magma_heart', 'dec29', (3712, -12800)), ('magma_heart', '7dec18', (6016, -15488)),
            ('last_cave', 'dec19', (5184, -16640)),
            ('ember_pocket', 'Brnrock0', (5248, -10880)),
            ('chest_vault', 'dec29', (1664, -1664)),
            ('slag_pocket', '7dec18', (1536, -5504)),
    ], 1):
        deco(f'rubble_{i:02d}', rid, d, at)
    # A wisp of smoke over each trap chest's embers (D-51 polish, the engine's `smoke` since merge point 25)
    for i, which in enumerate(VAULT_CHESTS):
        if which != 'real':
            x, y = vault_chest_at(i)
            deco(f'smoke_{which}', 'chest_vault', 'smoke', (x, y + 88), floor_height=F0 + DAIS_RISE,
                 notes="A thin smoke over the embers at the trap chest's foot (the tell); the real chest has none.")

    lights = []

    def light(name, rid, at, height, radius, color, **kw):
        d = {'id': f'light:{name}', 'room': f'room:{rid}', 'at': F(*at), 'height': height, 'radius': radius,
             'color': F(*color)}
        d.update(kw)
        lights.append(d)

    lava = (255, 104, 40)
    ember = (255, 120, 48)
    dim = (200, 120, 80)
    PULSE = FlowDict(intensity=F(0.6, 1), frequency=0.33)
    # The lake: four glows over the lava, low, pulsing
    for i, at in enumerate([(3840, 704), (3840, -704), (5376, 704), (5376, -704), (5376, 0)], 1):
        light(f'lake_{i}', 'fire_lake', at, 160, 1600, lava, pulse=PULSE)
    light('isle', 'fire_lake', DEVIL_ALTAR, 512, 1000, (255, 150, 90))
    for i, at in enumerate([(4352, -13440), (5376, -13440), (4352, -14848), (5376, -14848), HEART_C], 1):
        light(f'heart_{i}', 'magma_heart', at, 160, 1700, lava, pulse=PULSE)
    for i, at in enumerate([(2496, -4800), (2496, -5664)], 1):
        light(f'river_{i}', 'magma_caves', at, 160, 1300, lava, pulse=PULSE)
    # Each trap chest: a faint ember glow at its foot (the tell); the real chest has none
    for i, which in enumerate(VAULT_CHESTS):
        if which != 'real':
            x, y = vault_chest_at(i)
            light(f'embers_{which}', 'chest_vault', (x, y + 64), 24, 240, (255, 100, 24),
                  pulse=FlowDict(intensity=F(0.45, 1), frequency=0.7, phase=round(i / 6, 2)),
                  floor_height=F0 + DAIS_RISE)
    # Room lights
    plain = {'mouth': ((384, 0), 360, 1200, (255, 236, 200)),
             'ash_gallery': ((1920, 0), 320, 1400, dim),
             'vault_ante': ((2176, -928), 320, 900, dim),
             'chest_vault': ((2176, -1856), 400, 1100, dim),
             'fissure': ((5568, 2496), 520, 1100, (255, 150, 70)),
             'demon_shrine': ((5696, 4096), 560, 1500, (255, 140, 80)),
             'cinder_run': ((6464, 512), 280, 1600, dim),
             'stair_head': ((5760, -2048), 400, 900, dim),
             'stair_foot': ((5760, -5120), 400, 900, dim),
             'lever_hall': ((4416, -4608), 720, 1400, (230, 150, 110)),
             'steam_vents': ((5952, -6336), 440, 1200, dim),
             'slag_pocket': ((1216, -5248), 320, 800, dim),
             'gate_run_1': ((4416, -6656), 320, 600, dim),
             'gate_run_3': ((4416, -7936), 320, 600, dim),
             'gate_run_5': ((4416, -9216), 320, 600, dim),
             'landing': ((4864, -12032), 400, 1100, (210, 120, 120)),
             'ember_pocket': ((5504, -11136), 320, 800, ember),
             'glass_caves': ((2880, -13440), 480, 1500, (230, 110, 90)),
             'ash_pits': ((6848, -13440), 440, 1500, dim),
             'last_cave': ((4864, -16256), 400, 900, (230, 110, 70)),
             'cool_passage': ((4864, -17664), 320, 900, (190, 210, 230))}
    for rid, (at, h, rad, col) in plain.items():
        light(rid, rid, at, h, rad, col)
    light('ember_vent', 'ember_pocket', (5376, -10944), 400, 500, (255, 90, 30), pulse=FlowDict(intensity=F(0.3, 1),
                                                                                              frequency=0.5))
    light('steps', 'rough_steps', (5760, -3584), 320, 1000, dim)
    light('deep_steps', 'deep_stair', (4416, -10560), 320, 1000, dim)

    sounds = [
        {'id': 'sound:lake', 'room': 'room:fire_lake', 'at': F(4608, 0), 'sound': 'bubbling cauldron01',
         'radius': 3200, 'inner_radius': 1200, 'volume': 0.5, 'notes': "The lava's bubbling (the shipped cauldron)."},
        {'id': 'sound:heart', 'room': 'room:magma_heart', 'at': F(*HEART_C), 'sound': 'bubbling cauldron01',
         'radius': 3200, 'inner_radius': 1200, 'volume': 0.5},
        {'id': 'sound:river', 'room': 'room:magma_caves', 'at': F(2496, -5248), 'sound': 'bubbling cauldron01',
         'radius': 2200, 'inner_radius': 700, 'volume': 0.4},
        {'id': 'sound:cool', 'room': 'room:cool_passage', 'at': F(4864, -18176), 'sound': 'whistling wind',
         'radius': 1400, 'inner_radius': 400, 'volume': 0.3, 'notes': "Cool air through the fallen stones."},
    ]

    exits = [
        {'id': 'exit:way_end', 'room': 'room:cool_passage', 'at': F(4864, -18432),
         'size': F(256, 320), 'surface': S('7solid01', 128, 256),
         'to': 'exit:xd17_way', 'notes': "The passage's end: fallen stones with cool air between them, the way to XD-17."},
        {'id': 'exit:mouth', 'room': 'room:mouth', 'wall': 'west', 'size': F(448, 384), 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
         'to': 'exit:x7_mouth', 'notes': "The cave mouth: daylight on X7's slope between the idols."},
    ]
    destructibles = [
        {'id': 'destructible:demon_skull', 'of': 'deco:demon_skull', 'hp': 1, 'damage': False, 'trigger_only': True,
         'material': 'stone', 'effect_scale': 0.6,
         'notes': "Broken only by the altar's question (q-c26.demon_skull); shown broken on every later load."},
        {'id': 'destructible:devil_skull', 'of': 'deco:devil_skull', 'hp': 1, 'damage': False, 'trigger_only': True,
         'material': 'stone', 'effect_scale': 0.6,
         'notes': "Broken only by the altar's question (q-c26.devil_skull)."},
    ]
    floors = [
        {'id': 'floor:lake', 'of': 'level:lake', 'kind': 'lava'},
        {'id': 'floor:river_n', 'of': 'level:river_n', 'kind': 'lava'},
        {'id': 'floor:river_s', 'of': 'level:river_s', 'kind': 'lava'},
        {'id': 'floor:heart', 'of': 'level:heart', 'kind': 'lava'},
    ]

    return {'format': 0,
            'start': {'room': 'room:mouth', 'at': F(*START), 'facing': 'e',
                      'notes': "In the cave mouth about 256 inside, facing east into the cave."},
            'arrivals': [
                FlowDict(entrance='entrance:x7_mouth', room='room:mouth', at=F(*START), facing='e',
                         notes="In the cave mouth about 256 inside, facing east (X7's door between the idols arrives "
                               "here)."),
                FlowDict(entrance='entrance:xd17_way', room='room:cool_passage', at=F(*XD17_ARRIVAL), facing='n',
                         notes="In the cool passage about 256 inside its far end, facing back down toward the last "
                               "cave (XD-17's way back arrives here; XD-17 is not built)."),
            ],
            'doors': doors, 'floors': floors, 'sounds': sounds, 'lights': lights, 'switches': switches,
            'chests': chests, 'monsters': monsters, 'decorations': decos, 'exits': exits,
            'destructibles': destructibles, 'relations': []}


def on_wall(rid, at, inset=12):
    x0, y0, x1, y1 = bbox(rid)
    x, y = at
    side = min((x - x0, 'w'), (x1 - x, 'e'), (y - y0, 's'), (y1 - y, 'n'))[1]
    return {'w': (x0 + inset, y), 'e': (x1 - inset, y), 's': (x, y0 + inset), 'n': (x, y1 - inset)}[side]


TORCHES = [
    ('demon_shrine', (4736, 4096)), ('demon_shrine', (6656, 4096)), ('demon_shrine', (5248, 4736)),
    ('demon_shrine', (6144, 4736)),
    ('vault_ante', (1792, -768)), ('chest_vault', (1536, -1920)), ('chest_vault', (2816, -1920)),
]


def check_torches():
    for rid, at in TORCHES:
        p = on_wall(rid, at)
        for oid, (pt, width, ax, a, b) in OPEN_AT.items():
            if rid not in (a, b):
                continue
            dx, dy = abs(p[0] - pt[0]), abs(p[1] - pt[1])
            along, across = (dx, dy) if ax == 0 else (dy, dx)
            if across < 200 and along < width / 2 + 96:
                raise SystemExit(f'torch in {rid} at {p} too near opening {oid}')


# ---------------------------------------------------------------------------------------------------------------------
# wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def sound_at(name, x, y, z):
    return {'lua': f'evt.PlaySoundName("{name}", {x}, {y}, {z})'}


SKULLS = {
    'demon': dict(altar='platform:demon_altar', deco='destructible:demon_skull', bit='demon_skull',
                  ask="The skull of a demon grins wickedly at you, and you have a sudden desire to smash it.  Destroy?",
                  ref='aaze0046:0', at=(DEMON_ALTAR[0], DEMON_ALTAR[1], 140), title='Demon skull'),
    'devil': dict(altar='platform:devil_altar', deco='destructible:devil_skull', bit='devil_skull',
                  ask="The skull of a devil stares at you as though daring you to damage it.  Destroy?",
                  ref='aaze0046:1', at=(DEVIL_ALTAR[0], DEVIL_ALTAR[1], 140), title='Devil skull'),
}


def wiring_yml():
    ev = []

    def e(**kw):
        ev.append(kw)

    e(id='evt:arrive', preset='script', trigger='timer', every=1, once=True,
      effects=[{'lua': 'local x, y = evt.GetPartyPosition()\n'
                       'if x >= 0 and x <= 768 and y >= -384 and y <= 384 then\n'
                       '    evt.StatusText("Heat on your face and a red glow far ahead. Behind you, daylight between a '
                       'demon and a devil of black stone.", 6)\n'
                       'end'}],
      notes="Say where the party is (a one-shot timer: the party arrives standing in the mouth). Only in the mouth "
            "(room:mouth): a party back from XD-17 arrives in the cool passage, where daylight behind would be wrong.")
    e(id='evt:exit_x7', preset='exit', source='exit:mouth', title='Leave the Volcano Cave',
      notes="Out to X7 (installed) at its named arrival entrance:xd16_mouth (512, 9728, 2240) facing west: the game's "
            "own leave window (D-24); 'Leave the Volcano Cave?' (aaze0046:5) is its meaning.")
    # Doors
    e(id='evt:door_vault', preset='door', source='door:vault', title='Door')
    e(id='evt:door_shrine', preset='door', source='door:shrine', title='Iron door')
    # The skulls (D-47; A3's hooks): a real choice, the source's question; Yes calls the hook and breaks the skull
    for k, s in SKULLS.items():
        e(id=f'evt:{k}_skull', preset='script', source=s['altar'], title=s['title'],
          condition={'not': {'qbit': s['bit']}},
          question={'ask': s['ask'], 'answers': ['yes', 'y']},
          effects=[hook(f'q-c26.{k}_skull'), {'destroy': s['deco']}, sound_at('xeen_fire_ignite', *s['at'])],
          else_effects=[hook(f'q-c26.{k}_skull')],
          notes=f"{s['ref']}: the source's question (a real choice). Yes: A3's q-c26.{k}_skull (5,000; the second "
                f"skull sets q-c26.done 112522) and the skull breaks; once broken the altar gives the hook's "
                f"'splinters' line.")
        e(id=f'evt:{k}_skull_load', preset='script', trigger='load', condition={'qbit': s['bit']},
          effects=[{'destroy': s['deco']}], notes="A broken skull stays broken on every later load.")
    # The way (D-47 Q4): the rock grinds open in the same visit as the second skull, and on every later load
    e(id='evt:way_grind', preset='script', trigger='timer', every=1,
      condition={'all': [{'qbit': 'way_open'}, {'not': {'qbit': 'rock_drawn'}}]}, opens=['door:way'],
      effects=[{'qbit': 'rock_drawn'}, sound_at('6stone door0101', 4864, -16768, -1100)],
      notes="The skull that sets q-c26.done grinds the way's rock open within a second in the same visit (the "
            "skulls are two floors up); map qbit rock_drawn 118054 marks it drawn.")
    e(id='evt:way_load', preset='script', trigger='load', condition={'qbit': 'way_open'}, opens=['door:way'],
      effects=[{'qbit': 'rock_drawn'}], notes="With q-c26.done the rock stands open on every load.")
    e(id='evt:door_way', preset='door', source='door:way', title='Bare rock', action='open',
      condition={'qbit': 'way_open'}, else_effects=[hook('q-c26.way')],
      notes="Before done the rock's click gives q-c26.way's fail text ('Bare rock, hot to the touch. ...'); after it "
            "stands open.")
    e(id='evt:cool_air', preset='script', trigger='step', source='room:cool_passage', once=True,
      condition={'qbit': 'way_open'}, effects=[hook('q-c26.way')],
      notes="The first step into the cool passage: q-c26.way's text ('Beyond the last cave, cool air ...').")
    e(id='evt:way_end', preset='exit', source='exit:way_end', title='The way to Shangri-La',
      notes="Out to XD-17 (installed, A5) at its named arrival entrance:xd16_way (-1280, -4736, 4) facing north: the "
            "game's own leave window (D-24).")
    # The four lever stones (D-47 Q3; A3's q-c26.lever, q-c26.lever_down)
    for n in range(1, 5):
        e(id=f'evt:lever_{n}', preset='switch', source=f'switch:lever_{n}', title=SLAB_NAMES[n - 1],
          condition={'not': {'qbit': f'slab_{n}'}}, opens=[f'door:slab_{n}'],
          effects=[{'qbit': f'slab_{n}'}, hook('q-c26.lever')],
          else_effects=[hook('q-c26.lever_down')],
          notes=f"One-way (D-43): lowers the {SLAB_NAMES[n - 1].lower()} (map qbit {QBITS[f'slab_{n}']}); a second "
                "click gives 'The lever is down.'")
        e(id=f'evt:slab_{n}', preset='text', source=f'door:slab_{n}', title=SLAB_NAMES[n - 1],
          text="A slab of black rock fills the passage. It does not move for you.",
          notes="Clicking the slab itself: its lever is on the pillar in the lever hall.")
    for n in range(1, 5):
        e(id=f'evt:slab_{n}_load', preset='switch', trigger='load', condition={'qbit': f'slab_{n}'},
          opens=[f'door:slab_{n}'], notes="A lowered slab stays down on every later load.")
    # The vault of chests (D-47 Q2)
    for i, which in enumerate(VAULT_CHESTS):
        x, y = vault_chest_at(i)
        if which == 'real':
            e(id='evt:chest_vault_real', preset='chest', source='chest:vault_real', title='Chest')
            continue
        e(id=f'evt:chest_{which}', preset='script', source=f'chest:{which}', title='Chest',
          condition={'not': {'qbit': which}},
          effects=[{'qbit': which}, sound_at('explosion', x, y, 64),
                   {'damage': {'amount': 50, 'kind': 'fire', 'who': 'all'}},
                   {'text': "The chest explodes!"}],
          else_effects=[{'text': "The chest is empty."}],
          notes=f"A trap chest (map qbit {QBITS[which]}): the first opening bursts it, Fire 50 on each member (about "
                "10-15 % of a level-48 member's HP), 'The chest explodes!' (aaze0046:6); after that 'The chest is "
                "empty.' (aaze0046:2).")
    for c in ('ante', 'vents', 'slag', 'ember'):
        e(id=f'evt:chest_{c}', preset='chest', source=f'chest:{c}', title='Chest')
    ev.sort(key=lambda x: x['id'])
    return {'format': 0, 'variables': [], 'events': ev}


# ---------------------------------------------------------------------------------------------------------------------
# project.yml


def project_yml(level):
    return {
        'format': 0, 'id': 'xeen_xd16', 'name': 'Volcano Cave', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon',
        'identity': {'shape': 'cave', 'family': '7d07', 'seen': [  # D-89 (A7 s28)
            "a scorched cave mouth and the ash gallery's broken rock",
            "the fire lake and the magma heart: rough caves of Thunderfist rock, floors that rise and fall, high vaults",
            "the demon skull's shrine in the Fire Lord's black volcanic stone"]},
        'map_code': 'XD-16', 'units': FlowDict(plan_grid=512),
        'extent': FlowDict(footprint_cells=F(14, 37), climbs='s'),
        'map_stats': {
            'id': MAP_STATS_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5,
            'trap_dice': 8, 'perception_difficulty': 15, 'refill_days': 672, 'music': MUSIC, 'environment': 'cave',
            'lock_difficulty': 15,
            'slots': [FlowDict(monster='Xeen Demon', tier=5, per_marker=F(1, 2), weight=100)],
        },
        'neighbours': [{
            'id': 'exit:x7_mouth', 'to': 'xeen_x7.odm', 'kind': 'door', 'arrival': X7_ARRIVAL,
            'arrival_hint': "On X7 in front of the Volcano Cave's mouth at Mount Firestone's west foot, between the "
                            "demon and devil idols (A5's entrance:xd16_mouth, (512, 9728, 2240) facing west).",
            'notes': "X7 installed (A5). The way out names X7's named arrival entrance:xd16_mouth; the facing comes "
                     "with it. X7's door:xd16 (thing:xd16_mouth, 'Enter the Volcano Cave?', aaze0017:1) names this "
                     "map's arrival entrance:x7_mouth: in the cave mouth (256, 0, 0) facing east."},
            {
            'id': 'exit:xd17_way', 'to': 'xeen_xd17.blv', 'kind': 'door', 'arrival': 'entrance:xd16_way',
            'screen': FlowDict(text=5017),
            'arrival_hint': "In XD-17 (Shangri-La's way) at A5's entrance:xd16_way (-1280, -4736, 4) facing north.",
            'notes': "XD-17 installed (A5, 01:45). XD-17's way back names this map's arrival entrance:xd17_way: in the "
                     "cool passage (4864, -18176, -1280) facing north."}],
        'qbits': dict(sorted(QBITS.items())),
        'notes': f"Xeen design brief, level {level}: XD-16 Volcano Cave, on X7 (Mount Firestone), Act V, class M "
                 "(MU-6 graph devdocs/xeen/mockups/act5_graphs/xd16.graph.yml, decider D-47 in "
                 "mockups/act5_a7_decisions.md). Q-C26: the demon and devil skulls (A3's q-c26.demon_skull, "
                 "devil_skull; the second sets done 112522), the four lever stones and slabs (q-c26.lever, "
                 "lever_down), the way's rock and the cool passage (q-c26.way). Monsters, all placed and hostile in "
                 "groups 10-33 by room: 20 Demon 11630 (42), 14 Devil 11631 (50), 6 Screamer 11632 (58): 40 (under "
                 "M's 45, D-47 Q1). Rest encounters 10 % from the demons at Dif 5 (D-47 Q6). Map card 9142, music 7, "
                 "treasure 5. Map qbits 118050-118059: slab_1-4 118050-118053, rock_drawn 118054, trap_1-5 "
                 "118055-118059. The way out to X7 (installed) is live; the cool passage's end to XD-17 is live "
                 "(XD-17 not built).",
    }


# ---------------------------------------------------------------------------------------------------------------------
# plan.yml

PLAN_SPACES = [
    ('mouth', 'cave', 'S', "The arrival (entrance:x7_mouth): heat on the face, daylight behind, the demon and devil "
                           "idols outside framing it. Quiet (D-11.3).", None),
    ('ash_gallery', 'corridor', 'M', "A wide passage floored with grey ash, red light ahead; the first demons. A side "
                                     "way south to the vault.", None),
    ('vault_ante', 'corridor', 'S', "Smoke curling from under the vault's iron door; a lone chest by the wall (the "
                                    "source's (15,11), a real one).", 5),
    ('chest_vault', 'room', 'S', "The source's six chests on a dais: five are traps that burst in flame (embers glow "
                                 "under them; Fire 50 on each member once, 'The chest explodes!', then 'The chest is "
                                 "empty.'), one is a real T5 chest (D-47 Q2). Quiet.", 5),
    ('fire_lake', 'hall', 'L', "Set piece: a tall cavern round a lake of lava 128 below the shore (banked, it burns), "
                               "lit from below; the island in the middle (the source's (9,9)) with the devil skull's "
                               "black altar ('Destroy?', aaze0046:1; q-c26.devil_skull) and three devils, reached by "
                               "a causeway of crust; shores north (the fissure) and south (the stair head).", None),
    ('fissure', 'corridor', 'M', "A crack running north from the lake's shore, glowing seams in the walls; the demon "
                                 "shrine's iron door.", None),
    ('demon_shrine', 'room', 'M', "The source's (0,15): a worked chamber, braziers, the demon skull on a black altar "
                                  "('Destroy?', aaze0046:0; q-c26.demon_skull); three demons. The cinder run south.",
     None),
    ('cinder_run', 'corridor', 'M', "A low burnt passage from the shrine back down to the stair head (the floor-0 "
                                    "loop).", None),
    ('stair_head', 'stair', 'S', "On the lake's south shore: rough steps down into the dark (walked; no sign).", None),
    ('rough_steps', 'stair', 'S', "Twenty rough steps down to the gate stones.", None),
    ('stair_foot', 'stair', 'S', "The steps' foot; ways west to the lever hall and south to the steam vents.", None),
    ('lever_hall', 'hall', 'M', "The source's four wall switches: four lever stones round a black pillar, each "
                                "hovering its slab's name, each lowering one of the four slabs across the gate run "
                                "(in sight of the pillar); one-way (D-43, D-47 Q3).", None),
    ('steam_vents', 'cave', 'M', "Vents hissing out of the floor, a chest wedged in a dry corner.", 5),
    ('magma_caves', 'cave', 'M', "A river of lava across the floor (banked, it burns), stepping crust across it; to "
                                 "the slag pocket.", None),
    ('slag_pocket', 'cave', 'S', "A dead end with a chest: an old dwarf's pick and pack by a cooled slag heap.", 5),
    ('gate_run', 'corridor', 'M', "A straight passage south from the lever hall closed by the four slabs in a row "
                                  "(four doors, opened by the four levers); beyond the last slab the deep stair.",
     None),
    ('deep_stair', 'stair', 'S', "Twenty steps down to the heart (walked; no sign).", None),
    ('landing', 'stair', 'S', "The deep stair's foot: black glass underfoot, heat rising from ahead.", None),
    ('ember_pocket', 'cave', 'S', "A dead end with a chest, embers drifting from a vent in the roof.", 5),
    ('glass_caves', 'cave', 'M', "Caves of black volcanic glass, the lava's light in every face; to the heart's west "
                                 "ledge.", None),
    ('ash_pits', 'cave', 'M', "Pits of grey ash; to the heart's east ledge (the floor -2 loop).", None),
    ('magma_heart', 'hall', 'L', "Set piece: a pool of lava at the mountain's root (banked, it burns), a ring ledge "
                                 "round it, the roof lost in smoke; the Screamers on the ledge. The last cave south.",
     None),
    ('last_cave', 'cave', 'S', "The source's (9,10): a short cave ending in a slab of bare rock. Before q-c26.done its "
                               "click is q-c26.way's fail text; the second skull grinds it open in the same visit, and "
                               "it stands open on every later load (D-47 Q4).", None),
    ('cool_passage', 'corridor', 'S', "Behind the rock: cool air and the smell of grass (q-c26.way's text at the first "
                                      "step); its end leads to XD-17; XD-17's way back "
                                      "arrives here (entrance:xd17_way). Quiet.", None),
]


def plan_yml(level):
    pop = {}
    for rid, group, ms in PLACED:
        sid = ROOMS[rid].get('space', rid)
        for mon, _, _ in ms:
            pop.setdefault(sid, {}).setdefault(mon, 0)
            pop[sid][mon] += 1
    spaces = []
    for sid, kind, size, purpose, chest in PLAN_SPACES:
        rids = [r for r in ROOMS if ROOMS[r].get('space', r) == sid]
        xs = [bbox(r)[0] for r in rids] + [bbox(r)[2] for r in rids]
        ys = [bbox(r)[1] for r in rids] + [bbox(r)[3] for r in rids]
        r = ROOMS[rids[0]]
        kind = {'cave': 'room', 'hall': 'room', 'stair': 'corridor'}.get(kind, kind)
        s = {'id': f'room:{sid}', 'name': r['name'] if len(rids) == 1 else 'Gate run', 'kind': kind, 'size': size,
             'extent': F(max(xs) - min(xs), max(ys) - min(ys))}
        s['floor'] = r['floor'] if 'slope' not in r else F(min(r['floor'], r['slope']['to']),
                                                            max(r['floor'], r['slope']['to']))
        s['purpose'] = purpose
        if sid in pop:
            s['population'] = [{'actor': m, 'groups': 1, 'levels': F(LEVEL[m], LEVEL[m]),
                                'notes': f"{n} placed {NAMES[m]}{'s' if n > 1 else ''}."} for m, n in pop[sid].items()]
        else:
            s['empty'] = True
        if chest:
            s['treasure'] = [FlowDict(kind='chest', count=1, tier=chest)]
        spaces.append(s)

    def L(lid, a, b, kind, **kw):
        return {'id': f'link:{lid}', 'from': f'room:{a}', 'to': f'room:{b}', 'kind': kind, **kw}

    links = [
        L('mouth_ash', 'mouth', 'ash_gallery', 'open'),
        L('ash_lake', 'ash_gallery', 'fire_lake', 'open'),
        L('lake_fissure', 'fire_lake', 'fissure', 'open', notes="North shore."),
        L('fissure_shrine', 'fissure', 'demon_shrine', 'door', notes="Iron door."),
        L('shrine_cinder', 'demon_shrine', 'cinder_run', 'open'),
        L('cinder_stair', 'cinder_run', 'stair_head', 'open'),
        L('lake_stair', 'fire_lake', 'stair_head', 'open', notes="South shore."),
        L('ash_ante', 'ash_gallery', 'vault_ante', 'open'),
        L('ante_vault', 'vault_ante', 'chest_vault', 'door', notes="Vault door."),
        L('head_steps', 'stair_head', 'rough_steps', 'open'),
        L('steps_foot', 'rough_steps', 'stair_foot', 'stairs', rise=-640),
        L('foot_lever', 'stair_foot', 'lever_hall', 'open'),
        L('foot_vents', 'stair_foot', 'steam_vents', 'open'),
        L('vents_lever', 'steam_vents', 'lever_hall', 'open'),
        L('lever_magma', 'lever_hall', 'magma_caves', 'open'),
        L('magma_slag', 'magma_caves', 'slag_pocket', 'open', notes="Over the stepping crust."),
        L('lever_gates', 'lever_hall', 'gate_run', 'door',
          condition={'all': [{'qbit': QBITS[f'slab_{n}']} for n in range(1, 5)]},
          notes="Four slabs in a row across the gate run, each lowered by its lever stone on the pillar."),
        L('gates_stair', 'gate_run', 'deep_stair', 'open'),
        L('stair_down2', 'deep_stair', 'landing', 'stairs', rise=-640),
        L('landing_ember', 'landing', 'ember_pocket', 'open'),
        L('landing_glass', 'landing', 'glass_caves', 'open'),
        L('landing_ash', 'landing', 'ash_pits', 'open'),
        L('glass_heart', 'glass_caves', 'magma_heart', 'open', notes="West ledge."),
        L('ash_heart', 'ash_pits', 'magma_heart', 'open', notes="East ledge."),
        L('heart_last', 'magma_heart', 'last_cave', 'open'),
        L('last_way', 'last_cave', 'cool_passage', 'door', condition={'qbit': QBITS['way_open']},
          notes="The way's rock: open with q-c26.done."),
    ]
    plan = {
        'format': 0, 'level': min(level, 'L3'),
        'pitch': "A burning cave behind the demon and devil idols at Mount Firestone's west foot. A tall cavern round a "
                 "lake of lava with the devil skull on its island, the demon skull in a shrine beyond the fissure; "
                 "below, four lever stones round a black pillar lower four slabs across the gate run; at the root of "
                 "the mountain the magma heart, and beyond it a wall of bare rock that grinds open when both skulls "
                 "are broken: cool air, and the smell of grass.",
        'purpose': "Q-C26 Shangri-La (Act V, party 48-52): the two skulls (q-c26.demon_skull, devil_skull; the second "
                   "sets done), the gate stones (q-c26.lever), the way (q-c26.way, to XD-17). 40 demons at 42-58 "
                   "(Demon, Devil, Screamer), treasure 5, five trap chests.",
        'mood': "Dark brown-black rock lit red from below by lava; ash underfoot; worked stone and braziers in the "
                "demon shrine; cool blue air at the very end.",
        'datum': 'arrival',
        'spaces': spaces,
        'links': links,
        'loops': [
            {'id': 'loop:lake_ring', 'spaces': [f'room:{x}' for x in ('fire_lake', 'fissure', 'demon_shrine',
                                                                      'cinder_run', 'stair_head')],
             'notes': "Round the fire lake: the north shore, the fissure and the shrine, back by the cinder run to the "
                      "south shore."},
            {'id': 'loop:vents', 'spaces': [f'room:{x}' for x in ('stair_foot', 'lever_hall', 'steam_vents')],
             'notes': "The lever hall from the stair foot directly or through the steam vents."},
            {'id': 'loop:heart_ledges', 'spaces': [f'room:{x}' for x in ('landing', 'glass_caves', 'magma_heart',
                                                                         'ash_pits')],
             'notes': "Round the heart: in by the glass caves and the west ledge, out by the east ledge and the ash "
                      "pits."},
        ],
        'entrances': [
            {'id': 'entrance:x7_mouth', 'space': 'room:mouth', 'kind': 'both', 'neighbour': 'exit:x7_mouth',
             'facing': 'e',
             'how': "From X7's door between the idols ('Enter the Volcano Cave?', aaze0017:1): in the cave mouth about "
                    "256 inside, facing east; the mouth leads back out (the exit preset)."},
            {'id': 'entrance:xd17_way', 'space': 'room:cool_passage', 'kind': 'arrival', 'facing': 'n',
             'how': "XD-17's way back from Shangri-La: in the cool passage about 256 inside its far end, facing back "
                    "down toward the last cave. The passage's end leads to XD-17's entrance:xd16_way."},
        ],
        'critical_path': [f'room:{x}' for x in ('mouth', 'ash_gallery', 'fire_lake', 'fissure', 'demon_shrine',
                                                'cinder_run', 'stair_head', 'rough_steps', 'stair_foot',
                                                'lever_hall', 'gate_run', 'deep_stair', 'landing', 'glass_caves',
                                                'magma_heart', 'last_cave', 'cool_passage')],
        'return_path': [f'room:{x}' for x in ('cool_passage', 'last_cave', 'magma_heart', 'ash_pits', 'landing',
                                              'deep_stair', 'gate_run', 'lever_hall', 'steam_vents', 'stair_foot',
                                              'rough_steps', 'stair_head', 'fire_lake', 'ash_gallery', 'mouth')],
        'goals': [
            {'id': 'goal:devil_skull', 'space': 'room:fire_lake', 'kind': 'use', 'story': 'Q-C26',
             'what': "Smash the devil skull on the island's altar (q-c26.devil_skull 112521).",
             'gives': {'qbit': 112521}},
            {'id': 'goal:demon_skull', 'space': 'room:demon_shrine', 'kind': 'use', 'story': 'Q-C26',
             'what': "Smash the demon skull on the shrine's altar (q-c26.demon_skull 112520).",
             'gives': {'qbit': 112520}},
            {'id': 'goal:way', 'space': 'room:cool_passage', 'kind': 'reach', 'story': 'Q-C26',
             'what': "Through the way's rock into the cool passage (q-c26.done 112522), the way to Shangri-La."},
        ],
        'set_pieces': [
            {'id': 'set:fire_lake', 'kind': 'scripted', 'spaces': ['room:fire_lake'],
             'rule': "A lake of lava round the island of the devil skull, a causeway of crust to it; the lava burns, "
                     "its outer banks let a party walk out."},
            {'id': 'set:gate_stones', 'kind': 'scripted', 'spaces': ['room:lever_hall', 'room:gate_run'],
             'rule': "Four lever stones on the black pillar, each lowering its own slab across the gate run."},
            {'id': 'set:heart', 'kind': 'scripted', 'spaces': ['room:magma_heart', 'room:last_cave'],
             'rule': "The magma heart's pool and the last cave's rock, which grinds open when both skulls break."},
        ],
        'diagram': FlowDict(file='diagram.txt'),
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(ROOMS), 'monsters_about': 40, 'chests': 5, 'loops': 3,
                   'doors': 7, 'fixed_actors': 0, 'floor_area_munits2': round(floor_area() / 1e6)},
        'notes': "Class M (MAPS: 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors); 40 monsters "
                 "under M's 45 by MAPS §0's own count (D-47 Q1). From the MU-6 graph "
                 "devdocs/xeen/mockups/act5_graphs/xd16.graph.yml and D-47 (five trap chests with a tell and one real; "
                 "four one-way lever slabs; the way's rock opening in the same visit; lava banked so a party walks "
                 "out; stairs walked, no signs). The devil skull's island is part of the fire lake's room (the lake a "
                 "sunken level round it); the gate run is five short rooms between its four slabs.",
    }
    if level in ('L3', 'L4'):
        plan['sketch'] = FlowDict(file='rooms.yml', grid=512)
    return plan


def floor_area():
    tot = 0
    for r in ROOMS.values():
        p = r['pts']
        tot += abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
                       for i in range(len(p)))) / 2
    return tot


DIAGRAM = r"""XD-16 Volcano Cave (x east, y north; the mouth opens west onto X7; floors 0 / -640 / -1280)

  0      [DEMON SHRINE: demon skull, braziers]======cinder run (south, along the lake's east side)
                 | iron door                              |
             [Fissure]                                    |
                 |                                        |
  [Mouth]--[Ash gallery]--[FIRE LAKE: lava round the island, DEVIL SKULL; causeway]
     ^X7       |                         |                |
           [Smoking passage: chest]   [Stair head]--------+
               | iron door               | rough steps (20, south)
           [VAULT: 6 chests, 5 traps]    v
  -640   [Slag pocket]--[MAGMA CAVES: river, crust]--[LEVER HALL: pillar, 4 levers]--[Stair foot]
                                                          |   \__ [Steam vents: chest] __/
                                               [Gate run: slab 1..4 (one per lever)]
                                                          | deep stair (20, south)
  -1280             [Ember pocket: chest]--[Obsidian landing]
                     [Glass caves]------------/    \----------[Ash pits]
                          \__ west ledge [MAGMA HEART: lava pool] east ledge __/
                                          [Last cave: the rock (q-c26.done)]
                                          [Cool passage] -> XD-17        
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
        dump(d / 'rooms.yml', rooms_yml())
    if level == 'L4':
        dump(d / 'objects.yml', objects_yml())
        dump(d / 'wiring.yml', wiring_yml())


if __name__ == '__main__':
    check_torches()
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
        if lv == 'L4':
            # D-89 cave shape (A7 s28, tools/xeen/cave_shape.py): floors that rise and fall, vaulted roofs, rough
            # walls in the natural caves (every opening names its walls by number: no corner is cut)
            sys.path.insert(0, str(ROOT / 'tools' / 'xeen'))
            import cave_shape
            cave_shape.shape_l4(BRIEFS / 'L4', {
                'room:mouth': {'floor': 48, 'roof': 128},
                'room:ash_gallery': {'floor': 48, 'roof': 160},
                'room:fire_lake': {'floor': 96, 'roof': 320, 'stalactites': (4, 256)},
                'room:fissure': {'floor': 64, 'roof': 256},
                'room:cinder_run': {'floor': 32, 'roof': 96},
                'room:stair_head': {'floor': 48, 'roof': 160},
                'room:stair_foot': {'floor': 48, 'roof': 160},
                'room:steam_vents': {'floor': 64, 'roof': 192, 'stalactites': (2, 160)},
                'room:magma_caves': {'floor': 64, 'roof': 256},
                'room:slag_pocket': {'floor': 48, 'roof': 128},
                'room:lever_hall': {'floor': 48, 'roof': 256, 'stalactites': (3, 224)},
                'room:ash_pits': {'floor': 64, 'roof': 192},
                'room:glass_caves': {'floor': 64, 'roof': 192},
                'room:landing': {'floor': 48, 'roof': 160},
                'room:ember_pocket': {'floor': 48, 'roof': 128},
                'room:magma_heart': {'floor': 96, 'roof': 384, 'stalactites': (4, 288)},
                'room:last_cave': {'floor': 48, 'roof': 160},
                'room:cool_passage': {'floor': 32, 'roof': 96},
            })
    print('written', sys.argv[1:] or 'L1-L4', 'floor area', round(floor_area() / 1e6, 1), 'M; rooms', len(ROOMS))
