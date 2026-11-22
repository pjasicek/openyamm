#!/usr/bin/env python3
"""DD-01 Castleview Sewer: the geometry (rooms, openings) shared by L2, L3 and L4.

Two levels in one frame (x east, y north, heights from the arrival floor):
- the town drains at 0: the drain cross under the square (the hatch shaft south of it), the west drain (the shaft
  under the guild row at its end, the jammed sluice north of it, Felix's tunnel and Valio's niche south of it), the
  north drain (the gate shaft), the east drain (the market and temple shafts; the cellar's grate in its floor), the
  overflow cistern south-west of the cross with its stair down;
- the deep culverts at -512: the deep cistern (the outfall east of it, the rat runs north-east), the flooded culvert
  north of the rat runs, the nest ramp rising to the rat queen's nest (-224), the bone slide down to the midden (-480)
  and the drowned cellar under the east drain (its ladder up through the floor grate).
Rooms are chamfered rectangles (caves with `rough` walls) whose axis-aligned sides carry the openings; walls between
rooms are 128 thick. The drains have a sewage channel (a sunken level) down their middle.
"""

U0, U1 = 0, -512
NEST = -224
MIDDEN = -480


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# MM6 Shadow Guild Hideout (6d03) and the MM6 sewer stone of its family (dungeon_families.yml `sewers`).
BLOCK = S_('d1wlbct1', 256, 256)          # cut block stone: the cross, the sluice, Valio's niche
WETWALL = S_('d1wldle2', 256, 256)        # the drains' walls, a wet green tide line at the foot
WETWALL2 = S_('d1wldle3', 256, 256)       # the cisterns' walls
OLDWALL = S_('d1medbw', 128, 128)         # the oldest, mossy stone: the east drain, the cellar
ROUGHWALL = S_('d1wle', 256, 256)         # the deep culverts, Felix's tunnel
OUTLET = S_('d1wldsp', 256, 256)          # a wall with a grated outlet (panels in the drains)
REVEAL = S_('d1wlbre1', 128, 256)         # the jambs of doorways
FLAGS = S_('d2flor2', 128, 128)           # stone flags: the drains' walks
PLANKS = S_('bemvwal', 128, 256)          # plank floors: Felix's tunnel, Valio's niche, the bed's frame
MUCK = S_('d1sbpa', 32, 32, scale=8)      # straw and muck: the rat runs, the nest, the midden, the bed's top
TRIM = S_('bemh', 256, 32)                # a timber rail (Felix's bench)
DOOR = S_('beemdorc', 128, 256)           # wooden doors
IRONDOOR = S_('d8dore', 256, 256)         # the iron doors (sluice house, outfall)
GRATE = S_('d1lggrt', 256, 256, scale=1.25)  # the outfall's round grate: one on its 320 face
SKYGRATE = S_('d1lggrt', 256, 256)         # four round street grates over each shaft        # one round street grate over each shaft
FLOORGRATE = S_('d1lggrt', 256, 256)      # the cellar's floor grate: one round grate on the slab
LADDER = S_('d1ladder', 128, 256)         # the shafts' iron ladders
SEWAGE = {'texture': 'swprrf3', 'liquid': 'water'}   # MM6 sewage (engine liquid sewage_mm6)
# Castleview's own grey ashlar where a shaft comes down under a civic building (D1's kit, MM8 t09).
ASHLAR = S_('t09a01', 128, 256)
ASHLAR_TRIM = S_('t09b11b', 128, 32)

