#!/usr/bin/env python3
"""P5's MU-3 drawing, MU-4 blockouts and measured figures, from design.py (A5 sub-agent, 2026-11-21). After X9's
render_x9.py.

    render_p5.py        writes into output/studio_cal/p5/mockups/:
      plan_p5.png               the to-scale plan (40 px a cell), plan_p5_2x.png for crops
      blockout_walk.png         a crude perspective of the walk camera (Codex's composition reference)
      blockout_shrine.png       the same for the shrine camera (after the ceremony: the pavilion shown)
      figures.json              the measured figures for the board, NOTES.md and plan.yml's totals

Nothing here is read by the game or the studio. The pad outlines are the review's own (X9's 24-point clouds); L2
draws the studio's platforms from the plan's `at` and `extent`.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import design as D
import geom as G

OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p5') / 'mockups'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONTI = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'
COMPASS = {'n': (0, 1), 'e': (1, 0), 's': (0, -1), 'w': (-1, 0), 'ne': (0.7071, 0.7071), 'nw': (-0.7071, 0.7071),
           'se': (0.7071, -0.7071), 'sw': (-0.7071, -0.7071)}
PLACE = {p['id']: p for p in D.PLACES}


def font(size, kind=''):
    return ImageFont.truetype({'b': FONTB, 'i': FONTI}.get(kind, FONT), size)


# ------------------------------------------------------------------------------------------------ the walk
def walk_segments():
    pts = D.WALK
    segs, total = [], 0.0
    for a, b in zip(pts, pts[1:]):
        length = G.length(a, b)
        segs.append((a, b, total, length))
        total += length
    return segs, total


def along(pt):
    """Distance along the walk to the point's nearest spot on it, and how far off the line it is."""
    segs, _ = walk_segments()
    best = None
    for a, b, start, length in segs:
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / (length * length)))
        q = (a[0] + dx * t, a[1] + dy * t)
        off = G.length(pt, q)
        if best is None or off < best[1]:
            best = (start + length * t, off)
    return best


def poly_gap(pa, pb):
    """Smallest distance between two outlines (vertex to edge, both ways)."""
    def seg_dist(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        d2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / d2))
        return G.length(p, (a[0] + dx * t, a[1] + dy * t))
    best = 1e18
    for P, Q in ((pa, pb), (pb, pa)):
        for p in P:
            for i in range(len(Q)):
                best = min(best, seg_dist(p, Q[i], Q[(i + 1) % len(Q)]))
    return best


