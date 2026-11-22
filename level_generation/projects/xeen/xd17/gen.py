#!/usr/bin/env python3
"""XD-17 Shangri-La: writes L2-L4 (A5, 2026-11-21) from places_l2.py (the layout) and geo.py (the valley's shape).

    gen.py            L2 (plan, project), L3 (+ rooms, objects' start, atmosphere), L4 (+ objects, wiring)

The project has no hand edits: this script is its source (then `oymap fmt`, `validate`, `build`; v.sh and b.sh).
The route is X8's (an open-air BLV, profile region) with the valley's ground drawn as terrain (atmosphere `ground`).
"""
import copy
import math
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo as G  # noqa: E402
import places_l2 as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
BRIEF = ROOT / 'devdocs/xeen/briefs/xd17'
WORLD = ROOT / 'assets_dev/worlds/xeen'

# Textures (all shipped; no new ones): the valley floor's three ground layers and the rest.
GRASS, ROAD, ROCK = '7grastyl', 'crdflr3', 'gcav1flr'
CLIFF_WALL, PAVE, MARBLE, WATER = 'gcav2wal', 'gtempflr', '7tws1f', 'orwtrmarb'
# A1's NPC-on-a-placed-monster word (monsters[].npc): in the studio's schema, not in the 00:57 build-xeen oymap
# ("unknown key"). Set True once the binary takes it, then v.sh and b.sh.
NPC_WORD = True
SKY = {'texture': CLIFF_WALL, 'size': [256, 512], 'sky': True, 'uneven': True}


# One size per texture in a map (the build keeps one): each texture's own size (its x4 picture / 4), the cliffs twice.
SZ = {'7hhr1bs2': [256, 512], 'chb1': [128, 256], 'ch1b1': [128, 256], '7tws1f': [128, 128], 'hhm2b2': [256, 512],
      'hhm3b': [256, 512], 'hhm1b1': [256, 512], 'hhp1b': [256, 512], 'hhm2b1': [256, 512], '7hhr1b': [256, 512],
      'gstrrf': [128, 128], '7hhr1rf': [128, 128], 'hhm1rf': [128, 128], '6grastyl': [128, 128],
      'ygtemprf': [128, 128], 'hhm2rf': [128, 128], 'xtslate': [128, 128], 'hhm3rf': [128, 128], 'hhp2rf': [128, 128],
      'gtemprf': [128, 128], '7hhr1d': [128, 256], 'hhm3d': [128, 256], 'hhm2d': [128, 256], 'hhm1d': [128, 256],
      'hhp1d': [128, 256], '7sgtvrn': [64, 64], 'sgweapon': [64, 64], '7sgarm': [64, 64], 'sgtempl': [64, 64],
      'sglight': [64, 64], 'gcrysc2': [16, 32], '7grastyl': [128, 128], 'crdflr3': [128, 128], 'gtempflr': [128, 128],
      'gcav1flr': [256, 256], 'gcav2wal': [256, 512], 'orwtrmarb': [256, 256], 'gcstroof': [128, 128],
      'xdpyrdor': [128, 256], 't5d1': [128, 256], '7solid01': [16, 16], 'gcav1wal': [256, 256], '7hhr1p': [128, 128]}


def surf(tex, size, **kw):
    s = {'texture': tex, 'size': list(SZ.get(tex, size))}
    s.update(kw)
    return s


def fall_model_bound():
    """The fall's decoration exists once S binds `xeen_waterfall` in the world (D-50 Q7, fallback (b) until then)."""
    for f in (WORLD / 'models').glob('*.yml'):
        if L.FALL_MODEL in f.read_text():
            return True
    return False


