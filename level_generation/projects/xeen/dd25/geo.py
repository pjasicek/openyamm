#!/usr/bin/env python3
"""DD-25 Bosco's Hall: the geometry (rooms, openings) shared by L2, L3 and L4.

One frame: x east, y north, z 0 = the gate's sill (D5's 2688). The gate (two t09a03a/t09a03b leaves) in the east wall
of the gate passage at x 2304; the hall runs west into the crag:
- the gate passage (arrival), the gate hall (the Alehall's front on its south wall), the smiths' gallery north of the
  gate hall and the great hall (Bosco's Forge and the Mailwright's Burrow on its north wall, the forge bay between),
  the great hall (the round hearth, the well, benches), the burrow lane south of it (the Tinker's Burrow), the King's
  steps west up 128 to the throne hall (two hinged leaves; the dais, the throne under xdbosban, the King's Hall door,
  the tasting table);
- the guild stair from the lane's west end down to the Deep Guild hall at z -384 (the guild's door).
Walls between rooms are 128 thick. The six house doors are clicked wall panels (no geometry behind them): a timber or
stone house front of three panels laid once each (`fit: true`), shingle eaves over the timber fronts, a sign above the
services' doors.
"""

G0, DEEP, THRONE = 0, -384, 128


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM7 Stone City 7d24's town quarter (D-62 Q35).
CWB = S_('cwb', 128, 256)          # dressed stone walls
ROCK = S_('cwb1', 128, 256)        # raw rock: vaults, the lane, the guild hall
FLAGS = S_('7tfb1', 128, 128)      # dressed flag floors
SOIL = S_('cfb1', 128, 128)        # rock floors (lane, guild, bay)
TRIM = S_('trim1_32', 32, 64)      # the corner strips (wood)
POST = S_('7trimd', 128, 256)      # upright planks: benches, the table, the throne
PLANK = S_('7trimda', 256, 128)    # level planks: tops of benches and the table
HEARTH = S_('7cdb', 128, 256)      # the hearth's sandstone ring
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
EAVES = S_('hhm1rf', 128, 128)     # shingle eaves over the timber fronts
LEAF_L = S_('hdr1dl', 128, 256)    # the throne hall's left leaf
LEAF_R = S_('hdr1dr', 128, 256)    # and its right leaf
GATE_L = S_('t09a03a', 128, 256)   # the gate's left leaf (D5's pair, D-49)
GATE_R = S_('t09a03b', 128, 256)   # the gate's right leaf: t09a03a's own right-hand picture
BANNER = S_('xdbosban', 128, 256)  # Bosco's banner (new, D-62 Q35)

# House fronts: (side panels, door panel, eaves, sign)
FRONTS = {
    'forge': (S_('hdp1b', 128, 256), S_('hdp1d', 128, 256), True, S_('sgweapon', 64, 64)),
    'mailwright': (S_('hdp2b', 128, 256), S_('hdp2d', 128, 256), True, None),
    'alehall': (S_('hdm2b', 128, 256), S_('hdm2d', 128, 256), True, S_('7sgtvrn', 64, 64)),
    'tinker': (S_('hdp2b', 128, 256), S_('hdp2d', 128, 256), True, None),
    'guild_earth': (S_('hdm1b', 128, 256), S_('hdm1d', 128, 256), False, S_('sgearth', 64, 64)),
    'kings_hall': (S_('hdr1b', 128, 256), S_('hdm1d', 128, 256), False, None),
}
FRONT_W, FRONT_H = 160, 320        # each front panel: the 128 x 256 picture at 1.25

THEMES = [
    {'id': 'theme:hall', 'wall': CWB, 'floor': FLAGS, 'ceiling': ROCK, 'door': LEAF_L, 'ends': {'length': 32, 'surface': TRIM},
     'notes': "The dwarves' dressed halls: 7d24's dressed stone (cwb) under the raw rock vault (cwb1), flag floors (7tfb1), timber corner strips (trim1_32)."},
    {'id': 'theme:throne', 'wall': CWB, 'floor': FLAGS, 'ceiling': ROCK, 'door': LEAF_L, 'ends': {'length': 32, 'surface': TRIM},
     'notes': "The throne hall: as the halls, its dais and furniture in planks (7trimd, 7trimda)."},
    {'id': 'theme:rock', 'wall': ROCK, 'floor': SOIL, 'ceiling': ROCK, 'door': LEAF_L,
     'notes': "Dug rock: the burrow lane, the guild stair and the Deep Guild hall (cwb1 over cfb1)."},
]

