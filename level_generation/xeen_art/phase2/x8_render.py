#!/usr/bin/env python3
"""MU-3 drawing and the MU-4 blockout for X8 Cloudreach (an open-air BLV of cloud islands), from its brief's plan.yml:
islands are plan spaces with `at` (map units, the middle) and `extent`, links are the bridges and causeways.

    x8_render.py      -> phase2/x8/{colour.png, plan_x8.svg, blockout_bridge.png}
"""
import base64
import io
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import plan_render as pr

HERE = pr.HERE / 'x8'
RES = pr.RES
N = pr.N
BASE = 2000          # the islands' datum above the cloud sea, for the drawings

POINTS = {  # cells [x, y]: where each thing stands on its island (the plan gives the island)
    'entrance:witch_stair': ((92, 79), 'entrance', 'Arrival: Witch Tower roof stair (XD-04)'),
    'entrance:high_magic_stair': ((38, 77), 'entrance', 'Arrival: Stairway to Heaven (XD-11)'),
    'poi:explorer_statue': ((99, 37), 'poi', "Explorer's statue"),
    'poi:offering_1': ((78, 64), 'poi', 'Offering statues'),
    'poi:offering_2': ((81, 68), 'poi', None),
    'poi:rhyme_1': ((86, 89), 'npc', 'Rhyme statue 1'),
    'poi:rhyme_2': ((29, 61), 'npc', 'Rhyme statue 2'),
    'poi:rhyme_3': ((52, 61), 'npc', 'Rhyme statue 3'),
    'poi:nest_1': ((94, 54), 'camp', 'Harpy nests (burn)'),
    'poi:nest_2': ((98, 59), 'camp', None),
    'poi:nest_queen': ((86, 43), 'camp', "Harpy Queen's nest"),
    'poi:nest_perch': ((88, 87), 'camp', None),
    'poi:observatory': ((46, 55), 'landmark', 'Observatory (telescope)'),
    'poi:gap_1': ((65, 64), 'poi', 'Gap: Lake Darzog below'),
    'poi:gap_2': ((61, 47), 'poi', 'Gap: the lagoon below'),
    'chest:queen': ((88, 45), 'chest', None),
    'chest:observatory': ((47, 57), 'chest', None),
    'chest:golems': ((33, 43), 'chest', 'Cache'),
    'chest:lantern': ((51, 88), 'chest', None),
    'actor:golems': ((36, 46), 'dungeon', 'Cloud Golems x2 (50)'),
}
GAPS = [(65, 65.5, 3.2), (61, 46.5, 2.6), (40, 96, 4.0), (104, 70, 3.5), (74, 40, 3.0)]


def cells(at):
    return at[0] / 512 + 64, 64 - at[1] / 512


def island_mask(space, rng):
    cx, cy = cells(space['at'])
    w, d = space['extent'][0] / 512, space['extent'][1] / 512
    size = N * RES
    yy, xx = np.mgrid[0:size, 0:size] / RES
    ang = np.arctan2(yy - cy, xx - cx)
    wobble = 1 + 0.12 * np.sin(3 * ang + rng.random() * 6) + 0.07 * np.sin(5 * ang + rng.random() * 6)
    r = ((xx - cx) / (w / 2)) ** 2 + ((yy - cy) / (d / 2)) ** 2
    return r <= wobble ** 2


def build(plan):
    size = N * RES
    rng = np.random.default_rng(4)
    height = np.zeros((size, size))
    island = np.zeros((size, size), bool)
    floors = {}
    for space in plan['spaces']:
        if space['kind'] != 'room':
            continue
        m = island_mask(space, rng)
        floors[space['id']] = space['floor']
        dist = ndimage.distance_transform_edt(m) / RES
        rounded = np.clip(dist / 1.2, 0, 1) ** 0.5
        h = (BASE + space['floor']) * (0.82 + 0.18 * rounded)
        height = np.where(m, np.maximum(height, h), height)
        island |= m
    centres = {s['id']: cells(s['at']) for s in plan['spaces'] if s['kind'] == 'room'}
    lines = []
    for link in plan['links']:
        a, b = centres[link['from']], centres[link['to']]
        ha, hb = BASE + floors[link['from']], BASE + floors[link['to']]
        bridge = link['kind'] == 'bridge'
        width = link.get('width', 512) / 512
        steps = 200
        for i in range(steps + 1):
            t = i / steps
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            h = ha + (hb - ha) * t - (math.sin(math.pi * t) * 180 if bridge else 0)
            r = max(1, int(width * RES / 2))
            px, py = int(x * RES), int(y * RES)
            ys, xs = slice(max(py - r, 0), py + r + 1), slice(max(px - r, 0), px + r + 1)
            if not island[py, px] or not bridge:
                height[ys, xs] = np.maximum(height[ys, xs], h)
        lines.append((a, b, link))
    return height, island, lines