# ---------------------------------------------------------------- the valley room
def valley_room():
    outline = G.outline()
    pts, lines, regions = {}, [], []

    def add(x, y, z):
        pts[(int(x), int(y))] = int(round(z))

    # outline corners: their heights from the model; along the bluffs' sides a point every 512 (the wall's feet
    # follow the floor between its points)
    for (x, y) in outline:
        add(x, y, G.height(x, y))
    notch_pts = set(L.BLUFF_S + L.BLUFF_S_SIDES + L.WEDGE_FRONT + L.WEDGE_N + L.WEDGE_S)
    for a, b in zip(outline, outline[1:] + outline[:1]):
        if a in notch_pts or b in notch_pts:
            dx, dy = b[0] - a[0], b[1] - a[1]
            g = math.gcd(dx, dy)
            px, py = dx // g, dy // g
            plen = math.hypot(px, py)
            if plen > 256:
                continue
            step = max(1, round(512 / plen))
            for j in range(step, g - step // 2, step):
                q = (a[0] + px * j, a[1] + py * j)
                if G.height(*q) > 0:
                    add(q[0], q[1], G.height(*q))
    # the foot of the cliffs, level 0, as two lines (the bluffs' fronts are walls)
    foot = G.FOOT
    for (x, y) in foot:
        add(x, y, 0)
    fi = [foot.index(L.BLUFF_S[0]), foot.index(L.WEDGE_FRONT[0])]
    # foot from the south bluff's east corner round to the wedge's north corner, and from the wedge's south corner
    # round to the bluff's west corner (counter-clockwise)
    def arc(a, b):
        out, k = [], a
        while True:
            out.append(foot[k])
            if k == b:
                return out
            k = (k + 1) % len(foot)
    lines.append(arc(foot.index(L.BLUFF_S[1]), foot.index(L.WEDGE_FRONT[0])))
    lines.append(arc(foot.index(L.WEDGE_FRONT[1]), foot.index(L.BLUFF_S[0])))
    # the cliff's rings (inside the outline only), each a line broken where a point is left out
    for n, ring in G.rings().items():
        run = []
        for p in ring + ring[:1]:
            if p is not None and G.inside(outline, p[:2]) and G.edge_dist(outline, p[:2]) >= 384:
                add(*p)
                run.append(p[:2])
            else:
                if len(run) > 1:
                    lines.append(run)
                run = []
        if len(run) > 1:
            lines.append(run)
    # the summit: crater, rim, two rings
    sx, sy = G.S
    add(sx, sy, G.SUMMIT_RINGS[0][1])
    rim = []
    for r, z in G.SUMMIT_RINGS[1:]:
        n = 8 if r < 1000 else 10
        ring = []
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (r > 1000)) / n
            jr = 0 if r < 1000 else 96 * G.H(r, k)
            p = (round(sx + (r + jr) * math.cos(a)), round(sy + (r + jr) * math.sin(a)))
            if G.inside(outline, p):
                add(p[0], p[1], z + (0 if r < 1000 else 120 * G.H(r, k, 3)))
                ring.append(p)
        if r < 1000:
            rim = ring
        elif len(ring) > 1:
            lines.append(ring + ring[:1] if len(ring) == n else ring)
    lines.append(rim + rim[:1])
    floor_points = [[x, y, z] for (x, y), z in sorted(pts.items())]
    print('valley floor points', len(floor_points), 'lines', len(lines), 'outline', len(outline), file=sys.stderr)
    floor_lines = [[list(p) for p in ln] for ln in lines]
    floor_surfaces = [{'steeper_than': 0.5, 'surface': surf(ROCK, (256, 256))},
                      {'at': [sx, sy], 'surface': surf(ROCK, (256, 256))}]
    # the ceiling (sky): just over the crest round the rim, high over the summit and its sightlines
    ceil = {}

    cz = ceiling_at
    outline_set = set(outline)
    foot_set = set(G.FOOT)
    # every floor point carries a ceiling point: near the bluffs just over the rock (their walls end there, a rib along
    # the slope, the cave's lintel and the gorge open to the sky); elsewhere over the crest and the summit's sightlines
    crest_pts = {p[:2] for p in G.rings()[len(G.PROFILE) - 1] if p}
    for (x, y), z in pts.items():
        if math.dist((x, y), G.S) < 1400:
            continue
        nb = near_bluff_ceiling(x, y, z)
        near = bluff_dist(x, y) < 700
        if (x, y) in crest_pts or (x, y) in outline_set or near or (nb is not None and z == 0):
            ceil[(x, y)] = nb or cz(x, y)
    for (fa, fb), nrm in (((L.BLUFF_S[0], L.BLUFF_S[1]), (0, 1)), ((L.WEDGE_FRONT[0], L.WEDGE_FRONT[1]), (11, -9))):
        mx, my = (fa[0] + fb[0]) / 2, (fa[1] + fb[1]) / 2
        n = math.hypot(*nrm)
        for d in (900, 1800):
            q = (round(mx + nrm[0] / n * d), round(my + nrm[1] / n * d))
            ceil[q] = near_bluff_ceiling(q[0], q[1], 0) or cz(*q)
    for gx in range(-6144, 7000, 4096):
        for gy in range(-4096, 5000, 4096):
            if G.inside(outline, (gx, gy)) and all(math.dist((gx, gy), q) > 1200 for q in pts):
                ceil[(gx, gy)] = cz(gx, gy)
    ceil[(sx, sy)] = 5900
    for (x, y), z in pts.items():
        if math.dist((x, y), G.S) < 1400:
            ceil[(x, y)] = max(ceil.get((x, y), 0), z + 240)
    ceiling_points = [[x, y, z] for (x, y), z in sorted(ceil.items())]
    ceiling_lines = [[list(p) for p in ln] for ln in lines[2:] if all(tuple(q) in ceil for q in ln)]
    # the bluffs' walls (outline edges): basalt, the crystal on the south bluff's front
    walls = []
    n = len(outline)
    s_front = outline.index(L.BLUFF_S[0])
    w_front = outline.index(L.WEDGE_FRONT[0])
    for start, count in ((s_front - 2, 5), (w_front - 3, 7)):
        for k in range(start, start + count):
            k %= n
            walls.append({'wall': k, 'surface': surf(ROCK, (256, 256), uneven=True)})
    for w in walls:
        if w['wall'] == s_front:
            w['panels'] = [{'id': 'panel:crystal', 'offset': L.CRYSTAL_X - L.BLUFF_S[0][0] - 16, 'length': 32,
                            'bottom': 136, 'height': 64, 'surface': surf('gcrysc2', (16, 32), fit=True),
                            'notes': "The hidden crystal (D-50 Q5), at eye height east of the cave mouth: A3's "
                                     "xd17.crystal."}]
    room = {
        'id': 'room:valley', 'name': 'The valley', 'outline': [list(p) for p in outline], 'floor': 0,
        'floor_points': floor_points, 'floor_lines': floor_lines, 'floor_surfaces': floor_surfaces,
        'steep_floor': True, 'ceiling': 6000, 'ceiling_points': ceiling_points, 'ceiling_lines': ceiling_lines, 'walls': walls,
        'levels': levels(),
        'flights': flights(),
        'platforms': platforms(),
        'ambient': 20,
        'notes': ("The hidden valley, open to the sky: the town floor level at 0, three terraces (the library 256, "
                  "the temple 384, the pyramid 256) with stone banks and ramps, lanes on the compass axes, the black "
                  "cliffs to a jagged crest (2,300 south to 3,300 north-east), Firestone's summit over the north-east "
                  "rim (5,632). The south bluff holds the cave throat, the north-west bluff the back passage."),
    }
    return room