THEMES = [
    {'id': 'theme:cross', 'wall': BLOCK, 'floor': FLAGS, 'ceiling': BLOCK, 'door': DOOR, 'reveal': REVEAL,
     'notes': "The drain cross: MM6 6d03's cut block stone d1wlbct1 on walls and vault, d2flor2 flags."},
    {'id': 'theme:drain', 'wall': WETWALL, 'floor': FLAGS, 'ceiling': BLOCK, 'door': DOOR, 'reveal': REVEAL,
     'notes': "The west and north drains: the sewer stone with its wet green tide line (d1wldle2), flags, block vault."},
    {'id': 'theme:old', 'wall': OLDWALL, 'floor': FLAGS, 'ceiling': ROUGHWALL, 'door': DOOR, 'reveal': REVEAL,
     'notes': "The east drain and the drowned cellar: the oldest mossy stone (d1medbw)."},
    {'id': 'theme:shaft', 'wall': ASHLAR, 'floor': FLAGS, 'ceiling': SKYGRATE, 'door': DOOR,
     'bands': [{'height': 32, 'surface': ASHLAR_TRIM}],
     'notes': "The five shafts: Castleview's grey ashlar (t09a01 over a t09b11b plinth) up to a round street grate (d1lggrt)."},
    {'id': 'theme:sluice', 'wall': BLOCK, 'floor': FLAGS, 'ceiling': BLOCK, 'door': IRONDOOR, 'reveal': REVEAL,
     'notes': "The town's sluice house: block stone, its iron door d8dore."},
    {'id': 'theme:tunnel', 'wall': ROUGHWALL, 'floor': FLAGS, 'ceiling': ROUGHWALL, 'door': DOOR,
     'notes': "Felix's tunnel: rough stone d1wle over flags."},
    {'id': 'theme:niche', 'wall': BLOCK, 'floor': PLANKS, 'ceiling': ROUGHWALL, 'door': DOOR,
     'notes': "Valio's dry niche: block stone over a plank floor (6d03's bemvwal)."},
    {'id': 'theme:cistern', 'wall': WETWALL2, 'floor': FLAGS, 'ceiling': ROUGHWALL, 'door': IRONDOOR, 'reveal': REVEAL,
     'notes': "The overflow and deep cisterns: wet stone (d1wldle3), flags, the rough vault."},
    {'id': 'theme:culvert', 'wall': ROUGHWALL, 'floor': FLAGS, 'ceiling': ROUGHWALL, 'door': IRONDOOR,
     'notes': "The deep culverts and the outfall: rough sewer stone d1wle."},
    {'id': 'theme:rats', 'wall': ROUGHWALL, 'floor': FLAGS, 'ceiling': ROUGHWALL, 'door': DOOR,
     'notes': "Where the brick has fallen in: rough sewer stone d1wle in broken cave walls over the old flags."},
    {'id': 'theme:nest', 'wall': ROUGHWALL, 'floor': MUCK, 'ceiling': ROUGHWALL, 'door': DOOR,
     'notes': "The rat queen's nest: rough stone over straw and muck (d1sbpa)."},
]


def cave(x0, y0, x1, y1, c=256):
    """A chamfered rectangle, counter-clockwise from the south-west; c is one chamfer or (sw, se, ne, nw)."""
    sw, se, ne, nw = (c, c, c, c) if isinstance(c, int) else c
    pts = []
    for p in ([x0 + sw, y0], [x1 - se, y0], [x1, y0 + se], [x1, y1 - ne], [x1 - ne, y1], [x0 + nw, y1],
              [x0, y1 - nw], [x0, y0 + sw]):
        if not pts or pts[-1] != p:
            pts.append(p)
    if pts[0] == pts[-1]:
        pts.pop()
    return pts


ROUGH = {'step': 192, 'depth': 40}

