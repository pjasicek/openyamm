#!/usr/bin/env python3
"""X9 Clouds of Xeen: writes the L3 and L4 rooms.yml (A5 sub-agent, 2026-11-21), modelled on X8's gen.py.

One open-air room (room:air) from the safety floor at -6000 to the sky at 6400; its walls, floor and ceiling are sky
faces. Every cloud is a hanging platform with the L1 outline (geom.blob: the plan's islands, so the spans measured at
L1 are the spans built), a cloud top and cloud sides, and flared roots under it. Necks are cloud slabs, the Xeen road a
cloud slab with cloud-stone flags on top, rope bridges plank decks with rope rails, the aviary stair a cloud-stone
ramp, the unseen way a slab whose top is the faint wisp texture and whose sides and underside are sky faces (not drawn).
Castle Xeen's shell is a closed set of blocks (walls, towers, keep, roof) on its own cloud, over XD-19's measured
footprint (design.py CASTLE_HEIGHTS, XD19_OFFSET).

    python3 level_generation/projects/xeen/x9/gen.py     # writes devdocs/xeen/briefs/x9/L3 and L4 rooms.yml (+ L3's start)
"""
import math
import random
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design as D  # noqa: E402
import geom as G  # noqa: E402

ROOT = HERE.parents[3]
BRIEF = ROOT / 'devdocs/xeen/briefs/x9'

FLOOR = -6000          # the safety floor (a fall the one-second check misses ends here and runs the same fall)
SINK = 8               # how far a block is sunk into what it stands on (X8's, F62: no bottom on the walking plane)
CEIL = 6400
SLAB = 256             # cloud slab thickness under its top

CLOUD_TOP = {'texture': 'xccloud', 'size': [256, 256], 'scale': 2}
CLOUD_SIDE = {'texture': 'xccloudsd', 'size': [256, 256], 'scale': 2, 'uneven': True}
WISP = {'texture': 'xcwisp', 'size': [256, 256], 'scale': 2, 'translucent': 0.55}   # faint: the sky shows through
SKY = {'texture': 'xccloud', 'size': [256, 256], 'scale': 32, 'sky': True}
MARBLE = {'texture': '7tws1f', 'size': [128, 128]}
DECK = {'texture': 't66floor', 'size': [128, 128]}
ROPE = {'texture': 'hwm2rf', 'size': [128, 128]}
ROCK = {'texture': 'gcav1flr', 'size': [128, 128]}
STRAW = {'texture': 'gkp1flr', 'size': [128, 128]}
BRONZE = {'texture': 'xngong5', 'size': [128, 32]}
CANVAS = {'texture': 'tentwal7b', 'size': [128, 256], 'scale': 2}   # MM6's red and white tent canvas (D-50: shipped
                                                                    # first) at twice its size: once up every wall
AWNING = {'texture': 'tentwal7b', 'size': [128, 256], 'scale': 4}   # the awnings: once over each 1,024 x 496 roof
VALANCE = {'texture': 'tentwal7a', 'size': [128, 256]}         # the same with its scalloped hem along the top
STONE = {'texture': 'gnecwal1', 'size': [256, 256]}            # XD-19's black stone (MM8 Escaton's Palace, d35)
FRIEZE = {'texture': 'gnecwalt', 'size': [256, 256]}           # its gold frieze row: one band at each wall's top
LEAF_L = {'texture': 'gnecdr1l', 'size': [128, 256], 'fit': True}
LEAF_R = {'texture': 'gnecdr1r', 'size': [128, 256], 'fit': True}
TARGET = {'texture': 'xctarget', 'size': [128, 128], 'fit': True}

SPACE = G.SPACE


CASTLE = SPACE['zone:castle']
CX, CY = CASTLE['at']
CW, CD = CASTLE['extent']
SHELL = (CX - CW / 2, CY - CD / 2, CX + CW / 2, CY + CD / 2)       # x0, y0, x1, y1: XD-19's measured footprint
BASE = CASTLE['floor']                                              # 768: the castle cloud's top, the gate sill
H = D.CASTLE_HEIGHTS
GATE = G.place_at(next(p for p in D.PLACES if p['id'] == 'poi:castle_gate'), {})   # (0, 11776)


def polys():
    return G.outlines()


POLYS = polys()
OUTLINES = {k: [[int(round(x)), int(round(y))] for x, y in v] for k, v in POLYS.items()}
CLOUDS = [s for s in D.SPACES if s['kind'] in ('cloud', 'sealed', 'castle')]


def key(sid):
    return sid.split(':', 1)[1]


def floor_of(sid):
    return SPACE[sid]['floor']


def inside(poly, p):
    x, y = p
    c = False
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def rim_distance(poly, p):
    best = 1e18
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