BLUFF_EDGES = None


def near_bluff_ceiling(x, y, z):
    """The ceiling at a point near a bluff's walls: the cave's lintel at the south front, the rock's height plus 192
    along the sides (None away from them)."""
    global BLUFF_EDGES
    if BLUFF_EDGES is None:
        BLUFF_EDGES = [L.BLUFF_S_SIDES[0], L.BLUFF_S[0], L.BLUFF_S[1], L.BLUFF_S_SIDES[1]], \
            [L.WEDGE_N[1], L.WEDGE_N[0], L.WEDGE_FRONT[0], L.WEDGE_FRONT[1], L.WEDGE_S[0], L.WEDGE_S[1]]
    for path, front in zip(BLUFF_EDGES, (L.BLUFF_LINTEL, L.WEDGE_LIP)):
        d = min(G.edge_dist(path[i:i + 2], (x, y)) for i in range(len(path) - 1))
        if d < 2400:
            low = max(front, z + 192)
            t = max(0.0, (d - 300) / 2100)
            t = t * t * (3 - 2 * t)
            return int(round(low + (max(low, ceiling_at(x, y)) - low) * t))
    return None


def bluff_dist(x, y):
    near_bluff_ceiling(0, 0, 0)
    return min(min(G.edge_dist(path[i:i + 2], (x, y)) for i in range(len(path) - 1)) for path in BLUFF_EDGES)


def ceiling_at(x, y):
    th = math.atan2(y, x)
    c = 1.06 * G.crest_of(th) + 96
    c = max(c, 5800 - 0.3 * math.dist((x, y), G.S))
    c = max(c, G.height(x, y) + 160)
    return int(round(c))


# ---------------------------------------------------------------- terraces, the pool, steps, paving
def levels():
    out = []
    for tid, t in L.TERRACES.items():
        x0, y0, x1, y1 = t['top']
        out.append({'id': 'level:' + tid.split(':')[1], 'outline': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                    'floor': t['h'], 'bank': t['bank'], 'surface': surf(MARBLE, (256, 256)),
                    'edge': surf(MARBLE, (256, 256), uneven=True),
                    'notes': f"The {tid.split(':')[1]} terrace at {t['h']}, its stone bank {t['bank']} wide."})
    out.append({'id': 'level:pool', 'outline': [list(p) for p in G.water_outline()], 'floor': L.POOL['level'],
                'surface': surf(WATER, (128, 128), liquid='water'), 'edge': surf(ROCK, (256, 256)),
                'notes': 'The cold pool at the east cliff and its stream to the sinkhole at the south-east foot.'})
    return out


def flights():
    out = []
    for tid, t in L.TERRACES.items():
        x0, y0, x1, y1 = t['top']
        c, w, n = t['at'], t['width'], t['length']
        if t['side'] == 'e':
            f, to = [x1 + n, c], [x1, c]
        else:
            f, to = [c, y0 - n], [c, y0]
        out.append({'key': tid.split(':')[1] + '_steps', 'from': f, 'to': to, 'width': w,
                    'riser': surf(MARBLE, (256, 64)), 'tread': surf(MARBLE, (256, 256)),
                    'notes': f"The broad steps up to the {tid.split(':')[1]} terrace."})
    return out