# id: (name, box, floor, ceiling, theme)
R = {
    # the town drains (0)
    'cross': ("The drain cross", (-640, -640, 640, 640), U0, 704, 'theme:cross'),
    'shaft_square': ("Square shaft (the hatch)", (-256, -1280, 256, -768), U0, 1280, 'theme:shaft'),
    'west_drain': ("West drain", (-3200, -384, -768, 384), U0, 512, 'theme:drain'),
    'shaft_west': ("West shaft (guild row)", (-3840, -256, -3328, 256), U0, 1280, 'theme:shaft'),
    'sluice': ("The jammed sluice", (-2816, 512, -896, 2048), U0, 640, 'theme:sluice'),
    'north_drain': ("North drain", (-768, 768, 2560, 1536), U0, 512, 'theme:drain'),
    'shaft_north': ("North shaft (the gate)", (1664, 1664, 2176, 2176), U0, 1280, 'theme:shaft'),
    'east_drain': ("East drain", (768, -384, 5120, 384), U0, 480, 'theme:old'),
    'shaft_market': ("Market shaft", (2944, 512, 3456, 1024), U0, 1280, 'theme:shaft'),
    'shaft_temple': ("Temple shaft", (5248, -256, 5760, 256), U0, 1280, 'theme:shaft'),
    'felix': ("Felix's tunnel", (-3072, -2944, -2688, -512), U0, 384, 'theme:tunnel'),
    'valio': ("Valio's bed", (-2560, -2048, -1920, -1408), U0, 384, 'theme:niche'),
    'overflow': ("Overflow cistern", (-1792, -2304, -512, -1024), U0, 768, 'theme:cistern'),
    # the deep culverts (-512)
    'deep_cistern': ("Deep cistern", (-2304, -5632, 0, -3840), U1, 256, 'theme:cistern'),
    'outfall': ("Outfall tunnel", (128, -5120, 4352, -4608), U1, -128, 'theme:culvert'),
    'rat_runs': ("Rat runs", (128, -4480, 2560, -3200), U1, 0, 'theme:rats'),
    'culvert': ("Nest culvert", (1024, -3072, 1536, -1920), U1, -224, 'theme:culvert'),
    'rat_nest': ("The rat queen's nest", (2304, -3072, 4096, -1152), NEST, 448, 'theme:nest'),
    'midden': ("Bone midden", (5248, -2944, 6528, -1408), MIDDEN, 128, 'theme:rats'),
    'cellar': ("Drowned cellar", (4480, -1280, 5888, 32), MIDDEN, -96, 'theme:old'),
}
# Sloping tunnels: (name, path, floor, to, ceiling, theme)
P = {
    'overflow_stair': ("Overflow stair", [[-1152, -2432], [-1152, -3712]], U0, U1, 384,
                       'theme:cistern'),
    'nest_ramp': ("Nest ramp", [[1280, -1792], [1280, -1408], [2176, -1408]], U1, NEST, 384, 'theme:culvert'),
    'bone_slide': ("Bone slide", [[4224, -2048], [5120, -2048]], NEST, MIDDEN, 384, 'theme:rats'),
}
PATH_WIDTH = 384

CHAMFER = {
    'cross': 192, 'overflow': 320, 'deep_cistern': 256, 'rat_runs': (0, 320, 320, 320), 'rat_nest': (384, 256, 320, 0),
    'midden': 256, 'sluice': 0, 'valio': 0, 'felix': 0, 'culvert': 0, 'outfall': 0, 'cellar': 0,
    'west_drain': 0, 'north_drain': 0, 'east_drain': 0,
    'shaft_square': 0, 'shaft_west': 0, 'shaft_north': 0, 'shaft_market': 0, 'shaft_temple': 0,
}

ORDER = sorted(list(R) + list(P))


def outline(rid):
    b = R[rid][1]
    return cave(*b, CHAMFER.get(rid, 256))


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
    if a not in P and b not in P and kw.get('in') != 'floor':
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
    if kw.get('in') == 'floor':
        d['at'] = at
    if kw.get('in') != 'floor':
        d['width'] = width
        d['height'] = height
    d.update(kw)
    return d


# The cellar's floor grate: the hole in the east drain's south walk over the drowned cellar.
GRATE_AT = [4736, -128]
GRATE_HOLE = [224, 224]

