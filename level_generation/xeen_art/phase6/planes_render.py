#!/usr/bin/env python3
"""The planes' review drawings and measures (A6's planes sub-agent, 2026-11-21), from planes_design.py.

    planes_render.py p1 [p2 ...] [--png]     writes level_generation/xeen_art/phase6/planes/<key>/:
      plan_<key>.svg         the to-scale plan: spaces, links, the walk, places, groups, hazards, the camera
      plan_<key>.png         the same through headless Chrome (--png; one Chrome at a time, own profile, deleted)
      blockout_<key>.png     a crude perspective of the arrival camera (Codex's composition reference)
      measure.json           the figures (planes_geom.Plane.figures)

Nothing here is read by the game or the studio.
"""
import argparse
import json
import math
import shutil
import subprocess
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import planes_design as D
import planes_geom as G

OUT = Path(__file__).resolve().parent / 'planes'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
COMPASS = {'n': (0, 1), 'e': (1, 0), 's': (0, -1), 'w': (-1, 0), 'ne': (0.7071, 0.7071), 'nw': (-0.7071, 0.7071),
           'se': (0.7071, -0.7071), 'sw': (-0.7071, -0.7071)}

STYLE = {
    'fire': dict(ground='#5a1a0c', ground2='#c8461a', rim='#1f1714', crust='#4a423d', crust_edge='#2a2420',
                 arena='#26201f', hall='#3b302c', link='#57504a', glass='#1c1818', label='#fbe9d8', grid='#ffffff',
                 walk='#ffe27a', hazard='#ffb020', text='#2b1d17'),
    'air': dict(ground='#bcd3ee', ground2='#e5eef9', rim=None, crust='#f6f6f2', crust_edge='#a9b4c4',
                arena='#e9ecef', hall='#fbf6e6', link='#d8cfbf', glass='#d8cfbf', label='#16243a', grid='#5b6b85',
                walk='#c0392b', hazard='#6a40c8', text='#16243a'),
    'earth': dict(rim='#3b3026', crust='#a8957a', crust_edge='#5a4a3a', arena='#7d766e', hall='#6c6258',
                  link='#c2ae90', glass='#8a7a66', label='#fff4e0', grid='#ffffff', walk='#ffe27a', hazard='#e8a020',
                  text='#2a2018'),
    'water': dict(rim='#40565c', crust='#e6ece6', crust_edge='#6f8c8c', arena='#d4dedb', hall='#c9dcd6',
                  link='#f2efe4', glass='#bfe6ee', label='#0f2a30', grid='#ffffff', walk='#c0392b', hazard='#3a70d8',
                  text='#0f2a30'),
}
LOW_FILL = {'lava': ('#ff8a2a', '#d9481a', '#8c2310'), 'scree': ('#7a6a58', '#655646', '#4e4236'),
            'sea': ('#3aa0a8', '#2a8090', '#1d5e6e')}


