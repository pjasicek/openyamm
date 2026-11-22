#!/usr/bin/env python3
"""XD-17 Shangri-La: the MU-3 plan drawing, the MU-4 blockouts and the figures (A5, 2026-11-20).

    render_xd17.py            mockups/plan_xd17.png, blockout_arrival.png, blockout_signature.png, figures.json

The plan is to scale (512 grid, labels every 2,048), drawn from places.py. The blockouts are crude painter's-algorithm
perspective renders of the same places from the two MU-4 cameras, used as Codex's composition reference.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import places as P

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/xd17') / 'mockups'


def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/{name}', size)


def crest_poly():
    out = []
    for x, y in P.FLOOR:
        r = math.hypot(x, y)
        k = (r + P.CREST_OUT) / r
        out.append((x * k, y * k, P.crest_height(x, y)))
    return out


def inside(pt, poly):
    x, y = pt
    n, c = len(poly), False
    for i in range(n):
        x1, y1 = poly[i][:2]
        x2, y2 = poly[(i + 1) % n][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def lane_dist(p):
    return min(seg_dist(p, a, b) for line in P.LANES.values() for a, b in zip(line, line[1:]))


# ---------------------------------------------------------------- figures
def figures():
    doors = P.doors()
    svc = [d for d in doors if d[5]['id'] in P.SERVICES]
    svc_pts = [d[3] for d in svc]
    cx = sum(p[0] for p in svc_pts) / len(svc_pts)
    cy = sum(p[1] for p in svc_pts) / len(svc_pts)
    centre = (cx, cy)
    nearest_svc = sorted(min(P.dist(p, q) for q in svc_pts if q != p) for p in svc_pts)
    # per building (services by building: Arm and Hammer's two doors are two services of one building)
    b_pts = [(b, b['at'], b['size'][0] * b['size'][1]) for b in P.BUILDINGS]
    dists = sorted((P.dist(at, centre), area) for b, at, area in b_pts)
    tot = sum(a for _, a in dists)
    acc, core = 0, None
    for d, a in dists:
        acc += a
        if acc >= tot / 2:
            core = d
            break
    plain = sorted(d for d, _ in dists)
    p90 = plain[min(len(plain) - 1, int(round(0.9 * (len(plain) - 1))))]
    beyond = sum(a for d, a in dists if d > 1.5 * core) / tot
    arrival = P.XD16_ARRIVAL
    by_arrival = sorted(P.BUILDINGS, key=lambda b: min(P.dist(arrival, d[3]) for d in b['doors']))
    tavern_rank = [b['id'] for b in by_arrival].index('building:tavern_xanadu') / (len(by_arrival) - 1)
    by_centre = sorted(P.BUILDINGS, key=lambda b: P.dist(b['at'], centre))
    rank = {b['id']: i / (len(by_centre) - 1) for i, b in enumerate(by_centre)}
    # town land: floor within 1,536 of a door (raster, 64-unit cells)
    step = 64
    land = built = 0
    for ix in range(-6600 // step, 6600 // step):
        for iy in range(-5300 // step, 5300 // step):
            pt = (ix * step + step / 2, iy * step + step / 2)
            if not inside(pt, P.FLOOR):
                continue
            if min(P.dist(pt, d[3]) for d in doors) > 1536:
                continue
            land += 1
            for b in P.BUILDINGS:
                if abs(pt[0] - b['at'][0]) <= b['size'][0] / 2 and abs(pt[1] - b['at'][1]) <= b['size'][1] / 2:
                    built += 1
                    break
    floor_cells = 0
    for ix in range(-7000 // 128, 7000 // 128):
        for iy in range(-5600 // 128, 5600 // 128):
            if inside((ix * 128 + 64, iy * 128 + 64), P.FLOOR):
                floor_cells += 1
    floor_area = floor_cells * 128 * 128
    lane_d = sorted(lane_dist(d[3]) for d in doors)
    house_near = sorted(min(P.dist(b['at'], c['at']) for c in P.BUILDINGS if c is not b) for b in P.BUILDINGS)
    floors = sorted(d[5]['floor'] for d in doors)
    weapon = next(d[3] for d in doors if d[0] == 'door:arm_and_hammer_arms')
    armour = next(d[3] for d in doors if d[0] == 'door:arm_and_hammer_armour')
    crest = crest_poly()
    xs = [p[0] for p in P.FLOOR]
    ys = [p[1] for p in P.FLOOR]
    passage_len = sum(P.dist(a, b) for a, b in zip(P.PASSAGE, P.PASSAGE[1:]))
    f = {
        'buildings': len(P.BUILDINGS),
        'doors': len(doors),
        'services': 5,
        'residences': 10,
        'service_kinds': 'weapon, armour, temple, tavern, Light guild',
        'weapon_to_armour': round(P.dist(weapon, armour)),
        'service_nearest_median': round(nearest_svc[len(nearest_svc) // 2]),
        'service_nearest': [round(v) for v in nearest_svc],
        'farthest_service': round(max(P.dist(p, centre) for p in svc_pts)),
        'core_radius': round(core),
        'p90_distance': round(p90),
        'farthest_building': round(plain[-1]),
        'fringe_over_core': round(p90 / core, 2),
        'beyond_1_5_core': round(beyond, 2),
        'town_built_share': round(built / land, 3),
        'tavern_rank_from_arrival': round(tavern_rank, 2),
        'tavern_rank_from_centre': round(rank['building:tavern_xanadu'], 2),
        'temple_rank_from_centre': round(rank['building:earth_temple'], 2),
        'doors_on_axes': 1.0,
        'door_to_lane_median': round(lane_d[len(lane_d) // 2]),
        'door_to_lane_max': round(lane_d[-1]),
        'doors_with_lane_1024': round(sum(1 for v in lane_d if v <= 1024) / len(lane_d), 2),
        'house_to_nearest_house_median': round(house_near[len(house_near) // 2]),
        'door_level_p10_p90': [floors[max(0, int(0.1 * (len(floors) - 1)))], floors[int(0.9 * (len(floors) - 1))]],
        'wells': 1,
        'valley_floor_extent': [max(xs) - min(xs), max(ys) - min(ys)],
        'valley_floor_area_m': round(floor_area / 1e6, 1),
        'valley_floor_cells_512': round(floor_area / 512 / 512),
        'crest_range': [round(min(p[2] for p in crest)), round(max(p[2] for p in crest))],
        'arrival_to_first_door': round(min(P.dist(arrival, d[3]) for d in doors)),
        'arrival_to_tavern_door': round(P.dist(arrival, next(d[3] for d in doors
                                                             if d[0] == 'door:tavern_xanadu'))),
        'arrival_to_well': round(P.dist(arrival, P.WELL)),
        'well_to_pyramid_portal': round(P.dist(P.WELL, P.PYRAMID['portal'])),
        'well_to_passage_mouth': round(P.dist(P.WELL, P.PASSAGE[0])),
        'passage_length': round(passage_len),
        'cleft_arrival_to_valley': round(P.dist(P.X7CLEFT_ARRIVAL, P.PASSAGE[0])),
        'lacey_to_well': round(P.dist(P.LACEY, P.WELL)),
        'summit_from_cameras': {k: round(P.dist(c['at'], P.SUMMIT['at'])) for k, c in P.CAMERAS.items()},
        'monsters': 0,
        'chests': 0,
        'poi_count': 3 + len(doors),   # D-20 / D-50 change 6: well, pyramid, crystal, doors (the falls a landmark)
    }
    return f


# ---------------------------------------------------------------- plan drawing
X0, X1, Y0, Y1 = -10752, 11264, -7424, 9216
INSIDE_LABELS = {'door:tavern_xanadu', 'door:arm_and_hammer_arms', 'door:arm_and_hammer_armour'}
S = 0.125


def to_px(x, y):
    return ((x - X0) * S + 40, (Y1 - y) * S + 60)


def plan():
    w = int((X1 - X0) * S) + 80
    h = int((Y1 - Y0) * S) + 120
    img = Image.new('RGB', (w, h), (22, 22, 26))
    d = ImageDraw.Draw(img, 'RGBA')
    crest = crest_poly()
    # cliffs: crest polygon dark, shaded by height
    d.polygon([to_px(x, y) for x, y, _ in crest], fill=(48, 46, 50))
    for i in range(len(crest)):
        a, b = crest[i], crest[(i + 1) % len(crest)]
        fa, fb = P.FLOOR[i], P.FLOOR[(i + 1) % len(P.FLOOR)]
        shade_ = int(40 + (a[2] - 2300) / 1000 * 40)
        d.polygon([to_px(*fa), to_px(*fb), to_px(b[0], b[1]), to_px(a[0], a[1])],
                  fill=(shade_, shade_ - 2, shade_ + 4))
    for x, y, hgt in crest:
        px = to_px(x, y)
        d.text((px[0] - 14, px[1] - 6), f'{int(round(hgt, -2))}', font=font(11), fill=(150, 150, 160))
    # summit backdrop
    sx, sy = P.SUMMIT['at']
    for r, col in ((P.SUMMIT['radius'] * 0.55, (90, 70, 64)), (P.SUMMIT['crater'], (160, 70, 34))):
        a, b = to_px(sx - r, sy + r), to_px(sx + r, sy - r)
        d.ellipse([a, b], outline=col, width=3)
    px = to_px(sx, sy)
    d.text((px[0] - 70, px[1] + 10), f"Firestone's summit (backdrop, {P.SUMMIT['height']:,})", font=font(12),
           fill=(210, 150, 120))
    # floor
    d.polygon([to_px(*p) for p in P.FLOOR], fill=(86, 128, 70))
    # terraces
    for zid in ('zone:west_terrace', 'zone:north_terrace'):
        _, c, ext, _, _ = P.ZONES[zid]
        a = to_px(c[0] - ext[0] / 2, c[1] + ext[1] / 2)
        b = to_px(c[0] + ext[0] / 2, c[1] - ext[1] / 2)
        d.rounded_rectangle([a, b], radius=18, fill=(104, 146, 82))
    # orchard
    _, c, ext, _, _ = P.ZONES['zone:orchard']
    a = to_px(c[0] - ext[0] / 2, c[1] + ext[1] / 2)
    b = to_px(c[0] + ext[0] / 2, c[1] - ext[1] / 2)
    d.rounded_rectangle([a, b], radius=14, fill=(96, 136, 72))
    for t in P.ORCHARD_TREES:
        px = to_px(*t)
        d.ellipse([px[0] - 9, px[1] - 9, px[0] + 9, px[1] + 9], fill=(48, 92, 40), outline=(30, 60, 26))
    # pool, stream, fall
    (px_, py_), (rx, ry) = P.POOL['at'], P.POOL['radii']
    d.ellipse([to_px(px_ - rx, py_ + ry), to_px(px_ + rx, py_ - ry)], fill=(70, 130, 170), outline=(200, 230, 245))
    d.line([to_px(*p) for p in P.STREAM], fill=(90, 150, 190), width=5)
    lp = to_px(*P.FALL['lip'])
    d.polygon([(lp[0] + 6, lp[1] - 10), (lp[0] + 6, lp[1] + 10), (lp[0] - 22, lp[1])], fill=(235, 245, 255))
    d.text((lp[0] + 8, lp[1] - 24), f"the white fall (lip {P.FALL['z']:,})", font=font(12), fill=(225, 240, 255))
    # court
    _, c, ext, _, _ = P.ZONES['zone:court']
    a = to_px(c[0] - ext[0] / 2, c[1] + ext[1] / 2)
    b = to_px(c[0] + ext[0] / 2, c[1] - ext[1] / 2)
    d.rectangle([a, b], fill=(110, 160, 84), outline=(205, 195, 170), width=6)
    # lanes
    for line in P.LANES.values():
        d.line([to_px(*p) for p in line], fill=(196, 180, 140), width=max(3, int(320 * S)), joint='curve')
    # passage and mouth
    d.line([to_px(*p) for p in P.PASSAGE], fill=(120, 116, 112), width=int(P.PASSAGE_WIDTH * S))
    mp = to_px(*P.MOUTH)
    me = to_px(*P.MOUTH_EXIT)
    d.rectangle([mp[0] - 22, mp[1] - 2, me[0] + 22, me[1]], fill=(14, 14, 16))
    # buildings
    fb = font(12, True)
    fs = font(11)
    for bld in P.BUILDINGS:
        x, y = bld['at']
        bw, bd = bld['size']
        a = to_px(x - bw / 2, y + bd / 2)
        b = to_px(x + bw / 2, y - bd / 2)
        svc = bld['id'] in P.SERVICES
        fill = (226, 190, 120) if svc else (236, 232, 222)
        if bld['id'] in ('building:guild_light', 'building:sally'):
            d.ellipse([a, b], fill=fill, outline=(40, 40, 40), width=2)
        else:
            d.rectangle([a, b], fill=fill, outline=(40, 40, 40), width=2)
        for aid, house, sid, pt, face in bld['doors']:
            p = to_px(*pt)
            d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=(200, 40, 40))
        cxp, cyp = to_px(x, y)
        name = bld['name'].replace("Shangri-La Wizard's Guild", 'Light guild')
        words, rows = name.split(), []
        for w_ in words:
            if rows and d.textlength(rows[-1] + ' ' + w_, font=fb) <= (b[0] - a[0]) - 6:
                rows[-1] += ' ' + w_
            else:
                rows.append(w_)
        top = a[1] + 6 if bld['size'][1] * S > 70 else cyp - 7 * len(rows)
        for i, row in enumerate(rows):
            d.text((cxp, top + 14 * i), row, font=fb, fill=(20, 20, 20), anchor='ma')
        for aid, house, sid, pt, face in bld['doors']:
            p = to_px(*pt)
            off, anchor = {'e': ((9, 0), 'lm'), 'w': ((-9, 0), 'rm'), 'n': ((0, -9), 'md'),
                           's': ((0, 9), 'ma')}[face]
            if aid in INSIDE_LABELS:
                off, anchor = (-off[0], -off[1]), {'lm': 'rm', 'rm': 'lm'}.get(anchor, anchor)
            d.text((p[0] + off[0], p[1] + off[1]), f'{house} {aid}', font=fs, fill=(255, 236, 236), anchor=anchor,
                   stroke_width=2, stroke_fill=(60, 10, 10))
    # pyramid
    pxp = P.PYRAMID
    half = pxp['base'] / 2
    a = to_px(pxp['at'][0] - half, pxp['at'][1] + half)
    b = to_px(pxp['at'][0] + half, pxp['at'][1] - half)
    d.rectangle([a, b], fill=(200, 184, 150), outline=(60, 50, 40), width=2)
    d.line([a, b], fill=(120, 104, 80), width=2)
    d.line([(a[0], b[1]), (b[0], a[1])], fill=(120, 104, 80), width=2)
    pp = to_px(*pxp['portal'])
    d.ellipse([pp[0] - 6, pp[1] - 6, pp[0] + 6, pp[1] + 6], fill=(140, 90, 220))
    d.text((a[0] - 8, a[1] + 20), 'travel pyramid', font=fb, fill=(240, 230, 250), anchor='rm', stroke_width=2,
           stroke_fill=(30, 20, 40))
    d.text((a[0] - 8, a[1] + 36), '(Castle Alamar, after M30)', font=fs, fill=(240, 230, 250), anchor='rm',
           stroke_width=2, stroke_fill=(30, 20, 40))
    # well, Lacey, Stumpy, crystal
    wp = to_px(*P.WELL)
    d.ellipse([wp[0] - 11, wp[1] - 11, wp[0] + 11, wp[1] + 11], fill=(90, 160, 220), outline=(250, 250, 250), width=3)
    d.text((wp[0] + 14, wp[1] - 26), '+1 level well', font=fb, fill=(255, 255, 255))
    for pt, label, col in ((P.LACEY, 'Lacey (4719)', (255, 255, 255)), (P.STUMPY, 'Stumpy (4718)', (150, 100, 50))):
        p = to_px(*pt)
        d.polygon([(p[0], p[1] - 9), (p[0] + 8, p[1] + 7), (p[0] - 8, p[1] + 7)], fill=col, outline=(0, 0, 0))
        d.text((p[0] + 10, p[1] + 2), label, font=fb, fill=(255, 245, 200))
    cp = to_px(*P.CRYSTAL)
    d.polygon([(cp[0], cp[1] - 8), (cp[0] + 6, cp[1]), (cp[0], cp[1] + 8), (cp[0] - 6, cp[1])], fill=(140, 240, 255))
    d.text((cp[0] + 10, cp[1] + 6), 'the hidden crystal', font=fs, fill=(170, 240, 255))
    # arrivals and exits
    f13 = font(13, True)

    def arrow(pt, ang, label, col, dx=12, dy=-6):
        p = to_px(*pt)
        a = math.radians(ang)
        tip = (p[0] + 34 * math.cos(a), p[1] - 34 * math.sin(a))
        d.line([p, tip], fill=col, width=4)
        left = (tip[0] - 12 * math.cos(a - 0.5), tip[1] + 12 * math.sin(a - 0.5))
        right = (tip[0] - 12 * math.cos(a + 0.5), tip[1] + 12 * math.sin(a + 0.5))
        d.polygon([tip, left, right], fill=col)
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=col)
        d.text((p[0] + dx, p[1] + dy), label, font=f13, fill=col, stroke_width=2, stroke_fill=(20, 20, 20))

    arrow(P.XD16_ARRIVAL, 90, 'entrance:xd16_way (from XD-16)', (120, 255, 140), 14, 4)
    arrow(P.MOUTH_EXIT, 270, '"Leave Shangri-La?" -> XD-16 entrance:xd17_way', (255, 200, 90), 30, -2)
    arrow(P.X7CLEFT_ARRIVAL, 0, 'entrance:x7_cleft (from X7)', (120, 255, 140), -40, 14)
    arrow(P.PASSAGE_EXIT, 180, 'rockfall: xd17.cleft_opened -> X7 entrance:xd17_cleft', (255, 200, 90), -40, -44)
    arrow(P.PYRAMID['arrival'], 270, 'entrance:d6_pyramid', (120, 255, 140), 12, -4)
    # cameras
    for name, cam in P.CAMERAS.items():
        p = to_px(*cam['at'])
        for side in (-1, 1):
            a = math.radians(cam['yaw'] + side * cam['fov'] / 2)
            d.line([p, (p[0] + 230 * math.cos(a), p[1] - 230 * math.sin(a))], fill=(255, 220, 60, 170), width=2)
        a = math.radians(cam['yaw'])
        d.line([p, (p[0] + 900 * math.cos(a), p[1] - 900 * math.sin(a))], fill=(255, 220, 60, 110), width=2)
        d.rectangle([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=(255, 220, 60))
        d.text((p[0] - 12, p[1] + 10), f'MU-4 {name}', font=f13, fill=(255, 225, 90), anchor='ra', stroke_width=2,
               stroke_fill=(40, 30, 0))
    # grid and labels
    fg = font(11)
    for gx in range(-10240, 11264 + 1, 2048):
        a, b = to_px(gx, Y1), to_px(gx, Y0)
        d.line([a, b], fill=(255, 255, 255, 26), width=1)
        d.text((a[0] - 14, 42), f'{gx}', font=fg, fill=(150, 150, 150))
    for gy in range(-6144, 9216 + 1, 2048):
        a, b = to_px(X0, gy), to_px(X1, gy)
        d.line([a, b], fill=(255, 255, 255, 26), width=1)
        d.text((4, a[1] - 6), f'{gy}', font=fg, fill=(150, 150, 150))
    # scale bar and north
    sb0 = to_px(X0 + 400, Y0 + 500)
    sb1 = (sb0[0] + 2048 * S, sb0[1])
    d.line([sb0, sb1], fill=(255, 255, 255), width=4)
    d.text((sb0[0], sb0[1] + 6), '2,048 units (4 cells of 512)', font=font(12), fill=(230, 230, 230))
    n = to_px(X1 - 600, Y1 - 600)
    d.polygon([(n[0], n[1] - 26), (n[0] - 10, n[1]), (n[0] + 10, n[1])], fill=(255, 255, 255))
    d.text((n[0] - 5, n[1] + 4), 'N', font=font(16, True), fill=(255, 255, 255))
    d.text((40, 10), 'XD-17 Shangri-La: MU-3 plan (to scale; red dots are doors, A4 house id and door id)',
           font=font(20, True), fill=(240, 240, 240))
    img.save(HERE / 'plan_xd17.png')
    return img


# ---------------------------------------------------------------- blockouts
class Cam:
    def __init__(self, at, z, yaw, pitch, fov, w=1536, h=1024):
        self.p = (at[0], at[1], z)
        y, pt = math.radians(yaw), math.radians(pitch)
        self.f = (math.cos(y) * math.cos(pt), math.sin(y) * math.cos(pt), math.sin(pt))
        self.r = (math.sin(y), -math.cos(y), 0)
        fx, fy, fz = self.f
        rx, ry, rz = self.r
        self.u = (ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx)
        self.w, self.h = w, h
        self.k = (w / 2) / math.tan(math.radians(fov / 2))

    def cam(self, v):
        d = (v[0] - self.p[0], v[1] - self.p[1], v[2] - self.p[2])

        def dot(a):
            return a[0] * d[0] + a[1] * d[1] + a[2] * d[2]
        return dot(self.r), dot(self.u), dot(self.f)

    def proj(self, c):
        x, y, z = c
        return self.w / 2 + self.k * x / z, self.h / 2 - self.k * y / z


def clip_near(poly, near=32):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ain, bin_ = a[2] >= near, b[2] >= near
        if ain:
            out.append(a)
        if ain != bin_:
            t = (near - a[2]) / (b[2] - a[2])
            out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
    return out


def shade(col, normal_):
    light = (0.45, 0.35, 0.82)
    n = math.sqrt(sum(c * c for c in normal_)) or 1
    lam = abs(sum(l * c for l, c in zip(light, normal_)) / n)
    k = 0.55 + 0.45 * lam
    return tuple(int(min(255, c * k)) for c in col)


def normal(poly):
    a, b, c = poly[0], poly[1], poly[2]
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def box(x, y, z0, w, dpt, h, col, roof=None):
    x0, x1, y0, y1, z1 = x - w / 2, x + w / 2, y - dpt / 2, y + dpt / 2, z0 + h
    polys = [
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], col),
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], col),
        ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], col),
        ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], col),
    ]
    if roof:
        rh = min(w, dpt) * 0.45
        apex = (x, y, z1 + rh)
        corners = [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for i in range(4):
            polys.append(([corners[i], corners[(i + 1) % 4], apex], roof))
    else:
        polys.append(([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], col))
    return polys


def cylinder(x, y, z0, r, h, col, sides=10, cap=None, cap_h=0):
    polys = []
    pts = [(x + r * math.cos(2 * math.pi * i / sides), y + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    for i in range(sides):
        a, b = pts[i], pts[(i + 1) % sides]
        polys.append(([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z0 + h), (a[0], a[1], z0 + h)], col))
    if cap:
        apex = (x, y, z0 + h + cap_h)
        for i in range(sides):
            a, b = pts[i], pts[(i + 1) % sides]
            polys.append(([(a[0], a[1], z0 + h), (b[0], b[1], z0 + h), apex], cap))
    return polys


def scene():
    polys = []
    # floor fan (subdivided for sorting)
    n = len(P.FLOOR)
    for i in range(n):
        a, b = P.FLOOR[i], P.FLOOR[(i + 1) % n]
        for k in range(6):
            t0, t1 = k / 6, (k + 1) / 6
            p0 = (a[0] * (1 - t0), a[1] * (1 - t0))
            p1 = (a[0] * (1 - t1), a[1] * (1 - t1))
            q0 = (b[0] * (1 - t0), b[1] * (1 - t0))
            q1 = (b[0] * (1 - t1), b[1] * (1 - t1))
            polys.append(([(*p0, 0), (*q0, 0), (*q1, 0), (*p1, 0)], (92, 140, 74)))
    # cliffs
    crest = crest_poly()
    for i in range(n):
        fa, fb = P.FLOOR[i], P.FLOOR[(i + 1) % n]
        ca, cb = crest[i], crest[(i + 1) % n]
        for k in range(3):
            t0, t1 = k / 3, (k + 1) / 3
            fa0 = (fa[0] + t0 * (fb[0] - fa[0]), fa[1] + t0 * (fb[1] - fa[1]))
            fa1 = (fa[0] + t1 * (fb[0] - fa[0]), fa[1] + t1 * (fb[1] - fa[1]))
            ca0 = tuple(ca[j] + t0 * (cb[j] - ca[j]) for j in range(3))
            ca1 = tuple(ca[j] + t1 * (cb[j] - ca[j]) for j in range(3))
            polys.append(([(*fa0, 0), (*fa1, 0), ca1, ca0], (58, 56, 62)))
            out0 = (ca0[0] * 1.25, ca0[1] * 1.25, ca0[2] - 200)
            out1 = (ca1[0] * 1.25, ca1[1] * 1.25, ca1[2] - 200)
            polys.append(([ca0, ca1, out1, out0], (44, 42, 46)))
    # terraces
    for zid, hgt in (('zone:west_terrace', 256), ('zone:north_terrace', 256)):
        _, c, ext, _, _ = P.ZONES[zid]
        polys += box(c[0], c[1], 0, ext[0], ext[1], hgt, (120, 150, 96))
    # court and lanes (flat strips just above the floor)
    _, c, ext, _, _ = P.ZONES['zone:court']
    polys.append(([(c[0] - ext[0] / 2, c[1] - ext[1] / 2, 4), (c[0] + ext[0] / 2, c[1] - ext[1] / 2, 4),
                   (c[0] + ext[0] / 2, c[1] + ext[1] / 2, 4), (c[0] - ext[0] / 2, c[1] + ext[1] / 2, 4)],
                  (120, 176, 90)))
    for line in P.LANES.values():
        for a, b in zip(line, line[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L * 150, dx / L * 150
            polys.append(([(a[0] + nx, a[1] + ny, 8), (b[0] + nx, b[1] + ny, 8), (b[0] - nx, b[1] - ny, 8),
                           (a[0] - nx, a[1] - ny, 8)], (190, 176, 140)))
    # pool and fall
    (px_, py_), (rx, ry) = P.POOL['at'], P.POOL['radii']
    pts = [(px_ + rx * math.cos(2 * math.pi * i / 16), py_ + ry * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    polys.append(([(x, y, 6) for x, y in pts], (80, 140, 185)))
    lx, ly = P.FALL['lip']
    polys.append(([(lx - 120, ly - 260, P.FALL['z']), (lx - 120, ly + 260, P.FALL['z']), (lx - 300, ly + 220, 10),
                   (lx - 300, ly - 220, 10)], (240, 248, 255)))
    # buildings
    for b in P.BUILDINGS:
        x, y = b['at']
        svc = b['id'] in P.SERVICES
        wall = (226, 200, 150) if svc else (238, 234, 224)
        roof = (150, 70, 50)
        if b['id'] == 'building:earth_temple':
            wall, roof = (90, 86, 80), (80, 120, 60)
        if b['id'] == 'building:public_library':
            wall, roof = (220, 216, 206), (170, 160, 150)
        if b['id'] == 'building:guild_light':
            polys += cylinder(x, y, b['floor'], b['size'][0] / 2, b['height'], (245, 245, 240), 12, (230, 190, 60),
                              420)
            continue
        if b['id'] == 'building:sally':
            polys += cylinder(x, y, b['floor'], b['size'][0] / 2, b['height'] * 0.6, wall, 10, (60, 60, 140), 260)
            continue
        polys += box(x, y, b['floor'], b['size'][0], b['size'][1], b['height'] * 0.65, wall, roof)
    # pyramid
    pa = P.PYRAMID
    half = pa['base'] / 2
    cx, cy = pa['at']
    z0 = pa['floor']
    corners = [(cx - half, cy - half, z0), (cx + half, cy - half, z0), (cx + half, cy + half, z0),
               (cx - half, cy + half, z0)]
    apex = (cx, cy, z0 + pa['height'])
    for i in range(4):
        polys.append(([corners[i], corners[(i + 1) % 4], apex], (210, 196, 160)))
    # well
    polys += cylinder(P.WELL[0], P.WELL[1], 0, 96, 110, (170, 170, 175), 8)
    # orchard trees, Stumpy, Lacey (crude blobs, composition only)
    for t in P.ORCHARD_TREES:
        polys += cylinder(t[0], t[1], 0, 40, 140, (90, 70, 50), 6, (60, 110, 50), 320)
    polys += cylinder(P.STUMPY[0], P.STUMPY[1], 0, 90, 260, (110, 80, 50), 6, (70, 130, 60), 420)
    polys += box(P.LACEY[0], P.LACEY[1], 0, 200, 70, 150, (255, 255, 255))
    # summit backdrop
    sx, sy = P.SUMMIT['at']
    R, H, cr = P.SUMMIT['radius'], P.SUMMIT['height'], P.SUMMIT['crater']
    ring = [(sx + R * math.cos(2 * math.pi * i / 20), sy + R * math.sin(2 * math.pi * i / 20), 1800) for i in range(20)]
    top = [(sx + cr * math.cos(2 * math.pi * i / 20), sy + cr * math.sin(2 * math.pi * i / 20), H) for i in range(20)]
    for i in range(20):
        polys.append(([ring[i], ring[(i + 1) % 20], top[(i + 1) % 20], top[i]], (40, 36, 38)))
    polys.append(([(sx - 160, sy, H), (sx + 160, sy, H), (sx + 1500, sy + 400, H + 2600),
                   (sx + 900, sy + 400, H + 2700)], (170, 166, 164)))
    return polys


def label_points():
    b = {x['id']: x for x in P.BUILDINGS}

    def top(i, extra=150):
        x, y = b[i]['at']
        return (x, y, b[i]['floor'] + b[i]['height'] + extra)
    sx, sy = P.SUMMIT['at']
    summit = (sx, sy, P.SUMMIT['height'] + 200)
    fall = (P.FALL['lip'][0] - 200, P.FALL['lip'][1], P.FALL['z'] * 0.6)
    pyramid = (P.PYRAMID['at'][0], P.PYRAMID['at'][1], P.PYRAMID['floor'] + P.PYRAMID['height'] + 150)
    return {
        'arrival': [(top('building:tavern_xanadu'), 'tavern'), (top('building:arm_and_hammer'), 'smithy'),
                    ((0, 0, 200), 'well'), (pyramid, 'pyramid'), (top('building:guild_light'), 'guild tower'),
                    (fall, 'white fall'), (summit, 'Firestone summit'), (top('building:benedict'), 'house')],
        'signature': [((0, 0, 200), 'well'), ((P.LACEY[0], P.LACEY[1], 220), 'unicorn'),
                      (top('building:guild_light'), 'guild tower'), (fall, 'white fall'), (pyramid, 'pyramid'),
                      (top('building:pilar'), 'pavilion'), (summit, 'Firestone summit'),
                      (top('building:an_education'), 'school'), (top('building:sally'), 'round hut'),
                      ((P.POOL['at'][0], P.POOL['at'][1], 60), 'pool')],
    }


def blockout(name):
    c = P.CAMERAS[name]
    cam = Cam(c['at'], c['z'], c['yaw'], c['pitch'], c['fov'])
    img = Image.new('RGB', (cam.w, cam.h))
    d = ImageDraw.Draw(img)
    for i in range(cam.h):
        t = i / cam.h
        d.line([(0, i), (cam.w, i)], fill=(int(120 + 80 * t), int(170 + 50 * t), int(225 + 20 * t)))
    items = []
    for poly, col in scene():
        cp = clip_near([cam.cam(v) for v in poly])
        if len(cp) < 3:
            continue
        depth = sum(v[2] for v in cp) / len(cp)
        items.append((depth, [cam.proj(v) for v in cp], shade(col, normal(poly))))
    items.sort(key=lambda t: -t[0])
    for _, pts, col in items:
        d.polygon(pts, fill=col)
    f = font(18, True)
    for pos, text in label_points()[name]:
        cp = cam.cam(pos)
        if cp[2] < 64:
            continue
        x, y = cam.proj(cp)
        if 0 <= x < cam.w and 0 <= y < cam.h:
            d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=(30, 60, 255), width=3)
            d.text((x + 10, y - 22), text, font=f, fill=(30, 60, 255))
    img.save(HERE / f'blockout_{name}.png')


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    f = figures()
    (HERE / 'figures.json').write_text(json.dumps(f, indent=1))
    plan()
    for name in P.CAMERAS:
        blockout(name)
    print(json.dumps(f, indent=1))


if __name__ == '__main__':
    main()