OPENINGS = [
    opening('open:square_cross', 'shaft_square', 'cross', at=0, width=384, height=384, link='link:square_cross'),
    opening('open:cross_west', 'cross', 'west_drain', at=0, width=256, height=320, link='link:cross_west'),
    opening('open:west_shaft', 'west_drain', 'shaft_west', at=0, width=320, height=352, link='link:west_shaft'),
    opening('open:west_sluice', 'west_drain', 'sluice', at=-1408, width=384, height=384, link='link:west_sluice'),
    opening('open:sluice_north', 'sluice', 'north_drain', at=1152, width=256, height=320, link='link:sluice_north'),
    opening('open:north_cross', 'north_drain', 'cross', at=-256, width=256, height=320, link='link:north_cross'),
    opening('open:north_shaft', 'north_drain', 'shaft_north', at=1920, width=320, height=352, link='link:north_shaft'),
    opening('open:cross_east', 'cross', 'east_drain', at=0, width=256, height=320, link='link:cross_east'),
    opening('open:east_temple', 'east_drain', 'shaft_temple', at=0, width=320, height=352, link='link:east_temple'),
    opening('open:east_market', 'east_drain', 'shaft_market', at=3200, width=256, height=320, link='link:east_market'),
    opening('open:west_felix', 'west_drain', 'felix', at=-2880, width=320, height=352, link='link:west_felix'),
    opening('open:felix_valio', 'felix', 'valio', at=-1728, width=320, height=320, link='link:felix_valio'),
    opening('open:valio_overflow', 'valio', 'overflow', at=-1728, width=256, height=320, link='link:valio_overflow'),
    opening('open:overflow_stair', 'overflow', 'overflow_stair', width=320, height=352, link='link:overflow_stair'),
    opening('open:stair_deep', 'overflow_stair', 'deep_cistern', width=320, height=352, link='link:stair_deep'),
    opening('open:deep_runs', 'deep_cistern', 'rat_runs', at=-4288, width=256, height=352, link='link:deep_runs'),
    opening('open:deep_outfall', 'deep_cistern', 'outfall', at=-4864, width=256, height=320, link='link:deep_outfall'),
    opening('open:runs_culvert', 'rat_runs', 'culvert', at=1280, width=320, height=256, link='link:culvert'),
    opening('open:culvert_ramp', 'culvert', 'nest_ramp', width=320, height=256, link='link:culvert_ramp'),
    opening('open:ramp_nest', 'nest_ramp', 'rat_nest', width=320, height=352, link='link:ramp_nest'),
    opening('open:nest_slide', 'rat_nest', 'bone_slide', width=320, height=352, link='link:nest_slide'),
    opening('open:slide_midden', 'bone_slide', 'midden', width=320, height=352, link='link:slide_midden'),
    opening('open:midden_cellar', 'midden', 'cellar', at=5696, width=256, height=352, link='link:midden_cellar'),
    opening('open:cellar_grate', 'east_drain', 'cellar', link='link:cellar_east', **{'in': 'floor'}, at=GRATE_AT,
            size=GRATE_HOLE,
            notes="The hole under the cellar's floor grate, in the east drain's south walk: the ladder's way up."),
]

CHANNEL_W = 192