# ------------------------------------------------------------------------------------------------ the plan (SVG)
def plan_svg(pl, f):
    d = pl.d
    st = STYLE[d['element']]
    halo = st['text'] if d['element'] in ('fire', 'earth') else '#fff'
    size = 1084
    margin = 24
    span = 2 * pl.half[0]
    k = (size - 2 * margin) / span

    def P(pt):
        return (margin + (pt[0] + pl.half[0]) * k, margin + (pl.half[1] - pt[1]) * k)

    def pts(poly):
        return ' '.join(f'{x:.1f},{y:.1f}' for x, y in (P(p) for p in poly))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
         'font-family="DejaVu Sans, sans-serif">']
    lf = LOW_FILL[d['low']['kind']] if 'low' in d else LOW_FILL['lava']
    o.append(f'<defs><radialGradient id="lava" cx="50%" cy="50%" r="60%"><stop offset="0" stop-color="{lf[0]}"/>'
             f'<stop offset="0.6" stop-color="{lf[1]}"/><stop offset="1" stop-color="{lf[2]}"/></radialGradient>'
             '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9ec0e8"/>'
             '<stop offset="1" stop-color="#d8e6f6"/></linearGradient>'
             '<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<line x1="0" y1="0" x2="0" y2="8" stroke="#2e8b57" stroke-width="2"/></pattern></defs>')
    x0, y0 = P((-pl.half[0], pl.half[1]))
    x1, y1 = P((pl.half[0], -pl.half[1]))
    if 'low' in d:
        o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{st["rim"]}"/>')
        o.append(f'<polygon points="{pts(pl.rim_poly())}" fill="url(#lava)" stroke="#000" stroke-width="2"/>')
    else:
        o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="url(#sky)"/>')
    for c in range(0, d['room'][0] + 1, 2):
        gx = margin + c * 512 * k
        o.append(f'<line x1="{gx:.1f}" y1="{y0}" x2="{gx:.1f}" y2="{y1}" stroke="{st["grid"]}" stroke-opacity=".12"/>')
        o.append(f'<line x1="{x0}" y1="{gx:.1f}" x2="{x1}" y2="{gx:.1f}" stroke="{st["grid"]}" stroke-opacity=".12"/>')
    # shadows (air) and the floors
    if d['element'] == 'air':
        for poly in pl.polys.values():
            o.append(f'<polygon points="{pts([(x + 140, y - 180) for x, y in poly])}" fill="#5f7390" '
                     'fill-opacity=".28"/>')
    ribbons = pl.ribbons()
    for l in d['links']:
        fill = st['glass'] if l['style'] in ('glass', 'stair') else st['link']
        dash = ' stroke-dasharray="7 4"' if l.get('gate') else ''
        o.append(f'<polygon points="{pts(ribbons[l["id"]])}" fill="{fill}" stroke="{st["crust_edge"]}" '
                 f'stroke-width="1.5"{dash}><title>{escape(l["id"])}: {f["links"][l["id"]]["length"]:,} long, '
                 f'{l["width"]} wide, rise {f["links"][l["id"]]["rise"]}</title></polygon>')
    for s in d['spaces']:
        fill = {'arena': st['arena'], 'hall': st['hall']}.get(s['kind'], st['crust'])
        o.append(f'<polygon points="{pts(pl.polys[s["id"]])}" fill="{fill}" stroke="{st["crust_edge"]}" '
                 f'stroke-width="2"><title>{escape(s["name"])} (+{s["floor"]})</title></polygon>')
        if s.get('safe'):
            o.append(f'<polygon points="{pts(pl.polys[s["id"]])}" fill="url(#hatch)" fill-opacity=".35"/>')
    # the walk with ticks
    o.append(f'<polyline points="{pts(d["walk"])}" fill="none" stroke="{st["walk"]}" stroke-width="3" '
             'stroke-dasharray="10 6" stroke-linejoin="round"/>')
    segs, total = pl.walk_segments()
    dd = 2048
    while dd < total:
        for a, b, start, n in segs:
            if start <= dd <= start + n:
                t = (dd - start) / n
                x, y = P((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{st["walk"]}" stroke="#000" '
                         'stroke-width=".8"/>')
                o.append(f'<text x="{x + 5:.1f}" y="{y - 4:.1f}" font-size="10" fill="{st["label"]}">'
                         f'{dd:,}</text>')
                break
        dd += 2048
    # hazards
    for c in d['hazard']['cells']:
        x, y = P(c)
        o.append(f'<path d="M{x - 7:.1f},{y:.1f} L{x - 2:.1f},{y - 2:.1f} L{x:.1f},{y - 8:.1f} L{x + 2:.1f},'
                 f'{y - 2:.1f} L{x + 7:.1f},{y:.1f} L{x + 2:.1f},{y + 2:.1f} L{x:.1f},{y + 8:.1f} L{x - 2:.1f},'
                 f'{y + 2:.1f} Z" fill="{st["hazard"]}" stroke="#000" stroke-width=".7"><title>'
                 f'{escape(d["hazard"]["kind"])} cell</title></path>')
    # camera wedge
    cam = d['camera']
    yaw, half = math.radians(cam['yaw_deg']), math.radians(cam['fov'] / 2)
    reach = 3800
    wedge = [cam['at']] + [(cam['at'][0] + reach * math.cos(a), cam['at'][1] + reach * math.sin(a))
                           for a in (yaw - half, yaw + half)]
    o.append(f'<polygon points="{pts(wedge)}" fill="#1f6fd1" fill-opacity=".18" stroke="#1f6fd1" '
             'stroke-opacity=".7"/>')
    # groups
    for g in d['groups']:
        x, y = P(g['at'])
        row = D.ROWS[g['row']]
        r = 9 + 2 * g['count']
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#d0302a" fill-opacity=".85" stroke="#fff" '
                 f'stroke-width="1.5"><title>{escape(g["id"])}: {g["count"]} x {escape(row["actor"])}</title>'
                 '</circle>')
        o.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" font-size="11" font-weight="bold" text-anchor="middle" '
                 f'fill="#fff">{g["count"]}x{row["level"]}</text>')
    x, y = P(d['test_at'])
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="none" stroke="#7a0f0a" stroke-width="3" '
             'stroke-dasharray="5 3"/>')
    o.append(f'<text x="{x:.1f}" y="{y + 36:.1f}" font-size="11" font-weight="bold" text-anchor="middle" '
             f'fill="{st["label"]}">test: 75 + 2x70 (rise on accept)</text>')
    # places
    for p in d['places']:
        x, y = P(p['at'])
        kind = p['kind']
        t = f'<title>{escape(p["id"])}: {escape(p["text"])}</title>'
        if kind == 'arrival':
            o.append(f'<rect x="{x - 8:.1f}" y="{y - 8:.1f}" width="16" height="16" fill="#0b6b3a" stroke="#fff" '
                     f'stroke-width="2">{t}</rect>')
            fx, fy = COMPASS[p['face']]
            o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + fx * 26:.1f}" y2="{y - fy * 26:.1f}" '
                     'stroke="#0b6b3a" stroke-width="3"/>')
        elif kind in ('exit', 'dais'):
            fill = '#111' if kind == 'exit' else '#777'
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{fill}" stroke="#fff" stroke-width="2">{t}'
                     '</circle>')
            o.append(f'<path d="M{x - 5:.1f},{y + 2:.1f} L{x:.1f},{y - 5:.1f} L{x + 5:.1f},{y + 2:.1f}" '
                     'stroke="#fff" stroke-width="2" fill="none"/>')
        elif kind == 'statue':
            o.append(f'<polygon points="{star(x, y, 11, 5)}" fill="#7a1f6a" stroke="#fff" stroke-width="1.5">{t}'
                     '</polygon>')
        elif kind == 'pedestal':
            o.append(f'<polygon points="{x:.1f},{y - 11:.1f} {x + 10:.1f},{y + 8:.1f} {x - 10:.1f},{y + 8:.1f}" '
                     f'fill="#e0a800" stroke="#000" stroke-width="1.5">{t}</polygon>')
        elif kind == 'sleeper':
            o.append(f'<rect x="{x - 14:.1f}" y="{y - 6:.1f}" width="28" height="12" rx="5" fill="#1d5fa8" '
                     f'stroke="#fff" stroke-width="2">{t}</rect>')
        elif kind == 'chest':
            o.append(f'<polygon points="{x:.1f},{y - 9:.1f} {x + 9:.1f},{y:.1f} {x:.1f},{y + 9:.1f} {x - 9:.1f},'
                     f'{y:.1f}" fill="#b8860b" stroke="#000" stroke-width="1.5">{t}</polygon>')
        elif kind == 'device':
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#9b59b6" stroke="#fff" stroke-width="1.5">{t}'
                     '</circle>')
        elif kind == 'gate':
            fx, fy = COMPASS[p['face']]
            o.append(f'<line x1="{x - fy * 14:.1f}" y1="{y - fx * 14:.1f}" x2="{x + fy * 14:.1f}" '
                     f'y2="{y + fx * 14:.1f}" stroke="#000" stroke-width="6">{t}</line>')
        elif kind == 'landmark':
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#c06000" stroke="#fff" stroke-width="1.2">{t}'
                     '</circle>')
    # labels
    for s in d['spaces']:
        x, y = P((s['at'][0], s['at'][1] + s['extent'][1] / 2 + 160))
        o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" font-style="italic" font-weight="bold" '
                 f'text-anchor="middle" fill="{st["label"]}" stroke="{halo}"'
                 f' stroke-width="3" paint-order="stroke">{escape(s["name"])} {s["floor"]:+d}</text>')
    short = {'entrance:d7_fall': 'arrival (D7 drop)', 'exit:way_up': 'way up (to D7)', 'poi:statue': 'statue, plaque',
             'poi:test': "'Accept the test?'", 'gate:sleeper': "sleeper's gate", 'poi:sleeper': 'the sleeper',
             'poi:test_chest': "test's chest", 'exit:dais': 'return dais (to D7)'}
    for p in d['places']:
        label = short.get(p['id'])
        if not label:
            if p['kind'] in ('device', 'chest'):
                label = p['id'].split(':')[1].replace('_', ' ')
            else:
                continue
        x, y = P(p['at'])
        o.append(f'<text x="{x + 12:.1f}" y="{y + 16:.1f}" font-size="11" fill="{st["label"]}" '
                 f'stroke="{halo}" stroke-width="2.5" '
                 f'paint-order="stroke">{escape(label)}</text>')
    # scale bar and title
    bx, by = P((-pl.half[0] + 500, -pl.half[1] + 420))
    o.append(f'<rect x="{bx - 6}" y="{by - 16}" width="{2048 * k + 130}" height="26" fill="#000" fill-opacity=".55"/>')
    o.append(f'<line x1="{bx}" y1="{by}" x2="{bx + 2048 * k}" y2="{by}" stroke="#fff" stroke-width="4"/>')
    o.append(f'<text x="{bx + 2048 * k + 8}" y="{by + 4}" font-size="12" fill="#fff">2,048 (4 cells)</text>')
    tx, ty = P((-pl.half[0] + 420, pl.half[1] - 360))
    o.append(f'<text x="{tx}" y="{ty}" font-size="17" font-weight="bold" fill="{st["label"]}" '
             f'stroke="{halo}" stroke-width="3" paint-order="stroke">'
             f'{escape(d["code"])} {escape(d["name"])}: north up, {d["room"][0]} x {d["room"][1]} cells, '
             f'walk {f["walk_length"]:,}</text>')
    o.append('</svg>')
    return '\n'.join(o)


