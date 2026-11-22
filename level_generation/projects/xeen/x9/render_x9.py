#!/usr/bin/env python3
"""X9's MU-3 drawing, MU-4 blockout and measured figures, from design.py (A5, 2026-11-20).

    render_x9.py        writes into output/studio_cal/x9/mockups/:
      plan_x9.png             the to-scale plan (14 px a cell), plan_x9_2x.png for crops
      blockout_signature.png  a crude perspective of the signature camera (Codex's composition reference)
      figures.json            the measured figures for the board, NOTES.md and plan.yml's totals

Nothing here is read by the game or the studio. The island outlines are the review's own (16-point clouds, as X8's
platforms); L2 draws the studio's platforms from the plan's `at` and `extent`.
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

OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x9') / 'mockups'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONTI = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'


def font(size, kind=''):
    return ImageFont.truetype({'b': FONTB, 'i': FONTI}.get(kind, FONT), size)


ACTOR_COLOUR = {11561: (40, 150, 150), 11562: (220, 130, 40), 11592: (110, 110, 130)}
KIND_STYLE = {
    'arrival': ((30, 130, 70), 'square'), 'return': ((30, 130, 70), 'square'), 'sign': ((120, 80, 40), 'post'),
    'statue': ((40, 90, 190), 'dot'), 'offering': ((130, 40, 120), 'dot'), 'nest': ((190, 50, 40), 'tri'),
    'booth': ((230, 110, 30), 'booth'), 'stand': ((230, 110, 30), 'booth'), 'gate': ((20, 20, 20), 'square'),
    'chest': ((200, 150, 20), 'diamond'), 'landmark': ((150, 100, 60), 'dot'),
}


# ------------------------------------------------------------------------------------------------ figures
def figures(polys):
    places = {p['id']: G.place_at(p, polys) for p in D.PLACES}
    groups = [(g, G.place_at(g, polys)) for g in D.GROUPS]
    f = {}
    walk = G.cloud_mask(polys, include=('cloud', 'castle'))
    h, w = walk.shape
    img = Image.new('L', (w, h), 0)
    ImageDraw.Draw(img).polygon([G.to_px(p) for p in G.castle_walls(G.SPACE['zone:castle'])], fill=255)
    walls = np.array(img) > 0
    walk &= ~walls
    px = G.RES * G.RES
    f['walk_area_m'] = round(walk.sum() * px / 1e6, 1)
    f['castle_area_m'] = round(walls.sum() * px / 1e6, 1)
    ys, xs = np.nonzero(walk | walls)
    f['cloud_bbox_cells'] = [round((xs.max() - xs.min()) * G.RES / 512, 1), round((ys.max() - ys.min()) * G.RES / 512, 1)]
    f['room_cells'] = list(D.ROOM)
    f['room_units'] = [D.ROOM[0] * 512, D.ROOM[1] * 512]
    # quiet: walkable cloud farther than 2,048 from any group
    yy, xx = np.mgrid[0:h, 0:w]
    near = np.zeros_like(walk)
    for g, at in groups:
        gx, gy = G.to_px(at)
        near |= (xx - gx) ** 2 + (yy - gy) ** 2 <= (2048 / G.RES) ** 2
    f['quiet_share'] = round(float((walk & ~near).sum() / walk.sum()), 3)
    # monsters
    count = {}
    for g, _ in groups:
        count[g['actor']] = count.get(g['actor'], 0) + g['count']
    f['monsters'] = sum(count.values())
    f['by_row'] = {str(k): {'name': D.ROWS[k][0], 'level': D.ROWS[k][1], 'count': v, 'xp': D.ROWS[k][2] * v}
                   for k, v in sorted(count.items())}
    party = sum(D.ROWS[k][2] * v for k, v in count.items())
    f['kill_xp_party'] = party
    f['kill_xp_member'] = round(party / 4)
    f['kill_xp_target'] = 26100
    f['groups'] = len(groups)
    f['group_sizes'] = sorted({g['count'] for g, _ in groups})
    # first fights and quiet radii
    def nearest_group(pt):
        best = min(groups, key=lambda ga: G.length(pt, ga[1]))
        return round(G.length(pt, best[1])), best[0]['id']
    f['first_fight'] = {k: nearest_group(places[k]) for k in ('entrance:xd12_roof', 'entrance:xd19_gate',
                                                               'poi:xeendom_sign', 'poi:prize_stand')}
    # links
    f['links'] = {}
    for l in D.LINKS:
        p, q = G.link_ends(l, polys)
        rise = G.SPACE[l['b']]['floor'] - G.SPACE[l['a']]['floor']
        f['links'][l['id']] = {'style': l['style'], 'length': round(G.length(p, q)), 'rise': rise, 'width': l['width']}
    bl = [v['length'] for v in f['links'].values() if v['style'] == 'bridge']
    f['bridge_range'] = [min(bl), max(bl)]
    f['unseen_way'] = f['links']['link:unseen_way']['length']
    # POI census (D-20: chained within 400; the arrival, the return point and the landmark out)
    pois = [(k, v) for k, v in places.items() if k.startswith('poi:')]
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
    nn = sorted(min(G.length(a[1], b[1]) for b in pois if b is not a) for a in pois)
    f['poi_spacing'] = {'median': round(nn[len(nn) // 2]), 'min': round(nn[0]), 'max': round(nn[-1])}
    kinds = {}
    for p in D.PLACES:
        kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
    f['kinds'] = kinds
    # heights
    floors = [s['floor'] for s in D.SPACES if s['kind'] in ('cloud', 'castle')]
    f['floors'] = [min(floors), max(floors)]
    # the signature
    cam = camera(polys)
    gate = places['poi:castle_gate']
    f['signature'] = {'at': [round(cam['at'][0]), round(cam['at'][1])], 'z': cam['z'],
                      'to_gate': round(G.length(cam['at'], gate)),
                      'castle_width_deg': round(math.degrees(2 * math.atan(G.SPACE['zone:castle']['extent'][0] / 2 / G.length(cam['at'], gate))), 1)}
    # the Dragon Clouds' gap to the nearest island (sealed)
    dc = G.SPACE['room:dragon_clouds']
    best = None
    for s in D.SPACES:
        if s['id'] == dc['id'] or s['kind'] == 'sealed':
            continue
        p = G.ray_exit(polys[dc['id']], dc['at'], s['at'])
        q = G.ray_exit(polys[s['id']], s['at'], dc['at'])
        d = G.length(p, q)
        if best is None or d < best[0]:
            best = (round(d), s['id'])
    f['dragon_clouds_gap'] = best
    f['places'] = {k: [round(v[0]), round(v[1])] for k, v in places.items()}
    f['group_at'] = {g['id']: [round(at[0]), round(at[1])] for g, at in groups}
    return f


def camera(polys):
    c = D.CAMERA
    s = G.SPACE[c['space']]
    at = G.place_at(c, polys)
    return {'at': at, 'z': s['floor'] + c['eye'], 'yaw': math.radians(c['yaw_deg']),
            'pitch': math.radians(c['pitch_deg']), 'fov': math.radians(c['fov'])}


# ------------------------------------------------------------------------------------------------ the plan
SCALE = 14.0 / 512  # px per unit at 1x
MARGIN = 60


def plan(polys, f, k=2):
    s = SCALE * k
    W = int(D.ROOM[0] * 512 * s + 2 * MARGIN * k)
    H = int(D.ROOM[1] * 512 * s + 2 * MARGIN * k)

    def P(pt):
        return (MARGIN * k + (pt[0] + D.HALF[0]) * s, MARGIN * k + (D.HALF[1] - pt[1]) * s)

    img = Image.new('RGB', (W, H), (236, 233, 226))
    # the cloud sea: soft blue-grey noise
    rng = np.random.default_rng(9)
    nw, nh = D.ROOM[0] // 2 + 2, D.ROOM[1] // 2 + 2
    noise = rng.uniform(0, 1, (nh, nw))
    sea = Image.fromarray((noise * 255).astype(np.uint8)).resize(
        (int(D.ROOM[0] * 512 * s), int(D.ROOM[1] * 512 * s)), Image.BICUBIC)
    a = np.array(sea).astype(float) / 255.0
    base = np.stack([196 + 22 * a, 206 + 18 * a, 222 + 14 * a], -1).astype(np.uint8)
    img.paste(Image.fromarray(base), (MARGIN * k, MARGIN * k))
    dr = ImageDraw.Draw(img, 'RGBA')
    # grid every 8 cells, ruler
    fr = font(11 * k)
    for c in range(0, D.ROOM[0] + 1, 8):
        x = MARGIN * k + c * 512 * s
        dr.line([(x, MARGIN * k), (x, H - MARGIN * k)], fill=(150, 160, 175, 90), width=1)
        dr.text((x - 6 * k, MARGIN * k - 18 * k), str(c), font=fr, fill=(120, 120, 120))
    for c in range(0, D.ROOM[1] + 1, 8):
        y = MARGIN * k + c * 512 * s
        dr.line([(MARGIN * k, y), (W - MARGIN * k, y)], fill=(150, 160, 175, 90), width=1)
        dr.text((MARGIN * k - 28 * k, y - 7 * k), str(c), font=fr, fill=(120, 120, 120))
    dr.rectangle([P((-D.HALF[0], D.HALF[1])), P((D.HALF[0], -D.HALF[1]))], outline=(90, 100, 120), width=2 * k)
    # the fall rule
    dr.text(P((-D.HALF[0] + 600, D.HALF[1] - 500)), 'North up. Off any cloud edge the party falls:',
            font=font(13 * k, 'b'), fill=(40, 60, 140))
    dr.text(P((-D.HALF[0] + 600, D.HALF[1] - 1300)), 'it lands on X2, on Darzog\'s island by the tower door.',
            font=font(13 * k, 'b'), fill=(40, 60, 140))
    # monster rings (under the clouds' outlines so they read as areas)
    for g in D.GROUPS:
        at = G.place_at(g, polys)
        r = 1536 * s
        x, y = P(at)
        col = ACTOR_COLOUR[g['actor']]
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col + (38,), outline=col + (140,), width=k)
    # shadows, then clouds
    for sid, poly in polys.items():
        sp = G.SPACE[sid]
        dr.polygon([P((x + 220, y - 300)) for x, y in poly], fill=(120, 130, 150, 90))
    for l in D.LINKS:
        if l['style'] in ('neck', 'road'):
            p, q = G.link_ends(l, polys)
            dr.polygon([P(v) for v in G.capsule(p, q, l['width'] if l['style'] == 'neck' else 1536)],
                       fill=(250, 248, 242))
    for sid, poly in polys.items():
        sp = G.SPACE[sid]
        fill = (250, 248, 242) if sp['kind'] != 'sealed' else (238, 236, 246)
        dr.polygon([P(v) for v in poly], fill=fill, outline=(170, 168, 160), width=k)
        if sp['kind'] == 'sealed':
            # hatching for the sealed Dragon Clouds
            x0, y0 = P((sp['at'][0] - sp['extent'][0] / 2, sp['at'][1] + sp['extent'][1] / 2))
            x1, y1 = P((sp['at'][0] + sp['extent'][0] / 2, sp['at'][1] - sp['extent'][1] / 2))
            for t in range(int(x0) - int(y1 - y0), int(x1), 10 * k):
                dr.line([(t, y1), (t + (y1 - y0), y0)], fill=(150, 130, 200, 110), width=k)
    # causeways (cloud-stone)
    for l in D.LINKS:
        if l['style'] == 'causeway':
            p, q = G.link_ends(l, polys)
            dr.polygon([P(v) for v in G.capsule(p, q, max(l['width'], 768))], fill=(250, 248, 242))
            dr.polygon([P(v) for v in G.capsule(p, q, l['width'])], fill=(196, 188, 170), outline=(150, 140, 120))
    # the Xeen road's flags across the plaza and the court
    road = [(0, G.place_at(next(p for p in D.PLACES if p['id'] == 'poi:xeendom_sign'), polys)[1] + 400), (0, 11264)]
    dr.polygon([P(v) for v in G.capsule(road[0], road[1], 768)], fill=(208, 200, 182), outline=(160, 150, 130))
    # the castle
    cs = G.SPACE['zone:castle']
    walls = G.castle_walls(cs)
    dr.polygon([P(v) for v in walls], fill=(36, 34, 40), outline=(200, 160, 60), width=2 * k)
    for (x, y) in walls:
        r = 640 * s
        cx, cy = P((x, y))
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(46, 44, 52), outline=(200, 160, 60), width=k)
    kx, ky = cs['at']
    dr.rectangle([P((kx - 1536, ky + 1792)), P((kx + 1536, ky - 512))], outline=(200, 160, 60), width=k)
    # the gate leaves
    gx, gy = G.place_at(next(p for p in D.PLACES if p['id'] == 'poi:castle_gate'), polys)
    dr.rectangle([P((gx - 256, gy + 96)), P((gx + 256, gy - 96))], fill=(200, 160, 60))
    dr.text(P((kx - 2900, ky + 600)), 'CASTLE XEEN (XD-19)', font=font(15 * k, 'b'), fill=(230, 200, 120))
    dr.text(P((kx - 2900, ky - 200)), f"closed shell, {cs['extent'][0]:,} x {cs['extent'][1]:,}", font=font(11 * k), fill=(200, 190, 170))
    dr.text(P((kx - 2900, ky - 800)), 'gone on m35.done', font=font(11 * k), fill=(200, 190, 170))
    # bridges: striped
    for l in D.LINKS:
        if l['style'] == 'bridge':
            p, q = G.link_ends(l, polys)
            dr.polygon([P(v) for v in G.capsule(p, q, 300)], fill=(110, 80, 50))
            n = max(2, int(G.length(p, q) / 260))
            for i in range(n):
                t = (i + 0.5) / n
                a = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                dx, dy = q[0] - p[0], q[1] - p[1]
                d = math.hypot(dx, dy)
                nx, ny = -dy / d * 140, dx / d * 140
                dr.line([P((a[0] + nx, a[1] + ny)), P((a[0] - nx, a[1] - ny))], fill=(220, 190, 130), width=k)
    # the unseen way
    l = next(l for l in D.LINKS if l['id'] == 'link:unseen_way')
    p, q = G.link_ends(l, polys)
    n = 9
    for i in range(n):
        a = (p[0], p[1] + (q[1] - p[1]) * i / n)
        b = (p[0], p[1] + (q[1] - p[1]) * (i + 0.62) / n)
        dr.polygon([P(v) for v in G.capsule(a, b, 512)], fill=(255, 255, 255, 150), outline=(120, 140, 200, 200))
    # camera wedge
    cam = camera(polys)
    cx, cy = cam['at']
    half = cam['fov'] / 2
    reach = 7000
    pts = [(cx, cy)]
    for a in (cam['yaw'] - half, cam['yaw'] + half):
        pts.append((cx + reach * math.cos(a), cy + reach * math.sin(a)))
    dr.polygon([P(v) for v in pts], fill=(70, 110, 220, 40), outline=(70, 110, 220, 160))
    gate = G.place_at(next(p for p in D.PLACES if p['id'] == 'poi:castle_gate'), polys)
    for i in range(0, 46):
        if i % 2 == 0:
            a = (cx + (gate[0] - cx) * i / 46, cy + (gate[1] - cy) * i / 46)
            b = (cx + (gate[0] - cx) * (i + 1) / 46, cy + (gate[1] - cy) * (i + 1) / 46)
            dr.line([P(a), P(b)], fill=(70, 110, 220, 200), width=2 * k)
    dr.text(P((cx + 2600, cy + 2200)), 'MU-4 camera: the signature', font=font(11 * k, 'b'), fill=(50, 80, 200))
    # places
    fl = font(11 * k)
    for p in D.PLACES:
        at = G.place_at(p, polys)
        x, y = P(at)
        col, shape = KIND_STYLE[p['kind']]
        r = 5 * k
        if shape == 'square':
            dr.rectangle([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255))
        elif shape == 'dot':
            dr.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255))
        elif shape == 'tri':
            dr.polygon([(x, y - r - 2), (x - r - 1, y + r), (x + r + 1, y + r)], fill=col, outline=(255, 255, 255))
        elif shape == 'diamond':
            dr.polygon([(x, y - r - 1), (x + r + 1, y), (x, y + r + 1), (x - r - 1, y)], fill=col, outline=(90, 60, 0))
        elif shape == 'post':
            dr.rectangle([x - 2 * k, y - r - 3 * k, x + 2 * k, y + r], fill=col)
            dr.rectangle([x - r, y - r - 3 * k, x + r, y - r + 1 * k], fill=col)
        elif shape == 'booth':
            dr.rectangle([x - r - 2, y - r - 2, x + r + 2, y + r + 2], fill=(255, 255, 255), outline=col, width=2 * k)
            for t in range(-r, r + 1, 3 * k):
                dr.line([(x + t, y - r), (x + t, y + r)], fill=(220, 50, 50), width=k)
    # labels
    LABELS = {
        'entrance:xd12_roof': ('Arrival: XD-12\'s cloud stair', (400, -250)),
        'entrance:xd19_gate': ('XD-19 return point (facing south)', (500, -300)),
        'poi:danger_sign': ("'Danger! Go back!'", (350, 80)),
        'poi:nine_north': ("'Xeen--9N.'", (-3600, 120)),
        'poi:xeendom_sign': ("'Now entering Xeendom'", (-5800, 60)),
        'poi:aviary_sign': ("'Xeen's Aviary'", (300, -700)),
        'poi:statue_1': ('Rhyme 1', (300, 120)), 'poi:statue_2': ('Rhyme 2', (300, -350)),
        'poi:statue_3': ('Rhyme 3', (-2300, 120)), 'poi:statue_4': ('Rhyme 4', (300, -350)),
        'poi:nest_sw': ('Roc nest', (-2700, 380)), 'poi:nest_se': ('Roc nest', (400, 380)),
        'poi:offering_1': ('Offering', (400, 100)), 'poi:offering_2': ('Offering', (400, 100)),
        'poi:offering_3': ('Offering', (400, 100)), 'poi:offering_4': ('Offering', (400, 100)),
        'poi:offering_5': ('Offering', (400, 100)), 'poi:offering_6': ('Offering', (400, 100)),
        'poi:might_game': ('Might: bell and hammer', (400, 0)), 'poi:speed_game': ('Speed: gremlin track', (400, 100)),
        'poi:endurance_game': ('Endurance: treadmill', (-1200, 700)),
        'poi:accuracy_game': ('Accuracy: bullseye', (-2600, -350)),
        'poi:prize_stand': ("Slick's prize stand", (-4400, 60)),
        'poi:castle_gate': ('Gate (m34.gate, two leaves)', (-6600, 300)),
        'poi:chest_hollow': ('Chest', (300, -100)), 'poi:chest_cache': ('Chest', (300, -100)),
        'poi:chest_pack': ('Chest', (300, -300)), 'poi:chest_hoard': ('Hoard', (300, 100)),
        'landmark:dragon_rock': ('dragon-head rock', (-3000, -800)),
    }
    for p in D.PLACES:
        if p['id'] in LABELS:
            text, (dx, dy) = LABELS[p['id']]
            at = G.place_at(p, polys)
            x, y = P((at[0] + dx, at[1] + dy))
            dr.text((x, y), text, font=fl, fill=(30, 30, 40))
    # space names with floors
    fi = font(11 * k, 'i')
    NAME_OFF = {'room:carnival': (-3300, 2400), 'room:gate_court': (-3800, -1900), 'room:landing': (1500, -400),
                'room:brink': (1500, -300), 'room:stair_head': (-2000, 1100), 'room:aviary': (-2400, 2700),
                'room:back_lot': (-3000, 1700), 'room:dragon_clouds': (-3800, 2200), 'zone:castle': None,
                'room:west_wing': (-1800, 1900), 'room:east_wing': (-1600, 1900), 'room:sw_nest': (-2400, 2300),
                'room:se_nest': (-1600, 2300), 'room:nw_isle': (-2500, 2300), 'room:east_horn': (-1800, 2100),
                'room:west_spine': (1300, 1800), 'room:west_pillar': (1400, 1300), 'room:west_shelf': (1700, 1400),
                'room:east_pillar': (-5800, 1300), 'room:east_ledge': (-5800, 1400)}
    for sp in D.SPACES:
        off = NAME_OFF.get(sp['id'], (-1500, 1800))
        if off is None:
            continue
        x, y = P((sp['at'][0] + off[0], sp['at'][1] + off[1]))
        label = (f"{sp['name']} ({sp['floor']:+d})" if sp['kind'] != 'sealed'
                 else f"{sp['name']} (+{sp['floor']}): sealed, Q-F1")
        dr.text((x, y), label, font=fi, fill=(70, 60, 50))
    # group counts
    fb = font(10 * k, 'b')
    for g in D.GROUPS:
        at = G.place_at(g, polys)
        x, y = P(at)
        col = ACTOR_COLOUR[g['actor']]
        r = 7 * k
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255))
        t = str(g['count'])
        dr.text((x - 3 * k, y - 6 * k), t, font=fb, fill=(255, 255, 255))
    # link lengths for bridges and the unseen way
    fs = font(10 * k)
    for l in D.LINKS:
        if l['style'] in ('bridge', 'unseen', 'causeway', 'road'):
            p, q = G.link_ends(l, polys)
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            x, y = P(m)
            text = f"{round(G.length(p, q)):,}"
            if l['style'] == 'unseen':
                text = f"unseen way, 9 cells = {round(G.length(p, q)):,}"
                x += 10 * k
            dr.text((x + 6 * k, y - 6 * k), text, font=fs, fill=(70, 50, 30) if l['style'] != 'unseen' else (40, 60, 160))
    # scale bar
    x0, y0 = P((-D.HALF[0] + 800, -D.HALF[1] + 700))
    dr.rectangle([x0 - 6 * k, y0 - 14 * k, x0 + 5120 * s + 100 * k, y0 + 10 * k], fill=(60, 60, 70, 200))
    dr.line([(x0, y0), (x0 + 5120 * s, y0)], fill=(255, 255, 255), width=3 * k)
    dr.text((x0 + 5120 * s + 8 * k, y0 - 8 * k), '5,120 (10 cells)', font=fs, fill=(255, 255, 255))
    return img


# ------------------------------------------------------------------------------------------------ blockout
def blockout(polys, out, W=1536, H=1024):
    cam = camera(polys)
    cx, cy = cam['at']
    cz = cam['z']
    yaw, pitch = cam['yaw'], cam['pitch']
    fwd = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
    right = (math.sin(yaw), -math.cos(yaw), 0.0)
    up = (fwd[1] * right[2] - fwd[2] * right[1], fwd[2] * right[0] - fwd[0] * right[2],
          fwd[0] * right[1] - fwd[1] * right[0])
    if up[2] < 0:
        up = tuple(-v for v in up)
    fpx = (W / 2) / math.tan(cam['fov'] / 2)
    NEAR = 40.0

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

    def proj(c):
        return (W / 2 + c[0] / c[2] * fpx, H / 2 - c[1] / c[2] * fpx)

    faces = []  # (depth, points3d, colour)

    campos = (cx, cy, cz)

    def facing(poly3, normal):
        p = poly3[0]
        return sum(normal[i] * (campos[i] - p[i]) for i in range(3)) > 0

    def add(poly3, colour, bias=0.0, normal=None):
        if normal is not None and not facing(poly3, normal):
            return
        cs = [cam_space(p) for p in poly3]
        cs = clip(cs)
        if len(cs) < 3:
            return
        depth = sum(c[2] for c in cs) / len(cs) + bias
        faces.append((depth, [proj(c) for c in cs], colour))

    def prism(poly2, z0, z1, top, side, bias=0.0):
        n = len(poly2)
        area = sum(poly2[i][0] * poly2[(i + 1) % n][1] - poly2[(i + 1) % n][0] * poly2[i][1] for i in range(n))
        sgn = 1.0 if area > 0 else -1.0
        for i in range(n):
            a, b = poly2[i], poly2[(i + 1) % n]
            normal = (sgn * (b[1] - a[1]), -sgn * (b[0] - a[0]), 0.0)
            add([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], side, bias, normal)
        add([(x, y, z1) for x, y in poly2], top, bias, (0.0, 0.0, 1.0))

    def box(cxy, sx, sy, z0, z1, top, side):
        x, y = cxy
        prism([(x - sx / 2, y - sy / 2), (x + sx / 2, y - sy / 2), (x + sx / 2, y + sy / 2), (x - sx / 2, y + sy / 2)],
              z0, z1, top, side)

    def ngon(cxy, r, n=8):
        return [(cxy[0] + r * math.cos(2 * math.pi * i / n), cxy[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

    CLOUD_TOP, CLOUD_SIDE, CLOUD_UNDER = (246, 244, 238), (200, 205, 216), (176, 184, 200)
    for sid, poly in polys.items():
        s = G.SPACE[sid]
        z = s['floor']
        prism(poly, z - 256, z, CLOUD_TOP, CLOUD_SIDE)
        # the hanging root: a cone under the island
        n = len(poly)
        tip = (s['at'][0], s['at'][1], z - 256 - 0.3 * max(s['extent']))
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            a3 = (a[0] * 0.8 + s['at'][0] * 0.2, a[1] * 0.8 + s['at'][1] * 0.2, z - 256)
            b3 = (b[0] * 0.8 + s['at'][0] * 0.2, b[1] * 0.8 + s['at'][1] * 0.2, z - 256)
            u = (b3[0] - a3[0], b3[1] - a3[1], 0.0)
            v = (tip[0] - a3[0], tip[1] - a3[1], tip[2] - a3[2])
            nrm = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            mid = ((a3[0] + b3[0]) / 2 - s['at'][0], (a3[1] + b3[1]) / 2 - s['at'][1])
            if nrm[0] * mid[0] + nrm[1] * mid[1] < 0:
                nrm = tuple(-c for c in nrm)
            add([a3, b3, tip], CLOUD_UNDER, 0.0, nrm)
    for l in D.LINKS:
        za, zb = G.SPACE[l['a']]['floor'], G.SPACE[l['b']]['floor']
        p, q = G.link_ends(l, polys)
        if l['style'] == 'neck':
            cap = G.capsule(p, q, l['width'])
            add([(cap[0][0], cap[0][1], za), (cap[1][0], cap[1][1], zb), (cap[2][0], cap[2][1], zb),
                 (cap[3][0], cap[3][1], za)], CLOUD_TOP, 30)
        elif l['style'] == 'causeway':
            cap = G.capsule(p, q, l['width'])
            add([(cap[0][0], cap[0][1], za + 8), (cap[1][0], cap[1][1], zb + 8), (cap[2][0], cap[2][1], zb + 8),
                 (cap[3][0], cap[3][1], za + 8)], (200, 192, 176), -20)
        elif l['style'] == 'bridge':
            cap = G.capsule(p, q, 256)
            mid = -180
            add([(cap[0][0], cap[0][1], za), (cap[1][0], cap[1][1], zb), (cap[2][0], cap[2][1], zb),
                 (cap[3][0], cap[3][1], za)], (120, 90, 60), -10)
        elif l['style'] == 'unseen':
            cap = G.capsule(p, q, 512)
            add([(cap[0][0], cap[0][1], za + 4), (cap[1][0], cap[1][1], zb + 4), (cap[2][0], cap[2][1], zb + 4),
                 (cap[3][0], cap[3][1], za + 4)], (222, 228, 240), -5)
    # the road
    zl, zc, zg = (G.SPACE[k]['floor'] + 8 for k in ('room:landing', 'room:carnival', 'room:gate_court'))
    for (y0, z0), (y1, z1) in (((-5600, zl), (0, zc)), ((0, zc), (6400, zc)), ((6400, zc), (11520, zg))):
        add([(-384, y0, z0), (384, y0, z0), (384, y1, z1), (-384, y1, z1)], (206, 198, 180), -15)
    # castle
    cs = G.SPACE['zone:castle']
    base = cs['floor']
    BLACK, BLACKS, GOLD = (52, 50, 60), (36, 34, 42), (196, 160, 70)
    walls = G.castle_walls(cs)
    CH = D.CASTLE_HEIGHTS
    prism(walls, base, base + CH['walls'], (60, 58, 70), BLACK)
    inner = G.castle_walls(dict(at=cs['at'], extent=(cs['extent'][0] - 256, cs['extent'][1] - 256)))
    prism(inner, base + CH['walls'], base + CH['walls'] + 96, GOLD, GOLD)
    kx, ky = cs['at']
    box((kx, ky + 640), CH['keep_size'][0], CH['keep_size'][1], base, base + CH['keep'], (70, 66, 80), BLACKS)
    box((kx, ky + 640), CH['keep_size'][0] - 512, CH['keep_size'][1] - 512, base + CH['keep'], base + CH['keep'] + 96,
        GOLD, GOLD)
    for (x, y) in walls:
        prism(ngon((x, y), CH['tower_radius']), base, base + CH['towers'], (70, 66, 80), BLACKS)
        prism(ngon((x, y), CH['tower_radius'] + 64), base + CH['towers'], base + CH['towers'] + 64, GOLD, GOLD)
    gx, gy = G.place_at(next(p for p in D.PLACES if p['id'] == 'poi:castle_gate'), polys)
    add([(gx - 256, gy - 6, base), (gx + 256, gy - 6, base), (gx + 256, gy - 6, base + 640), (gx - 256, gy - 6, base + 640)],
        (150, 110, 40), -50)
    # booths, statues, nests, signs
    for p in D.PLACES:
        at = G.place_at(p, polys)
        z = G.SPACE[p['space']]['floor']
        if p['kind'] in ('booth', 'stand'):
            box(at, 512, 384, z, z + 288, (220, 60, 50), (230, 220, 200))
            box(at, 640, 512, z + 288, z + 352, (240, 240, 235), (220, 60, 50))
        elif p['kind'] in ('statue', 'offering'):
            box(at, 192, 192, z, z + 96, (210, 205, 195), (180, 176, 168))
            box(at, 112, 112, z + 96, z + 400, (200, 196, 186), (170, 166, 160))
        elif p['kind'] == 'nest':
            prism(ngon(at, 420, 10), z, z + 96, (120, 90, 50), (100, 75, 45))
        elif p['kind'] == 'sign':
            box(at, 24, 24, z, z + 224, (110, 80, 50), (110, 80, 50))
            box((at[0], at[1]), 192, 20, z + 160, z + 240, (140, 100, 60), (140, 100, 60))
    # the aviary's rock spurs
    av = G.SPACE['room:aviary']
    rng = np.random.default_rng(3)
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.3
        r = 0.42 * min(av['extent'])
        at = (av['at'][0] + r * math.cos(a) * 1.25, av['at'][1] + r * math.sin(a))
        h = rng.uniform(500, 1100)
        prism(ngon(at, rng.uniform(220, 360), 6), av['floor'], av['floor'] + h, (150, 140, 130), (120, 112, 104))
    # rocs over the aviary and nests: small dark diamonds
    birds = []
    for g in D.GROUPS:
        at = G.place_at(g, polys)
        z = G.SPACE[g['space']]['floor'] + 700
        for i in range(g['count']):
            birds.append((at[0] + 400 * math.cos(i * 2.1), at[1] + 400 * math.sin(i * 2.1), z + 150 * i))
    img = Image.new('RGB', (W, H))
    dr = ImageDraw.Draw(img)
    # sky above the horizon, cloud sea below
    hz = H / 2 - math.tan(pitch) * fpx * -1
    hz = H / 2 + math.tan(-pitch) * fpx * -1
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
    for b in birds:
        c = cam_space(b)
        if c[2] > NEAR:
            x, y = proj(c)
            r = max(2, 9000 / c[2])
            dr.polygon([(x - 2 * r, y), (x, y + r * 0.6), (x + 2 * r, y), (x, y + r * 0.2)], fill=(60, 50, 45))
    # annotations (Codex paints the things, never the words)
    fa = font(18)
    ANN = [('Castle Xeen', (0, G.SPACE['zone:castle']['at'][1], 2600)),
           ("Slick's carnival", (*G.SPACE['room:carnival']['at'], 700)),
           ("Xeen's Aviary", (*G.SPACE['room:aviary']['at'], 1700)), ('unseen way (9N)', (0, -8200, 300)),
           ("Xeendom's landing", (*G.SPACE['room:landing']['at'], 500)),
           ('Dragon Clouds', (*G.SPACE['room:dragon_clouds']['at'], 2200))]
    for text, p in ANN:
        c = cam_space(p)
        if c[2] > NEAR:
            x, y = proj(c)
            if 0 < x < W and 0 < y < H:
                dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(40, 70, 220), width=2)
                dr.text((x + 8, y - 22), text, font=fa, fill=(40, 70, 220))
    img.save(out)


def main():
    polys = G.outlines()
    f = figures(polys)
    (OUT / 'figures.json').write_text(json.dumps(f, indent=1) + '\n')
    big = plan(polys, f, k=2)
    big.save(OUT / 'plan_x9_2x.png')
    big.resize((big.width // 2, big.height // 2), Image.LANCZOS).save(OUT / 'plan_x9.png')
    blockout(polys, OUT / 'blockout_signature.png')
    print(json.dumps({k: f[k] for k in ('walk_area_m', 'cloud_bbox_cells', 'monsters', 'kill_xp_member', 'quiet_share',
                                        'first_fight', 'bridge_range', 'unseen_way', 'poi_census', 'poi_spacing',
                                        'signature', 'dragon_clouds_gap')}, indent=1))


if __name__ == '__main__':
    main()