def platform_slab(pid, a, b, z0, z1, width, surface, top_surface, thickness, notes=None, bottom=None):
    """A hanging slab from point a (top z0) to b (top z1), `width` wide (X8's)."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    facing = math.degrees(math.atan2(by - ay, bx - ax))
    low = min(z0, z1) - thickness
    entry = {
        'id': pid,
        'at': [int(round((ax + bx) / 2)), int(round((ay + by) / 2))],
        'size': [int(round(length)), width],
        'facing': round(facing, 2),
        'base': int(low - FLOOR),
        'rise': int(min(z0, z1) - low),
        'top_heights': [int(z0 - low), int(z1 - low), int(z1 - low), int(z0 - low)],
        'thickness': thickness,
        'surface': surface,
        'top_surface': top_surface,
        'bottom_surface': bottom or surface,
    }
    if int(z0) == int(z1):
        del entry['top_heights'], entry['thickness']    # a level span (F62's landings): base and rise
    if notes:
        entry['notes'] = notes
    return entry


def block(pid, at, size, z, rise, surface, top=None, facing=None, top_size=None, notes=None, sink=SINK, **kw):
    # F62 (X8 p8, ported 2026-11-25): every block hangs from the room's floor at -6,000, so the studio draws its
    # bottom; a bottom lying on the cloud (or on the block under it) is a ceiling at the party's feet. Each block is
    # sunk SINK into what it stands on, its top where it was (tools/xeen/check_floor_cross.py floor.lid); not a block
    # whose sides run on in the plane of the sides under it (sink=0: they would flicker), which nobody walks under.
    e = {'id': pid, 'at': [int(round(at[0])), int(round(at[1]))], 'size': [int(round(size[0])), int(round(size[1]))],
         'base': int(round(z - sink - FLOOR)), 'rise': int(round(rise + sink)), 'surface': surface}
    if top:
        e['top_surface'] = top
    if facing is not None:
        e['facing'] = round(facing, 2)
    if top_size:
        e['top_size'] = top_size
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def ring(cx, cy, r, sides=16, phase=0.0):
    return [[int(round(cx + r * math.cos(phase + 2 * math.pi * k / sides))),
             int(round(cy + r * math.sin(phase + 2 * math.pi * k / sides)))] for k in range(sides)]


def link_ends(link):
    return G.link_ends(link, POLYS)


def link_cut(link, into):
    """The link's two rim points, run `into` each cloud along its line."""
    p, q = link_ends(link)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * into, p[1] - uy * into), (q[0] + ux * into, q[1] + uy * into), d, (ux, uy)


def landing_end(poly, start, u, width, margin=24):
    """Where a deck of `width` leaving `start` (on its cloud) along `u` is past the cloud across its whole width: the
    point on the centre line `margin` beyond the furthest bit of cloud under the deck (X8's, F62)."""
    ux, uy = u
    nx, ny = -uy, ux
    far = 0
    for k in range(9):
        o = (k / 8 - 0.5) * width
        t = 0
        while t < 20000:
            if inside(poly, (start[0] + ux * t + nx * o, start[1] + uy * t + ny * o)):
                far = max(far, t)
            t += 8
            if t > far + 2000:
                break
    far += margin
    return (start[0] + ux * far, start[1] + uy * far)


def level_spans(link, a, b, u, width, za8, zb8, partial=True):
    """F62 (the player's pins 2026-11-25, X8 "bridge is clipping"): a deck sloping straight from inside one cloud to
    inside the other dips under the higher cloud's top before its rim, or stands out of the lower one. It lies level
    at each cloud's height out to where it is past that cloud across its whole width, and slopes only between:
    [(p, q, z0, z1)] from a to b. When the clouds leave no room between (they overlap), it lies level on the higher
    cloud only and slopes from inside the lower one (`partial`; a rising deck stands out of the lower cloud, which is
    meant), else one straight span."""
    ux, uy = u

    def along(p, q):
        return (q[0] - p[0]) * ux + (q[1] - p[1]) * uy
    pa = landing_end(POLYS[link['a']], a, (ux, uy), width)
    pb = landing_end(POLYS[link['b']], b, (-ux, -uy), width)
    if along(pa, pb) >= 64:
        return [(a, pa, za8, za8), (pa, pb, za8, zb8), (pb, b, zb8, zb8)]
    if partial and zb8 > za8 and along(a, pb) >= 64 and along(pb, b) >= 64:
        return [(a, pb, za8, zb8), (pb, b, zb8, zb8)]
    if partial and za8 > zb8 and along(a, pa) >= 64 and along(pa, b) >= 64:
        return [(a, pa, za8, za8), (pa, b, za8, zb8)]
    return [(a, b, za8, zb8)]


# ------------------------------------------------------------------------------------------------ clouds

