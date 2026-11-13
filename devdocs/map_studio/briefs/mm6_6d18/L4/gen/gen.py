#!/usr/bin/env python3
# Writes the Gharik's Forge rebuild project (devdocs/map_studio/briefs/mm6_6d18/L4) from the tables below.
# Scratch tool of the rebuild agent: the project files are the truth once written; run `oymap fmt` after it.
import json, math, os, sys

ROOT = '/home/pjasicek/github/OpenYAMM/'
L4 = ROOT + 'devdocs/map_studio/briefs/mm6_6d18/L4/'
W = ROOT + 'output/studio_cal/mm6_6d18/'
SIZES = {k: v['size'] for k, v in json.load(open(W + 'texsizes.json')).items()}
ORIG = json.load(open(W + 'orig.json'))['map']


def S(name, **kw):
    d = {'texture': name.lower(), 'size': SIZES[name.lower()]}
    d.update(kw)
    return d


def area(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2


def ccw(p):
    p = [list(q) for q in p]
    return p if area(p) > 0 else p[::-1]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def inside(p, x, y):
    c = False
    n = len(p)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
    return c


def seg_dist(a, b, x, y):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
    px, py = a[0] + t * dx, a[1] + t * dy
    return math.hypot(x - px, y - py), t


def poly_dist(p, x, y):
    if inside(p, x, y):
        return 0
    return min(seg_dist(p[i], p[(i + 1) % len(p)], x, y)[0] for i in range(len(p)))


THEMES = {}
ROOMS = []
RB = {}
OPEN = []


def theme(wall, floor, ceiling):
    key = (wall.lower(), floor.lower(), ceiling.lower())
    if key not in THEMES:
        THEMES[key] = 'theme:' + '_'.join(key)
    return THEMES[key]


def room(rid, name, outline, floor, ceiling, wall, ftex, ctex, notes=None, zmin=None, tread=None, **kw):
    r = {'id': 'room:' + rid, 'name': name, 'outline': ccw(outline), 'floor': floor, 'ceiling': ceiling,
         'theme': theme(wall, ftex, ctex)}
    r.update(kw)
    if notes:
        r['notes'] = notes
    ROOMS.append(r)
    RB[rid] = r
    return r


def op(a, b, width='full', height='full', notes=None, **kw):
    o = {'id': 'open:%s_%s' % (a, b) + kw.pop('suffix', ''), 'from': 'room:' + a, 'to': 'room:' + b, 'width': width,
         'height': height}
    o.update(kw)
    if notes:
        o['notes'] = notes
    OPEN.append(o)
    return o['id']


def edge_along(rid, x, y):
    """The outline edge of a room nearest a point, and the position along it (0 to 1)."""
    p = RB[rid]['outline']
    best = None
    for i in range(len(p)):
        d, t = seg_dist(p[i], p[(i + 1) % len(p)], x, y)
        if best is None or d < best[0]:
            best = (d, i, t)
    return best[1], round(best[2], 4)


def door_along(a, b, x, y):
    """`along` for an opening centred at (x, y) on room a's wall facing room b."""
    pa, pb = RB[a]['outline'], RB[b]['outline']
    i, _ = edge_along(a, x, y)
    a0, a1 = pa[i], pa[(i + 1) % len(pa)]
    L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    ux, uy = (a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L
    # the facing edge of b: nearest edge to the point that is antiparallel
    best = None
    for j in range(len(pb)):
        b0, b1 = pb[j], pb[(j + 1) % len(pb)]
        Lb = math.hypot(b1[0] - b0[0], b1[1] - b0[1])
        vx, vy = (b1[0] - b0[0]) / Lb, (b1[1] - b0[1]) / Lb
        if ux * vx + uy * vy > -0.99:
            continue
        d, _ = seg_dist(b0, b1, x, y)
        if best is None or d < best[0]:
            best = (d, b0, b1)
    _, b0, b1 = best
    ts = sorted([((b0[0] - a0[0]) * ux + (b0[1] - a0[1]) * uy), ((b1[0] - a0[0]) * ux + (b1[1] - a0[1]) * uy)])
    t0, t1 = max(0, ts[0]), min(L, ts[1])
    tc = (x - a0[0]) * ux + (y - a0[1]) * uy
    return round((tc - t0) / (t1 - t0), 4)


LAVA = 'OrFyrLgA'
SLAB = S('D2WlActr')

# ---------------------------------------------------------------------------------------------------------------
# Rooms. Numbers in names are the original's sector numbers.
# ---------------------------------------------------------------------------------------------------------------

# --- the entrance tower -----------------------------------------------------------------------------------------
room('start_a', 'Entrance landing, arm to the bridge (6)', rect(-2816, 512, -2176, 768), 1152, 1408, 'D2WlActr', 'vlcflorA', 'D2Ceil1',
     notes='The original landing is one L-shaped room; as one room its leg would face the tower across 384 of rock on a '
           'longer stretch than the arm that touches it, and the opening would be cut there.')
room('start', 'Entrance landing (6)', rect(-2816, 768, -2560, 1280),
     1152, 1408, 'D2WlActr', 'vlcflorA', 'D2Ceil1',
     notes='The party arrives here, 1,664 above the lava of the tower; the exit door is the north end wall.')

TOWER_FLOOR = -512


def tower():
    plats, flights = [], []

    def slab(cx, cy, w, d, top, facing=None, thick=32):
        b = {'at': [cx, cy], 'size': [w, d], 'base': top - thick - TOWER_FLOOR, 'rise': thick, 'surface': SLAB}
        if facing:
            b['facing'] = facing
        plats.append(b)

    corners = {'NE': (-707, 1725, 135), 'NW': (-1981, 1725, 45), 'SW': (-1981, -445, 135), 'SE': (-707, -445, 45)}
    # the centre line of the ramp along each wall, from one corner to the next
    axis = {'E': ((-579, -640), (-579, 1920)), 'N': ((-768, 1853), (-1920, 1853)), 'W': ((-2109, 1920), (-2109, -640)),
            'S': ((-1920, -573), (-768, -573))}

    def end(wall, corner, L, x=None):
        """The point of a wall's ramp line that lies in the corner's landing, furthest from the corner."""
        cx, cy, f = corners[corner]
        ux, uy = math.cos(math.radians(f)), math.sin(math.radians(f))
        (x0, y0), (x1, y1) = axis[wall]
        if x is not None:
            x0 = x1 = x
        best = None
        for i in range(0, 641):
            t = i / 640
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            al = (px - cx) * ux + (py - cy) * uy
            de = -(px - cx) * uy + (py - cy) * ux
            if abs(al) <= L / 2 - 6 and abs(de) <= 88:
                d = math.hypot(px - cx, py - cy)
                if best is None or d > best[0]:
                    best = (d, [round(px), round(py)])
        return best[1]

    # going down from the top: (landing, height, length of the landing), then the wall the next ramp follows.
    # The landings of the lower turn are longer than those of the upper turn above them and are listed first, and
    # the flights are listed from the lowest up: a flight's end finds the block or step listed last at its point.
    seq = [('SE', 1024, 380), ('SW', 896, 380), ('NW', 768, 380), ('NE', 640, 380), ('SE', 512, 500), ('SW', 384, 500),
           ('NW', 256, 500), ('NE', 128, 500)]
    walls = {('SE', 'SW'): 'S', ('SW', 'NW'): 'W', ('NW', 'NE'): 'N', ('NE', 'SE'): 'E'}
    for c, h, L in reversed(seq):
        cx, cy, f = corners[c]
        slab(cx, cy, L, 188, h, f)
    XM, XW = -617, -550
    # the foot: the last ramp comes down the east wall onto a slab level with the corridor
    slab(-576, 656, 126, 286, 0)
    flights.append({'from': [XW, 790], 'to': end('E', 'NE', 500, XW), 'width': 74, 'steps': 4, 'riser': SLAB})
    for (c0, h0, L0), (c1, h1, L1) in reversed(list(zip(seq, seq[1:]))):
        w = walls[(c0, c1)]
        if w == 'E':
            flights.append({'from': end(w, c1, L1, XM), 'to': end(w, c0, L0, XM), 'width': 54, 'steps': 4, 'riser': SLAB})
        else:
            flights.append({'from': end(w, c1, L1), 'to': end(w, c0, L0), 'width': 132, 'steps': 4, 'riser': SLAB})
    # the top bridge and the ramp from it down to the first landing
    slab(-1344, 640, 1662, 258, 1152)
    flights.append({'from': end('E', 'SE', 380, XW), 'to': [XW, 520], 'width': 74, 'steps': 4, 'riser': SLAB})
    return plats, flights


tp, tf = tower()
tp.insert(0, {'at': [-1280, 768], 'size': [128, 128], 'rise': 64, 'surface': S('OrFyr64B')})
room('tower', 'Lava tower (5)',
     [[-2176, -384], [-1920, -640], [-768, -640], [-512, -384], [-512, 1664], [-768, 1920], [-1920, 1920], [-2176, 1664]],
     TOWER_FLOOR, 2688, 'vlcwl1LG', LAVA, 'sky_nit2', platforms=tp, flights=tf,
     levels=[{'outline': [[-1536, 640], [-1408, 512], [-1152, 512], [-1024, 640], [-1024, 896], [-1152, 1024], [-1408, 1024], [-1536, 896]],
              'floor': -496, 'surface': S('6voltyl'), 'edge': S('6voltyl'),
              'notes': 'The island in the lava: whoever falls stands here out of the fire and clicks the raised tile in its middle to be put back at the start.'}],
     notes='An eight-sided shaft 1,664 by 2,560 with lava for a floor (-512) and the night sky for a ceiling (2,688). '
           'A bridge crosses it at 1,152 from the entrance landing; from its east end a ramp 128 wide winds down the walls, '
           'two full turns, to the corridor at 0. The original ramp is a free slab 32 thick that slopes 128 along each '
           'wall, with level corner pieces on the diagonal walls. Here: free slabs (platforms with a base) for the bridge, '
           'the eight corner landings and the foot, and a flight of four steps of 32 for each ramp. Along the east wall, '
           'where three ramps run one above another, the flights are narrower than the ramp and stand side by side (74 '
           'against the wall, 54 inside), because a flight\'s end finds whatever block or step is listed last at its point. '
           'An island in the middle of the lava carries the tile that puts a fallen party back at the start. Not sayable: a '
           'sloping slab; a block flush against a diagonal wall (the corner landings are turned rectangles with square '
           'ends); a surface for a flight\'s treads (they take the room\'s floor surface, so every step here is lava; a '
           'take with the lava as a level inside a stone ledge was tried and thrown away, see NOTES.md). The lava itself is '
           'only a floor texture.')

room('s2', 'Tower corridor (2)', [[256, 1024], [8, 1024], [8, 768], [-512, 768], [-512, 512], [256, 512]], 0, 256,
     'vlcwl1', 'vlcflorE', 'vlctrm3')
room('s1', 'Gate hall (1)', [[512, 2048], [-256, 2048], [-256, 1280], [0, 1024], [256, 1024], [512, 1280]], 0, 384,
     'vlcwl1LG', 'vlcflorE', 'vlctrm3',
     notes='Its whole north side is open onto the first lava hall; the door in its east wall leads to the lever room.')
room('s7', 'Lever room (7)', [[544, 1536], [1032, 1536], [1032, 768], [1536, 768], [1536, 1280], [1280, 1280], [1280, 1792], [544, 1792]],
     0, 256, 'vlcwl1LG', 'vlcflorE', 'vlctrm3', notes='The lever at its south end extends the bridge of the lava hall.')

# --- first lava hall ---------------------------------------------------------------------------------------------
room('s3', 'First lava hall (3)', rect(-1536, 2048, 1792, 3072), -768, 512, 'vlcwl3a', LAVA, 'vlcceilA',
     platforms=[{'at': [128, 2081], 'size': [260, 64], 'base': 640, 'rise': 112, 'surface': SLAB}],
     levels=[{'outline': rect(-1024, 2944, -512, 3072), 'floor': -752, 'surface': S('6voltyl'), 'edge': S('6voltyl'),
              'notes': 'The island with the tile that puts a fallen party back in the tower corridor.'}],
     notes='Lava (-768) from wall to wall, 768 below the two doors that face each other across it (the gate hall on the '
           'south, the corridor on the north). A stub of bridge stands out 64 from the south side at -16; the lever in the '
           'lever room pushes it 959 across to the north door. Here the stub is a free block and the bridge is a lift '
           '(objects.yml lift:bridge3) that rises out of the lava. The original lava runs on 256 under both end walls '
           '(a slot 64 high): not drawn.')
room('s4', 'North corridor (4)', rect(0, 3072, 256, 4096), 0, 256, 'vlcwl2', 'vlcflorA', 'vlctrm3')
room('s8', 'West corridor (8)', rect(-2048, 3840, 0, 4096), 0, 256, 'vlcwl2', 'vlcflorA', 'vlctrm3')

# --- lava gallery and the west rooms -----------------------------------------------------------------------------
room('s9', 'Lava gallery (9)', rect(-2048, 4128, -1536, 6144), -256, 384, 'vlcwl2', LAVA, 'vlcflorB',
     platforms=[{'at': [-1792, 5136], 'size': [158, 2014], 'base': 224, 'rise': 32, 'surface': SLAB,
                 'top_surface': S('vlcflorA')},
                {'at': [-1634, 5248], 'size': [194, 158], 'base': 224, 'rise': 32, 'surface': SLAB,
                 'top_surface': S('vlcflorA')}],
     levels=[{'outline': rect(-2048, 4992, -1952, 5376), 'floor': -240, 'surface': S('6voltyl'), 'edge': S('6voltyl'),
              'notes': 'The island with the tile that puts a fallen party back in the west corridor.'}],
     notes='A walkway at 0 over lava at -256: a strip 138 wide from the south door to the north door with an arm to the '
           'east door, free slabs here. The original walkway has kerbs 21 wide and 64 high along its edges: not drawn '
           '(a parapet stands on a room floor or a level, not on a free block).')
room('s10', 'West treasure room (10)',
     [[-1664, 6176], [-1408, 6432], [-1408, 6944], [-1664, 7200], [-1920, 7200], [-2176, 6944], [-2176, 6432], [-1920, 6176]],
     0, 256, 'vlcwl1A', 'vlcflorA', 'D8florH',
     ceiling_levels=[{'outline': rect(-1920, 6432, -1664, 6944), 'ceiling': 384}],
     notes='Eight-sided. The original ceiling slopes from 256 at the walls to a flat 384 in the middle; here a raised panel.')
room('s11', 'Gallery side corridor (11)', rect(-1504, 5120, -768, 5376), 0, 256, 'vlcwl3a', 'vlcflorA', 'vlctrm3')
room('s13', 'Cross corridor (13)', rect(-1024, 4864, 768, 5120), 0, 256, 'vlcwl3a', 'vlcflorA', 'vlctrm3')
room('s12', 'Ante-room (12)', [[-512, 5152], [-256, 5152], [-256, 5640], [0, 5640], [0, 5888], [-512, 5888]], 0, 256,
     'vlcwl3a', 'vlcflorA', 'vlcflorB')
room('s14', 'Eight-sided hall (14)',
     [[0, 5632], [256, 5376], [608, 5376], [864, 5632], [864, 6400], [608, 6656], [256, 6656], [0, 6400]],
     0, 256, 'vlcflorE', 'vlcflorA', 'vlcflorB',
     ceiling_levels=[{'outline': rect(256, 5632, 608, 6400), 'ceiling': 384}],
     notes='In the original this hall reaches x 1024 and so stands 128 inside the stair passage (46), which runs through '
           'the same space at the same height: the two never see each other. A rebuild cannot overlap rooms, so the hall '
           'ends at x 864 here.')

# --- south hall, its alcove, the two-storey machine room ----------------------------------------------------------
room('s15', 'South hall (15)', rect(512, 4608, 3328, 4864), 0, 256, 'vlcwl3a', 'vlcflorA', 'vlctrm3')
room('alcove', 'Chest alcove (15)', rect(768, 4096, 1408, 4352), 0, 256, 'vlcwl3a', 'vlcflorA', 'vlcgnrc2',
     notes='Two chests. Its neck (128 wide, 256 long) is closed by the "lava wall", a wall face the lever on the '
           'machine room\'s north-east balcony makes vanish (the original lists it in a door record that has no '
           'vertices, and OpenYAMM hides the face by script). Here: a lifting door in the neck.')
room('n50', 'South-west gate lobby (15)', rect(1792, 4896, 2048, 5120), 0, 256, 'vlcwl3a', '6voltyl', 'vlctrm3')
room('n49', 'South-east gate lobby (16)', rect(3072, 4864, 3328, 5088), 0, 256, 'vlcwl3a', 'vlctrm3', 'vlctrm3')
room('n48', 'North-east gate lobby (17)', rect(3072, 6944, 3328, 7168), 0, 256, 'vlcwl1LG', 'vlcflorA', 'vlcflorE')
room('p52', 'Lower south-east passage (16)', rect(2784, 4600, 3040, 5088), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')


def machine():
    plats = []
    for top, xs, w in ((0, (1920, 3200), 260), (-512, (2208, 2912), 254)):
        for cx in xs:
            plats.append({'at': [cx, 5249], 'size': [w, 256], 'base': top - 32 + 768, 'rise': 32,
                          'surface': S('D2Ceil1'), 'top_surface': S('vlctrm3')})
            plats.append({'at': [cx, 6655], 'size': [w, 512], 'base': top - 32 + 768, 'rise': 32,
                          'surface': S('D2Ceil1'), 'top_surface': S('vlctrm3')})
    return plats


room('machine', 'Machine room (16, 17)', rect(1536, 5120, 3840, 6912), -768, 384, 'vlcwl1A', LAVA, 'vlcGnrc1',
     platforms=machine(),
     levels=[{'outline': rect(2688, 6688, 2816, 6912), 'floor': -752, 'surface': S('6voltyl'), 'edge': S('6voltyl'),
              'notes': 'The island with the tile that puts a fallen party on the north-west balcony.'}],
     notes='One hall 2,304 by 1,792 over lava (-768), ceiling 384. Eight balconies hang from its south and north walls, '
           'free slabs 32 thick: at 0 and, straight below them, at -512, at x 1792 to 2048 and x 3072 to 3328 (256 deep on '
           'the south side, 512 on the north). Each has a lever. The upper pairs are joined across the lava by ONE bridge '
           '(992 long, kerbs 64 high) that slides 1,280 sideways between the west pair and the east pair when the lever on '
           'the lower south-east balcony is used; the lower balconies have no bridge and are reached from the lower '
           'passages. Gates 256 wide and 240 high close four of the eight ways in. Here: the balconies are free blocks, '
           'and the sliding bridge is two lifts (objects.yml), the west one up and the east one down, which the lever '
           'swaps for good. The lower balconies stand 288 nearer the middle than the upper ones (x 2080 to 2336 '
           'and 2784 to 3040) instead of straight below them, with their passages: two openings cannot stand one '
           'above the other in one wall.')

room('n43', 'North-west balcony lobby (43)', rect(1792, 6912, 2048, 7168), 0, 256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')
room('s43', 'North-west passage (43)', rect(896, 7168, 2048, 7424),
     0, 256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')
room('s46s', 'Stair passage, south steps (46)', rect(896, 4864, 1152, 5280), 0, 256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2',
     slope={'to': -260, 'toward': 'north', 'steps': 13})
room('s46m', 'Stair passage (46)', rect(896, 5280, 1152, 6752), -260, 256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2',
     notes='A sunken passage between the south hall and the north-west passage: 13 steps of 20 down at each end, and '
           'from the middle of its west wall a flight on down to the lower passages.')
room('s46n', 'Stair passage, north steps (46)', rect(896, 6752, 1152, 7168), 0, 256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2',
     slope={'to': -260, 'toward': 'south', 'steps': 13})
room('s47st', 'Lower stair (47)', rect(512, 5888, 896, 6144), -512, -4, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2',
     slope={'to': -260, 'toward': 'east', 'steps': 13},
     notes='12 steps of 20 from the lower west passage up to the stair passage, under the eight-sided hall. The '
           'original ceiling rakes with the steps; here it is flat at the top.')
room('s47', 'Lower west passage (47)', rect(256, 4352, 512, 7424), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')
room('s44', 'Lower north passage (44)', rect(512, 7168, 3328, 7424), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2',
     notes='Under the north-west passage.')
room('n44', 'Lower north-west lobby (44)', rect(2080, 6912, 2336, 7168), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')
room('n51', 'Lower north-east lobby (44)', rect(2784, 6944, 3040, 7168), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')
room('s45', 'Lower south passage (45)', rect(512, 4352, 3328, 4600), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2',
     notes='Under the south hall. 8 narrower than the original, whose north wall stands exactly 512 from the machine '
           'room: an opening takes the longest pair of facing walls within 512, and would take that one.')
room('n45', 'Lower south-west lobby (45)', rect(2080, 4600, 2336, 5120), -512, -256, 'vlcGnrc1', 'vlcflorA', 'vlcgnrc2')

# --- the north-east ring -----------------------------------------------------------------------------------------
room('s18', 'North corridor bend (18)', [[5120, 7680], [5120, 7936], [3072, 7936], [3072, 7168], [3328, 7168], [3328, 7680]],
     0, 256, 'vlcwl1LG', 'vlcflorA', 'vlcflorE')
room('s19', 'Crystal room lobby (19)', [[4096, 7936], [4096, 8704], [3616, 8704], [3616, 8448], [3840, 8448], [3840, 7936]],
     0, 256, 'vlcwl1LG', 'vlcflorA', 'vlcflorE')
room('s20', 'Crystal room (20)',
     [[3072, 8192], [3584, 8448], [3584, 8704], [3072, 8960], [2816, 9216], [1792, 9216], [1280, 8704], [1280, 8448], [1792, 7936], [2816, 7936]],
     0, 384, 'vlcwl4B', 'vlctrm3', 'D2Ceil3')
room('s21', 'East corridor (21)', rect(4864, 5664, 5120, 7680), 0, 256, 'vlcwl1LG', 'vlcflorA', 'vlcflorE')
room('s23', 'Eight-sided east hall (23)',
     [[5632, 4608], [5632, 5120], [5120, 5632], [4864, 5632], [4352, 5120], [4352, 4608], [4864, 4352], [5120, 4352]],
     0, 384, 'vlcwl4B', 'vlcflorC', 'D2Ceil3',
     ceiling_levels=[{'outline': rect(4864, 4600, 5120, 5112), 'ceiling': 576}],
     notes='The original ceiling slopes from 384 at the walls to a flat 576 in the middle; here a raised panel.')
room('s22', 'East hall lobby (22)', rect(3840, 4608, 4320, 4864), 0, 256, 'vlcwl1', 'vlcflorA', 'vlcflorE')
room('loop', 'Long corridor and loop (25, 26, 27)',
     [[3072, 2816], [4096, 2816], [4096, 4608], [3840, 4608], [3840, 3584], [3072, 3584]], 0, 256,
     'vlcwl1', 'vlcflorA', 'vlcflorE', pillars=[{'at': [3584, 3200], 'size': [512, 256], 'surface': S('vlcwl1')}],
     notes='The original\'s corridor 25 (256 wide, 1,792 long) and the two rooms 26 and 27 that leave its west side and '
           'meet again round a block of rock 512 by 256: one room with the block as a pillar.')
room('s24', 'Lift corridor (24)', rect(4128, 3328, 4864, 3584), 0, 256, 'vlcwl1', 'vlcflorA', 'vlcflorE')
room('s30', 'Lift lobby (30)', rect(4608, 2592, 4864, 3328), 0, 256, 'vlcwl1', 'vlcflorA', 'vlcflorE')
room('s28', 'Chest room passage (28)', [[2816, 3840], [2560, 3840], [2560, 3072], [3040, 3072], [3040, 3328], [2816, 3328]],
     0, 256, 'vlcwl1', 'vlcflorA', 'vlcflorE')
room('s29', 'Two-chest room (29)', [[2560, 3840], [3328, 3840], [3584, 4096], [3584, 4352], [2560, 4352]], 0, 384,
     'vlcwl1', 'vlcflorA', 'vlcflorE')

# --- the lift and the lower floor --------------------------------------------------------------------------------
room('shaft', 'Lift shaft (31)', rect(4608, 2304, 4864, 2560), -2048, 256, 'vlcwl1LG', 'ctFlor1', 'vlcflorE',
     notes='256 square and 2,304 deep. The lift floor (256 by 240) starts at -16, 16 below the lobby door, and sinks '
           '2,032 to the lower floor at 200 units a second; a lever beside it at the top and another at the bottom call it.')
room('shaftb', 'Lift foot (31)', rect(4608, 2080, 4864, 2304), -2048, -1792, 'ctwl5', 'ctFlor1', 'ctCeil3',
     notes='The recess the lift is left by at the bottom; the laboratory door (it needs Gharik\'s key) is in its south wall.')
room('s32', 'Laboratory corridor (32)', rect(4608, 1280, 4864, 2048), -2048, -1792, 'ctwl2', 'ctFlor1', 'ctCeil3')
room('n33', 'Channel hall lobby (33)', rect(5888, 1056, 6144, 1280), -2048, -1792, 'ctwl2', 'ctFlor1', 'ctCeil3')
room('s33', 'Laboratory corridor bend (33)', rect(4864, 1280, 6144, 1536),
     -2048, -1792, 'ctwl2', 'ctFlor1', 'ctCeil3')

L34 = -2260
room('s34', 'Lava channel hall (34)', rect(3328, -256, 6144, 1024), L34, -1280, 'ctwl2', LAVA, 'ctCeil2',
     levels=[
         {'outline': [[3328, -256], [4354, -256], [4354, 384], [3840, 384], [3840, 512], [4354, 512], [4354, 1024], [3328, 1024]],
          'floor': -2048, 'surface': S('ctFlor4'), 'edge': S('ctwl2'), 'notes': 'The west floor.'},
         {'outline': [[5118, -256], [6144, -256], [6144, 1024], [5118, 1024], [5118, 512], [5632, 512], [5632, 384], [5118, 384]],
          'floor': -2048, 'surface': S('ctFlor4'), 'edge': S('ctwl2'), 'notes': 'The east floor.'},
         {'outline': rect(4354, -256, 4480, 512), 'floor': -2240, 'surface': S('ctFlor1'), 'edge': S('ctFlor1'),
          'notes': 'The west bank, 20 above the lava, south of the bridge.'},
         {'outline': rect(4354, 768, 4480, 1024), 'floor': -2240, 'surface': S('ctFlor1'), 'edge': S('ctFlor1'),
          'notes': 'The west bank north of the bridge. The original bank runs on under the bridge; here it stops, because a flight cannot end on a block that stands over a level.'},
         {'outline': rect(4992, -256, 5118, 512), 'floor': -2240, 'surface': S('ctFlor1'), 'edge': S('ctFlor1'),
          'notes': 'The east bank, south of the bridge.'},
         {'outline': rect(4992, 768, 5118, 1024), 'floor': -2240, 'surface': S('ctFlor1'), 'edge': S('ctFlor1'),
          'notes': 'The east bank north of the bridge.'}],
     platforms=[{'at': [4736, 640], 'size': [788, 260], 'base': -2016 - L34, 'rise': 64, 'surface': S('ctFlor1'),
                 'top_surface': S('ctFlor4')}],
     flights=[{'from': [4040, 640], 'to': [4362, 640], 'width': 254, 'steps': 6, 'riser': S('ctFlor1')},
              {'from': [5432, 640], 'to': [5110, 640], 'width': 254, 'steps': 6, 'riser': S('ctFlor1')},
              {'from': [4360, 448], 'to': [3834, 448], 'width': 126, 'steps': 6, 'riser': S('ctFlor1')},
              {'from': [5112, 448], 'to': [5638, 448], 'width': 126, 'steps': 6, 'riser': S('ctFlor1')}],
     notes='A hall 2,816 by 1,280 with its floor (-2048) either side of a channel 768 wide: banks 128 wide at -2240 and '
           'between them 512 of lava at -2260, which flows out through the whole south side into the lava river. A bridge '
           'at -1952 crosses the channel, six steps of 16 up to it from each floor, and a ramp 128 wide leads from each '
           'floor down to its bank (192 over 512). Here the room\'s floor is the lava and the floors and banks are levels (the treads of the four flights take the room\'s floor surface and so are lava), '
           'so that the mouth to the river opens at the lava\'s height; the bridge is a free block; the ramps are flights '
           'of six steps. The original has a strip 64 wide at the foot of the west and east walls: not drawn.')
room('s35', 'Tower corridor, lower (35)', rect(2208, -256, 3296, 0), -2048, -1792, 'ctwl2', 'ctFlor1', 'ctCeil2')

room('s36', 'Lava river (36)',
     [[5120, -256], [4352, -256], [4352, -2560], [3840, -3072], [3328, -3072], [2816, -2560], [2816, -1664], [1920, -768],
      [-2304, -768], [-2304, -1536], [1536, -1536], [2048, -2048], [2048, -2944], [2944, -3840], [4352, -3840], [5120, -2944]],
     L34, -1600, 'ctwl5', LAVA, 'ctCeil1',
     levels=[
         {'outline': [[4480, -256], [4352, -256], [4352, -2560], [3840, -3072], [3328, -3072], [2816, -2560], [2816, -1664],
                      [1920, -768], [-2304, -768], [-2304, -896], [1792, -896], [2688, -1792], [2688, -2688], [3200, -3200],
                      [3968, -3200], [4480, -2688]],
          'floor': -2240, 'surface': S('ctFlor1'), 'edge': S('ctFlor1'), 'notes': 'The inner bank.'},
         {'outline': [[5120, -256], [4992, -256], [4992, -2816], [4224, -3712], [3072, -3712], [2176, -2816], [2176, -1920],
                      [1664, -1408], [-2304, -1408], [-2304, -1536], [1536, -1536], [2048, -2048], [2048, -2944],
                      [2944, -3840], [4352, -3840], [5120, -2944]],
          'floor': -2240, 'surface': S('ctFlor1'), 'edge': S('ctFlor1'), 'notes': 'The outer bank.'}],
     notes='A dead-end tunnel 768 wide and about 9,500 long that leaves the channel hall southward, turns round the '
           'south-east corner of the map and runs west under the tower: 512 of lava (-2260) between two banks 128 wide '
           '(-2240), where the party walks without burning. Fire elementals live along it.')


def helix():
    plats, flights = [], []
    F = -2048
    SB = S('BemVwal')

    def land(corner, top, s):
        sx = 1 if corner in ('NE', 'SE') else -1
        sy = 1 if corner in ('NE', 'NW') else -1
        cx = (2175 - s / 2) if sx > 0 else (513 + s / 2)
        cy = (639 - s / 2) if sy > 0 else (-639 + s / 2)
        plats.append({'at': [cx, cy], 'size': [s, s], 'base': top - 32 - F, 'rise': 32, 'surface': SB})

    def end(wall, corner, s):
        if wall in ('N', 'S'):
            y = 573 if wall == 'N' else -573
            return [513 + s - 6, y] if corner in ('NW', 'SW') else [2175 - s + 6, y]
        x = 579 if wall == 'W' else 2109
        return [x, 639 - s + 6] if corner in ('NW', 'NE') else [x, -639 + s - 6]

    seq = [('NW', -1920, 130), ('SW', -1856, 130), ('SE', -1728, 130), ('NE', -1664, 130), ('NW', -1536, 108),
           ('SW', -1472, 108), ('SE', -1344, 108), ('NE', -1280, 108), ('NW', -1152, 86), ('SW', -1088, 86),
           ('SE', -960, 86)]
    walls = {('NW', 'SW'): 'W', ('SW', 'SE'): 'S', ('SE', 'NE'): 'E', ('NE', 'NW'): 'N'}
    for c, h, s in seq:
        land(c, h, s)
    # the top landing in front of the door: a strip along the north wall (the lower north-east landings must stay
    # findable under it, see NOTES.md)
    plats.append({'at': [2048, 620], 'size': [254, 36], 'base': -896 - 32 - F, 'rise': 32, 'surface': SB})
    flights.append({'from': [1900, 573], 'to': end('N', 'NW', 130), 'width': 132, 'steps': 4, 'riser': SB})
    for (c0, h0, s0), (c1, h1, s1) in zip(seq, seq[1:]):
        w = walls[(c0, c1)]
        flights.append({'from': end(w, c0, s0), 'to': end(w, c1, s1), 'width': 132,
                        'steps': 4 if h1 - h0 > 64 else 2, 'riser': SB})
    flights.append({'from': end('E', 'SE', 86), 'to': [2109, 606], 'width': 132, 'steps': 2, 'riser': SB})
    return plats, flights


hp, hf = helix()
room('s37', 'Stair tower (37)', rect(512, -640, 2176, 640), -2048, -512, 'ctwl2', 'ctFlor5', 'ctCeil3',
     platforms=hp, flights=hf,
     notes='A hall 1,664 by 1,280 and 1,536 high. A ramp 128 wide climbs its four walls three times round, from the '
           'floor (-2048) to the door at -896: free slabs 32 thick that rise 128 along the north and south walls and 64 '
           'along the east and west walls, with level corner pieces. Here: free square landings in the corners and a '
           'flight of steps for each ramp (the same gap as the entrance tower: no sloping free slab). Five crystals stand '
           'on the floor.')
room('s38', 'Upper laboratory passage (38)', [[1920, 672], [2176, 672], [2176, 1024], [3072, 1024], [3072, 1280], [1920, 1280]],
     -896, -640, 'ctwl5', 'ctFlor5', 'ctCeil3')
room('s39', 'Lava cavern (39)', rect(2304, 1408, 3840, 2560), -1408, -384, 'vlcwl1LE', LAVA, 'ctCeil3',
     platforms=[{'at': [2944, 1984], 'size': [260, 1150], 'base': 448, 'rise': 64, 'surface': S('D2Ceil1'),
                 'top_surface': S('ctFlor5')}],
     notes='Lava (-1408) under a walkway 256 wide at -896 that crosses it from the south door to the north door, a free '
           'slab 64 thick with nothing at its edges. A recess in the north wall holds the way out for whoever falls. '
           'The original lava runs on 128 under the west and east walls (a slot 64 high): not drawn.')
room('n39', 'Lava cavern door (39)', rect(2816, 1280, 3072, 1408), -896, -640, 'ctwl5', 'ctFlor5', 'ctCeil3')
room('s39a', 'Lava cavern recess (39)', rect(2432, 2560, 2688, 2688), -1408, -1152, 'ctwl5', 'ctFlor5', 'ctCeil3',
     notes='Dry floor at the lava\'s height; the tile on its back wall sends the party to the lower tower corridor.')
room('s40', 'Library passage (40)', rect(2816, 2560, 3072, 3072), -896, -640, 'ctwl5', 'ctFlor5', 'ctCeil3')
room('s41', 'Library corridor (41)', rect(3072, 2816, 5088, 3072), -896, -640, 'ctwl5', 'ctFlor5', 'ctCeil3')
room('s42', "Gharik's laboratory (42)",
     [[5120, 2816], [5376, 2816], [5888, 2304], [6656, 2304], [6656, 3584], [5888, 3584], [5376, 3072], [5120, 3072]],
     -896, -384, 'vlcwl4B', 'vlctrm3', 'ctCeil1',
     platforms=[{'at': [6527, 3519], 'size': [254, 126], 'rise': 144, 'surface': S('BemVwal')}],
     notes='The goal: the chest with the hourglass of time against the east wall, a bookcase 640 long along the south '
           'wall (searched for scrolls), a bench in the north-east corner. The original ceiling slopes from -512 at the '
           'door to -384; here flat at -384.')

# ---------------------------------------------------------------------------------------------------------------
# Openings
# ---------------------------------------------------------------------------------------------------------------
op('start', 'start_a')
op('start_a', 'tower', notes='Onto the bridge, 1,664 above the lava.')
op('tower', 's2', notes='From the foot of the ramp.')
op('s2', 's1')
op('s1', 's3', notes='The gate hall\'s whole north side (768), open to the lava hall at the hall\'s ceiling height.')
op('s3', 's4')
op('s4', 's8')
op('s11', 's13')
op('s13', 's15')
op('s12', 's14')
op('s15', 's46s')
op('s46s', 's46m')
op('s46m', 's46n')
op('s46n', 's43')
op('s46m', 's47st')
op('s47st', 's47')
op('s47', 's44')
op('s47', 's45')
op('n50', 'machine', height=240)
op('machine', 'n43')
op('n43', 's43')
op('machine', 'n44', notes='From the lower north-west balcony.')
op('n44', 's44')
op('n51', 's44')
op('machine', 'n45', notes='From the lower south-west balcony.')
op('n45', 's45')
op('s15', 'n49')
op('n48', 's18')
op('p52', 's45')
op('s18', 's19')
op('s18', 's21')
op('s22', 'loop')
op('s28', 's29')
op('s24', 's30')
op('shaft', 'shaftb')
op('s32', 's33')
op('s33', 'n33')
op('s34', 's36', notes='The channel (two banks and the lava between) runs out through the whole 768.')
op('s38', 'n39')
op('n39', 's39')
op('s39', 's40', height=256)
op('s39', 's39a')
op('s40', 's41')

DOORS, SWITCHES, EVENTS, LIFTS = [], [], [], []
CV = S('CVDOR1', fit=True)


def door(did, a, b, cx, cy, width=128, height=256, surface=CV, state='closed', speed=500, notes=None, thickness=None):
    oid = op(a, b, width=width, height=height, along=door_along(a, b, cx, cy))
    d = {'id': 'door:' + did, 'opening': oid, 'kind': 'slide_up', 'state': state, 'speed': speed, 'surface': surface}
    if thickness:
        d['thickness'] = thickness
    if notes:
        d['notes'] = notes
    DOORS.append(d)
    return d['id']


def switch(sid, rid, x, y, z, notes=None, **kw):
    e, t = edge_along(rid, x, y)
    s = {'id': 'switch:' + sid, 'room': 'room:' + rid, 'wall': e, 'along': t,
         'height': z - RB[rid]['floor'], 'size': [32, 32]}
    s.update(kw)
    if notes:
        s['notes'] = notes
    SWITCHES.append(s)
    return s['id']


def lever_door(n, a, b, cx, cy, lever_room, lx, ly, lz, door_no, **kw):
    """Event n of the original: a lever that lifts a door for good."""
    d = door('d%d' % door_no, a, b, cx, cy, **kw)
    s = switch('lever%d' % n, lever_room, lx, ly, lz)
    EVENTS.append({'id': 'evt:lever%d' % n, 'preset': 'switch', 'source': s, 'title': 'Lever', 'opens': [d],
                   'notes': 'Original event %d: lever (door %d, a plate that sinks 16) and door %d.' % (n, door_no - 1, door_no)})
    EVENTS.append({'id': 'evt:budge%d' % door_no, 'preset': 'text', 'source': d, 'title': 'Door',
                   'text': "The Door won't budge.", 'notes': 'Original event 55, on the door\'s two faces.'})


# the split doors, clicked themselves (events 2 and 13)
d = door('d1', 's1', 's7', 512, 1664, width=224, height=256, surface=S('D2WlActr'), speed=200,
         notes='Original doors 1 and 2: the doorway is closed by two halves one above the other, the lower (0 to 128) '
               'sliding north into the wall and the upper (130 to 256) sliding south, both 255 at 200 a second, when either '
               'is clicked (event 2). No kind slides sideways or splits a leaf: one leaf lifts.')
EVENTS.append({'id': 'evt:door1', 'preset': 'door', 'source': d, 'title': 'Door', 'action': 'open'})
d = door('d23', 'loop', 's28', 3072, 3200, width=224, height=256, surface=S('D2WlActr'), speed=200,
         notes='Original doors 23 and 24, clicked (event 13): the same split, sideways-sliding pair as door:d1.')
EVENTS.append({'id': 'evt:door23', 'preset': 'door', 'source': d, 'title': 'Door', 'action': 'open'})

lever_door(4, 's8', 's9', -1792, 4096, 's8', -1696, 4096, 124, 6)
lever_door(5, 's9', 's10', -1792, 6144, 's9', -1696, 6144, 124, 8)
lever_door(6, 's9', 's11', -1536, 5248, 's9', -1536, 5344, 124, 10)
lever_door(7, 's13', 's12', -384, 5120, 's13', -288, 5120, 124, 12)
lever_door(9, 's19', 's20', 3616, 8576, 's19', 3616, 8480, 124, 16)
lever_door(10, 's21', 's23', 4992, 5664, 's21', 4896, 5664, 124, 18)
lever_door(11, 's23', 's22', 4352, 4736, 's23', 4352, 4832, 124, 20)
lever_door(12, 'loop', 's24', 4096, 3456, 'loop', 4096, 3360, 124, 22)
lever_door(14, 's30', 'shaft', 4736, 2592, 's30', 4640, 2592, 124, 26)
lever_door(17, 'n33', 's34', 6016, 1056, 'n33', 5916, 1056, -1924, 32)
lever_door(18, 's34', 's35', 3328, -128, 's34', 3328, -32, -1924, 34)
lever_door(19, 's35', 's37', 2208, -128, 's35', 2208, -32, -1924, 36)
lever_door(20, 's37', 's38', 2048, 640, 's37', 2144, 640, -772, 38)
lever_door(21, 's41', 's42', 5088, 2944, 's41', 5088, 2848, -772, 40, surface=S('vlcdorC', fit=True))

# the laboratory door (event 16): Gharik's key
d30 = door('d30', 'shaftb', 's32', 4736, 2080)
s16 = switch('lever16', 'shaftb', 4640, 2080, -1924)
EVENTS.append({'id': 'evt:lever16', 'preset': 'switch', 'source': s16, 'title': 'Lever', 'opens': [d30],
               'condition': {'any': [{'item': 'gharik_key'}, {'qbit': 'lab_door_opened'},
                                     {'qbit': 'tomb_opened', 'not': {'qbit': 'seer_key_bit'}}]},
               'locked_text': 'The Door is locked',
               'effects': [{'take_item': 'gharik_key'}, {'qbit': 'lab_door_opened'}, {'clear_qbit': 'seer_key_bit'}],
               'notes': 'Original event 16: the lever opens the door (lever plate 29, door 30) when the party carries the Key '
                        'to Gharik\'s Laboratory or has opened it before (qbit 1400); it also opens without the key when '
                        'qbit 1035 is set and qbit 1223 is not. It takes the key, sets 1400 and clears 1223.'})
EVENTS.append({'id': 'evt:budge30', 'preset': 'text', 'source': d30, 'title': 'Door', 'text': "The Door won't budge."})

# the bridge of the first lava hall (event 3)
LIFTS.append({'id': 'lift:bridge3', 'room': 'room:s3', 'at': [128, 2592], 'size': [260, 958], 'travel': 744, 'speed': 200,
              'state': 'down', 'surface': SLAB,
              'notes': 'Stands for original door 4: the end face of the bridge stub, which the lever pushes 959 north at 200 '
                       'a second, stretching the bridge (256 wide, top at -16, 112 thick) across the lava to the north door. '
                       'No moving part slides sideways or stretches; the nearest that can be said is a block of the same '
                       'plan that rises 752 out of the lava to the same height.'})
s3 = switch('lever3', 's7', 1500, 768, 154, notes='At the lever room\'s far south-east corner.')
EVENTS.append({'id': 'evt:lever3', 'preset': 'switch', 'source': s3, 'title': 'Lever', 'opens': ['lift:bridge3'],
               'notes': 'Original event 3: lever plate (door 3) and the bridge (door 4), once.'})

# the lift (event 15) with a lever at the top and one at the bottom
LIFTS.append({'id': 'lift:shaft', 'room': 'room:shaft', 'at': [4736, 2432], 'size': [254, 240], 'travel': 2024,
              'speed': 200, 'state': 'up', 'surface': S('vlcwl1LG'),
              'notes': 'Original door 28: the lift floor, 256 by 240, from -16 down 2,032 at 200 a second (ten seconds). '
                       'A lift here is a solid block from the shaft floor, where the original is a floor 16 thick.'})
st = switch('lever15_top', 'shaft', 4832, 2560, 124)
sb = switch('lever15_foot', 'shaft', 4832, 2560, -1924)
for s, nm in ((st, 'top'), (sb, 'foot')):
    EVENTS.append({'id': 'evt:lever15_' + nm, 'preset': 'switch', 'source': s, 'title': 'Lever', 'toggles': ['lift:shaft'],
                   'notes': 'Original event 15, bound to the lever at the top of the shaft and to the one at its foot '
                            '(door 27 is both plates).'})

# the machine room
g50 = door('gate50', 's15', 'n50', 1920, 4864, width=224, height=240, surface=S('vlcwl3a'), state='open',
           notes='Original door 50: a gate 256 wide that drops 239 from the lintel; starts open.')
g49 = door('gate49', 'n49', 'machine', 3200, 5088, width=224, height=240, surface=S('vlcwl3a'),
           notes='Original door 49; starts closed.')
g48 = door('gate48', 'machine', 'n48', 3200, 6912, width=224, height=240, surface=S('vlcwl1LG'), state='open',
           notes='Original door 48; starts open.')
g52 = door('gate52', 'p52', 'machine', 2912, 5088, width=224, height=240, surface=S('vlcGnrc1'),
           notes='Original door 52 (lower level); starts closed.')
g51 = door('gate51', 'machine', 'n51', 2912, 6912, width=224, height=240, surface=S('vlcGnrc1'),
           notes='Original door 51 (lower level); starts closed.')
lw = door('lava_wall', 's15', 'alcove', 1088, 4608, width=128, height=256, surface=S('vlcwl3a'), speed=50, thickness=32,
          notes='Stands for original door 53 and wall face 2255 (the "lava wall").')
LIFTS.append({'id': 'lift:bridge_w', 'room': 'room:machine', 'at': [1920, 5888], 'size': [256, 1026], 'travel': 760,
              'speed': 200, 'state': 'up', 'surface': S('BemVwal'),
              'notes': 'Original door 14 in its starting place: the bridge between the two upper west balconies.'})
LIFTS.append({'id': 'lift:bridge_e', 'room': 'room:machine', 'at': [3200, 5888], 'size': [256, 1026], 'travel': 760,
              'speed': 200, 'state': 'down', 'surface': S('BemVwal'),
              'notes': 'Original door 14 after the lever: the same bridge, 1,280 to the east, between the upper east '
                       'balconies. One bridge that slides sideways cannot be said; two lifts that swap say the same '
                       'connections.'})


def mlever(n, x, y, z, notes, **kw):
    s = switch('lever%d' % n, 'machine', x, y, z)
    e = {'id': 'evt:lever%d' % n, 'preset': 'switch', 'source': s, 'title': 'Lever', 'notes': notes}
    e.update(kw)
    EVENTS.append(e)


mlever(33, 3352, 5120, 124, 'Original event 33 (upper south-east balcony): toggles gate 48.', toggles=[g48])
mlever(34, 1768, 5120, 124, 'Original event 34 (upper south-west balcony): toggles gate 50.', toggles=[g50])
mlever(35, 3352, 6912, 124, 'Original event 35 (upper north-east balcony): toggles the lava wall of the chest alcove.',
       toggles=[lw])
mlever(36, 1768, 6912, 124, 'Original event 36 (upper north-west balcony): toggles gate 51.', toggles=[g51])
mlever(38, 2360, 5120, -388, 'Original event 38 (lower south-west balcony): toggles gate 48.', toggles=[g48])
mlever(8, 2760, 5120, -388, 'Original event 8 (lower south-east balcony): slides the bridge east for good and opens gate 49.',
       opens=['lift:bridge_e', g49], closes=['lift:bridge_w'])
mlever(39, 2760, 6912, -388, 'Original event 39 (lower north-east balcony): toggles gate 52 and opens gate 49.',
       toggles=[g52], opens=[g49])
mlever(40, 2360, 6912, -388, 'Original event 40 (lower north-west balcony): toggles gate 49.', toggles=[g49])

# the cavern's way out (event 43): a clicked tile on the recess wall
def tile(n, rid, x, y, z, to, direction, where):
    sw = switch('tile%d' % n, rid, x, y, z, size=[64, 64], off=S('OrFyr64B'), on='orfyr64b')
    EVENTS.append({'id': 'evt:tile%d' % n, 'preset': 'switch', 'source': sw, 'title': 'Tile',
                   'lua': 'SetValue(MapVar(2), 0)\nevt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 0)' % (to[0], to[1], to[2], direction),
                   'notes': 'Original event %d: a clicked tile that puts the party %s. The teleport preset takes no '
                            'source in a new map, so a switch runs the move as Lua.' % (n, where)})


tile(43, 's39a', 2560, 2688, -1248, (2324, -141, -2047), 896, 'in the lower tower corridor (the tile is on the recess wall in the original too)')
tile(42, 's3', -768, 3072, -700, (134, 1151, 1), 502, 'back in the tower corridor (in the original the tile lies on the island floor at the wall\'s foot)')
tile(41, 's9', -2048, 5184, -190, (-1822, 4049, 1), 502, 'back in the west corridor (a floor tile in the original)')
fw = switch('fire_wall', 's3', 128, 3072, 400, size=[64, 64], off=S('vlcwl3a'), on='vlcwl3a',
            notes='Stands for the wall face above the north door (256 wide, from 284 to 512) that the original binds event 91 to.')
EVENTS.append({'id': 'evt:fire_wall', 'preset': 'switch', 'source': fw,
               'lua': 'if not IsAtLeast(MapVar(46), 1) and not IsPlayerBitSet(PlayerBit(59)) then\n    SetValue(MapVar(46), 1)\n    SetPlayerBit(PlayerBit(59))\n    AddValue(FireResistance, 25)\nend',
               'notes': 'Original event 91: clicked once, the wall gives +25 fire resistance (player bit 59, map variable 46). No preset gives a resistance once per map, so Lua.'})
tile(31, 'machine', 2752, 6912, -700, (1916, 6618, 1), 502, 'on the north-west balcony (a floor tile in the original)')

# ---------------------------------------------------------------------------------------------------------------
# Objects taken from the original at their own places
# ---------------------------------------------------------------------------------------------------------------


def room_at(x, y, z, tol=48):
    best = None
    for rid, r in RB.items():
        lo = min(r['floor'], r.get('slope', {}).get('to', r['floor']))
        hi = max([r['ceiling']] + [c['ceiling'] for c in r.get('ceiling_levels', [])])
        if not (lo - 40 <= z <= hi + 8):
            continue
        d = poly_dist(r['outline'], x, y)
        if d <= tol and (best is None or d < best[0]):
            best = (d, rid)
    return best[1] if best else None


def nudge(rid, x, y, by=12):
    """A point at least `by` inside the room."""
    p = RB[rid]['outline']
    if inside(p, x, y) and min(seg_dist(p[i], p[(i + 1) % len(p)], x, y)[0] for i in range(len(p))) >= by:
        return [x, y]
    best = None
    for dx in range(-64, 65, 4):
        for dy in range(-64, 65, 4):
            qx, qy = x + dx, y + dy
            if inside(p, qx, qy) and min(seg_dist(p[i], p[(i + 1) % len(p)], qx, qy)[0] for i in range(len(p))) >= by:
                dd = dx * dx + dy * dy
                if best is None or dd < best[0]:
                    best = (dd, [qx, qy])
    return best[1] if best else None


DECOS, LIGHTS, SPAWNS, PLACE, LOST = [], [], [], [], []
n = 0
for e in ORIG['entities']:
    x, y, z = e['position']
    if e['name'] == 'Party Start':
        continue
    rid = room_at(x, y, z)
    at = nudge(rid, x, y) if rid else None
    if not at:
        LOST.append(('decoration', e['name'], e['position']))
        continue
    n += 1
    DECOS.append({'id': 'deco:%s_%02d' % (e['name'].lower(), n), 'room': 'room:' + rid, 'decoration': e['name'].lower(),
                  'at': at, 'height': z - RB[rid]['floor']})
n = 0
for l in ORIG['lights']:
    x, y, z = l['position']
    rid = room_at(x, y, z)
    at = nudge(rid, x, y) if rid else None
    if not at:
        LOST.append(('light', '', l['position']))
        continue
    n += 1
    LIGHTS.append({'id': 'light:l%02d' % n, 'room': 'room:' + rid, 'at': at, 'height': max(8, z - RB[rid]['floor']),
                   'radius': l['radius'], 'color': [255, 200, 140], 'brightness': l['brightness']})
SLOT = {1: 1, 2: 2, 3: 3, 4: 1, 5: 2, 6: 3, 7: 1, 8: 2, 9: 3, 10: 1, 11: 2, 12: 3}
n = 0
items = 0
for i, s in enumerate(ORIG['spawns']):
    x, y, z = s['position']
    rid = room_at(x, y, z)
    at = nudge(rid, x, y, 40) if rid else None
    if not at:
        LOST.append(('spawn', i, s['position']))
        continue
    if s['type_id'] == 3:
        n += 1
        SPAWNS.append({'id': 'spawn:m%02d' % i, 'room': 'room:' + rid, 'at': at, 'slot': SLOT[s['index']],
                       'radius': s['radius'],
                       'notes': 'Original spawn %d: monster index %d at z %d.' % (i, s['index'], z)})
    else:
        items += 1
        PLACE.append({'id': 'placeholder:item%02d' % i, 'room': 'room:' + rid, 'at': at,
                      'stands_for': 'A random item on the floor, treasure level %d (original spawn %d, an item spawn at z %d).' % (s['index'], i, z),
                      'size': [32, 32, 32]})

CHESTS = []


def chest(n, rid, x, y, facing, front, notes=None, **kw):
    c = {'id': 'chest:c%d' % n, 'room': 'room:' + rid, 'at': [x, y], 'facing': facing, 'size': [96, 62, 64],
         'surface': S(front), 'treasure_level': 4, 'random_items': 3}
    c.update(kw)
    if notes:
        c['notes'] = notes
    CHESTS.append(c)
    e = {'id': 'evt:chest%d' % n, 'preset': 'chest', 'source': c['id'], 'title': 'Chest'}
    EVENTS.append(e)
    return e


chest(1, 's10', -1440, 6704, 'w', 'ch3frntB', notes='Original chest 1 (event 44), against the east wall.')
chest(2, 's20', 2512, 7969, 'n', 'ch3frntB', notes='Original chest 2 (event 45), against the south wall.')
chest(3, 's29', 2864, 4319, 's', 'ch2FRNTb', notes='Original chest 3 (event 46).')
chest(4, 's29', 3280, 4319, 's', 'ch1frntB', notes='Original chest 4 (event 47).')
e = chest(5, 's42', 6623, 2864, 'w', 'ch2FRNTb', items=['hourglass_of_time'],
          notes='Original chests 5 and 8 (event 48): the first opening gives chest 5, with the Hourglass of Time, and sets '
                'qbits 1029 and 1207; a party that already has qbit 1029 from another visit gets chest 8 instead. One chest '
                'here; the second, lesser chest cannot be said (an event that opens one of two chests).')
e['effects'] = [{'qbit': 'hourglass_taken'}, {'qbit': 'seer_hourglass_bit'}]
c = {'id': 'chest:bookcase', 'room': 'room:s42', 'at': [6336, 2369], 'size': [638, 126, 256],
     'surface': S('Bookcas2'), 'end_surface': S('BemVwal'), 'treasure_level': 1, 'random_items': 1,
     'items': [1961, 1973, 1976, 1988],
     'notes': 'The bookcase along the south wall (original event 62): searched up to four times, each time one scroll '
              'drawn at random from six (items 1961, 1973, 1976, 1988, 1965, 1962) with "Found something!". Here a chest '
              'in the bookcase\'s shape holding four of them (and one random item: a chest cannot hold none).'}
CHESTS.append(c)
EVENTS.append({'id': 'evt:bookcase', 'preset': 'chest', 'source': c['id'], 'title': 'Bookcase'})
chest(6, 'alcove', 912, 4129, 'n', 'ch3frntB', notes='Original chest 6 (event 49).')
chest(7, 'alcove', 1232, 4129, 'n', 'ch3frntB', notes='Original chest 7 (event 50).')

EXITS = [{'id': 'exit:door', 'room': 'room:start', 'wall': edge_along('start', -2688, 1280)[0], 'along': 0.5,
          'size': [224, 256], 'surface': S('D2LgDor'), 'to': 'exit:new_sorpigal'}]
EVENTS.append({'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:door', 'title': "Leave Gharik's Forge"})

# things with no word
PLACE += [
    {'id': 'placeholder:tile32', 'room': 'room:tower', 'at': [-1280, 768], 'size': [128, 128, 64],
     'stands_for': 'A raised floor tile (OrFyr64B, 128 square, 64 above the island) that is clicked: teleports the party to the start (-2688, 1152, 1152). Original event 32.'},
]

# ---------------------------------------------------------------------------------------------------------------
# Check: the build cuts an opening in the pair of facing walls with the longest shared stretch (within 512).
# ---------------------------------------------------------------------------------------------------------------
def chosen_pair(a, b):
    pa, pb = RB[a]['outline'], RB[b]['outline']
    best = (0, None)
    for i in range(len(pa)):
        a0, a1 = pa[i], pa[(i + 1) % len(pa)]
        L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
        ux, uy = (a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L
        ox, oy = uy, -ux
        for j in range(len(pb)):
            b0, b1 = pb[j], pb[(j + 1) % len(pb)]
            Lb = math.hypot(b1[0] - b0[0], b1[1] - b0[1])
            vx, vy = (b1[0] - b0[0]) / Lb, (b1[1] - b0[1]) / Lb
            if ux * vx + uy * vy > -1 + 1e-9:
                continue
            gap = (b0[0] - a0[0]) * ox + (b0[1] - a0[1]) * oy
            if gap < -1e-6 or gap > 512:
                continue
            ts = (b0[0] - a0[0]) * ux + (b0[1] - a0[1]) * uy
            lo, hi = max(0, ts - Lb), min(L, ts)
            if hi - lo > best[0] + 1e-6:
                best = (hi - lo, (gap, [a0[0] + ux * (lo + hi) / 2, a0[1] + uy * (lo + hi) / 2]))
    return best


for o in OPEN:
    a, b = o['from'][5:], o['to'][5:]
    ov, info = chosen_pair(a, b)
    if info is None:
        print('NO PAIR', o['id'])
        continue
    if info[0] not in (0, 32) or ov not in (128, 248, 256, 512, 768, 384, 1152):
        print('check opening', o['id'], 'gap', info[0], 'stretch', ov, 'middle', info[1])

# ---------------------------------------------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------------------------------------------
themes = []
for (w, f, c), tid in sorted(THEMES.items(), key=lambda kv: kv[1]):
    themes.append({'id': tid, 'wall': S(w), 'floor': S(f), 'ceiling': S(c)})

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': themes[0]['id'], 'ambient': 16}, 'rooms': ROOMS,
             'openings': OPEN,
             'notes': "Gharik's Forge (MM6 6d18.blv) in the original's own frame. Every room is one of the original's "
                      "sectors (its number is in the name) or a part of one; outlines are the sectors' floor outlines as "
                      "measured, all straight walls on the original's 32 grid. Doors stand in walls 32 thick, as in the "
                      "original. The lava rooms have the lava as their floor and everything walked on as levels or free "
                      "blocks. Written by output/studio_cal/mm6_6d18/gen.py."}
objects_doc = {'format': 0, 'start': {'room': 'room:start', 'at': [-2688, 1216], 'facing': 'e',
                                      'notes': "The original's Party Start decoration."},
               'doors': DOORS, 'lifts': LIFTS, 'lights': LIGHTS, 'switches': SWITCHES, 'chests': CHESTS,
               'spawns': SPAWNS, 'decorations': DECOS, 'placeholders': PLACE, 'exits': EXITS}
wiring_doc = {'format': 0, 'events': EVENTS,
              'notes': 'Not wired, for want of a word: the lava (events 51 to 54), the fire and gold fountains (timers 56 to '
                       '61), four of the five escape tiles, the fire-resistance wall (91), the scroll bookcase (62), the '
                       'second hourglass chest. See NOTES.md.'}
project_doc = {
    'format': 0, 'id': 'cal6d18', 'name': "Gharik's Forge", 'world': 'mm6', 'kind': 'indoor', 'profile': 'dungeon',
    'map_stats': {'id': 9716, 'reference': '6d18.blv'},
    'neighbours': [{'id': 'exit:new_sorpigal', 'to': 'oute3.odm', 'kind': 'door', 'arrival': [15585, 11125, 97],
                    'direction': 90, 'arrival_hint': "Outside the forge's door."}],
    'qbits': {'tomb_opened': 1035, 'seer_key_bit': 1223, 'lab_door_opened': 1400, 'hourglass_taken': 1029,
              'seer_hourglass_bit': 1207},
    'items': {'gharik_key': 2107, 'hourglass_of_time': HOURGLASS} if (HOURGLASS := int(os.environ.get('HOURGLASS', '0'))) else {'gharik_key': 2107},
    'notes': "Rebuild of Gharik's Forge (mm6 6d18.blv) by devdocs/map_studio/REBUILD_PROCEDURE.md: a test of the room "
             "vocabulary on lava and mechanisms. NOTES.md beside this file holds the scores, the gaps and the tool defects."}
if 'hourglass_of_time' not in project_doc['items']:
    for c in CHESTS:
        c.pop('items', None)

for name, doc in (('rooms.yml', rooms_doc), ('objects.yml', objects_doc), ('wiring.yml', wiring_doc),
                  ('project.yml', project_doc)):
    json.dump(doc, open(L4 + name, 'w'), indent=1)
print('rooms', len(ROOMS), 'openings', len(OPEN), 'doors', len(DOORS), 'lifts', len(LIFTS), 'switches', len(SWITCHES),
      'events', len(EVENTS), 'decorations', len(DECOS), 'lights', len(LIGHTS), 'spawns', len(SPAWNS), 'item spawns', items)
for l in LOST:
    print('lost', l)