def channel(rid, axis, inset=128, cid=None):
    """A sewage channel down the middle of a drain: a level 48 down, inset from the end walls."""
    x0, y0, x1, y1 = R[rid][1]
    if axis == 'x':
        cy = (y0 + y1) // 2
        o = [[x0 + inset, cy - CHANNEL_W // 2], [x1 - inset, cy - CHANNEL_W // 2], [x1 - inset, cy + CHANNEL_W // 2],
             [x0 + inset, cy + CHANNEL_W // 2]]
    else:
        cx = (x0 + x1) // 2
        o = [[cx - CHANNEL_W // 2, y0 + inset], [cx + CHANNEL_W // 2, y0 + inset], [cx + CHANNEL_W // 2, y1 - inset],
             [cx - CHANNEL_W // 2, y1 - inset]]
    return {'id': cid or f'level:{rid}_channel', 'outline': o, 'floor': R[rid][2] - 48, 'edge': FLAGS,
            'surface': dict(SEWAGE), 'notes': "The slow sewage channel down the drain's middle."}


def plat(pid, at, size, rise, surface, top=None, notes=None, **kw):
    d = {'id': pid, 'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if top:
        d['top_surface'] = top
    d.update(kw)
    if notes:
        d['notes'] = notes
    return d


def ladder_wall(wall, pid):
    return {'wall': wall, 'panels': [{'id': pid, 'at': 'centre', 'length': 128, 'bottom': 0, 'height': 1024,
                                      'surface': dict(LADDER),
                                      'notes': "An iron ladder up the shaft to the street grate."}]}


SLUICE_CH = {'id': 'level:sluice_channel', 'outline': [[-1856, 640], [-1600, 640], [-1600, 1792], [-1856, 1792]],
             'floor': -96, 'edge': BLOCK, 'surface': dict(SEWAGE),
             'notes': "The town's sluice channel: water from the streets runs through the gate down to the drains."}

EXTRA = {
    'cross': {
        'ceiling_points': [[0, 0, 896], [0, -640, 704], [0, 640, 704], [-640, 0, 704], [640, 0, 704]],
        'pillars': [{'outline': cave(-416, -416, -288, -288, 16), 'surface': BLOCK},
                    {'outline': cave(288, -416, 416, -288, 16), 'surface': BLOCK},
                    {'outline': cave(288, 288, 416, 416, 16), 'surface': BLOCK},
                    {'outline': cave(-416, 288, -288, 416, 16), 'surface': BLOCK}],
        'levels': [{'id': 'level:cross_sump', 'outline': cave(-160, -160, 160, 160, 64), 'floor': -64, 'edge': FLAGS,
                    'surface': dict(SEWAGE), 'notes': "The sump where the four drains meet."}],
        'notes': "Four drains meet under the square in a vaulted cross on four piers; a sump of sewage in the middle; lamplight down the hatch shaft to the south.",
    },
    'shaft_square': {
        'walls': [{'wall': 's', 'panels': [{'at': 'centre', 'length': 128, 'bottom': 256, 'height': 896,
                                            'surface': dict(LADDER),
                                            'notes': "The hatch ladder above the exit's face, up to the hatch."}]}],
        'notes': "The iron hatch's shaft by the square's south-east corner: a ladder on the south wall up to the hatch (the way in and out).",
    },
    'shaft_west': {
        'walls': [ladder_wall('w', 'panel:ladder_west')],
        'platforms': [plat('platform:ledge_red', [-3456, 160], [128, 96], 128, ASHLAR, ASHLAR_TRIM,
                           "A stone ledge at the shaft's foot: a flask of Red Liquid.")],
        'notes': "Under the guild row: a ladder up to a grate bolted from above; a flask of Red Liquid on a ledge.",
    },
    'shaft_north': {
        'walls': [ladder_wall('n', 'panel:ladder_north')],
        'notes': "Under the gatehouse: a ladder up to a grate bolted from above; a gate guard's bones.",
    },
    'shaft_market': {
        'walls': [ladder_wall('n', 'panel:ladder_market')],
        'notes': "Under the market: a ladder to a grate bolted from above; a heap of things dropped through it (a chest).",
    },
    'shaft_temple': {
        'walls': [ladder_wall('e', 'panel:ladder_temple')],
        'platforms': [plat('platform:ledge_green', [5632, 160], [128, 96], 128, ASHLAR, ASHLAR_TRIM,
                           "A stone ledge at the shaft's foot: a flask of Green Liquid.")],
        'notes': "Under the temple: a ladder to a grate bolted from above; a flask of Green Liquid on a ledge.",
    },
    'west_drain': {
        'levels': [channel('west_drain', 'x')],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:outlet_w1', 'offset': 1344, 'length': 256, 'bottom': 0,
                                            'height': 256, 'surface': dict(OUTLET, fit=True)}]}],
        'notes': "A walk either side of a slow channel; bats under the vault; the sluice house north, Felix's tunnel south, the guild-row shaft at the end.",
    },
    'north_drain': {
        'levels': [channel('north_drain', 'x')],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:outlet_n1', 'offset': 1792, 'length': 256, 'bottom': 0,
                                            'height': 256, 'surface': dict(OUTLET, fit=True)}]}],
        'notes': "Under the north street: gremlin tools and a cut rope; the gate shaft at its east end.",
    },
    'east_drain': {
        'levels': [dict(channel('east_drain', 'x'), outline=[[896, 32], [4992, 32], [4992, 224], [896, 224]],
                        notes="The slow sewage channel along the drain's north side; the south walk wide for the cellar's grate.")],
        'walls': [{'wall': 'n', 'panels': [{'id': 'panel:outlet_e1', 'offset': 3072, 'length': 256, 'bottom': 0,
                                            'height': 256, 'surface': dict(OUTLET, fit=True)}]}],
        'notes': "Under the temple and the stables, the oldest stone; the market and temple shafts; the cellar's floor grate in the south walk.",
    },
    'sluice': {
        'levels': [SLUICE_CH],
        'notes': "The town's sluice house: the channel from the streets comes in under its north wall through a gate the gremlins wedged half open with the mill's gears; the lever on the north wall.",
    },
    'felix': {
        'platforms': [plat('platform:felix_bench', [-2880, -2848], [256, 96], 64, PLANKS, TRIM,
                           "Felix's workbench at the tunnel's end: tools, a lantern and a compass.", end_surface=dict(PLANKS, fit=False))],
        'notes': "A neat tunnel boarded underfoot, dug by Felix the Tinker; his bench at its end.",
    },
    'valio': {
        'platforms': [plat('platform:bed', [-2240, -1936], [352, 160], 48, PLANKS, MUCK,
                           "Valio's bed: a plank frame heaped with straw and blankets, Valio under them.")],
        'notes': "A dry niche off Felix's tunnel: Valio's bed and his chest.",
    },
    'overflow': {
        'ceiling_points': [[-1152, -1664, 960]],
        'levels': [{'id': 'level:overflow_pool', 'outline': cave(-1408, -1920, -896, -1408, 128), 'floor': -96,
                    'edge': WETWALL2, 'surface': dict(SEWAGE), 'notes': "The overflow's round pool."}],
        'notes': "A round cistern under a domed vault; its pool; the stair down to the culverts leaves from its south side.",
    },
    'deep_cistern': {
        'ceiling_points': [[-1152, -4736, 512]],
        'levels': [{'id': 'level:deep_pool', 'outline': cave(-1536, -5184, -768, -4480, 160), 'floor': -576,
                    'edge': WETWALL2, 'surface': dict(SEWAGE), 'notes': "The deep cistern's pool."}],
        'notes': "The overflow stair's foot: a tall wet cistern; the outfall tunnel east (south), the rat runs east (north).",
    },
    'outfall': {
        'notes': "The drain's way out under the town wall to the mill gorge: an iron grate at its east end, barred on this side.",
    },
    'rat_runs': {'rough': ROUGH, 'ceiling_points': [[1344, -3840, 128]],
                 'notes': "Where the brick has fallen in: burrows, gnawed bones, rat runs; the flooded culvert north."},
    'culvert': {'notes': "A low culvert to the nest, flooded to its roof while the town sluice runs (the water a sinking mover)."},
    'rat_nest': {'rough': ROUGH, 'ceiling_points': [[3200, -2112, 640]],
                 'notes': "A collapsed vault heaped with rags, bottle caps and buttons: Rooka's nest and her hoard."},
    'midden': {'rough': ROUGH, 'notes': "Where the rats drag what they kill: bones and a sodden pack."},
    'cellar': {
        'levels': [{'id': 'level:cellar_water', 'outline': [[5248, -1088], [5760, -1088], [5760, -576], [5248, -576]],
                    'floor': -528, 'edge': OLDWALL, 'surface': dict(SEWAGE),
                    'notes': "Sewage standing in the cellar's sunken corner."}],
        'notes': "An old house cellar the drain broke into; the gremlins store stolen tools here; a ladder up to the floor grate of the east drain.",
    },
}


def room_doc(rid):
    if rid in P:
        name, path, fl, to, h, theme = P[rid]
        return {'id': 'room:' + rid, 'name': name, 'path': path, 'width': PATH_WIDTH, 'smooth': 1, 'floor': fl,
                'slope': {'to': to}, 'ceiling': fl + h, 'theme': theme,
                'notes': {'overflow_stair': "The overflow stair: a ramp of wet stone from the overflow cistern down to the deep cistern (0 to -512).",
                          'nest_ramp': "From the culvert up to the nest (-512 to -224): the nest stands above the culvert's high water.",
                          'bone_slide': "A slope of filth from the nest down to the midden (-224 to -480)."}[rid]}
    name, b, fl, ce, theme = R[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
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