def paving():
    """The lanes (gravel, the ground's road) and the first square (flagstones) as slabs 4 high, cut into disjoint
    rectangles on a 64 grid."""
    step = 64
    gx0, gy0 = -6400, -5312
    lab = {}
    for label, rects in ((1, [r for v in L.LANES.values() for r in v]), (2, L.SQUARE)):
        for (x0, y0, x1, y1) in rects:
            for i in range((x0 - gx0) // step, (x1 - gx0) // step):
                for j in range((y0 - gy0) // step, (y1 - gy0) // step):
                    lab[(i, j)] = label
    out, used = [], set()
    for (i, j) in sorted(lab, key=lambda c: (c[1], c[0])):
        if (i, j) in used:
            continue
        lb = lab[(i, j)]
        w = 1
        while (i + w, j) in lab and lab[(i + w, j)] == lb and (i + w, j) not in used:
            w += 1
        h = 1
        while all((i + k, j + h) in lab and lab[(i + k, j + h)] == lb and (i + k, j + h) not in used for k in range(w)):
            h += 1
        for k in range(w):
            for m in range(h):
                used.add((i + k, j + m))
        x0, y0 = gx0 + i * step, gy0 + j * step
        out.append({'key': f'pave_{len(out)}', 'at': [x0 + w * step // 2, y0 + h * step // 2], 'size': [w * step, h * step],
                    'rise': 4, 'surface': surf(ROAD if lb == 1 else PAVE, (256, 256)),
                    'notes': 'Lane gravel.' if lb == 1 else 'The first square\'s flagstones.'})
    return out


# ---------------------------------------------------------------- buildings, doors, devices (platforms)
def floor_at(x, y):
    for t in L.TERRACES.values():
        x0, y0, x1, y1 = t['top']
        if x0 <= x <= x1 and y0 <= y <= y1:
            return t['h']
    return 0


def octagon(c, r):
    return [[round(c[0] + r * math.cos(math.radians(22.5 + 45 * k))), round(c[1] + r * math.sin(math.radians(22.5 + 45 * k)))]
            for k in range(8)]


def building(b):
    st = L.STYLE[b['id']]
    key = b['id'].split(':')[1]
    cx, cy = b['at']
    sx, sy = b['size']
    W = st['wall']
    wall = surf(st['walls'], (W // 2, W))
    out = []
    if st['kind'] in ('gable', 'dome'):
        x0, y0, x1, y1 = cx - sx // 2, cy - sy // 2, cx + sx // 2, cy + sy // 2
        if st['kind'] == 'gable':
            R = st['roof']
            if sx >= sy:
                ol = [[x0, cy], [x0, y0], [x1, y0], [x1, cy], [x1, y1], [x0, y1]]
            else:
                ol = [[cx, y0], [x1, y0], [x1, y1], [cx, y1], [x0, y1], [x0, y0]]
            # the walls one bay tall, then the roof as its own block: its gable ends stucco (half-timber) or the
            # wall's stone, never the bay picture tiled up the gable
            gable = surf('7hhr1p', (128, 128)) if st['walls'].startswith(('hh', '7hhr')) else wall
            out.append({'id': 'platform:' + key, 'at': [cx, cy], 'size': [sx, sy], 'rise': W, 'surface': wall,
                        'end_surface': dict(wall, fit=False), 'top_surface': surf(st['roof_tex'], (256, 256)),
                        'notes': f"{b['name']}: {b['look']}."})
            out.append({'key': key + '_roof', 'outline': ol, 'base': W, 'rise': 16,
                        'top_heights': [R + 16, 16, 16, R + 16, 16, 16], 'surface': gable,
                        'top_surface': surf(st['roof_tex'], (256, 256)), 'notes': f"{b['name']}'s roof."})
        else:
            out.append({'id': 'platform:' + key, 'at': [cx, cy], 'size': [sx, sy], 'rise': W, 'surface': wall,
                        'end_surface': dict(wall, fit=False), 'top_surface': surf(st['roof_tex'], (256, 256)),
                        'notes': f"{b['name']}: {b['look']}."})
            for k, (a, top, rise) in enumerate(((sx - 128, sx - 320, 128), (sx - 320, 64, 160))):
                out.append({'key': f'{key}_dome{k}', 'at': [cx, cy], 'size': [a, a], 'base': W + (0 if k == 0 else 128),
                            'rise': rise, 'top_size': [top, top], 'surface': surf(st['roof_tex'], (256, 256)),
                            'notes': f"{b['name']}'s low dome."})
    else:
        r = sx // 2 / math.cos(math.radians(22.5))
        out.append({'id': 'platform:' + key, 'outline': octagon((cx, cy), round(r)), 'rise': W, 'surface': wall,
                    'top_surface': surf(st['roof_tex'], (256, 256)), 'notes': f"{b['name']}: {b['look']}."})
        if st['kind'] == 'tower':
            tiers = ((640, 512, 160), (512, 320, 160), (320, 32, 128))
        else:
            tiers = ((448, 48, 288),)
        base = W
        for k, (a, top, rise) in enumerate(tiers):
            out.append({'key': f'{key}_roof{k}', 'at': [cx, cy], 'size': [a, a], 'base': base, 'rise': rise,
                        'top_size': [top, top], 'surface': surf(st['roof_tex'], (256, 256)),
                        'notes': f"{b['name']}'s roof, tier {k + 1}."})
            base += rise
    # doors and signs
    for (aid, house, sid, pt, face) in b['doors']:
        dx, dy = pt
        nx, ny = {'e': (1, 0), 'w': (-1, 0), 'n': (0, 1), 's': (0, -1)}[face]
        size = [16, 128] if nx else [128, 16]
        out.append({'id': aid, 'at': [dx + nx * 8, dy + ny * 8], 'size': size, 'rise': 256,
                    'surface': surf(st['door'], (192, 320), fit=True),
                    'end_surface': surf(st['walls'], (128, 256), fit=False),
                    'notes': f"{b['name']}'s door (house {house}): clicked, evt.EnterHouse({house})."})
        sign = st.get('sign')
        if isinstance(sign, dict):
            sign = sign.get(aid)
        if sign:
            ss = [8, 96] if nx else [96, 8]
            out.append({'key': f'sign_{aid.split(":")[1]}', 'at': [dx + nx * 4, dy + ny * 4], 'size': ss, 'base': 288,
                        'rise': 96, 'surface': surf(sign, (64, 64), fit=True), 'end_surface': surf('gstrrf', (128, 128), fit=False),
                        'notes': f"The sign over {b['name']}'s door."})
    if st.get('colonnade'):
        pass
    if st.get('colonnade'):
        # four columns and their lintel before the library's east face, clear of the door's line
        fx = cx + sx // 2 + 192
        for k, oy in enumerate((-576, -320, 320, 576)):
            out.append({'key': f'column{k}', 'at': [fx, cy + oy], 'size': [64, 64], 'rise': 448,
                        'surface': surf(MARBLE, (64, 256)), 'notes': "A column of the library's colonnade."})
        out.append({'key': 'lintel', 'at': [fx, cy], 'size': [96, 1280], 'base': 448, 'rise': 48,
                    'surface': surf(MARBLE, (128, 48)), 'notes': "The colonnade's lintel on its four columns."})
    return on_terrace(out, floor_at(cx, cy))


def on_terrace(out, h):
    """Platforms are measured from the room's floor, not a raised level: lift them by the terrace's height."""
    if h:
        for p in out:
            p['base'] = p.get('base', 0) + h
    return out


def platforms():
    out = paving()
    for b in L.BUILDINGS:
        out += building(b)
    # the well (0, 0): a fieldstone basin with water at its brim
    out.append({'id': 'platform:well', 'outline': octagon(L.WELL, 176), 'rise': 112,
                'surface': surf('chb1', (128, 128)), 'top_surface': surf(WATER, (128, 128), liquid='water'),
                'notes': "The well in the court (the source's (7, 8)): A3's xd17.well."})
    # the travel pyramid on its terrace, the portal on its south face
    px, py = L.PYRAMID['at']
    pyr = []
    pyr.append({'key': 'pyramid', 'at': [px, py], 'size': [896, 896], 'rise': 704, 'top_size': [16, 16],
                'surface': surf('gcstroof', (256, 256)), 'notes': 'The small stone travel pyramid.'})
    pyr.append({'id': 'platform:pyramid_portal', 'at': [px, py - 448 - 8], 'size': [160, 16], 'rise': 320,
                'surface': surf('xdpyrdor', (128, 256), fit=True), 'end_surface': surf('gcstroof', (16, 320), fit=False),
                'notes': "The pyramid's portal: A3's xd17.pyramid (Xeen.travelPyramid(\"shangrila\") after m30.done)."})
    out += on_terrace(pyr, L.PYRAMID['floor'])
    # the anvil against the forge's west wall between its two doors (D-50 change 7)
    out.append({'key': 'anvil', 'at': [-128 - 40, -3072], 'size': [80, 128], 'rise': 96,
                'surface': surf('t5d1', (128, 96)), 'notes': "Arm and Hammer's anvil, against the wall between the doors."})
    return out


def throat_room():
    x0, y0, x1, y1 = L.THROAT
    return {'id': 'room:throat', 'name': 'The cave throat', 'outline': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
            'space': 'room:cave_mouth', 'floor': 0, 'ceiling': L.THROAT_CEILING, 'theme': 'theme:rock', 'ambient': 24,
            'notes': "The end of XD-16's cool passage: a low black throat 768 deep in the south bluff; its back is the "
                     "way out to XD-16 (the exit preset)."}


def passage_room():
    poly = L.PASSAGE
    # its ceiling at the mouth is the valley's there (the wedge's lip), so the opening has no lintel; deeper in, the
    # rock's height beside it plus 192 (a gorge open to the sky), the rockfall's end 1,536
    c_e = L.WEDGE_LIP
    cp = []
    for k, (x, y) in enumerate(poly):
        if k in (0, 1):
            z = c_e
        elif k in (3, 4):
            z = L.PASSAGE_END_CEILING
        else:
            z = max(c_e, round(G.height(x, y) + 192))
        cp.append([x, y, z])
    return {'id': 'room:passage', 'name': 'The back passage', 'space': 'room:back_passage',
            'outline': [list(p) for p in poly], 'floor': 0,
            'ceiling': c_e, 'ceiling_points': cp, 'theme': 'theme:slot', 'ambient': 28,
            'notes': "D-50 Q8: a slot open to the sky, 384 wide and about 2,060 long, its walls from the valley's crest "
                     "down to 1,536 at the rockfall; the rockfall at its west end is the way out to X7's cleft."}


def rooms():
    themes = [
        {'id': 'theme:valley', 'wall': SKY, 'floor': surf(GRASS, (256, 256)),
         'ceiling': {'texture': CLIFF_WALL, 'size': [256, 512], 'sky': True}},
        {'id': 'theme:rock', 'wall': surf(CLIFF_WALL, (256, 512)), 'floor': surf(ROCK, (256, 256)),
         'ceiling': surf(CLIFF_WALL, (256, 512))},
        {'id': 'theme:slot', 'wall': surf(ROCK, (256, 256), uneven=True), 'floor': surf(ROCK, (256, 256)),
         'ceiling': {'texture': CLIFF_WALL, 'size': [256, 512], 'sky': True}},
    ]
    return {
        'format': 0,
        'themes': themes,
        'defaults': {'theme': 'theme:valley', 'ambient': 20},
        'rooms': [valley_room(), throat_room(), passage_room()],
        'openings': [
            {'id': 'open:mouth', 'from': 'room:valley', 'to': 'room:throat', 'width': 352, 'height': 352,
             'shape': 'arch', 'apex': 416, 'reveal': surf(CLIFF_WALL, (256, 512)),
             'from_wall': G.outline().index(L.BLUFF_S[0]), 'to_wall': 'north',
             'notes': 'The cave mouth at the foot of the south bluff.'},
            {'id': 'open:cleft', 'from': 'room:valley', 'to': 'room:passage', 'width': 336, 'height': 'full',
             'reveal': surf(CLIFF_WALL, (256, 512)),
             'from_wall': G.outline().index(L.WEDGE_FRONT[0]), 'to_wall': 0,
             'notes': "The back passage's mouth in the north-west bluff, open to the sky."},
        ],
        'notes': "XD-17 Shangri-La, L3/L4 geometry: written by output/studio_cal/xd17/tools/gen.py (geo.py, "
                 "places_l2.py); never hand-edited.",
    }


# ---------------------------------------------------------------- objects
def objects():
    ax, ay = L.XD16_ARRIVAL
    px, py, pz = L.PYRAMID_ARRIVAL
    o = {
        'format': 1,
        'start': {'room': 'room:valley', 'at': [ax, ay], 'facing': 'n',
                  'notes': "entrance:xd16_way: out of the cave mouth, facing north into the valley (the map's start)."},
        'arrivals': [
            {'entrance': 'entrance:xd16_way', 'room': 'room:valley', 'at': [ax, ay], 'facing': 'n',
             'notes': "From XD-16's cool passage (A7's exit preset to this name)."},
            {'entrance': 'entrance:x7_cleft', 'room': 'room:passage', 'at': list(L.X7CLEFT_ARRIVAL), 'facing': 'e',
             'notes': "From X7's cleft once it is open (X7's door:xd17): 384 inside the stones, facing east down the "
                      "passage."},
            {'entrance': 'entrance:d6_pyramid', 'room': 'room:valley', 'at': [px, py], 'facing': 's',
             'notes': "From D6's pyramid outside Castle Alamar's gate (Xeen.PyramidArrivals.shangrila, (0, 3200, 256) "
                      "facing south)."},
        ],
        'exits': [
            {'id': 'exit:throat', 'room': 'room:throat', 'wall': 'south', 'size': [352, 352],
             'surface': surf('7solid01', (16, 16), uneven=True), 'to': 'exit:xd16_way',
             'notes': "The throat's dark back: on to XD-16's cool passage."},
            {'id': 'exit:cleft', 'room': 'room:passage', 'wall': 'west', 'size': [352, 352],
             'surface': {'texture': '7solid01', 'size': [256, 256]}, 'to': 'exit:x7_cleft',
             'notes': "The inside of the rockfall: on to X7's cleft."},
        ],
        'monsters': [
            {'id': 'monster:lacey', 'room': 'room:valley', 'monster': L.LACEY_MONSTER, 'at': list(L.LACEY),
             'facing': 45, 'hostile': False, 'group': 1,
             'notes': "Lacey the unicorn (MM8's Unicorn A, NPC 4719), peaceful, not counted (D-50 Q2). She wanders as "
                      "her row (Short): the studio has no indoor home radius, so not within D-50's 512 (open). Her "
                      "talk (NPC 4719) waits on A1's npc word in the studio binary (NPC_WORD)."},
            {'id': 'monster:stumpy', 'room': 'room:valley', 'monster': L.STUMPY_MONSTER, 'at': list(L.STUMPY),
             'facing': 180, 'hostile': False, 'group': 1, 'immobile': True,
             'notes': "Stumpy the tree (MM7's treant, NPC 4718), rooted in the orchard (stand), peaceful, not counted "
                      "(D-50 Q2, D-36 (5)). His talk (NPC 4718) waits on A1's npc word in the studio binary (NPC_WORD)."},
        ],
        'decorations': decorations(),
        'sounds': sounds(),
        'notes': "XD-17 Shangri-La, L4 objects: written by output/studio_cal/xd17/tools/gen.py.",
    }
    if NPC_WORD:
        o['monsters'][0]['npc'] = L.LACEY_NPC
        o['monsters'][1]['npc'] = L.STUMPY_NPC
    return o


def lane_dist(p):
    best = 1e9
    for rects in list(L.LANES.values()) + [L.SQUARE]:
        for (x0, y0, x1, y1) in rects:
            dx = max(x0 - p[0], 0, p[0] - x1)
            dy = max(y0 - p[1], 0, p[1] - y1)
            best = min(best, math.hypot(dx, dy))
    return best


def decorations():
    out = []
    trees = ['6tree03', '6tree07', '6tree17', '6tree19', '6tree25', '6tree27', '7tree01', '7tree16']
    k = 0
    for (x, y) in L.ORCHARD_TREES:
        jx, jy = round(96 * G.H(x, y, 1)), round(96 * G.H(x, y, 2))
        p = (x + jx, y + jy)
        if lane_dist(p) < 320 or math.dist(p, L.STUMPY) < 448:
            continue
        out.append({'id': f'deco:orchard_{k}', 'room': 'room:valley', 'decoration': trees[k % len(trees)],
                    'at': list(p), 'notes': 'A fruit tree of the orchard.'})
        k += 1
    # a few trees along the cliff foot and by the houses, clear of lanes and doors
    extra = [(-4352, -3456), (-5248, -2304), (-3072, 2304), (-4224, 2560), (2944, 4352), (3712, 4352),
             (-512, -4480), (512, -4544), (1536, -3968), (-2944, 3968), (5632, 3584)]
    for n, p in enumerate(extra):
        if lane_dist(p) < 320:
            continue
        out.append({'id': f'deco:tree_{n}', 'room': 'room:valley', 'decoration': trees[(n + 3) % len(trees)],
                    'at': list(p), 'notes': 'A tree on the valley floor.'})
    # barrels in pairs against walls: the tavern's south wall, the forge's east wall
    for n, (p, q) in enumerate((((-2752, -3528), (-2680, -3528)), ((808, -3584), (808, -3512)))):
        for m, at in enumerate((p, q)):
            out.append({'id': f'deco:barrel_{n}_{m}', 'room': 'room:valley', 'decoration': 'smlbarel', 'at': list(at),
                        'notes': 'A barrel against the wall (a pair).'})
    # urns either side of Murray's door, against his front wall
    mx, my = L.BUILDINGS[[b['id'] for b in L.BUILDINGS].index('building:murray')]['doors'][0][3]
    for m, ox in enumerate((-384, 384)):
        out.append({'id': f'deco:flowers_{m}', 'room': 'room:valley', 'decoration': '6flower07',
                    'at': [mx + ox, my - 40], 'notes': "Flowers against Murray's front wall, clear of his door."})
    # boulders fallen at the cliff foot, away from the lanes
    for n, p in enumerate(((-6016, -1024), (4864, -4096), (5888, 1024), (-3328, 4480), (2688, -4736))):
        out.append({'id': f'deco:boulder_{n}', 'room': 'room:valley', 'decoration': f'6rock0{n + 1}', 'at': list(p),
                    'notes': 'A boulder fallen from the cliff.'})
    if fall_model_bound():
        out.append({'id': 'deco:falls', 'room': 'room:valley', 'decoration': L.FALL_MODEL, 'at': list(L.FALL_AT),
                    'facing': L.FALL_FACING, 'notes': "S's white fall down the east cliff into the pool (D-50 Q7)."})
    return out


def sounds():
    """AU's list (level_generation/sounds/xeen_20261120/review/beds/xd17.yml), points moved with their things; the
    fall's sound only with the fall's decoration (D-50 Q7)."""
    src = yaml.safe_load(open(ROOT / 'level_generation/projects/xeen/common/beds/xd17.yml'))['sounds']
    moved = {'sound:falls': list(L.FALL_AT), 'sound:stream_north': [5472, -768], 'sound:stream_south': [5440, -2816]}
    out = []
    for s in src:
        if s['id'] == 'sound:falls' and not fall_model_bound():
            continue
        s = dict(s)
        if s['id'] in moved:
            s['at'] = moved[s['id']]
        out.append(s)
    return out


# ---------------------------------------------------------------- wiring
def wiring():
    ev = [
        {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
         'effects': [{'lua': 'XeenQuests.hook("xd17.arrival")'}],
         'notes': "A3's first-arrival line (xd17.arrival), once."},
        {'id': 'evt:well', 'preset': 'script', 'source': 'platform:well', 'title': 'Well',
         'effects': [{'lua': 'XeenQuests.hook("xd17.well")'}],
         'notes': "D-50 Q1: A3's xd17.well (20,000 experience once per character, the award Found Shangri-La; :27 then "
                  ":4)."},
        {'id': 'evt:crystal', 'preset': 'script', 'source': 'panel:crystal', 'title': 'Crystal',
         'effects': [{'lua': 'XeenQuests.hook("xd17.crystal")'}],
         'notes': "D-50 Q5: A3's xd17.crystal (Benedict's joke)."},
        {'id': 'evt:pyramid', 'preset': 'script', 'source': 'platform:pyramid_portal', 'title': 'Travel Pyramid',
         'effects': [{'lua': 'XeenQuests.hook("xd17.pyramid")'}],
         'notes': "A3's xd17.pyramid: Xeen.travelPyramid(\"shangrila\") after m30.done, else \"The moons are not "
                  "aligned. You are unable to pass.\" (aaze0049:25). D6's far end is not built (D-50 Q9)."},
        {'id': 'evt:throat', 'preset': 'exit', 'source': 'exit:throat', 'title': 'Leave Shangri-La',
         'notes': "D-24: the game's leave window (its meaning: \"Leave Shangri-La?\", aaze0049:32), to XD-16's "
                  "entrance:xd17_way."},
        {'id': 'evt:cleft', 'preset': 'exit', 'source': 'exit:cleft', 'title': 'Leave Shangri-La',
         'effects': [{'lua': 'XeenQuests.hook("xd17.cleft_opened")'}],
         'notes': "D-24 and D-40 (3): the game's leave window to X7's entrance:xd17_cleft; A3's xd17.cleft_opened "
                  "(once: sets cleft_open 116140, a status line) runs first."},
    ]
    for (aid, house, sid, pt, face, b) in L.doors():
        ev.append({'id': 'evt:' + aid.split(':')[1], 'preset': 'script', 'source': aid, 'title': b['name'],
                   'effects': [{'lua': f'evt.EnterHouse({house})'}],
                   'notes': f"A4's house {house}, {b['name']}."})
    return {'format': 0, 'events': ev, 'notes': 'XD-17 Shangri-La, L4 wiring: written by output/studio_cal/xd17/tools/gen.py.'}


# ---------------------------------------------------------------- atmosphere, plan, project
ATMOSPHERE = {
    'format': 0,
    'open_sky': {'mode': 'open', 'preset': 'fair', 'view': 'outdoor', 'view_distance_scale': 1.25},
    'daylight': {'ambient_rgb': [96, 98, 104], 'sun_rgb': [255, 250, 236], 'night_scale_rgb': [134, 143, 168],
                 'sun_gain': 3},
    'ground': {
        'layers': [
            {'material': 'grass', 'textures': [GRASS], 'color': [92, 112, 52]},
            {'material': 'road', 'textures': [ROAD]},
            {'material': 'basalt', 'textures': [ROCK], 'color': [58, 56, 60]},
        ],
        'slope': {'material': 'basalt'},
        # F5 (2026-11-21): the meadow's grass, flowers and tall patches; tools/terrain_materials.py plants writes
        # the file from worlds/xeen/terrain_decorations/plants.yml
        'grass': 'worlds/xeen/terrain_decorations/xeen_xd17_blv.yml',
    },
    'notes': "D-50 Q6: Cloudside's fair preset by name, seen as an outdoor map, no theme, no ash, no weather; view "
             "distance 1.25 so Firestone's summit (about 15,000 from the arrival) is drawn (Q3). The valley floor is "
             "drawn as terrain: grass, the gravel lanes as road, the cliffs as X7's basalt.",
}


def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan_for(level):
    import gen_l1
    gen_l1.P = L
    gen_l1.X7_CLEFT_POINT = '(4096, 8192, 2496) facing west (1024)'
    p = gen_l1.plan(18)
    p['level'] = 'L2' if level == 'L2' else 'L3'
    p['notes'] = ("L2-L4 (A5, 2026-11-21): the approved L1 with D-50 (changes 1-8, Q1-Q9). The layout fitted to the "
                  "studio's build (places_l2.py): terraces as parts of the floor with banks and ramps, buildings moved "
                  "off them by 128-768, lanes on the compass axes, the pool's rim on the flat floor. Written by "
                  "output/studio_cal/xd17/tools/gen.py.")
    for e in p['entrances']:
        if e['id'] == 'entrance:x7_cleft':
            e['how'] = (f"From X7's cleft once cleft_open is set (X7's door:xd17, A3's xd17.cleft): "
                        f"{list(L.X7CLEFT_ARRIVAL)}, 384 inside the stones, facing east down the passage.")
    return p


def project(level):
    p = load('L1', 'project.yml')
    p['map_stats']['bolster'] = 'LowerToEqual'
    p['map_stats']['treasure_level'] = 0   # maps.yml's "-" (D-50: no chests; row 9120 writes 0)
    p['notes'] = (f"Xeen design brief, level {level}: XD-17 Shangri-La, an open-air BLV (devdocs/INDOOR_OPEN_SKY.md; "
                  "X8's studio route, profile region) with its valley floor drawn as terrain (Map Studio S8b). Act V's "
                  "hidden town (Q-C26): five services and ten residences (A4's towns/xd17.yml, houses 4351-4365), no "
                  "monsters; Lacey (11915) and Stumpy (11916) peaceful and not counted (D-50). map_stats 9120 (A2's "
                  "row; the block here is the studio's copy), music 51.")
    for n in p['neighbours']:
        if n['id'] == 'pyramid:alamar':
            n['arrival'] = 'entrance:xd17_pyramid'
            n['notes'] = ("D-50 Q9: D6's working pyramid outside Castle Alamar's gate (A6), arrival entrance:xd17_pyramid "
                          "(-5120, 1024, 1856) facing north. Listed only: the click is A3's xd17.pyramid "
                          "(Xeen.travelPyramid(\"shangrila\"), refused before m30.done); D6's pyramid "
                          "(Xeen.travelPyramid(\"alamar_gate\")) arrives at this map's entrance:d6_pyramid.")
    return p


class Dumper(yaml.SafeDumper):
    pass


def _list(dumper, data):
    flat = all(not isinstance(v, (list, dict)) for v in data)
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=flat)


Dumper.add_representer(list, _list)
Dumper.add_representer(tuple, lambda d, t: _list(d, list(t)))


def write(level, name, data):
    (BRIEF / level).mkdir(parents=True, exist_ok=True)
    (BRIEF / level / name).write_text(yaml.dump(data, Dumper=Dumper, sort_keys=False, width=118, allow_unicode=True))


def main():
    r = rooms()
    for level in ('L2', 'L3', 'L4'):
        write(level, 'plan.yml', plan_for(level))
        write(level, 'project.yml', project(level))
    for level in ('L3', 'L4'):
        write(level, 'rooms.yml', r)
        write(level, 'atmosphere.yml', ATMOSPHERE)
    o = objects()
    write('L3', 'objects.yml', {'format': 1, 'start': o['start'], 'notes': o['notes']})
    write('L4', 'objects.yml', o)
    write('L4', 'wiring.yml', wiring())
    print('written L2-L4')


if __name__ == '__main__':
    main()