# id: (name, box, floor, ceiling, theme)
R = {
    'gate_passage': ("Gate passage", (1792, -448, 2304, 448), G0, 384, 'theme:hall'),
    'gate_hall': ("Gate hall", (896, -512, 1664, 768), G0, 640, 'theme:hall'),
    'great_hall': ("Great hall", (-1280, -768, 768, 768), G0, 768, 'theme:hall'),
    'smiths_gallery': ("Smiths' gallery", (-512, 896, 1664, 1408), G0, 640, 'theme:hall'),
    'forge_bay': ("Forge bay", (512, 1536, 768, 1792), G0, 288, 'theme:rock'),
    'burrow_lane': ("Burrow lane", (-1280, -1408, 0, -896), G0, 512, 'theme:rock'),
    'kings_steps': ("King's steps", (-1920, -384, -1408, 384), G0, 576, 'theme:hall'),
    'throne_hall': ("Throne hall", (-3584, -640, -2048, 640), THRONE, THRONE + 768, 'theme:throne'),
    'guild_hall': ("Deep Guild hall", (-3840, -1792, -2560, -768), DEEP, DEEP + 576, 'theme:rock'),
}
# Climbing tunnels: (name, path, floor, to, height above the floor, theme)
P = {
    'guild_stair': ("Guild stair", [[-1408, -1152], [-2432, -1152]], G0, DEEP, 384, 'theme:rock'),
}
PATH_WIDTH = 320

ORDER = sorted(list(R) + list(P))


def outline(rid):
    x0, y0, x1, y1 = R[rid][1]
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def shared(a, b):
    """The facing axis-aligned walls of rooms a and b: (gap, wall in a, wall in b, lo, hi, axis, p0, p1)."""
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
            if p0[0] == p1[0] and q0[0] == q1[0]:
                gap = abs(p0[0] - q0[0])
                lo = max(min(p0[1], p1[1]), min(q0[1], q1[1]))
                hi = min(max(p0[1], p1[1]), max(q0[1], q1[1]))
                ax = 1
            elif p0[1] == p1[1] and q0[1] == q1[1]:
                gap = abs(p0[1] - q0[1])
                lo = max(min(p0[0], p1[0]), min(q0[0], q1[0]))
                hi = min(max(p0[0], p1[0]), max(q0[0], q1[0]))
                ax = 0
            else:
                continue
            if hi - lo <= 0 or gap > 512 or gap == 0:
                continue
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            nx, ny = dy, -dx
            if ax == 1 and (q0[0] - p0[0]) * nx <= 0:
                continue
            if ax == 0 and (q0[1] - p0[1]) * ny <= 0:
                continue
            cand = (gap, i, j, lo, hi, ax, p0, p1)
            if best is None or gap < best[0]:
                best = cand
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b}')
    return best


def opening(oid, a, b, at=None, width=256, height=320, link=None, **kw):
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b}
    if a not in P and b not in P:
        gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
        if at is None:
            at = (lo + hi) / 2
        if at - width / 2 < lo + 32 or at + width / 2 > hi - 32:
            raise SystemExit(f'{oid}: {width} wide at {at} does not fit {lo}..{hi}')
        forward = (p1[ax] - p0[ax]) > 0
        along = round((at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo), 4)
        d['from_wall'] = i
        d['to_wall'] = j
        if along != 0.5:
            d['along'] = along
    if link:
        d['link'] = link
    d['width'] = 'full' if (a in P or b in P) else width
    d['height'] = height
    d.update(kw)
    return d


OPENINGS = [
    opening('open:passage_hall', 'gate_passage', 'gate_hall', at=0, width=384, height=320, link='link:gate_hall'),
    opening('open:gatehall_great', 'gate_hall', 'great_hall', at=128, width=640, height=448, link='link:gatehall_great',
            shape='arch', apex=544),
    opening('open:gatehall_gallery', 'gate_hall', 'smiths_gallery', at=1280, width=384, height=384, link='link:gatehall_gallery',
            shape='arch', apex=480),
    opening('open:great_gallery', 'great_hall', 'smiths_gallery', at=128, width=512, height=448, link='link:great_gallery',
            shape='arch', apex=544),
    opening('open:gallery_bay', 'smiths_gallery', 'forge_bay', at=640, width=160, height=224, link='link:forge_bay'),
    opening('open:great_lane', 'great_hall', 'burrow_lane', at=-384, width=384, height=384, link='link:great_burrow',
            shape='arch', apex=448),
    opening('open:great_steps', 'great_hall', 'kings_steps', at=0, width=512, height=448, link='link:great_steps',
            shape='arch', apex=544),
    opening('open:steps_throne', 'kings_steps', 'throne_hall', at=0, width=384, height=320, link='link:steps_throne'),
    opening('open:lane_stair', 'burrow_lane', 'guild_stair', width=320, height=352, link='link:guild_stair'),
    opening('open:stair_guild', 'guild_stair', 'guild_hall', width=320, height=352, link='link:guild_stair'),
]