def clouds():
    out = []
    for i, s in enumerate(CLOUDS):
        sid = s['id']
        fl = s['floor']
        name = s['name'] if s['kind'] != 'castle' else "Castle Xeen's cloud"
        out.append({
            'id': f'platform:{key(sid)}' if s['kind'] != 'castle' else 'platform:castle_cloud',
            'outline': OUTLINES[sid],
            'base': fl - SLAB - FLOOR,
            'rise': SLAB,
            'surface': CLOUD_SIDE,
            'top_surface': CLOUD_TOP,
            'bottom_surface': CLOUD_SIDE,
            'notes': f'{name}: a cloud, its top at {fl}.' + (' Sealed: no link (Q-F1, FD-04\'s roof).'
                                                              if s['kind'] == 'sealed' else ''),
        })
        # roots: two or three flared cloud masses under the cloud (X8's)
        ex, ey = s['extent'] if s['kind'] != 'castle' else (CW + 2048, CD + 2048)
        cx, cy = s['at']
        rnd = random.Random(100 + i)
        roots = 3 if ex * ey > 12e6 else 2
        for r in range(roots):
            ox = rnd.uniform(-0.08, 0.08) * ex
            oy = rnd.uniform(-0.08, 0.08) * ey
            top_w = int(0.5 * ex) // 16 * 16
            top_d = int(0.5 * ey) // 16 * 16
            depth = int(rnd.uniform(900, 1700)) // 16 * 16
            out.append({
                'id': f'platform:{key(sid)}_root{r + 1}',
                'at': [int(cx + ox), int(cy + oy)],
                'size': [max(160, top_w // 5), max(160, top_d // 5)],
                'top_size': [top_w, top_d],
                'base': fl - SLAB + 8 * (r + 1) - depth - FLOOR,
                'rise': depth,
                'surface': CLOUD_SIDE,
                'top_surface': CLOUD_SIDE,
                'bottom_surface': CLOUD_SIDE,
            })
    return out


# ------------------------------------------------------------------------------------------------ links

def links():
    platforms, beams = [], []
    # the gate causeway: cloud-stone flags from the gate court's middle up onto the castle's cloud, ending 64 short of
    # the return point (link:gate's approach; the two clouds only overlap, 64 apart in height)
    gc = SPACE['room:gate_court']
    a, b = (0, gc['at'][1]), (0, RETURN[1] - 64)
    # F62 (2026-11-25): the straight slope ran under the castle cloud's top before its rim (check_floor_cross.py
    # floor.cross at (-504, 10926)); it lies level at the castle's height where the castle cloud is under it
    pb = landing_end(POLYS['zone:castle'], b, (0, -1), 1024)
    spans = [(a, pb, gc['floor'] + 8, BASE + 8), (pb, b, BASE + 8, BASE + 8)] if a[1] + 64 <= pb[1] <= b[1] - 64 \
        else [(a, b, gc['floor'] + 8, BASE + 8)]
    for k, (p, q, z0, z1) in enumerate(spans):
        platforms.append(platform_slab('platform:gate_causeway' if k == 0 else f'platform:gate_causeway_{k + 1}', p,
                                       q, z0, z1, 1024, CLOUD_SIDE, MARBLE, 128,
                                       "The causeway up to Castle Xeen's gate: cloud-stone flags on a cloud tongue."
                                       if k == 0 else None, bottom=CLOUD_SIDE))
    for l in D.LINKS:
        if l['style'] == 'gate':
            continue
        za, zb = floor_of(l['a']), floor_of(l['b'])
        lid = key(l['id'])
        if l['style'] == 'neck':
            a, b, d, u = link_cut(l, 640)
            for k, (p, q, z0, z1) in enumerate(level_spans(l, a, b, u, l['width'], za + 8, zb + 8)):
                platforms.append(platform_slab(f'platform:{lid}' if k == 0 else f'platform:{lid}_{k + 1}', p, q,
                                               z0, z1, l['width'], CLOUD_SIDE, CLOUD_TOP, 192,
                                               f"{l['id']}: a waist of cloud, {int(d)} rim to rim" if k == 0 else None))
        elif l['style'] == 'road':
            a, b, d, u = link_cut(l, 320)
            for k, (p, q, z0, z1) in enumerate(level_spans(l, a, b, u, l['width'], za + 8, zb + 8)):
                platforms.append(platform_slab(f'platform:{lid}' if k == 0 else f'platform:{lid}_{k + 1}', p, q,
                                               z0, z1, l['width'], CLOUD_SIDE, MARBLE, 128,
                                               f"{l['id']}: the Xeen road, cloud-stone flags on a cloud tongue, "
                                               f"{int(d)} rim to rim" if k == 0 else None, bottom=CLOUD_SIDE))
        elif l['style'] == 'causeway':
            a, b, d, u = link_cut(l, 320)
            for k, (p, q, z0, z1) in enumerate(level_spans(l, a, b, u, l['width'], za + 8, zb + 8)):
                platforms.append(platform_slab(f'platform:{lid}' if k == 0 else f'platform:{lid}_{k + 1}', p, q,
                                               z0, z1, l['width'], MARBLE, MARBLE, 96,
                                               f"{l['id']}: the aviary's cloud-stone stair, {int(d)} rim to rim, "
                                               f"rising {zb - za}" if k == 0 else None))
        elif l['style'] == 'unseen':
            a, b, d, _ = link_cut(l, 160)
            platforms.append(platform_slab(
                f'platform:{lid}', a, b, za + 8, zb + 8, l['width'], SKY, WISP, 32,
                f"{l['id']}: 'Xeen--9N.' The unseen way, {int(d)} rim to rim (nine cells), {l['width']} wide: its top "
                "the faint wisp texture, its sides and underside sky faces (not drawn) (D-50 change 1)."))
        elif l['style'] == 'bridge':
            a, b, d, (ux, uy) = link_cut(l, 160)
            za8, zb8 = za + 8, zb + 8
            width = l['width']
            spans = level_spans(l, a, b, (ux, uy), width, za8, zb8, partial=False)
            pa, pb = spans[0][1], spans[-1][0]
            sag = min(160, int(d / 25))
            m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            zm = (za8 + zb8) / 2 - sag
            spans = ([spans[0]] if len(spans) == 3 else []) + [(pa if len(spans) == 3 else a, m, za8, zm),
                                                                (m, pb if len(spans) == 3 else b, zm, zb8)] + \
                ([spans[-1]] if len(spans) == 3 else [])
            for k, (p, q, z0, z1) in enumerate(spans):
                platforms.append(platform_slab(f'platform:{lid}_{k + 1}', p, q, int(z0), int(z1), width, ROPE, DECK,
                                               24, f"{l['id']}: rope bridge, {int(d)} rim to rim" if k == 0 else None))
                nx, ny = -uy * (width / 2 - 8), ux * (width / 2 - 8)
                for side in (1, -1):
                    beams.append({
                        'path': [[int(round(p[0] + side * nx)), int(round(p[1] + side * ny))],
                                 [int(round(q[0] + side * nx)), int(round(q[1] + side * ny))]],
                        'width': 8, 'depth': 8,
                        'bottom': int(z0 + 80), 'bottom_end': int(z1 + 80),
                        'surface': ROPE,
                    })
    return platforms, beams


def link_lengths():
    return {l['id']: int(round(link_cut(l, 0)[2])) for l in D.LINKS if l['style'] != 'gate'}


# ------------------------------------------------------------------------------------------------ places

PLACE = {p['id']: p for p in D.PLACES}


def at(pid):
    x, y = G.place_at(PLACE[pid], POLYS)
    return (int(round(x)), int(round(y)))


def space_floor(pid):
    return floor_of(PLACE[pid]['space'])


ARRIVAL = at('entrance:xd12_roof')          # (0, -17920)
RETURN = at('entrance:xd19_gate')           # (0, 11264)
DRAGON = SPACE['room:dragon_clouds']
FD04_ARRIVAL = (DRAGON['at'][0] - 512, DRAGON['at'][1] - 1024)   # (20352, 17280), D-57 Q36: facing north


def stair_steps():
    """Eight marble steps hanging down from the stair head's south rim into the cloud sea (XD-12's cloud stair)."""
    out = []
    x = ARRIVAL[0]
    rim = G.ray_exit(POLYS['room:stair_head'], (x, SPACE['room:stair_head']['at'][1]), (x, -40000))
    fl = floor_of('room:stair_head')
    for k in range(8):
        top = fl - 32 * (k + 1)
        y = rim[1] - 192 * k - 32
        out.append(block(f'platform:stair_step{k + 1}', (x, y), (512, 192), top - 32, 32, MARBLE, MARBLE))
    return out


def lips():
    out = []
    for pid, side in (('landmark:lip_south', 's'), ('landmark:lip_north', 'n')):
        x, y = at(pid)
        fl = space_floor(pid)
        out.append(block(f"platform:{key(pid)}", (x, y), (1024, 256), fl, 24, MARBLE, MARBLE,
                         notes=f"{PLACE[pid]['text']}"))
    return out


def plinth(pid, xy, fl, size=160):
    return block(pid, xy, (size, size), fl, 48, MARBLE, MARBLE)


def signs():
    """Four signposts: a post and a plank board, the board clicked (A3's x9.sign_* hooks)."""
    out = []
    for pid in ('poi:danger_sign', 'poi:nine_north', 'poi:xeendom_sign', 'poi:aviary_sign'):
        x, y = at(pid)
        fl = space_floor(pid)
        out.append(block(f'platform:{key(pid)}_post', (x, y), (24, 24), fl, 256, ROPE, ROPE))
        out.append(block(f'platform:{key(pid)}', (x, y + 20), (224, 16), fl + 192, 112, DECK, DECK,
                         notes=PLACE[pid]['text']))
    return out


def statues():
    out = []
    for pid in ('poi:statue_1', 'poi:statue_2', 'poi:statue_3', 'poi:statue_4'):
        out.append(plinth(f'platform:{key(pid)}_plinth', at(pid), space_floor(pid)))
    for k in range(1, 7):
        pid = f'poi:offering_{k}'
        out.append(plinth(f'platform:{key(pid)}_plinth', at(pid), space_floor(pid), 192))
    return out


def nests():
    out = []
    for pid in ('poi:nest_sw', 'poi:nest_se', 'poi:nest_a1', 'poi:nest_a2', 'poi:nest_a3'):
        x, y = at(pid)
        out.append({'id': f'platform:{key(pid)}', 'outline': ring(x, y, 320, 10, 0.2),
                    'base': space_floor(pid) - SINK - FLOOR,
                    'rise': 40 + SINK, 'surface': STRAW, 'top_surface': STRAW,
                    'notes': f"A roc nest of whole branches and straw: 'Roc Nest. Destroy?' ({PLACE[pid]['text']})."})
    return out


def aviary_spurs():
    """Broken rock spurs round the aviary (X8's eyrie ring), with gaps where the stair and the bridge come in."""
    out = []
    s = SPACE['room:aviary']
    cx, cy = s['at']
    fl = s['floor']
    ways = []
    for l in D.LINKS:
        if 'room:aviary' in (l['a'], l['b']):
            p, q = link_ends(l)
            e = q if l['b'] == 'room:aviary' else p
            ways.append(math.atan2(e[1] - cy, e[0] - cx))
    k = 0
    for i in range(14):
        a = 2 * math.pi * i / 14 + 0.21
        if min(abs(math.remainder(a - w, 2 * math.pi)) for w in ways) < math.radians(24):
            continue
        rx, ry = 0.40 * s['extent'][0], 0.38 * s['extent'][1]
        k += 1
        h = 640 + 224 * (i % 4)
        out.append(block(f'platform:aviary_spur_{k}', (cx + rx * math.cos(a), cy + ry * math.sin(a)), (448, 320), fl - 64,
                         h + 64,
                         ROCK, ROCK, top_size=[96, 64], notes='A broken rock spur round the rookery.'))
    return out


def dragon_rock():
    """The Dragon Clouds' dragon-head rock as studio masses (D-50 change 7; Q-F1's door and Eye in the skull's south
    face, D-57): skull, snout, jaw, horns."""
    s = DRAGON
    cx, cy = G.place_at(PLACE['landmark:dragon_rock'], POLYS)
    fl = s['floor']
    return [
        block('platform:dragon_skull', (cx, cy), (1280, 1024), fl - 64, 960, ROCK, ROCK, top_size=[1024, 768],
              notes="The dragon-head rock: the skull (Q-F1's landmark; the way down and the Eye in its south face)."),
        block('platform:dragon_snout', (cx - 1024, cy - 64), (896, 640), fl + 256, 384, ROCK, ROCK,
              top_size=[768, 512], notes='Its snout, raised toward the south-west.'),
        block('platform:dragon_jaw', (cx - 896, cy - 64), (768, 576), fl - 32, 224, ROCK, ROCK, notes='Its jaw.'),
        block('platform:dragon_horn_1', (cx + 256, cy + 320), (256, 256), fl + 896, 640, ROCK, ROCK,
              top_size=[32, 32], notes='A horn.'),
        block('platform:dragon_horn_2', (cx + 256, cy - 448), (256, 256), fl + 896, 640, ROCK, ROCK,
              top_size=[32, 32], notes='A horn.'),
    ]


# The Dragon Clouds' Q-F1 court (D-57 Q36): the arrival from FD-04's roof south of the snout, the way down in the
# skull's south face, the Eye on a ledge beside it, four Ancient Books on lecterns round the head, the three crystal
# balls west of the snout, the Well of Fantastic Skill and three Dragon Power Crystals. No monsters (Q37).
FD04_DOOR = (21632, 18048)                   # the skull's south face (y 18048); the leaf 256 x 512 against it
EYE_AT = (21056, 17984)                      # a rock ledge out of the same face, its top 128 over the cloud
QF1_BOOKS = [('in', (19600, 17300)), ('fi', (19712, 19200)), ('ni', (21300, 19700)), ('ty', (22450, 18300))]
QF1_BALLS = [('mind', (19350, 17900)), ('past', (19300, 18350)), ('future', (19400, 18800))]
QF1_WELL = (21800, 17250)
QF1_CRYSTALS = [(1, (20600, 19600), 'crys5'), (2, (21950, 19400), 'crys6'), (3, (22350, 18950), 'crclstr')]
DOOR_LEAF = {'texture': 'cvdor1', 'size': [128, 256], 'fit': True}   # MM6's stone cave door in its own frame, once
# (not 7solid01: that texture is pure black, a void, and read as a hole in the rock; tour s17)
BOOK = {'texture': 'xnpbook', 'size': [160, 160], 'fit': True}         # D6's open book on a lectern (reuse line)
WATER = {'texture': 'wtrtyl', 'size': [128, 128], 'liquid': 'water'}


def dragon_court():
    fl = DRAGON['floor']
    dx, dy = FD04_DOOR
    out = [
        block('platform:fd04_door', (dx, dy - 4), (256, 8), fl, 512, DOOR_LEAF, ROCK, end_surface=dict(ROCK, fit=False),
              notes="The way down into the Dragon Tower (FD-04's entrance:x9_clouds; 'Descend into Dragon Tower?')."),
        block('platform:fd04_step', (dx, dy - 136), (384, 256), fl, 16, MARBLE, MARBLE,
              notes='The worn step before the door.'),
        block('platform:dragon_eye_ledge', EYE_AT, (256, 128), fl + 96, 32, ROCK, ROCK,
              notes="The Eye of the Dragon's ledge: the crystal on it is the Eye (A3's q-f1.eye)."),
    ]
    for tag, (x, y) in QF1_BOOKS:
        out.append(block(f'platform:book_{tag}', (x, y), (160, 160), fl, 112, ROCK, BOOK,
                         notes=f'An Ancient Book of the Dragon on a rock lectern ({tag.upper()}).'))
    for tag, xy in QF1_BALLS:
        out.append(block(f'platform:ball_{tag}_plinth', xy, (160, 160), fl, 112, MARBLE, MARBLE,
                         notes=f'The plinth of the {tag.capitalize()} of the Dragon (a crystal ball).'))
    wx, wy = QF1_WELL
    o, t = 448, 64
    for nm, at_, sz in (('s', (wx, wy - (o - t) / 2), (o, t)), ('n', (wx, wy + (o - t) / 2), (o, t)),
                        ('w', (wx - (o - t) / 2, wy), (t, o - 2 * t)), ('e', (wx + (o - t) / 2, wy), (t, o - 2 * t))):
        out.append(block(f'platform:well_curb_{nm}', at_, sz, fl, 112, MARBLE, MARBLE, notes='The well\'s curb.'))
    out.append(block('platform:well_water', (wx, wy), (o - 2 * t, o - 2 * t), fl, 64, MARBLE, WATER,
                     notes='The Well of Fantastic Skill: the water inside the curb.'))
    return out


# ------------------------------------------------------------------------------------------------ the carnival

def frame(origin, phi, u, v):
    """A point u along a booth's front and v out toward its customers, for a booth at `origin` facing out at phi."""
    ox, oy = origin
    cu, su = math.cos(phi - math.pi / 2), math.sin(phi - math.pi / 2)    # along the front
    cv, sv = math.cos(phi), math.sin(phi)                                # toward the customers
    return (ox + u * cu + v * cv, oy + u * su + v * sv)


def booth(name, origin, out_deg, fl, title):
    """A booth under a striped awning, facing out at `out_deg`: a counter skirted in tent canvas (clicked), a canvas back
    wall, two posts and a sloping canvas awning with a scalloped hem. Local frame: u along the front, v outward."""
    phi = math.radians(out_deg)
    along = out_deg - 90                       # the facing of blocks whose size[0] runs along the front
    P = []
    P.append(block(f'platform:{name}', frame(origin, phi, 0, 0), (1024, 256), fl, 112, CANVAS, DECK, facing=along,
                   notes=f"{title}: the counter, skirted in MM6's striped tent canvas (clicked)."))
    P.append(block(f'platform:{name}_back', frame(origin, phi, 0, -320), (1024, 16), fl, 432, CANVAS, DECK,
                   facing=along, end_surface=dict(DECK, fit=False), notes='The canvas back wall.'))
    for u in (-480, 480):
        P.append(block(f'platform:{name}_post{1 if u < 0 else 2}', frame(origin, phi, u, 148), (24, 24), fl, 432,
                       ROPE, ROPE, facing=along))
    # the awning: a flat canvas roof over the counter, from the back wall out to the posts (fl + 432 .. 448)
    P.append(block(f'platform:{name}_awning', frame(origin, phi, 0, -76), (1024, 496), fl + 432, 16, AWNING, AWNING,
                   facing=along, bottom_surface=AWNING, end_surface=dict(AWNING, fit=False), sink=0,
                   notes='The striped awning.'))
    P.append(block(f'platform:{name}_hem', frame(origin, phi, 0, 176), (1008, 8), fl + 352, 96, VALANCE, VALANCE,
                   facing=along, notes="The awning's scalloped hem."))
    return P


BOOTH_FACING = {}


def carnival():
    out = []
    s = SPACE['room:carnival']
    cx, cy = s['at']
    fl = s['floor']
    # the paved plaza: the cloud's outline drawn in to 82 % (cloud-stone flags, 16 high)
    pav = [[int(round(cx + 0.82 * (x - cx))), int(round(cy + 0.82 * (y - cy)))] for x, y in OUTLINES['room:carnival']]
    out.append({'id': 'platform:plaza', 'outline': pav, 'base': fl - SINK - FLOOR, 'rise': 16 + SINK, 'surface': MARBLE,
                'top_surface': MARBLE, 'notes': "Slick's plaza: cloud-stone flags laid on the cloud (6,144 x 4,608, D-50)."})
    pf = fl + 16
    names = {'poi:might_game': ('booth_might', 'The Might booth'),
             'poi:speed_game': ('booth_speed', 'The Speed booth'),
             'poi:endurance_game': ('booth_endurance', 'The Endurance booth'),
             'poi:accuracy_game': ('booth_accuracy', 'The Accuracy booth')}
    for pid, (name, title) in names.items():
        x, y = at(pid)
        if pid == 'poi:accuracy_game':
            deg = 180.0                          # the shooting line looks west down the lane to the bullseye
        else:
            deg = math.degrees(math.atan2(cy - y, cx - x))   # the others face the plaza's middle
            deg = round(deg / 15) * 15
        BOOTH_FACING[pid] = deg
        # the booth stands 384 behind its point, so its customers stand on the point
        back = frame((x, y), math.radians(deg), 0, -384)
        out += booth(name, back, deg, pf, title)
    # the Might booth's high-striker: a pole, a bronze bell at its top, the striking pad at its foot
    x, y = at('poi:might_game')
    phi = math.radians(BOOTH_FACING['poi:might_game'])
    px, py = frame((x, y), phi, 704, -192)
    out.append(block('platform:striker_pad', (px, py), (160, 160), pf, 24, DECK, DECK, notes='The striking pad.'))
    out.append(block('platform:striker_pole', (px, py), (32, 32), pf + 24, 1024, ROPE, ROPE,
                     notes="The high-striker's pole, standing on its pad."))
    out.append(block('platform:striker_bell', (px, py), (40, 40), pf + 24 + 1024, 48, BRONZE, BRONZE,
                     notes='The bell on the pole\'s top (DING).'))
    # the Speed booth's gremlin track: a plank strip with start and finish posts, beside the booth
    x, y = at('poi:speed_game')
    phi = math.radians(BOOTH_FACING['poi:speed_game'])
    a = frame((x, y), phi, -704, 128)
    b = frame((x, y), phi, -704, 128 + 1536)
    out.append(block('platform:track', ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (1536, 256), pf, 8, DECK, DECK,
                     facing=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])),
                     notes="The gremlin's race track, 1,536 long."))
    for k, p in enumerate((a, b)):
        for side in (-1, 1):
            q = frame(p, phi, side * 160, 0)
            out.append(block(f'platform:track_post_{k + 1}{"ab"[side > 0]}', q, (24, 24), pf, 256, ROPE, ROPE))
    # the Endurance booth's treadmill
    x, y = at('poi:endurance_game')
    phi = math.radians(BOOTH_FACING['poi:endurance_game'])
    tx, ty = frame((x, y), phi, 768, -128)
    out.append(block('platform:treadmill', (tx, ty), (512, 288), pf, 48, DECK, DECK,
                     facing=BOOTH_FACING['poi:endurance_game'] - 90, notes='The treadmill.'))
    for side in (-1, 1):
        q = frame((tx, ty), phi, side * 224, 0)
        out.append(block(f'platform:treadmill_post_{"ab"[side > 0]}', q, (24, 24), pf + 48, 192, ROPE, ROPE))
    # the shooting line: the bullseye 1,536 west of the line on the plaza's west rim
    x, y = at('poi:accuracy_game')
    bx, by = at('landmark:bullseye')
    out.append(block('platform:shooting_line', (x - 64, y), (32, 768), pf, 8, DECK, DECK, notes='The shooting line.'))
    bz = pf if inside(pav, (bx, by)) else fl          # the target stands on the cloud past the flags
    out.append(block('platform:bullseye_bale', (bx, by), (96, 288), bz, 96, STRAW, STRAW,
                     notes='A straw bale under the target.'))
    # A5 s30: the top strip (16 x 256) in deck, not the target (audit textures.feature_repeated)
    out.append(block('platform:bullseye', (bx, by), (16, 256), bz + 96, 256, TARGET, dict(DECK, fit=False),
                     end_surface=dict(DECK, fit=False),
                     notes="The straw bullseye (xctarget), its face toward the line, 1,536 east."))
    return out