def colour(height, island):
    size = N * RES
    rng = np.random.default_rng(9)
    sea = ndimage.gaussian_filter(rng.normal(size=(size, size)), 2.5 * RES)
    sea = (sea - sea.min()) / (np.ptp(sea) + 1e-6)
    rgb = np.zeros((size, size, 3))
    rgb[:] = np.array((236, 240, 248))
    rgb = rgb * (0.85 + 0.15 * sea[..., None])
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for gx, gy, r in GAPS:
        d = np.hypot(xx - gx, yy - gy)
        w = np.clip((r - d) / 1.2, 0, 1)[..., None]
        land = np.array((86, 122, 76)) * (0.8 + 0.3 * sea[..., None])
        rgb = rgb * (1 - w) + land * w
    gy_, gx_ = np.gradient(height, 512 / RES)
    shade = np.clip(1 - (gx_ * 0.5 + gy_ * 0.6), 0.55, 1.2)
    stone = np.array((226, 220, 204))
    raised = height > 100
    rgb[raised] = (stone * shade[..., None])[raised]
    # the islands' cast shadow on the cloud sea (sun from the north-west)
    shadow = ndimage.shift(raised.astype(float), (3 * RES, 2 * RES), order=0)
    rgb[~raised] *= (1 - 0.18 * shadow[~raised])[..., None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def svg(plan, lines, scale=8):
    size = N * scale
    img = Image.open(HERE / 'colour.png').resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -30 {size + 60} {size + 60}" '
           f'width="{size + 60}" height="{size + 60}" font-family="DejaVu Sans, sans-serif">',
           f'<image href="data:image/jpeg;base64,{b64}" x="0" y="0" width="{size}" height="{size}"/>']
    for i in range(0, N + 1, 16):
        out.append(f'<line x1="{i * scale}" y1="0" x2="{i * scale}" y2="{size}" stroke="#000" stroke-opacity="0.15"/>')
        out.append(f'<line x1="0" y1="{i * scale}" x2="{size}" y2="{i * scale}" stroke="#000" stroke-opacity="0.15"/>')
        out.append(f'<text x="{i * scale}" y="-8" font-size="12" text-anchor="middle" fill="#ccc">{i}</text>')
        out.append(f'<text x="-8" y="{i * scale + 4}" font-size="12" text-anchor="end" fill="#ccc">{i}</text>')
    # the fall boundary
    out.append(f'<line x1="{64 * scale}" y1="{20 * scale}" x2="{64 * scale}" y2="{108 * scale}" stroke="#1f4fa8" '
               'stroke-width="2" stroke-dasharray="10 8"/>')
    out.append(f'<text x="{60 * scale}" y="{24 * scale}" font-size="14" text-anchor="end" fill="#1f4fa8" '
               'font-weight="bold">falls land on X3 Lifeforce Lagoon</text>')
    out.append(f'<text x="{68 * scale}" y="{24 * scale}" font-size="14" fill="#1f4fa8" font-weight="bold">'
               'falls land on X1 Vertigo Meadows</text>')
    for a, b, link in lines:
        bridge = link['kind'] == 'bridge'
        if bridge:
            out.append(f'<line x1="{a[0] * scale}" y1="{a[1] * scale}" x2="{b[0] * scale}" y2="{b[1] * scale}" '
                       'stroke="#5a3a1a" stroke-width="6"/>')
            out.append(f'<line x1="{a[0] * scale}" y1="{a[1] * scale}" x2="{b[0] * scale}" y2="{b[1] * scale}" '
                       'stroke="#d9b77a" stroke-width="2.5" stroke-dasharray="5 3"/>')
        else:
            out.append(f'<line x1="{a[0] * scale}" y1="{a[1] * scale}" x2="{b[0] * scale}" y2="{b[1] * scale}" '
                       f'stroke="#9a8f78" stroke-width="{link.get("width", 512) / 512 * scale + 2}" '
                       'stroke-opacity="0.75" stroke-linecap="round"/>')
    # camera
    x, y, lx, ly = 50, 59, 78, 62
    ang = math.atan2(ly - y, lx - x)
    p1 = (x + math.cos(ang - 0.6) * 26, y + math.sin(ang - 0.6) * 26)
    p2 = (x + math.cos(ang + 0.6) * 26, y + math.sin(ang + 0.6) * 26)
    out.append(f'<polygon points="{x * scale},{y * scale} {p1[0] * scale},{p1[1] * scale} {p2[0] * scale},'
               f'{p2[1] * scale}" fill="#1f6fd1" fill-opacity="0.10" stroke="#1f6fd1" stroke-dasharray="6 4"/>')
    out.append(f'<circle cx="{x * scale}" cy="{y * scale}" r="6" fill="#1f6fd1" stroke="#fff" stroke-width="1.5"/>')
    # island names, floors and monsters
    for space in plan['spaces']:
        if space['kind'] != 'room':
            continue
        cx, cy = cells(space['at'])
        out.append(f'<text x="{cx * scale}" y="{(cy - space["extent"][1] / 1024 - 0.6) * scale}" font-size="13" '
                   'text-anchor="middle" font-style="italic" fill="#222" stroke="#fff" stroke-width="3" '
                   f'paint-order="stroke">{pr.esc(space["name"])} ({space["floor"]:+d})</text>')
    for pid, ((x, y), kind, label) in POINTS.items():
        colour_p, shape = pr.SYMBOLS[kind]
        cx, cy = x * scale, y * scale
        if shape == 'sq':
            out.append(f'<rect x="{cx - 6}" y="{cy - 6}" width="12" height="12" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'diamond':
            out.append(f'<polygon points="{cx},{cy - 7} {cx + 7},{cy} {cx},{cy + 7} {cx - 7},{cy}" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'tri':
            out.append(f'<polygon points="{cx},{cy - 8} {cx + 7},{cy + 6} {cx - 7},{cy + 6}" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'star':
            pts = ' '.join(f'{cx + (9 if i % 2 == 0 else 4) * math.cos(-math.pi / 2 + i * math.pi / 5):.1f},'
                           f'{cy + (9 if i % 2 == 0 else 4) * math.sin(-math.pi / 2 + i * math.pi / 5):.1f}'
                           for i in range(10))
            out.append(f'<polygon points="{pts}" fill="{colour_p}" stroke="#fff" stroke-width="1.2"/>')
        else:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        if label:
            out.append(f'<text x="{cx + 9}" y="{cy + 4}" font-size="12.5" fill="#111" stroke="#fff" stroke-width="3.2" '
                       f'paint-order="stroke">{pr.esc(label)}</text>')
    for text, (x, y) in [('THE WITCH CLOUDS (over X1): harpies 14-24, 30 placed', (88, 26.5)),
                         ('THE HIGH MAGIC CLOUDS (over X3): flying feet 18, guardians 24, 26 placed', (40, 30)),
                         ('the long rope bridge, about 10,000 in two spans', (64, 57)),
                         ('cloud sea 2,000 below; gaps show the land', (64, 104))]:
        out.append(f'<text x="{x * scale}" y="{y * scale}" font-size="14" text-anchor="middle" fill="#333" '
                   f'font-weight="bold" stroke="#fff" stroke-width="3" paint-order="stroke">{pr.esc(text)}</text>')
    bx, by = 4 * scale, (N - 6) * scale
    out.append(f'<rect x="{bx - 6}" y="{by - 22}" width="{10 * scale + 120}" height="34" fill="#000" fill-opacity="0.55"/>')
    out.append(f'<line x1="{bx}" y1="{by}" x2="{bx + 10 * scale}" y2="{by}" stroke="#fff" stroke-width="4"/>')
    out.append(f'<text x="{bx + 10 * scale + 8}" y="{by + 5}" font-size="13" fill="#fff">5,120 units (10 cells)</text>')
    out.append('</svg>')
    return '\n'.join(out)


def main():
    import yaml
    plan = yaml.safe_load((pr.ROOT / 'devdocs/xeen/briefs/x8/L1/plan.yml').read_text())
    HERE.mkdir(exist_ok=True)
    height, island, lines = build(plan)
    img = colour(height, island)
    img.save(HERE / 'colour.png')
    (HERE / 'plan_x8.svg').write_text(svg(plan, lines))
    view = {'id': 'view:bridge', 'at': [50, 59], 'look': [78, 62], 'height': 260, 'pitch': -7.0}
    notes = [('long rope bridge', 60, 60.5, 0), ('half-way cloud', 65, 61, 50), ('offering terrace, statues', 80, 66, 100),
             ('nest spires', 96, 56, 600), ("Harpy Queen's eyrie (high)", 86, 44, 300),
             ('windward rock (low)', 60, 51, 50), ('witch landing', 92, 76, 50)]
    models = [(94, 54, None, 1400, 0.6, (110, 104, 96)), (98, 59, None, 1100, 0.5, (110, 104, 96)),
              (96, 56, None, 1700, 0.6, (110, 104, 96)), (86, 43, None, 500, 1.2, (96, 80, 60)),
              (79, 65, None, 260, 0.3, (170, 166, 150)), (81, 68, None, 260, 0.3, (170, 166, 150)),
              (52, 61, None, 260, 0.3, (170, 166, 150))]
    blockout_sky(height, img, view, models, notes, HERE / 'blockout_bridge.png')
    print('written', HERE)


def blockout_sky(height, img, view, models, notes, path):
    """plan_render's blockout with the sky below: heights 0 are the cloud sea far below, not the stars."""
    pr.blockout(height, img, view, models, path, fov=80.0, annotations=notes)
    # brighten what the ray caster drew as void (the stars colour) into a pale cloud sea
    image = np.asarray(Image.open(path).convert('RGB')).astype(float)
    void = (np.abs(image - np.array((14, 16, 32))).sum(-1) < 20)
    image[void] = (226, 232, 244)
    Image.fromarray(image.astype(np.uint8)).save(path)


if __name__ == '__main__':
    main()