def plat(pid, at, size, rise, surface, top=None, notes=None, **kw):
    d = {'id': pid, 'at': at, 'size': size, 'rise': rise, 'surface': surface}
    for k in ('id', 'at', 'size'):
        if d[k] is None:
            del d[k]
    if top:
        d['top_surface'] = top
    d.update(kw)
    if notes:
        d['notes'] = notes
    return d


def front(key, centre, bottom=0, notes=None):
    """A house front on a wall, centred `centre` along it (from the wall's start corner): side, door, side panels laid
    once each at 160 x 320; shingle eaves 80 high over the timber fronts; the sign 96 square above."""
    side, door, eaves, sign = FRONTS[key]
    w = FRONT_W
    out = [
        {'id': f'panel:front_{key}_1', 'offset': centre - 3 * w // 2, 'length': w, 'bottom': bottom, 'height': FRONT_H,
         'surface': dict(side, fit=True)},
        {'id': f'door:{key}', 'offset': centre - w // 2, 'length': w, 'bottom': bottom, 'height': FRONT_H,
         'surface': dict(door, fit=True), 'notes': notes},
        {'id': f'panel:front_{key}_2', 'offset': centre + w // 2, 'length': w, 'bottom': bottom, 'height': FRONT_H,
         'surface': dict(side, fit=True)},
    ]
    top = bottom + FRONT_H
    if eaves:
        out.append({'offset': centre - 3 * w // 2, 'length': 3 * w, 'bottom': top, 'height': 80,
                    'surface': dict(EAVES, scale=0.625)})
        top += 80
    if sign:
        out.append({'offset': centre - 48, 'length': 96, 'bottom': top + 16, 'height': 96,
                    'surface': dict(sign, fit=True)})
    # panels without a click carry no id (the front sides)
    for p in out:
        if p.get('id', '').startswith('panel:front_'):
            del p['id']
        if p.get('notes') is None:
            p.pop('notes', None)
    return out


# The throne hall's dais: three steps across the hall's west end (each 64 deep, 32 high), the top 96 over the floor.
DAIS = [(-3296, 576, 32), (-3328, 512, 64), (-3360, 448, 96)]   # (centre x, depth, rise); full width 1280
DAIS_TOP = THRONE + 96
THRONE_Y = 192
KINGS_DOOR_Y = -288

