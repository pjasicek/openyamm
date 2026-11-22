#!/usr/bin/env python3
"""D7's MU-3 plan drawing, MU-4 blockouts and measured figures, from d7_design.py (A6 sub-agent, 2026-11-21).

    d7_render.py      writes into level_generation/xeen_art/phase6/d7/:
      plan_d7.png, plan_d7.svg           the to-scale plan (12 px a cell), plan_d7_2x.png for crops
      plan_olympus.png, plan_olympus.svg Olympus at 48 px a cell
      blockout_arrival.png, blockout_signature.png   crude perspectives (Codex's composition references)
      measure.json                       the measured figures (board, NOTES, plan totals)

Nothing here is read by the game or the studio. Run under a memory cap (output/studio_cal/d7/run.sh).
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import d7_design as D
import d7_geom as G

OUT = Path(__file__).resolve().parent / 'd7'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONTI = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'

ELEMENT = {'fire': (215, 70, 40), 'air': (120, 170, 220), 'earth': (130, 110, 80), 'water': (40, 90, 190)}
ACTOR = {11562: (205, 125, 40), 11594: (95, 100, 125), 11650: (60, 150, 150), 11592: (150, 150, 170),
         11654: (150, 20, 30)}
KIND_FILL = {'rest': (250, 248, 240), 'corner': (250, 246, 236), 'road': (238, 240, 246), 'post': (248, 244, 228),
             'hatch': (236, 236, 236), 'lone': (240, 242, 248), 'town': (255, 252, 240), 'roost': (226, 222, 222),
             'lake': (238, 244, 250), 'cap': (250, 244, 220)}
FALL_TINT = {'D6': (120, 60, 40), 'D5': (190, 150, 70), 'D4': (60, 110, 150), 'D1': (90, 130, 80),
             'D2': (60, 140, 90), 'D3': (190, 140, 90)}
POINT_STYLE = {'corner': ((200, 40, 40), 'star'), 'toll': ((150, 30, 120), 'square'), 'merchant': ((210, 120, 20), 'tri'),
               'lamp': ((220, 180, 20), 'diamond'), 'bottle': ((60, 140, 200), 'dot'), 'scarab': ((40, 150, 90), 'tri'),
               'hatch': ((60, 60, 60), 'square'), 'door': ((60, 60, 60), 'square'), 'rope': ((120, 80, 40), 'square'),
               'chest': ((200, 150, 20), 'diamond'), 'mirror': ((120, 120, 200), 'star'), 'statue': ((40, 90, 190), 'dot'),
               'vault': ((90, 40, 40), 'square'), 'plaque': ((90, 40, 40), 'dot'), 'sewer': ((80, 70, 60), 'square'),
               'house_door': ((30, 30, 30), 'door'), 'board': ((140, 110, 80), 'post')}


class Canvas:
    """Draws the same primitives into a PIL image (supersampled) and an SVG document."""

    def __init__(self, w, h, scale, origin, ss=2, bg=(214, 224, 238)):
        self.w, self.h, self.scale, self.origin, self.ss = w, h, scale, origin, ss
        self.img = Image.new('RGB', (w * ss, h * ss), bg)
        self.d = ImageDraw.Draw(self.img)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
                    f'<rect width="{w}" height="{h}" fill="{self.hx(bg)}"/>']
        self._fonts = {}

    @staticmethod
    def hx(c):
        return '#%02x%02x%02x' % tuple(c[:3]) if c else 'none'

    def px(self, p):
        """map units -> canvas pixels"""
        return ((p[0] - self.origin[0]) * self.scale, (self.origin[1] - p[1]) * self.scale)

    def font(self, size, kind=''):
        key = (size, kind)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype({'b': FONTB, 'i': FONTI}.get(kind, FONT), int(size * self.ss))
        return self._fonts[key]

    def poly(self, pts, fill=None, outline=None, width=1, map_units=True, opacity=1.0):
        q = [self.px(p) for p in pts] if map_units else pts
        if fill is not None and opacity < 1.0:
            layer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon([(x * self.ss, y * self.ss) for x, y in q], fill=tuple(fill) + (int(255 * opacity),))
            self.img.paste(Image.alpha_composite(self.img.convert('RGBA'), layer).convert('RGB'))
            self.d = ImageDraw.Draw(self.img)
        elif fill is not None:
            self.d.polygon([(x * self.ss, y * self.ss) for x, y in q], fill=tuple(fill))
        if outline is not None:
            self.d.line([(x * self.ss, y * self.ss) for x, y in q + q[:1]], fill=tuple(outline), width=max(1, int(width * self.ss)))
        pts_s = ' '.join(f'{x:.1f},{y:.1f}' for x, y in q)
        self.svg.append(f'<polygon points="{pts_s}" fill="{self.hx(fill)}" fill-opacity="{opacity}" '
                        f'stroke="{self.hx(outline)}" stroke-width="{width}"/>')

    def line(self, pts, colour, width=1, map_units=True, dash=None):
        q = [self.px(p) for p in pts] if map_units else pts
        if dash:
            for (x0, y0), (x1, y1) in zip(q, q[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                n = max(1, int(L / (dash * 2)))
                for i in range(n):
                    a, b = i / n, (i + 0.5) / n
                    self.d.line([((x0 + (x1 - x0) * a) * self.ss, (y0 + (y1 - y0) * a) * self.ss),
                                 ((x0 + (x1 - x0) * b) * self.ss, (y0 + (y1 - y0) * b) * self.ss)],
                                fill=tuple(colour), width=max(1, int(width * self.ss)))
        else:
            self.d.line([(x * self.ss, y * self.ss) for x, y in q], fill=tuple(colour), width=max(1, int(width * self.ss)))
        pts_s = ' '.join(f'{x:.1f},{y:.1f}' for x, y in q)
        da = f' stroke-dasharray="{dash},{dash}"' if dash else ''
        self.svg.append(f'<polyline points="{pts_s}" fill="none" stroke="{self.hx(colour)}" stroke-width="{width}"{da}/>')

    def circle(self, c, r, fill=None, outline=None, width=1, map_units=True, r_units=False, opacity=1.0):
        x, y = self.px(c) if map_units else c
        rr = r * self.scale if r_units else r
        box = [(x - rr) * self.ss, (y - rr) * self.ss, (x + rr) * self.ss, (y + rr) * self.ss]
        if fill is not None and opacity < 1.0:
            layer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).ellipse(box, fill=tuple(fill) + (int(255 * opacity),))
            self.img.paste(Image.alpha_composite(self.img.convert('RGBA'), layer).convert('RGB'))
            self.d = ImageDraw.Draw(self.img)
            fill_now = None
        else:
            fill_now = tuple(fill) if fill is not None else None
        self.d.ellipse(box, fill=fill_now, outline=tuple(outline) if outline else None,
                       width=max(1, int(width * self.ss)))
        self.svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" fill="{self.hx(fill)}" fill-opacity="{opacity}" '
                        f'stroke="{self.hx(outline)}" stroke-width="{width}"/>')

    def text(self, xy, s, size=11, colour=(20, 20, 30), anchor='mm', kind='', map_units=True, halo=True):
        x, y = self.px(xy) if map_units else xy
        f = self.font(size, kind)
        if halo:
            self.d.text((x * self.ss, y * self.ss), s, font=f, fill=(255, 255, 255), anchor=anchor,
                        stroke_width=int(2 * self.ss), stroke_fill=(255, 255, 255))
        self.d.text((x * self.ss, y * self.ss), s, font=f, fill=tuple(colour), anchor=anchor)
        ta = {'m': 'middle', 'l': 'start', 'r': 'end'}[anchor[0]]
        db = {'m': 'central', 't': 'hanging', 'b': 'auto', 's': 'auto'}.get(anchor[1], 'central')
        wt = 'bold' if kind == 'b' else 'normal'
        st = 'italic' if kind == 'i' else 'normal'
        esc = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        halo_s = 'paint-order="stroke" stroke="#ffffff" stroke-width="3" ' if halo else ''
        self.svg.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="DejaVu Sans, sans-serif" font-size="{size}" '
                        f'font-weight="{wt}" font-style="{st}" text-anchor="{ta}" dominant-baseline="{db}" '
                        f'{halo_s}fill="{self.hx(colour)}">{esc}</text>')

    def marker(self, c, kind, size=5):
        colour, shape = POINT_STYLE.get(kind, ((0, 0, 0), 'dot'))
        x, y = self.px(c)
        s = size
        if shape == 'dot':
            self.circle((x, y), s * 0.8, fill=colour, outline=(255, 255, 255), width=1, map_units=False)
        elif shape == 'square' or shape == 'door':
            self.poly([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)], fill=colour,
                      outline=(255, 255, 255), width=1, map_units=False)
        elif shape == 'diamond':
            self.poly([(x, y - s * 1.3), (x + s, y), (x, y + s * 1.3), (x - s, y)], fill=colour,
                      outline=(255, 255, 255), width=1, map_units=False)
        elif shape == 'tri':
            self.poly([(x, y - s * 1.2), (x + s * 1.1, y + s * 0.8), (x - s * 1.1, y + s * 0.8)], fill=colour,
                      outline=(255, 255, 255), width=1, map_units=False)
        elif shape == 'star':
            pts = []
            for i in range(10):
                r = s * 1.6 if i % 2 == 0 else s * 0.7
                t = -math.pi / 2 + i * math.pi / 5
                pts.append((x + r * math.cos(t), y + r * math.sin(t)))
            self.poly(pts, fill=colour, outline=(255, 255, 255), width=1, map_units=False)
        elif shape == 'post':
            self.line([(x, y + s), (x, y - s)], colour, 2, map_units=False)
            self.poly([(x - s, y - s * 1.6), (x + s, y - s * 1.6), (x + s, y - s * 0.6), (x - s, y - s * 0.6)],
                      fill=colour, map_units=False)

    def save(self, png, svg, png2x=None):
        self.svg.append('</svg>')
        Path(svg).write_text('\n'.join(self.svg))
        if png2x:
            self.img.save(png2x)
        self.img.resize((self.w, self.h), Image.LANCZOS).save(png)


def arrow(cv, at, facing, length, colour):
    dx, dy = G.FACING[facing]
    tip = (at[0] + dx * length, at[1] + dy * length)
    cv.line([at, tip], colour, 2)
    x, y = cv.px(tip)
    bx, by = cv.px(at)
    ang = math.atan2(y - by, x - bx)
    cv.poly([(x, y), (x - 7 * math.cos(ang - 0.45), y - 7 * math.sin(ang - 0.45)),
             (x - 7 * math.cos(ang + 0.45), y - 7 * math.sin(ang + 0.45))], fill=colour, map_units=False)


# ------------------------------------------------------------------------------------------------ the plan
def plan(P, f):
    k = 12 / 512                                   # 12 px a cell
    margin_l, margin_t, margin_b = 30, 70, 40
    W = int(D.HALF[0] * 2 * k) + margin_l * 2
    H = int(D.HALF[1] * 2 * k) + margin_t + margin_b
    cv = Canvas(W, H, k, (-D.HALF[0] - margin_l / k, D.HALF[1] + margin_t / k))
    # fall zones
    for fz in D.FALLS:
        x0, x1 = fz['x']
        y0, y1 = fz['y']
        cv.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=FALL_TINT[fz['key']], opacity=0.10)
        cv.text(((x0 + x1) / 2, y1 - 900 if y1 > 0 else y0 + 900), f"falls land on {fz['key']} ({fz['squares']})",
                10, (70, 70, 90), kind='i')
    # source squares
    for i in range(7):
        x = -D.HALF[0] + i * D.SQUARE[0]
        cv.line([(x, -D.HALF[1]), (x, D.HALF[1])], (175, 188, 210), 1, dash=3)
    for j in range(5):
        y = D.HALF[1] - j * D.SQUARE[1]
        cv.line([(-D.HALF[0], y), (D.HALF[0], y)], (175, 188, 210), 1, dash=3)
    for c in range(6):
        for r in range(4):
            code = 'ABCDEF'[c] + str(r + 1)
            x = -D.HALF[0] + c * D.SQUARE[0] + 500
            y = D.HALF[1] - r * D.SQUARE[1] - 450
            cv.text((x, y), code, 9, (130, 145, 170), anchor='lt', halo=False)
    cv.poly([(-D.HALF[0], -D.HALF[1]), (D.HALF[0], -D.HALF[1]), (D.HALF[0], D.HALF[1]), (-D.HALF[0], D.HALF[1])],
            outline=(90, 100, 130), width=1.5)
    # the Megadragon's breath circle and leash
    b = D.BOSS
    cv.circle(b['at'], b['leash'] + D.BREATH_MARGIN, fill=(200, 40, 40), r_units=True, opacity=0.07)
    cv.circle(b['at'], b['leash'] + D.BREATH_MARGIN, outline=(190, 60, 60), r_units=True, width=1)
    # corner glows
    for s in D.SPACES:
        if s.get('element'):
            cv.circle(s['at'], 3600, fill=ELEMENT[s['element']], r_units=True, opacity=0.18)
    # links
    for l in D.LINKS:
        p, q = G.link_ends(l, P)
        poly = G.strip(p, q, l['width'])
        col = {'road': (232, 226, 210), 'causeway': (246, 238, 214), 'spur': (232, 226, 210),
               'bridge': (170, 130, 80)}[l['style']]
        cv.poly(poly, fill=col, outline=(120, 110, 100), width=0.8)
        if l['style'] == 'road':
            cv.line([p, q], (200, 190, 170), 1, dash=4)
        if l['style'] == 'bridge':
            cv.line([p, q], (110, 80, 40), 1.5, dash=2)
    # islands
    for s in D.SPACES:
        poly = P[s['id']]
        cv.poly(poly, fill=KIND_FILL[s['kind']], outline=(110, 120, 140), width=1.2)
        if s['kind'] in ('rest', 'corner'):
            cv.circle(s['at'], s['extent'][0] / 2 * 0.55, outline=(120, 170, 120), width=1, r_units=True)
        if s['kind'] == 'lake':
            cx, cy = s['at']
            cv.poly([(cx + 2400 * math.cos(t) + 400, cy + 1900 * math.sin(t) - 200)
                     for t in [i * math.pi / 12 for i in range(24)]], fill=(120, 170, 220), outline=(80, 120, 170))
        if s['kind'] == 'cap':
            cx, cy = s['at']
            cv.poly([(cx - 900, cy - 900), (cx + 900, cy - 900), (cx + 900, cy + 900), (cx - 900, cy + 900)],
                    fill=(220, 180, 60), outline=(150, 110, 30))
            cv.line([(cx - 900, cy - 900), (cx + 900, cy + 900)], (150, 110, 30), 1)
            cv.line([(cx + 900, cy - 900), (cx - 900, cy + 900)], (150, 110, 30), 1)
    # Olympus buildings (small)
    for bid, house, service, at, facing, fp, zone, note in D.BUILDINGS:
        dx, dy = G.FACING[facing]
        cx, cy = at[0] - dx * fp[0] * 256, at[1] - dy * fp[1] * 256
        wdt, hgt = fp[0] * 512, fp[1] * 512
        if facing in ('e', 'w'):
            wdt, hgt = fp[1] * 512, fp[0] * 512
        cv.poly([(cx - wdt / 2, cy - hgt / 2), (cx + wdt / 2, cy - hgt / 2), (cx + wdt / 2, cy + hgt / 2),
                 (cx - wdt / 2, cy + hgt / 2)], fill=(222, 214, 196), outline=(150, 140, 120), width=0.8)
    jet = [D.OLYMPUS_DOCK_START, D.OLYMPUS_DOCK_END]
    cv.poly(G.strip(jet[0], jet[1], 384), fill=(246, 238, 214), outline=(140, 130, 110), width=0.8)
    # groups
    for g in D.GROUPS + [D.BOSS]:
        col = ACTOR[g['actor']]
        r = 5 + 2.2 * g['count'] if g['actor'] != 11654 else 12
        cv.circle(g['at'], r, fill=col, outline=(40, 40, 40), width=1)
        cv.text(g['at'], str(g['count']) if g['actor'] != 11654 else 'M', 9, (255, 255, 255), kind='b', halo=False)
    for bnd in D.BANDITS:
        cv.circle(bnd['at'], 6, fill=(255, 255, 255), outline=(150, 30, 120), width=2)
    # points
    for p in D.POINTS:
        cv.marker(p['at'], p['kind'], 4 if p['kind'] == 'board' else 5)
    for bid, house, service, at, facing, fp, zone, note in D.BUILDINGS:
        cv.marker(at, 'house_door', 3)
    # arrivals
    for a in D.ARRIVALS:
        x, y = a['at']
        cv.poly([(x - 330, y - 330), (x + 330, y - 330), (x + 330, y + 330), (x - 330, y + 330)],
                fill=(30, 150, 70), outline=(255, 255, 255), width=1)
        arrow(cv, a['at'], a['facing'], 1300, (30, 130, 60))
    # cameras
    for name, cam in D.CAMERAS.items():
        yaw = math.radians(cam['yaw_deg'])
        half = math.radians(cam['fov_deg'] / 2)
        L = 9000
        a = cam['at']
        p1 = (a[0] + L * math.cos(yaw + half), a[1] + L * math.sin(yaw + half))
        p2 = (a[0] + L * math.cos(yaw - half), a[1] + L * math.sin(yaw - half))
        cv.poly([a, p1, p2], fill=(250, 210, 60), opacity=0.22)
        cv.line([p1, a, p2], (200, 150, 20), 1.5)
        cv.text((a[0] + 2200 * math.cos(yaw), a[1] + 2200 * math.sin(yaw) - 700), f'MU-4 {name}', 10,
                (150, 100, 10), kind='b')
    # labels
    LABEL = {'room:fire_corner': (0, -2900), 'room:air_corner': (0, -2900), 'room:earth_corner': (0, 2900),
             'room:water_corner': (0, 2900), 'zone:olympus': (0, 4500), 'room:roost': (0, -2800),
             'room:sky_lake': (0, -3700), 'room:rope_head': (3600, 1700), 'room:broken_launch': (0, -2500),
             'room:pyramid_cap': (0, -2700), 'room:genie_rock': (0, -1600), 'room:stranded_south': (0, -1400),
             'room:stranded_west': (0, 1350), 'room:north_tower_hatch': (2800, 0), 'room:south_tower_hatch': (2800, 0),
             'room:blackfang_hatch': (-2600, -1500), 'room:west_lookout': (2900, 0), 'room:smoke_post': (2900, -600),
             'room:west_toll': (2700, 0), 'room:mud_wharf': (-2900, 0), 'room:east_junction': (-3200, 1400)}
    for s in D.SPACES:
        off = LABEL.get(s['id'], (0, 2300 if s['at'][1] < 0 else -2300))
        at = (s['at'][0] + off[0], s['at'][1] + off[1])
        txt = s['name'].replace('The ', '') if s['kind'] != 'town' else 'OLYMPUS'
        cv.text(at, txt, 13 if s['kind'] == 'town' else 10, (30, 30, 60), kind='b')
        cv.text((at[0], at[1] - 620), f"{s['floor']}", 9, (90, 90, 110))
    # Megadragon breath note
    cv.text((b['at'][0], b['at'][1] - b['leash'] - D.BREATH_MARGIN + 600), 'breath reach (leash + 5,888)', 9,
            (170, 50, 50), kind='i')
    # title and legend
    cv.text((margin_l, 22), "D7 The Skyroads - MU-3 plan (L1, A6, 2026-11-21)", 18, (20, 20, 40), anchor='lm',
            map_units=False, kind='b', halo=False)
    cv.text((margin_l, 46),
            f"room {D.ROOM[0]} x {D.ROOM[1]} cells (65,536 x 45,056); x east, y north; floors in map units; "
            f"source squares A1-F4 dashed; {f['placed_monsters']} placed, {f['kill_xp_per_member']:,} kill XP a member; "
            f"{f['points_of_interest']} POIs; ring {f['ring_length']:,}", 11, (40, 40, 60), anchor='lm',
            map_units=False, halo=False)
    lx = margin_l
    ly = H - 20
    items = [('griffins 48', ACTOR[11562]), ('sky golems 75', ACTOR[11594]), ('cloud dragons 70', ACTOR[11650]),
             ('cloud golems 50', ACTOR[11592]), ('Megadragon 125', ACTOR[11654])]
    for name, col in items:
        cv.circle((lx + 6, ly), 6, fill=col, map_units=False)
        cv.text((lx + 16, ly), name, 10, (30, 30, 40), anchor='lm', map_units=False, halo=False)
        lx += 110
    for name, kind in [('corner step-off', 'corner'), ('toll', 'toll'), ('merchant', 'merchant'), ('lamp', 'lamp'),
                       ('bottle', 'bottle'), ('hatch/door', 'hatch'), ('chest', 'chest'), ('board (hover)', 'board')]:
        x, y = lx + 6, ly
        cv.marker(((x / k) + cv.origin[0], cv.origin[1] - y / k), kind, 5)
        cv.text((lx + 16, ly), name, 10, (30, 30, 40), anchor='lm', map_units=False, halo=False)
        lx += 98
    cv.poly([(lx, ly - 6), (lx + 12, ly - 6), (lx + 12, ly + 6), (lx, ly + 6)], fill=(30, 150, 70), map_units=False)
    cv.text((lx + 16, ly), 'arrival', 10, (30, 30, 40), anchor='lm', map_units=False, halo=False)
    cv.circle((lx + 90, ly), 6, fill=(255, 255, 255), outline=(150, 30, 120), width=2, map_units=False)
    cv.text((lx + 100, ly), 'bandits', 10, (30, 30, 40), anchor='lm', map_units=False, halo=False)
    cv.save(OUT / 'plan_d7.png', OUT / 'plan_d7.svg', OUT / 'plan_d7_2x.png')


def plan_olympus(P):
    k = 48 / 512
    s = D.SPACE['zone:olympus']
    x0, y0 = s['at'][0] - s['extent'][0] / 2 - 1400, s['at'][1] + s['extent'][1] / 2 + 1600
    W = int((s['extent'][0] + 2800 + 2600) * k)
    H = int((s['extent'][1] + 3200 + 2400) * k)
    cv = Canvas(W, H, k, (x0, y0), bg=(214, 224, 238))
    cv.poly(P['zone:olympus'], fill=(250, 246, 234), outline=(120, 120, 140), width=2)
    for l in D.LINKS:
        if 'zone:olympus' in (l['a'], l['b']):
            p, q = G.link_ends(l, P)
            cv.poly(G.strip(p, q, l['width']), fill=(246, 238, 214), outline=(140, 130, 110))
    for z in D.OLYMPUS_ZONES:
        cx, cy = z['at']
        ex, ey = z['extent']
        cv.poly([(cx - ex / 2, cy - ey / 2), (cx + ex / 2, cy - ey / 2), (cx + ex / 2, cy + ey / 2),
                 (cx - ex / 2, cy + ey / 2)], outline=(170, 160, 200), width=1)
        cv.text((cx, cy + ey / 2 - 220), z['name'], 14, (110, 100, 150), kind='i')
    for bid, house, service, at, facing, fp, zone, note in D.BUILDINGS:
        dx, dy = G.FACING[facing]
        cx, cy = at[0] - dx * fp[0] * 256, at[1] - dy * fp[1] * 256
        wdt, hgt = fp[0] * 512, fp[1] * 512
        if facing in ('e', 'w'):
            wdt, hgt = fp[1] * 512, fp[0] * 512
        cv.poly([(cx - wdt / 2, cy - hgt / 2), (cx + wdt / 2, cy - hgt / 2), (cx + wdt / 2, cy + hgt / 2),
                 (cx - wdt / 2, cy + hgt / 2)], fill=(226, 218, 200), outline=(130, 120, 100), width=1.2)
        cv.marker(at, 'house_door', 5)
        cv.text((cx, cy), service.replace('Olympus ', '').replace('House of ', ''), 13, (40, 30, 20), kind='b')
        cv.text((cx, cy - 330), f'{house}', 12, (90, 80, 70))
    jet = [D.OLYMPUS_DOCK_START, D.OLYMPUS_DOCK_END]
    cv.poly(G.strip(jet[0], jet[1], 384), fill=(246, 238, 214), outline=(140, 130, 110))
    cv.text((D.OLYMPUS_DOCK_END[0] + 300, D.OLYMPUS_DOCK_END[1] - 300), 'celestial boat', 13, (60, 60, 90), kind='i')
    sv = D.SOUL_STORAGE
    cx, cy = sv['room_at']
    cv.poly([(cx - sv['room'][0] / 2, cy - sv['room'][1] / 2), (cx + sv['room'][0] / 2, cy - sv['room'][1] / 2),
             (cx + sv['room'][0] / 2, cy + sv['room'][1] / 2), (cx - sv['room'][0] / 2, cy + sv['room'][1] / 2)],
            fill=(205, 195, 190), outline=(90, 40, 40), width=1.5)
    cv.text((cx, cy + 350), 'Soul Storage', 13, (90, 40, 40), kind='b')
    cv.circle(D.ANTS_LOOKOUT, 6, fill=(150, 130, 90), outline=(80, 60, 30), width=1)
    cv.text((D.ANTS_LOOKOUT[0] + 150, D.ANTS_LOOKOUT[1] - 300), "ants' lookout", 12, (80, 60, 30), anchor='lm', kind='i')
    for name, at, side in D.OLYMPUS_GATES:
        cv.circle(at, 7, fill=(200, 170, 60), outline=(90, 70, 20), width=1.5)
        cv.text((at[0], at[1] + 420), name, 13, (90, 70, 20), kind='b')
    for p in D.POINTS:
        if p['space'] == 'zone:olympus':
            cv.marker(p['at'], p['kind'], 6)
            lab = {'mirror': 'mirror', 'statue': p['id'].split('_')[-1], 'vault': 'vault door', 'plaque': 'plaque',
                   'sewer': 'DD-26 stair'}.get(p['kind'], '')
            if p['kind'] == 'statue':
                lab = 'statue ' + lab
            cv.text((p['at'][0], p['at'][1] - 360), lab, 13, (30, 30, 60))
    for a in D.ARRIVALS:
        if a['space'] == 'zone:olympus':
            x, y = a['at']
            cv.poly([(x - 150, y - 150), (x + 150, y - 150), (x + 150, y + 150), (x - 150, y + 150)],
                    fill=(30, 150, 70), outline=(255, 255, 255))
            arrow(cv, a['at'], a['facing'], 700, (30, 130, 60))
            cv.text((x + 260, y - 200), a['id'].split(':')[1], 13, (20, 100, 40), anchor='lm', kind='b')
    cv.text((10, 16), "Olympus (C2), floor 1,792 - 48 px a cell; A4's houses 4801-4814", 20, (20, 20, 40),
            anchor='lm', map_units=False, kind='b', halo=False)
    cv.save(OUT / 'plan_olympus.png', OUT / 'plan_olympus.svg')


# ------------------------------------------------------------------------------------------------ blockouts
def blockout(P, name, W=1536, H=1024):
    cam = D.CAMERAS[name]
    cx, cy = cam['at']
    cz = cam['z']
    yaw, pitch = math.radians(cam['yaw_deg']), math.radians(cam['pitch_deg'])
    fwd = (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))
    right = (math.sin(yaw), -math.cos(yaw), 0.0)
    up = (fwd[1] * right[2] - fwd[2] * right[1], fwd[2] * right[0] - fwd[0] * right[2],
          fwd[0] * right[1] - fwd[1] * right[0])
    if up[2] < 0:
        up = tuple(-v for v in up)
    fpx = (W / 2) / math.tan(math.radians(cam['fov_deg']) / 2)
    NEAR = 40.0
    campos = (cx, cy, cz)

    def cs(p):
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        return (sum(d[i] * right[i] for i in range(3)), sum(d[i] * up[i] for i in range(3)),
                sum(d[i] * fwd[i] for i in range(3)))

    def clip(poly):
        out = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            ina, inb = a[2] >= NEAR, b[2] >= NEAR
            if ina:
                out.append(a)
            if ina != inb:
                t = (NEAR - a[2]) / (b[2] - a[2])
                out.append(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
        return out

    def proj(c):
        return (W / 2 + c[0] / c[2] * fpx, H / 2 - c[1] / c[2] * fpx)

    faces = []
    labels = []

    def add(poly3, colour, normal=None, bias=0.0):
        if normal is not None:
            p = poly3[0]
            if sum(normal[i] * (campos[i] - p[i]) for i in range(3)) <= 0:
                return
        c = clip([cs(p) for p in poly3])
        if len(c) < 3:
            return
        depth = max(v[2] for v in c) * 0.5 + sum(v[2] for v in c) / len(c) * 0.5 + bias
        faces.append((depth, [proj(v) for v in c], colour))

    def shade(col, f):
        return tuple(max(0, min(255, int(v * f))) for v in col)

    def prism(poly2, z0, z1, top, side):
        n = len(poly2)
        area = sum(poly2[i][0] * poly2[(i + 1) % n][1] - poly2[(i + 1) % n][0] * poly2[i][1] for i in range(n))
        sg = 1.0 if area > 0 else -1.0
        for i in range(n):
            a, b = poly2[i], poly2[(i + 1) % n]
            nrm = (sg * (b[1] - a[1]), -sg * (b[0] - a[0]), 0.0)
            lit = 0.82 + 0.18 * (nrm[0] * 0.6 + nrm[1] * 0.8) / (math.hypot(nrm[0], nrm[1]) or 1)
            add([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], shade(side, lit), nrm)
        add([(x, y, z1) for x, y in poly2], top, (0.0, 0.0, 1.0))

    def box(c, sx, sy, z0, z1, top, side):
        x, y = c
        prism([(x - sx / 2, y - sy / 2), (x + sx / 2, y - sy / 2), (x + sx / 2, y + sy / 2), (x - sx / 2, y + sy / 2)],
              z0, z1, top, side)

    def ngon(c, r, n=10):
        return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

    def cone(c, r, z0, z1, col, n=10):
        ring = ngon(c, r, n)
        tip = (c[0], c[1], z1)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            mid = ((a[0] + b[0]) / 2 - c[0], (a[1] + b[1]) / 2 - c[1])
            nz = 1.0 if z1 > z0 else -1.0
            add([(a[0], a[1], z0), (b[0], b[1], z0), tip], shade(col, 0.85 + 0.15 * (mid[0] / r)),
                (mid[0], mid[1], nz * r * 0.5))

    def label(p3, text, far=26000):
        c = cs(p3)
        if c[2] > NEAR and c[2] < far:
            x, y = proj(c)
            if 0 <= x <= W and 0 <= y <= H:
                labels.append((x, y, text))

    TOP, SIDE, UNDER = (247, 243, 234), (214, 206, 196), (190, 180, 176)
    ROADC = (236, 226, 204)
    for s in D.SPACES:
        z = s['floor']
        poly = P[s['id']]
        top = (252, 249, 240) if s['kind'] == 'town' else TOP
        prism(poly, z - 320, z, top, SIDE)
        tip = (s['at'][0], s['at'][1], z - 320 - 0.35 * max(s['extent']))
        n = len(poly)
        for i in range(n):
            a = poly[i]
            b = poly[(i + 1) % n]
            a3 = (a[0] * 0.85 + s['at'][0] * 0.15, a[1] * 0.85 + s['at'][1] * 0.15, z - 320)
            b3 = (b[0] * 0.85 + s['at'][0] * 0.15, b[1] * 0.85 + s['at'][1] * 0.15, z - 320)
            mid = ((a3[0] + b3[0]) / 2 - s['at'][0], (a3[1] + b3[1]) / 2 - s['at'][1])
            add([a3, b3, tip], UNDER, (mid[0], mid[1], -0.6 * math.hypot(*mid)))
        if s.get('element') and False:
            el = ELEMENT[s['element']]
            # the step-off tip: a glow far below the corner
            cpt = next(p for p in D.POINTS if p['space'] == s['id'] and p['kind'] == 'corner')['at']
            add([(cpt[0] - 3000, cpt[1] - 3000, -2500), (cpt[0] + 3000, cpt[1] - 3000, -2500),
                 (cpt[0] + 3000, cpt[1] + 3000, -2500), (cpt[0] - 3000, cpt[1] + 3000, -2500)], shade(el, 1.1),
                (0, 0, 1))
        if s['kind'] in ('rest', 'corner'):
            hut = (s['at'][0] - s['extent'][0] * 0.18, s['at'][1] + s['extent'][1] * 0.12)
            box(hut, 640, 512, z, z + 448, (150, 110, 80), (175, 140, 100))
            label((hut[0], hut[1], z + 700), 'rest stop hut', 9000)
        if s['kind'] == 'cap':
            c = s['at']
            r = 1100
            base = [(c[0] - r, c[1] - r), (c[0] + r, c[1] - r), (c[0] + r, c[1] + r), (c[0] - r, c[1] + r)]
            zc = z + 380
            apex = (c[0], c[1], zc + 1500)
            for i in range(4):
                a, b = base[i], base[(i + 1) % 4]
                mid = ((a[0] + b[0]) / 2 - c[0], (a[1] + b[1]) / 2 - c[1])
                add([(a[0], a[1], zc), (b[0], b[1], zc), apex], shade((225, 185, 70), 0.8 + 0.2 * mid[0] / r),
                    (mid[0], mid[1], r * 0.7))
            label((c[0], c[1], zc + 1900), "the Pyramid's sky door (gold capstone)")
        if s['kind'] == 'lake':
            c = s['at']
            add([(c[0] + 2400 * math.cos(t) + 400, c[1] + 1900 * math.sin(t) - 200, z - 40)
                 for t in [i * math.pi / 12 for i in range(24)]], (150, 185, 215), (0, 0, 1))
            for p in D.POINTS:
                if p['kind'] == 'scarab':
                    box(p['at'], 300, 300, z, z + 300, (200, 60, 60), (230, 220, 200))
            label((c[0], c[1], z + 400), 'the Sky Lake, scarab stalls')
        if s['kind'] == 'roost':
            c = s['at']
            for i, (dx, dy, hh) in enumerate([(0, 0, 1400), (700, 500, 900), (-800, 300, 1000), (300, -700, 800)]):
                prism(ngon((c[0] + dx, c[1] + dy), 600 - i * 90, 7), z, z + hh, (60, 55, 60), (75, 70, 75))
            label((c[0], c[1], z + 2600), 'Megadragon on the roost (Alamar roof hatch)', 20000)
        if s['kind'] == 'road' and s['id'] == 'room:broken_launch':
            c = s['at']
            box((c[0] + 1700, c[1] + 300), 1800, 320, z - 40, z + 40, (230, 225, 210), (200, 195, 185))
            label((c[0], c[1], z + 600), 'broken launch (sky golems)')
    for l in D.LINKS:
        za, zb = D.SPACE[l['a']]['floor'], D.SPACE[l['b']]['floor']
        p, q = G.link_ends(l, P)
        L = G.dist(p, q)
        nseg = max(1, int(L / 600))
        dx, dy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        nx, ny = -dy * l['width'] / 2, dx * l['width'] / 2
        thick = 60 if l['style'] == 'bridge' else 256
        for i in range(nseg):
            t0, t1 = i / nseg, (i + 1) / nseg
            a = (p[0] + (q[0] - p[0]) * t0 - dx * (256 if i == 0 else 0), p[1] + (q[1] - p[1]) * t0 - dy * (256 if i == 0 else 0))
            b = (p[0] + (q[0] - p[0]) * t1 + dx * (256 if i == nseg - 1 else 0), p[1] + (q[1] - p[1]) * t1 + dy * (256 if i == nseg - 1 else 0))
            if l['style'] == 'bridge':
                sag = 160 * math.sin(math.pi * (t0 + t1) / 2)
            else:
                sag = 0
            z0 = za + (zb - za) * t0 - sag
            z1 = za + (zb - za) * t1 - sag
            corners = [(a[0] + nx, a[1] + ny, z0), (b[0] + nx, b[1] + ny, z1), (b[0] - nx, b[1] - ny, z1),
                       (a[0] - nx, a[1] - ny, z0)]
            col = (160, 120, 75) if l['style'] == 'bridge' else ((250, 244, 228) if l['style'] == 'causeway' else ROADC)
            add(corners, col, (0, 0, 1))
            for sgn in (1, -1):
                add([(a[0] + sgn * nx, a[1] + sgn * ny, z0), (b[0] + sgn * nx, b[1] + sgn * ny, z1),
                     (b[0] + sgn * nx, b[1] + sgn * ny, z1 - thick), (a[0] + sgn * nx, a[1] + sgn * ny, z0 - thick)],
                    SIDE if l['style'] != 'bridge' else (120, 90, 60), (sgn * nx, sgn * ny, 0))
    # Olympus
    oz = D.SPACE['zone:olympus']['floor']
    MARBLE, MARBLE_S, ROOF, GOLD = (246, 244, 238), (226, 222, 214), (170, 175, 190), (220, 180, 70)
    for bid, house, service, at, facing, fp, zone, note in D.BUILDINGS:
        dx, dy = G.FACING[facing]
        c = (at[0] - dx * fp[0] * 256, at[1] - dy * fp[1] * 256)
        wdt, hgt = fp[0] * 512, fp[1] * 512
        if facing in ('e', 'w'):
            wdt, hgt = fp[1] * 512, fp[0] * 512
        h = 704 if house != 4803 else 1024
        box(c, wdt, hgt, oz, oz + h, ROOF, MARBLE_S)
        if house == 4803:
            prism(ngon(c, 700, 12), oz + h, oz + h + 300, GOLD, GOLD)
            cone(c, 700, oz + h + 300, oz + h + 1000, GOLD, 12)
            for i in range(6):
                box((c[0] - 1100 + i * 440, c[1] - hgt / 2 - 300), 110, 110, oz, oz + h, MARBLE, MARBLE)
            label((c[0], c[1], oz + h + 1300), 'temple (gold dome)')
    # the balustrade round Olympus and the three gates
    tp = P['zone:olympus']
    for i in range(len(tp)):
        a, b = tp[i], tp[(i + 1) % len(tp)]
        a2 = (a[0] * 0.97 + D.SPACE['zone:olympus']['at'][0] * 0.03, a[1] * 0.97 + D.SPACE['zone:olympus']['at'][1] * 0.03)
        b2 = (b[0] * 0.97 + D.SPACE['zone:olympus']['at'][0] * 0.03, b[1] * 0.97 + D.SPACE['zone:olympus']['at'][1] * 0.03)
        nrm = (b2[1] - a2[1], -(b2[0] - a2[0]), 0)
        add([(a2[0], a2[1], oz), (b2[0], b2[1], oz), (b2[0], b2[1], oz + 200), (a2[0], a2[1], oz + 200)], MARBLE_S)
    for gname, at, side in D.OLYMPUS_GATES:
        for off in (-480, 480):
            if side in ('n', 's'):
                c = (at[0] + off, at[1])
            elif side == 'e':
                c = (at[0], at[1] + off)
            else:
                c = (at[0] + off * 0.7, at[1] - off * 0.7)
            box(c, 256, 256, oz, oz + 832, GOLD, MARBLE)
        label((at[0], at[1], oz + 1500), gname, 14000)
    for p in D.POINTS:
        if p['kind'] == 'statue':
            box(p['at'], 220, 220, oz, oz + 520, MARBLE, (200, 200, 205))
        if p['kind'] == 'mirror':
            box(p['at'], 120, 420, oz, oz + 600, (150, 160, 220), (190, 190, 200))
    jet = [D.OLYMPUS_DOCK_START, D.OLYMPUS_DOCK_END]
    L = G.dist(*jet)
    ux, uy = (jet[1][0] - jet[0][0]) / L, (jet[1][1] - jet[0][1]) / L
    nx, ny = -uy * 192, ux * 192
    add([(jet[0][0] + nx, jet[0][1] + ny, oz), (jet[1][0] + nx, jet[1][1] + ny, oz),
         (jet[1][0] - nx, jet[1][1] - ny, oz), (jet[0][0] - nx, jet[0][1] - ny, oz)], MARBLE, (0, 0, 1))
    boat = D.OLYMPUS_DOCK_END
    box((boat[0] + 300, boat[1] - 300), 1200, 420, oz - 200, oz + 120, (200, 160, 70), (170, 130, 60))
    label((boat[0], boat[1], oz + 500), "celestial boat at Lucio's dock", 14000)
    label((D.SPACE['zone:olympus']['at'][0], D.SPACE['zone:olympus']['at'][1], oz + 2600), 'OLYMPUS')
    # hatches, merchants, tolls, lamps, boards
    for p in D.POINTS:
        z = D.SPACE[p['space']]['floor']
        if p['kind'] in ('hatch',):
            box(p['at'], 360, 360, z, z + 60, (90, 90, 95), (80, 80, 85))
        if p['kind'] == 'merchant':
            box(p['at'], 900, 400, z, z + 260, (200, 160, 70), (180, 140, 60))
            box((p['at'][0], p['at'][1]), 60, 60, z + 260, z + 1100, (140, 110, 80), (140, 110, 80))
        if p['kind'] == 'toll':
            box((p['at'][0] - 500, p['at'][1]), 120, 120, z, z + 700, (200, 60, 60), (230, 230, 230))
            box((p['at'][0] + 500, p['at'][1]), 120, 120, z, z + 700, (200, 60, 60), (230, 230, 230))
        if p['kind'] == 'board':
            box(p['at'], 40, 40, z, z + 380, (120, 90, 60), (120, 90, 60))
            box((p['at'][0], p['at'][1]), 280, 30, z + 300, z + 480, (150, 115, 75), (150, 115, 75))
        if p['kind'] == 'lamp':
            box(p['at'], 120, 120, z, z + 80, (220, 180, 40), (200, 160, 30))
        if p['kind'] == 'rope':
            box(p['at'], 30, 30, z, z + 4200, (120, 90, 60), (120, 90, 60))
            label((p['at'][0], p['at'][1], z + 3000), 'the Dark Grove rope')
    for p in D.POINTS:
        if p['kind'] == 'board' and p['id'] == 'board:skyroad_board':
            label((p['at'][0], p['at'][1], D.SPACE[p['space']]['floor'] + 700), "'XEEN Skyroad' board", 12000)
    # monsters
    for g in D.GROUPS + [D.BOSS]:
        rname, level, xp, mode = D.ROWS[g['actor']]
        sp = D.SPACE.get(g['space'])
        z = sp['floor'] if sp else 1100
        if g['space'].startswith('link:'):
            l = next(l for l in D.LINKS if l['id'] == g['space'])
            z = (D.SPACE[l['a']]['floor'] + D.SPACE[l['b']]['floor']) / 2
        col = (70, 60, 60) if mode == 'fly' else (120, 125, 140)
        for i in range(g['count']):
            a = 2 * math.pi * i / max(1, g['count'])
            c = (g['at'][0] + 380 * math.cos(a), g['at'][1] + 380 * math.sin(a))
            if g['actor'] == 11654:
                zz = z + 1600
                add([(c[0] - 900, c[1], zz), (c[0], c[1] + 260, zz + 250), (c[0] + 900, c[1], zz),
                     (c[0], c[1] - 260, zz - 120)], (60, 20, 25))
            elif mode == 'fly':
                zz = z + 700 + 150 * i
                s = 260 if g['actor'] == 11562 else 420
                add([(c[0] - s, c[1], zz), (c[0], c[1] + s * 0.3, zz + s * 0.4), (c[0] + s, c[1], zz),
                     (c[0], c[1] - s * 0.3, zz - s * 0.2)], col)
            else:
                box(c, 160, 160, z, z + (360 if g['actor'] == 11592 else 520), col, shade(col, 0.8))
        label((g['at'][0], g['at'][1], z + 1500), f"{g['count']} {rname.lower()}s" if g['actor'] != 11654 else '', 14000)
    faces.sort(key=lambda t: -t[0])
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    # the Skyroads sky: an amber Darkside day, the sky below the horizon too (below_horizon: sky)
    hy = H / 2 - math.tan(pitch) * fpx
    for y in range(H):
        t = (y - hy) / H
        if t < 0:
            u = min(1, -t * 2.2)
            col = (int(232 - 120 * u), int(196 - 70 * u), int(150 - 20 * u))
        else:
            u = min(1, t * 2.5)
            col = (int(236 - 30 * u), int(210 - 40 * u), int(178 - 30 * u))
        d.line([(0, y), (W, y)], fill=col)
    for depth, pts, col in faces:
        if len(pts) >= 3:
            d.polygon(pts, fill=col, outline=shade(col, 0.88))
    f = ImageFont.truetype(FONT, 15)
    for x, y, t in labels:
        if not t:
            continue
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(30, 60, 220), width=2)
        d.text((x + 8, y - 9), t, font=f, fill=(30, 60, 220))
    img.save(OUT / f'blockout_{name}.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P = G.polys()
    f = G.figures(P)
    f['cameras'] = D.CAMERAS
    f['falls'] = [dict(id=z['id'], map=z['map'], squares=z['squares'], landing=list(z['landing']), facing=z['facing'],
                       owner=z['owner'], near=z['near']) for z in D.FALLS]
    (OUT / 'measure.json').write_text(json.dumps(f, indent=1))
    plan(P, f)
    plan_olympus(P)
    blockout(P, 'arrival')
    blockout(P, 'signature')
    print(json.dumps({k: f[k] for k in ('placed_monsters', 'kill_xp_per_member', 'points_of_interest',
                                        'walkable_area_millions', 'quiet_share', 'megadragon_clear', 'chests')}))


if __name__ == '__main__':
    main()