# ------------------------------------------------------------------------------------------------ figures
def figures(polys):
    f = {}
    walk = G.cloud_mask(polys)
    px = G.RES * G.RES
    f['walk_area_m'] = round(walk.sum() * px / 1e6, 1)
    ys, xs = np.nonzero(walk)
    f['cloud_bbox_cells'] = [round((xs.max() - xs.min()) * G.RES / 512, 1), round((ys.max() - ys.min()) * G.RES / 512, 1)]
    f['room_cells'] = list(D.ROOM)
    f['room_units'] = [D.ROOM[0] * 512, D.ROOM[1] * 512]
    _, total = walk_segments()
    f['walk_length'] = round(total)
    f['walk_seconds'] = {'walking': round(total / 384), 'running': round(total / 768)}
    f['monsters'] = 0
    # links
    f['links'] = {}
    for l in D.LINKS:
        p, q = G.link_ends(l, polys)
        rise = G.SPACE[l['b']]['floor'] - G.SPACE[l['a']]['floor']
        f['links'][l['id']] = {'style': l['style'], 'length': round(G.length(p, q)), 'rise': rise, 'width': l['width']}
    rl = [v['length'] for v in f['links'].values() if v['style'] == 'road']
    f['road_span_range'] = [min(rl), max(rl)]
    f['causeway'] = f['links']['link:causeway']['length']
    # the sky round the shrine: its outline to every pad and road but the causeway and the last Rest Stop
    shrine = polys['room:shrine']
    gaps = []
    for s in D.SPACES:
        if s['id'] in ('room:shrine', 'room:rest_south'):
            continue
        gaps.append((round(poly_gap(shrine, polys[s['id']])), s['id']))
    for l in D.LINKS:
        if l['style'] != 'road':
            continue
        p, q = G.link_ends(l, polys)
        gaps.append((round(poly_gap(shrine, G.capsule(p, q, l['width']))), l['id']))
    f['shrine_sky_gap'] = min(gaps)
    # the shortcut that must not exist: the crown (0) to the last Rest Stop (448)
    f['crown_to_last_stop'] = {'gap': round(poly_gap(polys['room:crown'], polys['room:rest_south'])),
                               'rise': G.SPACE['room:rest_south']['floor'] - G.SPACE['room:crown']['floor']}
    # stations along the walk
    f['stations'] = {}
    for p in D.PLACES:
        if p['kind'] in ('note', 'board', 'rest', 'observatory', 'shrine', 'exit'):
            d, off = along(p['at'])
            f['stations'][p['id']] = {'along': round(d), 'off_line': round(off), 'text': p['text'][:40]}
    # POI census (D-20: bound events chained within 400; figures, landmarks and the arrival out)
    pois = [(p['id'], p['at']) for p in D.PLACES if p['id'].startswith(('poi:', 'exit:'))]
    parent = list(range(len(pois)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(pois)):
        for j in range(i + 1, len(pois)):
            if G.length(pois[i][1], pois[j][1]) <= 400:
                parent[root(i)] = root(j)
    f['poi_census'] = len({root(i) for i in range(len(pois))})
    f['poi_census_without_chest'] = f['poi_census'] - 1
    nn = sorted(min(G.length(a[1], b[1]) for b in pois if b is not a) for a in pois)
    f['poi_spacing'] = {'median': round(nn[len(nn) // 2]), 'min': round(nn[0]), 'max': round(nn[-1])}
    kinds = {}
    for p in D.PLACES:
        kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
    f['kinds'] = kinds
    floors = [s['floor'] for s in D.SPACES]
    f['floors'] = [min(floors), max(floors)]
    f['cameras'] = {}
    for key, c in D.CAMERAS.items():
        f['cameras'][key] = {'at': list(c['at']), 'z': c['floor'] + c['eye'], 'yaw_deg': c['yaw_deg'], 'fov': c['fov']}
    f['cameras']['walk']['to_shrine'] = round(G.length(D.CAMERAS['walk']['at'], PLACE['poi:shrine']['at']))
    f['cameras']['shrine']['to_dais'] = round(G.length(D.CAMERAS['shrine']['at'], PLACE['poi:shrine']['at']))
    f['places'] = {p['id']: list(p['at']) for p in D.PLACES}
    return f


# ------------------------------------------------------------------------------------------------ the plan
SCALE = 40.0 / 512  # px per unit at 1x
MARGIN = 60


def board_line(at, face, width=448):
    fx, fy = COMPASS[face]
    rx, ry = fy, -fx
    return ((at[0] - rx * width / 2, at[1] - ry * width / 2), (at[0] + rx * width / 2, at[1] + ry * width / 2))


def plan(polys, f, k=2):
    s = SCALE * k
    W = int(D.ROOM[0] * 512 * s + 2 * MARGIN * k)
    H = int(D.ROOM[1] * 512 * s + 2 * MARGIN * k)

    def P(pt):
        return (MARGIN * k + (pt[0] + D.HALF[0]) * s, MARGIN * k + (D.HALF[1] - pt[1]) * s)

    img = Image.new('RGB', (W, H), (236, 233, 226))
    rng = np.random.default_rng(9)
    noise = rng.uniform(0, 1, (D.ROOM[1] + 2, D.ROOM[0] + 2))
    sea = Image.fromarray((noise * 255).astype(np.uint8)).resize(
        (int(D.ROOM[0] * 512 * s), int(D.ROOM[1] * 512 * s)), Image.BICUBIC)
    a = np.array(sea).astype(float) / 255.0
    base = np.stack([196 + 22 * a, 206 + 18 * a, 222 + 14 * a], -1).astype(np.uint8)
    img.paste(Image.fromarray(base), (MARGIN * k, MARGIN * k))
    dr = ImageDraw.Draw(img, 'RGBA')
    fr = font(11 * k)
    for c in range(0, D.ROOM[0] + 1, 2):
        x = MARGIN * k + c * 512 * s
        dr.line([(x, MARGIN * k), (x, H - MARGIN * k)], fill=(150, 160, 175, 70), width=1)
        dr.text((x - 6 * k, MARGIN * k - 18 * k), str(c), font=fr, fill=(120, 120, 120))
    for c in range(0, D.ROOM[1] + 1, 2):
        y = MARGIN * k + c * 512 * s
        dr.line([(MARGIN * k, y), (W - MARGIN * k, y)], fill=(150, 160, 175, 70), width=1)
        dr.text((MARGIN * k - 28 * k, y - 7 * k), str(c), font=fr, fill=(120, 120, 120))
    dr.rectangle([P((-D.HALF[0], D.HALF[1])), P((D.HALF[0], -D.HALF[1]))], outline=(90, 100, 120), width=2 * k)
    dr.text(P((-D.HALF[0] + 300, D.HALF[1] - 250)), 'North up. Off any cloud edge the party falls to X5,',
            font=font(13 * k, 'b'), fill=(40, 60, 140))
    dr.text(P((-D.HALF[0] + 300, D.HALF[1] - 600)), "on Darkstone's rock before the tower door (question 3).",
            font=font(13 * k, 'b'), fill=(40, 60, 140))
    # shadows, roads, pads
    for sid, poly in polys.items():
        dr.polygon([P((x + 120, y - 160)) for x, y in poly], fill=(120, 130, 150, 90))
    WHITE = (250, 248, 242)
    for l in D.LINKS:
        p, q = G.link_ends(l, polys)
        dr.polygon([P(v) for v in G.capsule(p, q, l['width'])], fill=WHITE if l['style'] == 'road' else (206, 196, 168),
                   outline=(170, 168, 160))
    for _, poly, _ in G.bulges(polys):
        dr.polygon([P(v) for v in poly], fill=WHITE)
    for sid, poly in polys.items():
        fill = WHITE if G.SPACE[sid]['kind'] == 'cloud' else (238, 226, 190)
        dr.polygon([P(v) for v in poly], fill=fill, outline=(170, 168, 160), width=k)
    # the road's dashed centre line of cloud-stone flags along the walk
    segs, total = walk_segments()
    for a, b, start, length in segs[:-1]:
        n = int(length / 384)
        for i in range(0, n, 2):
            u = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            v = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
            dr.line([P(u), P(v)], fill=(196, 186, 160), width=3 * k)
    # walk distance ticks every 4,096
    fs = font(10 * k)
    d = 4096
    while d < total:
        for a, b, start, length in segs:
            if start <= d <= start + length:
                t = (d - start) / length
                pt = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                x, y = P(pt)
                dr.ellipse([x - 4 * k, y - 4 * k, x + 4 * k, y + 4 * k], fill=(90, 90, 110))
                dr.text((x + 6 * k, y + 2 * k), f'{d:,}', font=fs, fill=(70, 70, 90))
                break
        d += 4096
    # the stair house
    sh = D.STAIR_HOUSE
    x, y = P(sh['at'])
    r = sh['radius'] * s
    dr.ellipse([x - r, y - r, x + r, y + r], fill=(36, 34, 40), outline=(150, 150, 160), width=k)
    dr.text((x + r + 4 * k, y + 4 * k), 'stair house (Darkstone crown)', font=fs, fill=(30, 30, 40))
    # the observatory
    ob = PLACE['landmark:observatory']['at']
    x, y = P(ob)
    r = 576 * s
    dr.ellipse([x - r, y - r, x + r, y + r], fill=(196, 190, 176), outline=(150, 110, 60), width=2 * k)
    dr.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], fill=(160, 120, 70))
    # the shrine's dais and hands
    sx, sy = PLACE['poi:shrine']['at']
    dr.rectangle([P((sx - 448, sy + 320)), P((sx + 448, sy - 320))], fill=(214, 190, 120), outline=(150, 120, 50), width=k)
    for hx in (-384, 384):
        x, y = P((sx + hx, sy + 64))
        dr.ellipse([x - 6 * k, y - 6 * k, x + 6 * k, y + 6 * k], fill=(120, 100, 70))
    # the pavilion (hidden until m42.done): a dashed outline
    pv = PLACE['thing:pavilion']['at']
    x0, y0 = P((pv[0] - 768, pv[1] + 512))
    x1, y1 = P((pv[0] + 768, pv[1] - 512))
    for t in np.linspace(0, 1, 24):
        if int(t * 23) % 2 == 0:
            dr.line([(x0 + (x1 - x0) * t, y0), (x0 + (x1 - x0) * min(1, t + 1 / 23), y0)], fill=(200, 150, 40), width=2 * k)
            dr.line([(x0 + (x1 - x0) * t, y1), (x0 + (x1 - x0) * min(1, t + 1 / 23), y1)], fill=(200, 150, 40), width=2 * k)
            dr.line([(x0, y0 + (y1 - y0) * t), (x0, y0 + (y1 - y0) * min(1, t + 1 / 23))], fill=(200, 150, 40), width=2 * k)
            dr.line([(x1, y0 + (y1 - y0) * t), (x1, y0 + (y1 - y0) * min(1, t + 1 / 23))], fill=(200, 150, 40), width=2 * k)
    dr.text((x0, y0 - 16 * k), 'pavilion (after m42.done)', font=fs, fill=(150, 100, 20))
    # camera wedges
    for key, c in D.CAMERAS.items():
        cx, cy = c['at']
        yaw, half = math.radians(c['yaw_deg']), math.radians(c['fov'] / 2)
        reach = 3600
        pts = [(cx, cy)] + [(cx + reach * math.cos(a_), cy + reach * math.sin(a_)) for a_ in (yaw - half, yaw + half)]
        dr.polygon([P(v) for v in pts], fill=(70, 110, 220, 36), outline=(70, 110, 220, 160))
        x, y = P((cx, cy))
        dr.text((x + 6 * k, y + 4 * k), f"MU-4 '{key}'", font=font(10 * k, 'b'), fill=(50, 80, 200))
    # places
    fl = font(10 * k)
    for p in D.PLACES:
        at = p['at']
        x, y = P(at)
        r = 5 * k
        kind = p['kind']
        if kind == 'board':
            a_, b_ = board_line(at, p['face'])
            dr.line([P(a_), P(b_)], fill=(150, 40, 40), width=4 * k)
            fx, fy = COMPASS[p['face']]
            dr.line([P(at), P((at[0] + fx * 220, at[1] + fy * 220))], fill=(150, 40, 40), width=k)
        elif kind == 'rest':
            a_, b_ = board_line(at, p['face'], 640)
            fx, fy = COMPASS[p['face']]
            back = [(a_[0] - fx * 512, a_[1] - fy * 512), (b_[0] - fx * 512, b_[1] - fy * 512)]
            dr.polygon([P(a_), P(b_), P(back[1]), P(back[0])], fill=(150, 105, 60), outline=(90, 60, 30))
        elif kind in ('arrival',):
            dr.rectangle([x - r, y - r, x + r, y + r], fill=(30, 130, 70), outline=(255, 255, 255))
        elif kind == 'exit':
            dr.rectangle([x - r, y - r, x + r, y + r], fill=(20, 20, 20), outline=(255, 255, 255))
        elif kind == 'note':
            dr.rectangle([x - 2 * k, y - r - 3 * k, x + 2 * k, y + r], fill=(120, 80, 40))
            dr.rectangle([x - r, y - r - 3 * k, x + r, y - r + 1 * k], fill=(120, 80, 40))
        elif kind == 'figure':
            dr.ellipse([x - r, y - r, x + r, y + r], fill=(40, 90, 190) if p['id'] != 'npc:pharaoh' else (200, 160, 40),
                       outline=(255, 255, 255))
        elif kind == 'chest':
            dr.polygon([(x, y - r - 1), (x + r + 1, y), (x, y + r + 1), (x - r - 1, y)], fill=(200, 150, 20),
                       outline=(90, 60, 0))
        elif kind == 'observatory':
            dr.rectangle([x - 3 * k, y - 3 * k, x + 3 * k, y + 3 * k], fill=(40, 40, 40))
        elif kind == 'disc':
            dr.ellipse([x - r - k, y - r - k, x + r + k, y + r + k], fill=(205, 205, 215), outline=(90, 90, 110))
    LABELS = {
        'entrance:fd03_roof': ('Arrival (FD-03 roof stair)', (250, 120)),
        'exit:stair_house': ("Way down: 'Descend into Darkstone Tower?'", (-300, -620)),
        'poi:pharaoh_note': ("The Pharaoh's note", (-1900, -380)),
        'poi:rest_1': ('Rest Stop 1', (200, 200)), 'poi:rest_2': ('Rest Stop 2', (-1500, 200)),
        'poi:rest_3': ('Rest Stop 3 (the last)', (300, -420)),
        'poi:observatory': ("'The observatory is closed.'", (420, -120)),
        'poi:shrine': ("The shrine (m42.shrine)", (520, -80)),
        'npc:pharaoh': ('Dragon Pharaoh', (300, -60)),
        'npc:roland': ('Roland', (-900, 120)), 'npc:kalindra': ('Kalindra', (120, 120)),
        'poi:gift_chest': ('gift (Q7)', (-700, -280)), 'landmark:cake': ('cake', (120, -140)),
    }
    for p in D.PLACES:
        x, y = P(p['at'])
        if p['kind'] == 'board':
            fx, fy = COMPASS[p['face']]
            tx, ty = P((p['at'][0] - fx * 520, p['at'][1] - fy * 520))
            text = f"'{p['text']}'"
            w = dr.textlength(text, font=fl)
            dr.rectangle([tx - w / 2 - 3, ty - 7 * k, tx + w / 2 + 3, ty + 7 * k], fill=(255, 255, 255, 200))
            dr.text((tx - w / 2, ty - 6 * k), text, font=fl, fill=(150, 30, 30))
        elif p['id'] in LABELS:
            text, (dx, dy) = LABELS[p['id']]
            x, y = P((p['at'][0] + dx, p['at'][1] + dy))
            dr.text((x, y), text, font=fl, fill=(30, 30, 40))
    fi = font(11 * k, 'i')
    NAME_OFF = {'room:crown': (-1300, -1500), 'room:rest_east': (-2400, 300), 'room:ne_turn': (-1900, 1350),
                'room:observatory': (-1250, 1550), 'room:nw_turn': (-1300, 1350), 'room:rest_west': (700, 300),
                'room:sw_turn': (-1200, -1500), 'room:rest_south': (-1100, -1350), 'room:shrine': (-1300, 1950)}
    for sp in D.SPACES:
        off = NAME_OFF[sp['id']]
        x, y = P((sp['at'][0] + off[0], sp['at'][1] + off[1]))
        dr.text((x, y), f"{sp['name']} (+{sp['floor']})", font=fi, fill=(70, 60, 50))
    for l in D.LINKS:
        p, q = G.link_ends(l, polys)
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        x, y = P(m)
        dr.text((x + 8 * k, y - 14 * k), f"{round(G.length(p, q)):,}", font=fs, fill=(90, 70, 40))
    x0, y0 = P((-D.HALF[0] + 400, -D.HALF[1] + 400))
    dr.rectangle([x0 - 6 * k, y0 - 14 * k, x0 + 2048 * s + 120 * k, y0 + 10 * k], fill=(60, 60, 70, 200))
    dr.line([(x0, y0), (x0 + 2048 * s, y0)], fill=(255, 255, 255), width=3 * k)
    dr.text((x0 + 2048 * s + 8 * k, y0 - 8 * k), '2,048 (4 cells)', font=fs, fill=(255, 255, 255))
    return img


# ------------------------------------------------------------------------------------------------ blockouts
def floor_at(pt, polys, skip_bulges=False):
    """The cloud's floor under a point: a pad's floor, or along a road between its pads' floors (a board's lobe takes
    the road's floor beside it)."""
    if not skip_bulges:
        for bid, poly, _ in G.bulges(polys):
            if G.point_in(pt, poly):
                return floor_at(PLACE[bid]['at'], polys, skip_bulges=True)
    for s in D.SPACES:
        if point_in(pt, polys[s['id']]):
            return s['floor']
    for l in D.LINKS:
        p, q = G.link_ends(l, polys)
        dx, dy = q[0] - p[0], q[1] - p[1]
        L2 = dx * dx + dy * dy
        t = ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / L2
        off = abs((pt[0] - p[0]) * dy - (pt[1] - p[1]) * dx) / math.sqrt(L2)
        if 0 <= t <= 1 and off <= 1200:
            za, zb = G.SPACE[l['a']]['floor'], G.SPACE[l['b']]['floor']
            return za + (zb - za) * t
    return 0


def point_in(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def blockout(polys, key, out, after=False, W=1536, H=1024):
    c = D.CAMERAS[key]
    cx, cy = c['at']
    cz = c['floor'] + c['eye']
    yaw, pitch, fov = math.radians(c['yaw_deg']), math.radians(c['pitch_deg']), math.radians(c['fov'])
    fwd = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
    right = (math.sin(yaw), -math.cos(yaw), 0.0)
    up = (fwd[1] * right[2] - fwd[2] * right[1], fwd[2] * right[0] - fwd[0] * right[2],
          fwd[0] * right[1] - fwd[1] * right[0])
    if up[2] < 0:
        up = tuple(-v for v in up)
    fpx = (W / 2) / math.tan(fov / 2)
    NEAR = 30.0
    campos = (cx, cy, cz)
    faces = []

    def cam_space(p):
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        return (d[0] * right[0] + d[1] * right[1] + d[2] * right[2],
                d[0] * up[0] + d[1] * up[1] + d[2] * up[2],
                d[0] * fwd[0] + d[1] * fwd[1] + d[2] * fwd[2])

    def clip(poly):
        out_ = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            ina, inb = a[2] >= NEAR, b[2] >= NEAR
            if ina:
                out_.append(a)
            if ina != inb:
                t = (NEAR - a[2]) / (b[2] - a[2])
                out_.append(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
        return out_

    def proj(c3):
        return (W / 2 + c3[0] / c3[2] * fpx, H / 2 - c3[1] / c3[2] * fpx)

    def add(poly3, colour, bias=0.0, normal=None):
        if normal is not None:
            p = poly3[0]
            if sum(normal[i] * (campos[i] - p[i]) for i in range(3)) <= 0:
                return
        cs = clip([cam_space(p) for p in poly3])
        if len(cs) < 3:
            return
        depth = sum(c3[2] for c3 in cs) / len(cs) + bias
        faces.append((depth, [proj(c3) for c3 in cs], colour))

    def prism(poly2, z0, z1, top, side, bias=0.0):
        n = len(poly2)
        area = sum(poly2[i][0] * poly2[(i + 1) % n][1] - poly2[(i + 1) % n][0] * poly2[i][1] for i in range(n))
        sgn = 1.0 if area > 0 else -1.0
        for i in range(n):
            a, b = poly2[i], poly2[(i + 1) % n]
            normal = (sgn * (b[1] - a[1]), -sgn * (b[0] - a[0]), 0.0)
            add([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], side, bias, normal)
        add([(x, y, z1) for x, y in poly2], top, bias, (0.0, 0.0, 1.0))

    def ngon(cxy, r, n=10):
        return [(cxy[0] + r * math.cos(2 * math.pi * i / n), cxy[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

    def oriented(at, face, w, d):
        """A rectangle w wide across the facing direction and d deep along it, centred on at."""
        fx, fy = COMPASS[face]
        rx, ry = fy, -fx
        return [(at[0] + rx * w / 2 + fx * d / 2, at[1] + ry * w / 2 + fy * d / 2),
                (at[0] - rx * w / 2 + fx * d / 2, at[1] - ry * w / 2 + fy * d / 2),
                (at[0] - rx * w / 2 - fx * d / 2, at[1] - ry * w / 2 - fy * d / 2),
                (at[0] + rx * w / 2 - fx * d / 2, at[1] + ry * w / 2 - fy * d / 2)]

    def cone(cxy, r, z0, h, colour, n=10):
        tip = (cxy[0], cxy[1], z0 + h)
        ring = ngon(cxy, r, n)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            mid = ((a[0] + b[0]) / 2 - cxy[0], (a[1] + b[1]) / 2 - cxy[1])
            add([(a[0], a[1], z0), (b[0], b[1], z0), tip], colour, 0.0, (mid[0], mid[1], r * r / max(h, 1)))

    CLOUD_TOP, CLOUD_SIDE, CLOUD_UNDER = (246, 244, 238), (200, 205, 216), (176, 184, 200)
    for sid, poly in polys.items():
        s = G.SPACE[sid]
        z = s['floor']
        prism(poly, z - 256, z, CLOUD_TOP if s['kind'] == 'cloud' else (236, 222, 180), CLOUD_SIDE)
        n = len(poly)
        tip = (s['at'][0], s['at'][1], z - 256 - 0.35 * max(s['extent']))
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            a3 = (a[0] * 0.8 + s['at'][0] * 0.2, a[1] * 0.8 + s['at'][1] * 0.2, z - 256)
            b3 = (b[0] * 0.8 + s['at'][0] * 0.2, b[1] * 0.8 + s['at'][1] * 0.2, z - 256)
            mid = ((a3[0] + b3[0]) / 2 - s['at'][0], (a3[1] + b3[1]) / 2 - s['at'][1])
            add([a3, b3, tip], CLOUD_UNDER, 0.0, (mid[0], mid[1], -0.3 * math.hypot(*mid)))
    for l in D.LINKS:
        za, zb = G.SPACE[l['a']]['floor'], G.SPACE[l['b']]['floor']
        p, q = G.link_ends(l, polys)
        cap = G.capsule(p, q, l['width'])
        col = CLOUD_TOP if l['style'] == 'road' else (206, 196, 168)
        add([(cap[0][0], cap[0][1], za + 2), (cap[1][0], cap[1][1], zb + 2), (cap[2][0], cap[2][1], zb + 2),
             (cap[3][0], cap[3][1], za + 2)], col, 30)
    for bid, poly, _ in G.bulges(polys):
        z = floor_at(PLACE[bid]['at'], polys, skip_bulges=True)
        prism(poly, z - 160, z + 1, CLOUD_TOP, CLOUD_SIDE, 20)
    # the dashed flagstone line down the road's middle
    segs, _ = walk_segments()
    for a, b, start, length in segs[1:-1]:
        n = int(length / 384)
        for i in range(0, n, 2):
            u = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            v = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
            zu, zv = floor_at(u, polys) + 6, floor_at(v, polys) + 6
            dx, dy = v[0] - u[0], v[1] - u[1]
            dl = math.hypot(dx, dy)
            nx, ny = -dy / dl * 64, dx / dl * 64
            add([(u[0] + nx, u[1] + ny, zu), (v[0] + nx, v[1] + ny, zv), (v[0] - nx, v[1] - ny, zv),
                 (u[0] - nx, u[1] - ny, zu)], (206, 196, 172), -5)
    BLACK, SLATE, FRIEZE = (46, 44, 52), (60, 64, 74), (120, 116, 110)
    sh = D.STAIR_HOUSE
    z0 = G.SPACE['room:crown']['floor']
    prism(ngon(sh['at'], sh['radius']), z0 - 100, z0 + sh['wall'], BLACK, BLACK)
    prism(ngon(sh['at'], sh['radius']), z0 + sh['wall'], z0 + sh['wall'] + sh['band'], FRIEZE, FRIEZE)
    cone(sh['at'], sh['radius'] + 32, z0 + sh['wall'] + sh['band'], sh['cone'], SLATE)
    # observatory: a round tower and a stepped dome
    ob = PLACE['landmark:observatory']['at']
    zo = G.SPACE['room:observatory']['floor']
    prism(ngon(ob, 576, 14), zo, zo + 896, (206, 198, 182), (196, 188, 172))
    for i, (r, h) in enumerate(((560, 120), (480, 110), (380, 100), (250, 90), (120, 60))):
        prism(ngon(ob, r, 14), zo + 896 + sum(x[1] for x in ((560, 120), (480, 110), (380, 100), (250, 90))[:i]),
              zo + 896 + sum(x[1] for x in ((560, 120), (480, 110), (380, 100), (250, 90), (120, 60))[:i + 1]),
              (176, 120, 70), (160, 110, 64))
    for p in D.PLACES:
        at = p['at']
        z = floor_at(at, polys)
        if p['kind'] == 'board':
            for off in (-160, 160):
                fx, fy = COMPASS[p['face']]
                leg = (at[0] + fy * off, at[1] - fx * off)
                prism(oriented(leg, p['face'], 24, 24), z, z + 224, (110, 80, 50), (110, 80, 50))
            prism(oriented(at, p['face'], 448, 24), z + 224, z + 480, (150, 40, 40), (238, 226, 200))
        elif p['kind'] == 'rest':
            fx, fy = COMPASS[p['face']]
            back = (at[0] - fx * 224, at[1] - fy * 224)
            prism(oriented(back, p['face'], 640, 48), z, z + 320, (150, 105, 60), (150, 105, 60))
            for off in (-300, 300):
                post = (at[0] + fy * off + fx * 200, at[1] - fx * off + fy * 200)
                prism(oriented(post, p['face'], 32, 32), z, z + 320, (130, 90, 50), (130, 90, 50))
            prism(oriented((at[0] - fx * 16, at[1] - fy * 16), p['face'], 760, 560), z + 320, z + 368,
                  (120, 70, 40), (120, 70, 40))
            prism(oriented((at[0] + fx * 240, at[1] + fy * 240), p['face'], 360, 16), z + 368, z + 480,
                  (40, 110, 60), (40, 110, 60))
        elif p['kind'] == 'note':
            prism(oriented(at, p['face'], 24, 24), z, z + 200, (110, 80, 50), (110, 80, 50))
            prism(oriented(at, p['face'], 160, 16), z + 140, z + 240, (230, 220, 190), (230, 220, 190))
        elif p['kind'] == 'shrine':
            prism(oriented(at, 's', 1024, 704), z, z + 64, (226, 204, 140), (200, 176, 110))
            for hx in (-384, 384):
                hand = (at[0] + hx, at[1] + 64)
                prism(oriented(hand, 's', 128, 128), z + 64, z + 448, (200, 190, 170), (180, 170, 150))
                prism(oriented(hand, 's', 224, 192), z + 448, z + 528, (200, 190, 170), (180, 170, 150))
                if after:
                    if hx < 0:
                        prism(oriented(hand, 's', 96, 96), z + 528, z + 624, (90, 160, 230), (60, 120, 200))
                    else:
                        prism(oriented(hand, 's', 32, 32), z + 528, z + 768, (230, 190, 60), (210, 170, 50))
        elif p['kind'] == 'figure' and (after or p['id'] == 'npc:pharaoh'):
            col = (220, 180, 60) if p['id'] == 'npc:pharaoh' else (70, 90, 170) if p['id'] == 'npc:roland' else (120, 60, 140)
            prism(oriented(at, p['face'], 96, 64), z, z + (230 if p['id'] == 'npc:pharaoh' else 180), col, col)
        elif p['kind'] == 'pavilion' and after:
            for ox in (-704, 704):
                for oy in (-448, 448):
                    prism(oriented((at[0] + ox, at[1] + oy), 's', 40, 40), z, z + 512, (230, 200, 120), (230, 200, 120))
            prism(oriented(at, 's', 1600, 1088), z + 512, z + 560, (250, 250, 246), (240, 236, 228))
            cone(at, 700, z + 560, 320, (252, 252, 248), 4)
        elif p['kind'] == 'landmark' and p['id'] == 'landmark:cake' and after:
            prism(oriented(at, 's', 160, 160), z, z + 96, (240, 236, 228), (200, 180, 150))
        elif p['kind'] == 'chest' and after:
            prism(oriented(at, 's', 96, 64), z, z + 64, (160, 110, 40), (140, 90, 30))
        elif p['kind'] == 'disc' and after:
            prism(ngon(at, 192, 12), z, z + 24, (214, 214, 224), (180, 180, 196))
    img = Image.new('RGB', (W, H))
    dr = ImageDraw.Draw(img)
    hz = H / 2 + math.tan(pitch) * fpx
    for y in range(H):
        if y < hz:
            t = y / max(hz, 1)
            col = (int(110 + 90 * t), int(150 + 70 * t), int(215 + 25 * t))
        else:
            t = min(1.0, (y - hz) / (H - hz))
            col = (int(214 + 20 * t), int(220 + 16 * t), int(232 + 10 * t))
        dr.line([(0, y), (W, y)], fill=col)
    for depth, pts, colour in sorted(faces, key=lambda f_: -f_[0]):
        dr.polygon(pts, fill=colour)
    fa = font(18)
    ANN = [("Pharaoh's shrine (hands)", (0, -384, 1400)), ('observatory', (*PLACE['landmark:observatory']['at'], 1500)),
           ('Rest Stop', (*PLACE['poi:rest_1']['at'], 600)), ('NE turn', (RING_XY := (D.RING, D.RING)) + (400,)),
           ('NW turn', (-D.RING, D.RING, 600))]
    if key == 'shrine':
        ANN = [('dais, two raised hands', (0, -384, 1100)), ('Dragon Pharaoh', (0, 192, 800)),
               ('pavilion: Roland, Kalindra', (0, 960, 1250)),
               ('observatory', (*PLACE['landmark:observatory']['at'], 1500))]
    for text, p in ANN:
        c3 = cam_space(p)
        if c3[2] > NEAR:
            x, y = proj(c3)
            if 0 < x < W and 0 < y < H:
                dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(40, 70, 220), width=2)
                dr.text((x + 8, y - 22), text, font=fa, fill=(40, 70, 220))
    img.save(out)


def main():
    polys = G.outlines()
    f = figures(polys)
    (OUT / 'figures.json').write_text(json.dumps(f, indent=1) + '\n')
    big = plan(polys, f, k=2)
    big.save(OUT / 'plan_p5_2x.png')
    big.resize((big.width // 2, big.height // 2), Image.LANCZOS).save(OUT / 'plan_p5.png')
    blockout(polys, 'walk', OUT / 'blockout_walk.png')
    blockout(polys, 'shrine', OUT / 'blockout_shrine.png', after=True)
    print(json.dumps({k: f[k] for k in ('walk_area_m', 'cloud_bbox_cells', 'walk_length', 'walk_seconds',
                                        'road_span_range', 'causeway', 'shrine_sky_gap', 'crown_to_last_stop',
                                        'poi_census', 'poi_spacing', 'floors', 'cameras')}, indent=1))


if __name__ == '__main__':
    main()