EXTRA = {
    'gate_passage': {
        'notes': "Inside the gate's two leaves (the exit to D5): the arrival 256 in from them; two of Bosco's guards in its corners by the gate.",
    },
    'gate_hall': {
        'walls': [{'wall': 0, 'panels': front('alehall', 288, notes="The Alehall (house 4702): Brunna's tavern, the first door from the gate.")}],
        'notes': "The Alehall's front on the south wall, a pair of ale barrels beside it; the wide arch west into the great hall, the arch north into the smiths' gallery.",
    },
    'great_hall': {
        'platforms': [
            plat('platform:hearth', None, None, 48, dict(HEARTH), dict(SOIL),
                 "The round hearth in the middle of the hall (7cdb), its fire on top: the town's square.",
                 outline=[[-256 + round(224 * c), round(224 * s)] for c, s in
                          [(1, 0), (0.7071, 0.7071), (0, 1), (-0.7071, 0.7071), (-1, 0), (-0.7071, -0.7071), (0, -1), (0.7071, -0.7071)]]),
            plat('platform:well', [384, -656], [224, 224], 64, dict(CWB), dict(WATER),
                 "The well against the south wall: a stone kerb round cold water."),
            plat(None, [-832, 736], [512, 64], 48, dict(POST), dict(PLANK), "A bench along the north wall."),
            plat(None, [-960, -736], [448, 64], 48, dict(POST), dict(PLANK), "A bench along the south wall."),
            plat(None, [608, 736], [256, 64], 48, dict(POST), dict(PLANK), "A short bench by the gallery arch."),
        ],
        'notes': "The town's square under a raw rock vault: the round hearth in the middle, the well against the south wall, benches by the walls, two chandeliers. Ways off: the gate hall (east), the smiths' gallery (north), the burrow lane (south), the King's steps (west).",
    },
    'smiths_gallery': {
        'walls': [{'wall': 2, 'panels': front('mailwright', 640, notes="The Mailwright's Burrow (house 4705): Hilde Ringwright.")
                   + front('forge', 1408, notes="Bosco's Forge (house 4701): Durgan Ironfist's weapon shop.")}],
        'platforms': [plat('platform:anvil', [-192, 1360], [128, 64], 48, dict(ROCK), dict(ROCK),
                           "An anvil block by the wall beside the Forge's front.")],
        'notes': "Along the north side, open at both ends: Bosco's Forge and the Mailwright's Burrow side by side on the north wall (768 apart), the forge bay's lit opening between them, an anvil by the wall.",
    },
    'forge_bay': {
        'notes': "The forge's hearth in a low bay behind the gallery's wall: its fire and glow inside it.",
    },
    'burrow_lane': {
        'walls': [{'wall': 0, 'panels': front('tinker', 640, notes="The Tinker's Burrow (house 4706): Gimble.")}],
        'notes': "Off the great hall's south side: the Tinker's Burrow on its south wall, the guild stair down from its west end.",
    },
    'kings_steps': {
        'notes': "Four steps up (128) from the great hall to the throne hall's two leaves.",
    },
    'throne_hall': {
        'walls': [{'wall': 3, 'panels': [
            {'id': 'panel:banner', 'offset': 640 - THRONE_Y - 80, 'length': 160, 'bottom': 432, 'height': 320,
             'surface': dict(BANNER, fit=True), 'notes': "Bosco's banner over his throne (xdbosban, once)."}]
            + front('kings_hall', 640 - KINGS_DOOR_Y, bottom=96,
                    notes="The King's Hall (house 4704): Bosco, behind the dais.")}],
        'levels': [{'id': f'level:dais_{i + 1}',
                    'outline': [[DAIS[i + 1][0] + DAIS[i + 1][1] // 2 if i + 1 < len(DAIS) else -3584, -640],
                                [x + d // 2, -640], [x + d // 2, 640],
                                [DAIS[i + 1][0] + DAIS[i + 1][1] // 2 if i + 1 < len(DAIS) else -3584, 640]],
                    'floor': THRONE + r, 'edge': dict(CWB), 'surface': dict(FLAGS),
                    'notes': "The dais: a step across the hall's west end."} for i, (x, d, r) in enumerate(DAIS)],
        'platforms': [plat('platform:throne', [-3480, THRONE_Y], [144, 160], 64, dict(POST), dict(PLANK),
                "Bosco's throne, empty: its seat, on the dais's top.", base=96),
           plat('platform:throne_back', [-3568, THRONE_Y], [32, 128], 256, dict(S_('hdr1b', 128, 256)), dict(PLANK),
                "The throne's high back against the wall, under the banner: a carved panel (hdr1b, once).",
                base=96, end_surface=dict(POST, fit=False)),
           plat('platform:table', [-2560, 560], [512, 96], 72, dict(POST), dict(PLANK),
                "The long tasting table on the north wall: the King's cups."),
           plat('platform:stool', [-2560, 448], [64, 64], 40, dict(POST), dict(PLANK), "The taster's stool.")],
        'notes': "Bosco's empty throne on a three-step dais at the west end under his banner, the King's Hall door behind the dais, the long tasting table on the north wall with its cups and the taster's stool, braziers on the floor by the dais.",
    },
    'guild_hall': {
        'walls': [{'wall': 3, 'panels': front('guild_earth', 512, notes="The Deep Guild of Earth (house 4703): Stonebeard.")}],
        'notes': "A raw-rock hall at the guild stair's foot: a vein of crystal by the north wall, floor lamps; the Deep Guild of Earth's door on the west wall under its sign.",
    },
}


# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s28 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-25: "brick corridors with timber house
# fronts: a town street, not a dwarf hall in the crag"): the halls cut in 7d24's raw rock (cwb1) over a dressed-stone
# base course (cwb), dressed stone only on the house fronts and in the throne hall; the great hall higher (1,024) under
# a raw-rock vault (1,344 at its ridge) on four rock-cut pillars; the burrow lane under a rock vault; anvils at the
# forge bay's mouth.
BASE = [{'height': 96, 'surface': dict(CWB)}]
for _t in THEMES:
    if _t['id'] == 'theme:hall':
        _t.update({'wall': dict(ROCK), 'bands': [dict(b) for b in BASE]})
        _t.pop('ends', None)
        _t['notes'] = ("The dwarves' halls cut in 7d24's raw rock (cwb1) over a dressed-stone base course (cwb), under "
                       "raw rock vaults; flag floors (7tfb1). Dressed stone only on the house fronts.")
_n, _b, _f, _c, _th = R['great_hall']
R['great_hall'] = (_n, _b, _f, 1024, _th)
IRON = S_('xnrustirn', 64, 64)


def rock_column(cx, cy, r=88):
    """A rock-cut octagonal pillar."""
    import math
    return {'outline': [[round(cx + r * math.cos(math.radians(22.5 + 45 * k))),
                         round(cy + r * math.sin(math.radians(22.5 + 45 * k)))] for k in range(8)],
            'surface': dict(ROCK), 'notes': "A pillar left standing when the hall was cut."}


EXTRA['great_hall'].update({
    'ceiling_points': [[-1280, 0, 1344], [768, 0, 1344], [-256, 0, 1344]],
    'pillars': [rock_column(-1024, 352), rock_column(-1024, -352), rock_column(384, 384), rock_column(576, -320)],
})
EXTRA['great_hall']['notes'] = EXTRA['great_hall']['notes'].replace(
    "The town's square under a raw rock vault:",
    "The town's square, 1,024 high under a raw rock vault (1,344 at its ridge) on four rock-cut pillars:")
EXTRA['burrow_lane']['ceiling_points'] = [[-1280, -1152, 640], [0, -1152, 640]]
EXTRA['burrow_lane']['notes'] += " A raw rock vault over it."


def anvil(cx, cy):
    """An anvil at the forge bay's mouth: a stone block and a flared iron top."""
    return [plat(None, [cx, cy], [64, 48], 48, dict(ROCK), dict(ROCK), "An anvil's stone block."),
            plat(None, [cx, cy], [96, 40], 24, dict(IRON), dict(IRON), "The anvil's iron, flaring to its face.",
                 base=48, top_size=[128, 48])]


EXTRA['smiths_gallery']['platforms'] += anvil(512, 1248) + anvil(768, 1248)
EXTRA['smiths_gallery']['notes'] += " Two more anvils flank the bay's mouth in its glow."


def room_doc(rid):
    if rid in P:
        name, path, fl, to, h, theme = P[rid]
        (xa, ya), (xb, yb) = path
        hw = PATH_WIDTH // 2
        return {'id': 'room:' + rid, 'name': name,
                'outline': [[min(xa, xb), ya - hw], [max(xa, xb), ya - hw], [max(xa, xb), ya + hw], [min(xa, xb), ya + hw]],
                'floor': fl, 'slope': {'to': to, 'toward': 'west', 'steps': 12}, 'ceiling': fl + h,
                'ceiling_slope': {'to': to + h, 'toward': 'west'}, 'theme': theme,
                'notes': "The guild stair from the burrow lane's west end down to the Deep Guild hall (0 to -384)."}
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    if rid == 'kings_steps':
        d['slope'] = {'to': THRONE, 'toward': 'west', 'steps': 4}
    d.update(EXTRA.get(rid, {}))
    return d


def extent(rid):
    pts = P[rid][1] if rid in P else outline(rid)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs) + (PATH_WIDTH if rid in P else 0)
    h = max(ys) - min(ys) + (PATH_WIDTH if rid in P else 0)
    return [w, h], [(max(xs) + min(xs)) // 2, (max(ys) + min(ys)) // 2]


def area(rid):
    if rid in P:
        pts = P[rid][1]
        return sum(abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)) * PATH_WIDTH
    o = outline(rid)
    return abs(sum(o[i][0] * o[(i + 1) % len(o)][1] - o[(i + 1) % len(o)][0] * o[i][1] for i in range(len(o)))) / 2


if __name__ == '__main__':
    tot = 0
    for r in ORDER:
        a = area(r)
        tot += a
        print(f'{r:16s} {a / 1e6:6.2f}')
    print('total', tot / 1e6)