def prize_stand():
    """Slick's prize stand on the gate causeway's west side, facing east toward the causeway: an open counter skirted
    in tent canvas (clicked, A3's m34.prize_stand) and the doll shelf on two posts behind it, Slick standing between
    them under the open sky (no awning: the game stands a placed monster on the highest top over his spot)."""
    x, y = at('poi:prize_stand')
    fl = floor_of('room:gate_court')
    origin = (x - 128, y)
    phi = 0.0
    P = [block('platform:prize_stand', origin, (1024, 256), fl, 112, CANVAS, DECK, facing=-90,
               notes="Slick's prize stand: the counter, skirted in MM6's striped tent canvas (clicked).")]
    k = 0
    for u in (-456, 456):
        for v in (-412, -388):              # four legs, two at each end, round the shelf's middle
            k += 1
            P.append(block(f'platform:doll_shelf_post{k}', frame(origin, phi, u, v), (16, 16), fl, 192, ROPE, ROPE))
    P.append(block('platform:doll_shelf', frame(origin, phi, 0, -400), (960, 48), fl + 192, 16, DECK, DECK,
                   facing=-90, notes='The doll shelf on its two posts behind Slick.'))
    return P


# ------------------------------------------------------------------------------------------------ Castle Xeen

def castle():
    """The shell over XD-19's footprint: walls (one block with the gate's recess) under a frieze course, four round
    corner towers and the keep, each closed on top; the gate's lintel and its two leaves. Every part is hidden on
    m35.done (wiring evt:castle_gone)."""
    x0, y0, x1, y1 = SHELL
    r = H['tower_radius']
    inset = 160                                    # the curtain stands 160 behind the towers' fronts and sides
    wx0, wy0, wx1, wy1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    gx, gy = GATE
    half = 384                                     # the recess: 768 wide, back to the gate's wall
    top = BASE + H['walls']                        # 4352
    band = 256
    sunk = 64                                      # every part stands 64 into its cloud
    walls_outline = [[wx0, wy0], [gx - half, wy0], [gx - half, gy], [gx + half, gy], [gx + half, wy0], [wx1, wy0],
                     [wx1, wy1], [wx0, wy1]]
    P = []
    P.append({'id': 'platform:castle_walls', 'outline': [[int(a), int(b)] for a, b in walls_outline],
              'base': BASE - sunk - FLOOR, 'rise': top - band - BASE + sunk, 'surface': STONE, 'top_surface': STONE,
              'notes': ("Castle Xeen's curtain walls and roof over XD-19's footprint, black stone (MM8 d35 gnecwal1); "
                        f"the gate's recess {2 * half} wide in the south wall, its back the gate wall at y {gy}.")})
    P.append({'id': 'platform:castle_frieze', 'outline': [[wx0, wy0], [wx1, wy0], [wx1, wy1], [wx0, wy1]],
              'base': top - band - FLOOR, 'rise': band, 'surface': FRIEZE, 'top_surface': STONE,
              'notes': 'The gold frieze course along the walls\' top (gnecwalt, one band), the roof closed.'})
    gate_h = H['gate_leaves'][1] + 128
    P.append({'id': 'platform:castle_lintel', 'outline': [[gx - half, wy0], [gx + half, wy0], [gx + half, gy],
                                                           [gx - half, gy]],
              'base': BASE + gate_h - FLOOR, 'rise': top - band - BASE - gate_h, 'surface': STONE,
              'top_surface': STONE, 'bottom_surface': STONE, 'notes': "The wall over the gate's recess."})
    towers = [(x0 + r, y0 + r), (x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r)]
    names = ['sw', 'se', 'ne', 'nw']
    ttop = BASE + H['towers']
    for (tx, ty), nm in zip(towers, names):
        P.append({'id': f'platform:castle_tower_{nm}', 'outline': ring(tx, ty, r, 16, math.pi / 16),
                  'base': BASE - 2 * sunk - FLOOR, 'rise': ttop - band - BASE + 2 * sunk, 'surface': STONE,
                  'top_surface': STONE, 'notes': f'The {nm} corner tower.'})
        P.append({'id': f'platform:castle_tower_{nm}_frieze', 'outline': ring(tx, ty, r, 16, math.pi / 16),
                  'base': ttop - band - FLOOR, 'rise': band, 'surface': FRIEZE, 'top_surface': STONE})
    kw, kd = H['keep_size']
    kx, ky = CX, CY + 1536
    ktop = BASE + H['keep']
    P.append(block('platform:castle_keep', (kx, ky), (kw, kd), top - band - 512, ktop - band - (top - band - 512),
                   STONE, STONE,
                   notes='The keep, over the throne.'))
    P.append(block('platform:castle_keep_frieze', (kx, ky), (kw, kd), ktop - band, band, FRIEZE, STONE, sink=0))
    # the gate: two leaves against the gate wall, each its own wing (D-50; the double-door rule)
    lw, lh = H['gate_leaves']
    for nm, surf, sx in (('l', LEAF_L, -1), ('r', LEAF_R, 1)):
        P.append(block(f'platform:gate_leaf_{nm}', (gx + sx * lw / 2, gy - 4), (lw, 8), BASE, lh, surf, STONE,
                       end_surface=dict(STONE, fit=False),
                       notes=f"Castle Xeen's gate, the {'left' if sx < 0 else 'right'} leaf ({surf['texture']})."))
    P.append(block('platform:gate_threshold', (gx, gy - 160), (2 * half - 32, 304), BASE, 16, MARBLE, MARBLE,
                   notes="The gate's threshold in the recess (after m35.done the castle-gone line, A3's x9.castle_gone)."))
    return P