def star(x, y, r, n):
    out = []
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * 0.45
        a = math.pi / 2 + math.pi * i / n
        out.append(f'{x + rr * math.cos(a):.1f},{y - rr * math.sin(a):.1f}')
    return ' '.join(out)


def chrome_png(svg_path, png_path, size=1084):
    profile = svg_path.parent / '.chrome'
    page = svg_path.parent / f'_{svg_path.stem}.html'
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
                    f'img{{display:block;width:{size}px;height:{size}px}}</style></head><body>'
                    f'<img src="{svg_path.name}"></body></html>')
    try:
        subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox',
                        f'--user-data-dir={profile}', '--hide-scrollbars', f'--window-size={size},{size}',
                        '--virtual-time-budget=4000', f'--screenshot={png_path}', page.as_uri()],
                       check=True, capture_output=True, timeout=180)
    finally:
        page.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ blockout
class Blockout:
    def __init__(self, pl, W=1536, H=1024):
        self.pl, self.W, self.H = pl, W, H
        c = pl.d['camera']
        self.cx, self.cy = c['at']
        self.cz = (pl.floor_at(c['at']) or 0) + c['eye']
        yaw, pitch = math.radians(c['yaw_deg']), math.radians(c['pitch_deg'])
        self.pitch = pitch
        self.fwd = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
        self.right = (math.sin(yaw), -math.cos(yaw), 0.0)
        f, r = self.fwd, self.right
        up = (f[1] * r[2] - f[2] * r[1], f[2] * r[0] - f[0] * r[2], f[0] * r[1] - f[1] * r[0])
        self.up = up if up[2] > 0 else tuple(-v for v in up)
        self.fpx = (W / 2) / math.tan(math.radians(c['fov']) / 2)
        self.faces = []
        self.near = 30.0

    def cam(self, p):
        d = (p[0] - self.cx, p[1] - self.cy, p[2] - self.cz)
        return (sum(d[i] * self.right[i] for i in range(3)), sum(d[i] * self.up[i] for i in range(3)),
                sum(d[i] * self.fwd[i] for i in range(3)))

    def proj(self, c3):
        return (self.W / 2 + c3[0] / c3[2] * self.fpx, self.H / 2 - c3[1] / c3[2] * self.fpx)

    def add(self, poly3, colour, bias=0.0, normal=None):
        if normal is not None:
            p = poly3[0]
            if sum(normal[i] * ((self.cx, self.cy, self.cz)[i] - p[i]) for i in range(3)) <= 0:
                return
        cs = [self.cam(p) for p in poly3]
        out = []
        for i in range(len(cs)):
            a, b = cs[i], cs[(i + 1) % len(cs)]
            if a[2] >= self.near:
                out.append(a)
            if (a[2] >= self.near) != (b[2] >= self.near):
                t = (self.near - a[2]) / (b[2] - a[2])
                out.append(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
        if len(out) < 3:
            return
        depth = sum(c[2] for c in out) / len(out) + bias
        self.faces.append((depth, [self.proj(c) for c in out], colour))

    def prism(self, poly, z0, z1, top, side, bias=0.0):
        n = len(poly)
        area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
        sgn = 1.0 if area > 0 else -1.0
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            normal = (sgn * (b[1] - a[1]), -sgn * (b[0] - a[0]), 0.0)
            shade = 0.75 + 0.25 * abs(normal[0]) / (math.hypot(*normal[:2]) or 1)
            col = tuple(int(c * shade) for c in side)
            self.add([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], col, bias, normal)
        self.add([(x, y, z1) for x, y in poly], top, bias, (0.0, 0.0, 1.0))

    def hang(self, poly, centre, z, depth, colour):
        """An island's underside: a cone from the outline down to a point."""
        tip = (centre[0], centre[1], z - depth)
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            mid = ((a[0] + b[0]) / 2 - centre[0], (a[1] + b[1]) / 2 - centre[1])
            self.add([(a[0], a[1], z), (b[0], b[1], z), tip], colour, 0.0, (mid[0], mid[1], -0.3 * math.hypot(*mid)))

    def render(self, sky_top, sky_bottom, below):
        img = Image.new('RGB', (self.W, self.H))
        dr = ImageDraw.Draw(img)
        hz = self.H / 2 + math.tan(self.pitch) * self.fpx
        for y in range(self.H):
            if y < hz:
                t = y / max(hz, 1)
                col = tuple(int(sky_top[i] + (sky_bottom[i] - sky_top[i]) * t) for i in range(3))
            else:
                t = min(1.0, (y - hz) / max(self.H - hz, 1))
                col = tuple(int(sky_bottom[i] + (below[i] - sky_bottom[i]) * t) for i in range(3))
            dr.line([(0, y), (self.W, y)], fill=col)
        for _, pts, colour in sorted(self.faces, key=lambda f: -f[0]):
            dr.polygon(pts, fill=colour)
        return img, dr


def ngon(c, r, n=10, phase=0.0):
    return [(c[0] + r * math.cos(phase + 2 * math.pi * i / n), c[1] + r * math.sin(phase + 2 * math.pi * i / n))
            for i in range(n)]


def oriented(at, face, w, dep):
    fx, fy = COMPASS[face]
    rx, ry = fy, -fx
    return [(at[0] + rx * w / 2 + fx * dep / 2, at[1] + ry * w / 2 + fy * dep / 2),
            (at[0] - rx * w / 2 + fx * dep / 2, at[1] - ry * w / 2 + fy * dep / 2),
            (at[0] - rx * w / 2 - fx * dep / 2, at[1] - ry * w / 2 - fy * dep / 2),
            (at[0] + rx * w / 2 - fx * dep / 2, at[1] + ry * w / 2 - fy * dep / 2)]


def pieces_fire(pl, b):
    ar = pl.space['room:arena']
    for i, (x, y) in enumerate(ngon(ar['at'], 1300, 16)):
        if i % 4 == 3:
            continue
        b.prism(ngon((x, y), 120, 6), ar['floor'], ar['floor'] + 420, (24, 20, 22), (30, 24, 26))
    b.prism(ngon(ar['at'], 420, 12), ar['floor'] - 4, ar['floor'] + 2, (255, 110, 30), (220, 80, 20), 50)
    sp = pl.space['room:spires']
    for i, (x, y) in enumerate(ngon(sp['at'], 900, 7, 0.4)):
        h = 520 + 220 * ((i * 37) % 5)
        b.prism(ngon((x, y), 150 + 30 * (i % 3), 6), sp['floor'], sp['floor'] + h, (54, 48, 46), (44, 40, 38))
    ch = pl.space['room:chamber']
    spire = (ch['at'][0] - 1000, ch['at'][1] + 900)
    b.prism(ngon(spire, 900, 8), ch['floor'], ch['floor'] + 3200, (38, 32, 30), (46, 38, 36))
    b.prism(ngon((ch['at'][0] + 300, ch['at'][1] - 100), 1000, 10), ch['floor'] + 760, ch['floor'] + 860,
            (30, 26, 26), (36, 30, 30))
    for x, y in ngon((ch['at'][0] + 300, ch['at'][1] - 100), 1000, 10):
        b.prism(ngon((x, y), 70, 5), ch['floor'], ch['floor'] + 760, (30, 26, 26), (36, 30, 30))


def pieces_air(pl, b):
    ar = pl.space['room:arena']
    for x, y in ngon(ar['at'], 1350, 12):
        b.prism(oriented((x, y), 'n', 180, 120), ar['floor'], ar['floor'] + 640, (200, 200, 196), (180, 182, 184))
    stn = pl.space['room:stones']
    for x, y in ngon(pl.place['poi:singing_stones']['at'], 640, 8):
        b.prism(ngon((x, y), 90, 6), stn['floor'], stn['floor'] + 520, (196, 190, 176), (170, 166, 156))
    ch = pl.space['room:chamber']
    dome = (ch['at'][0] + 300, ch['at'][1] + 200)
    for x, y in ngon(dome, 900, 8):
        b.prism(ngon((x, y), 60, 5), ch['floor'], ch['floor'] + 600, (246, 240, 226), (230, 224, 210))
    for i, (r, h) in enumerate(((960, 90), (820, 90), (640, 90), (420, 80), (200, 60))):
        z0 = ch['floor'] + 600 + sum(x[1] for x in ((960, 90), (820, 90), (640, 90), (420, 80))[:i])
        b.prism(ngon(dome, r, 12), z0, z0 + h, (250, 246, 232), (236, 230, 214))


def pieces_earth(pl, b):
    ar = pl.space['room:arena']
    for x, y in ngon(ar['at'], 1350, 12):
        b.prism(oriented((x, y), 'n', 220, 160), ar['floor'], ar['floor'] + 820, (96, 90, 84), (80, 74, 70))
    pi = pl.space['room:pillars']
    for i, (x, y) in enumerate(ngon(pi['at'], 820, 9, 0.3)):
        b.prism(ngon((x, y), 110, 6), pi['floor'], pi['floor'] + 700 + 260 * (i % 3), (120, 106, 90), (100, 88, 74))
    q = pl.space['room:quarry']
    for i, (x, y) in enumerate(ngon(q['at'], 700, 5, 0.7)):
        b.prism(oriented((x, y), 'n', 300, 300), q['floor'], q['floor'] + 300 + 120 * (i % 2), (150, 136, 116),
                (128, 116, 98))
    ch = pl.space['room:chamber']
    b.prism(ngon((ch['at'][0], ch['at'][1] - 600), 1500, 10), ch['floor'] + 900, ch['floor'] + 1300, (70, 60, 50),
            (60, 52, 44))


def pieces_water(pl, b):
    ar = pl.space['room:arena']
    for i, (x, y) in enumerate(ngon(ar['at'], 1350, 14)):
        h = 300 + 400 * ((i * 5) % 3)
        b.prism(ngon((x, y), 90, 8), ar['floor'], ar['floor'] + h, (214, 220, 212), (190, 200, 194))
    b.prism(ngon(ar['at'], 500, 14), ar['floor'] - 4, ar['floor'] + 2, (30, 100, 120), (20, 80, 100), 50)
    w = pl.space['room:wreck']
    b.prism(oriented((w['at'][0] + 200, w['at'][1] - 200), 'e', 600, 1800), w['floor'], w['floor'] + 360,
            (110, 80, 50), (90, 64, 40))
    for dx in (-500, 300):
        b.prism(ngon((w['at'][0] + 200 + dx, w['at'][1] - 200), 30, 5), w['floor'] + 360, w['floor'] + 1500,
                (90, 70, 50), (80, 60, 44))
    ch = pl.space['room:chamber']
    b.prism(ngon((ch['at'][0] - 300, ch['at'][1] - 300), 1300, 10), ch['floor'] + 800, ch['floor'] + 1100,
            (80, 96, 100), (70, 86, 90))
    for x, y in ngon((ch['at'][0] - 300, ch['at'][1] - 300), 1300, 5):
        b.prism(ngon((x, y), 160, 6), ch['floor'] - 200, ch['floor'] + 800, (80, 96, 100), (70, 86, 90))


PALETTE = {
    'fire': dict(top=(70, 64, 60), side=(44, 38, 36), under=(60, 52, 48), arena=(36, 32, 34), hall=(44, 38, 40),
                 link=(60, 55, 50), low=(226, 86, 28), rim=((40, 32, 30), (52, 42, 38)), plinth=(30, 28, 30),
                 statue=(190, 60, 30), statue_side=(160, 50, 26), exit=((255, 190, 120), (250, 170, 100)),
                 sleeper=((120, 40, 30), (90, 30, 20)), device=((255, 120, 40), (200, 90, 30)),
                 sky=((40, 8, 4), (150, 46, 18), (120, 40, 16))),
    'air': dict(top=(246, 245, 240), side=(205, 210, 220), under=(176, 186, 204), arena=(232, 230, 222),
                hall=(250, 244, 226), link=(214, 204, 186), low=None, rim=None, plinth=(210, 206, 196),
                statue=(236, 236, 232), statue_side=(220, 220, 216), exit=((236, 244, 252), (226, 236, 248)),
                sleeper=((150, 190, 230), (120, 160, 210)), device=((200, 196, 230), (170, 166, 210)),
                sky=((60, 120, 200), (214, 228, 244), (150, 186, 226))),
    'earth': dict(top=(132, 116, 96), side=(96, 82, 68), under=(80, 68, 56), arena=(110, 104, 98),
                  hall=(92, 84, 76), link=(140, 124, 104), low=(88, 74, 60), rim=((70, 60, 50), (84, 72, 60)),
                  plinth=(90, 86, 82), statue=(130, 120, 110), statue_side=(110, 102, 94),
                  exit=((226, 206, 170), (210, 190, 156)), sleeper=((120, 100, 70), (96, 80, 56)),
                  device=((150, 110, 190), (120, 86, 160)), sky=((40, 30, 24), (120, 92, 66), (90, 70, 52))),
    'water': dict(top=(206, 214, 206), side=(150, 168, 164), under=(120, 140, 140), arena=(196, 206, 200),
                  hall=(190, 204, 196), link=(220, 224, 214), low=(40, 120, 128), rim=((70, 86, 92), (84, 100, 104)),
                  plinth=(170, 180, 176), statue=(90, 150, 130), statue_side=(70, 126, 110),
                  exit=((200, 236, 240), (180, 220, 228)), sleeper=((60, 150, 170), (40, 120, 140)),
                  device=((90, 170, 190), (70, 140, 160)), sky=((40, 110, 110), (170, 214, 206), (120, 170, 170))),
}


def blockout(pl, out):
    d = pl.d
    b = Blockout(pl)
    el = d['element']
    pal = PALETTE[el]
    basin = 'low' in d
    if basin:
        low = d['low']['level']
        rim = pl.rim_poly(48)
        b.add([(x, y, low) for x, y in rim], pal['low'], 4000, (0.0, 0.0, 1.0))
        # the basin's wall (crater, bowl, sea stacks): an outward ring of tall faces
        for i in range(len(rim)):
            a, c = rim[i], rim[(i + 1) % len(rim)]
            h = d['rim']['height'] + 500 * math.sin(i * 1.7) + 300 * math.cos(i * 0.9)
            if el == 'water' and i % 3:
                continue                    # stacks and arches with open sea between, not a wall
            lean = 1.15 if el != 'earth' else 1.06
            b.add([(a[0], a[1], low), (c[0], c[1], low), (c[0] * lean, c[1] * lean, h), (a[0] * lean, a[1] * lean, h)],
                  pal['rim'][i % 2], 0, None)
    for s in d['spaces']:
        poly = pl.polys[s['id']]
        top = {'arena': pal['arena'], 'hall': pal['hall']}.get(s['kind'], pal['top'])
        if basin:
            b.prism(poly, d['low']['level'] - 10, s['floor'], top, pal['side'])
        else:
            b.prism(poly, s['floor'] - 256, s['floor'], top, pal['side'])
            b.hang(poly, s['at'], s['floor'] - 256, 0.45 * max(s['extent']), pal['under'])
    for l in d['links']:
        p, q = pl.link_ends(l)
        za, zb = pl.space[l['a']]['floor'], pl.space[l['b']]['floor']
        cap = G.capsule(p, q, l['width'])
        col = (30, 26, 28) if l['style'] == 'glass' else pal['link']
        zl = [za + 2, zb + 2, zb + 2, za + 2]
        b.add([(cap[i][0], cap[i][1], zl[i]) for i in range(4)], col, 30)
        if el != 'fire':
            under = d['low']['level'] if basin else None
            za0, zb0 = (under, under) if basin else (za - 60, zb - 60)
            b.add([(cap[3][0], cap[3][1], za0), (cap[2][0], cap[2][1], zb0), (cap[1][0], cap[1][1], zb0),
                   (cap[0][0], cap[0][1], za0)], tuple(int(c * 0.8) for c in pal['link']), 40)
        if l['style'] == 'veil':
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            b.prism(oriented(m, 'n', l['width'], 40), za, za + 700, (190, 230, 236), (170, 214, 224), -100)
    place = pl.place
    for p in d['places']:
        at = p['at']
        z = pl.floor_at(at) or 0
        k = p['kind']
        if k == 'statue':
            b.prism(oriented(at, p['face'], 256, 256), z, z + 160, pal['plinth'], pal['plinth'])
            b.prism(oriented(at, p['face'], 128 if el != 'earth' else 220, 128 if el != 'earth' else 200), z + 160,
                    z + 700, pal['statue'], pal['statue_side'])
        elif k == 'exit':
            b.prism(ngon(at, 150, 8), z, z + 2400, *pal['exit'], -200)
        elif k == 'pedestal':
            b.prism(oriented(at, p['face'], 96, 96), z, z + 110, (200, 160, 60), (170, 130, 40))
        elif k == 'sleeper':
            b.prism(oriented(at, p['face'], 320, 160), z, z + 96, *pal['sleeper'])
        elif k == 'chest':
            b.prism(oriented(at, p['face'], 96, 64), z, z + 64, (160, 110, 40), (140, 90, 30))
        elif k == 'device':
            b.prism(ngon(at, 96, 8), z, z + 96, *pal['device'])
    {'fire': pieces_fire, 'air': pieces_air, 'earth': pieces_earth, 'water': pieces_water}[el](pl, b)
    img, dr = b.render(*pal['sky'])
    font = ImageFont.truetype(FONT, 18)
    ann = [('the statue, plaque', place['poi:statue']['at'], 900),
           ("'Accept the test?' (the arena)", d['test_at'], 900),
           ("the sleeper's chamber", pl.space['room:chamber']['at'], 1500 if el == 'fire' else 1700)]
    for text, at, h in ann:
        c3 = b.cam((at[0], at[1], (pl.floor_at(at) or 0) + h))
        if c3[2] > b.near:
            x, y = b.proj(c3)
            if 0 < x < b.W and 0 < y < b.H:
                dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(40, 90, 255), width=2)
                dr.text((x + 8, y - 22), text, font=font, fill=(40, 90, 255))
    img.save(out)


# ------------------------------------------------------------------------------------------------ main
def run(key, png):
    pl = G.Plane(key)
    folder = OUT / key
    folder.mkdir(parents=True, exist_ok=True)
    f = pl.figures()
    (folder / 'measure.json').write_text(json.dumps(f, indent=1, default=float) + '\n')
    svg = folder / f'plan_{key}.svg'
    svg.write_text(plan_svg(pl, f))
    blockout(pl, folder / f'blockout_{key}.png')
    if png:
        chrome_png(svg, folder / f'plan_{key}.png')
    print(key, 'walk', f['walk_length'], 'area', f['walkable_area_m'], 'pois', f['poi_census'], 'xp/member',
          f['kill_xp_per_member'], 'first fight', f['first_fight']['straight'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('keys', nargs='+')
    parser.add_argument('--png', action='store_true')
    args = parser.parse_args()
    for key in args.keys:
        run(key, args.png)


if __name__ == '__main__':
    main()