SHELL_PARTS = None


def shell_ids():
    return [p['id'] for p in castle() if p['id'] not in ('platform:gate_threshold',)]


# ------------------------------------------------------------------------------------------------ the room

def room_outline():
    hx, hy = D.HALF
    return [[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]


def build_rooms():
    platforms = clouds()
    lp, beams = links()
    platforms += lp
    platforms += stair_steps() + lips() + signs() + statues() + nests() + aviary_spurs() + dragon_rock()
    platforms += dragon_court()
    platforms += carnival() + prize_stand() + castle()
    room = {
        'id': 'room:air',
        'space': 'void:cloud_sea',
        'name': 'Clouds of Xeen',
        'outline': room_outline(),
        'floor': FLOOR,
        'ceiling': CEIL,
        'platforms': platforms,
        'beams': beams,
        'notes': ('The open air over Lake Darzog: one room from the safety floor at -6000 to the sky at 6400, every '
                  'wall, floor and ceiling face a sky face. The clouds, bridges, the unseen way, the carnival and '
                  'Castle Xeen\'s shell hang in it.'),
    }
    return {
        'format': 0,
        'themes': [{'id': 'theme:air', 'wall': SKY, 'floor': SKY, 'ceiling': SKY}],
        'defaults': {'theme': 'theme:air', 'ambient': 30},
        'rooms': [room],
    }


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    rooms = build_rooms()
    for level in ('L3', 'L4'):
        write_yaml(BRIEF / level / 'rooms.yml', rooms)
    import gen_objects
    write_yaml(BRIEF / 'L3' / 'objects.yml', {'format': 1, 'start': gen_objects.objects()['start']})
    print('platforms', len(rooms['rooms'][0]['platforms']), 'beams', len(rooms['rooms'][0]['beams']))
    for lid, d in link_lengths().items():
        print(f'{lid:28s} {d:6d}')
    print('shell', SHELL, 'gate', GATE, 'return', RETURN)
