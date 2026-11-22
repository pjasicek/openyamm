#!/usr/bin/env python3
"""MU-3 plan drawings and MU-4 blockout views for an outdoor Xeen map, from its studio brief (A6, phase 2).

    plan_render.py x5        # reads devdocs/xeen/briefs/x5/L1/{plan,sketch,project}.yml

Writes into phase2/<key>/:
  colour.png               the land the plan implies (bands, points, ridges, cliffs, water), for the drawings only;
                           the studio build makes its own land from the same sketch.yml
  plan_<key>.svg           the to-scale plan: land, water, roads, plots, places, encounter and quiet areas, cameras
  blockout_<view>.png      a crude perspective of each sketch view (Codex's composition reference for MU-4)

Nothing here is read by the game or the studio; the brief files are the source.
"""
import base64
import io
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RES = 6                      # raster pixels per cell
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
N = 128

# Ground colours per plan space (sRGB), drawn over the default snow.
X5_GROUND = {
    'zone:steppe': (200, 196, 186),
    'zone:west_plateau': (232, 236, 240),
    'zone:snowfields': (236, 240, 246),
    'zone:troll_forest': (214, 222, 222),
    'zone:ogre_hills': (226, 230, 234),
    'zone:lagoon_marches': (178, 178, 150),
    'zone:arrival_meadow': (200, 200, 178),
    'zone:frostspine': (170, 170, 176),
    'zone:giants': (220, 226, 236),
    'zone:glacier': (196, 226, 240),
    'town:winterkill': (212, 206, 196),
    'town:monastery': (196, 190, 180),
    'town:glom': (214, 210, 200),
}
BAND_BASE = {'band:rim_sea': 0, 'band:ice': 800, 'band:low': 1000, 'band:mid': 1300, 'band:high': 1900,
             'band:peaks': 2700}
TREES = {  # space: (trees per cell, colour)
    'zone:troll_forest': (0.55, (38, 66, 54)),
    'zone:ogre_hills': (0.10, (46, 74, 60)),
    'zone:snowfields': (0.05, (46, 74, 60)),
    'zone:lagoon_marches': (0.07, (52, 76, 58)),
    'zone:druid_grove': (0.5, (40, 70, 56)),
    'zone:west_plateau': (0.02, (46, 74, 60)),
}


def load(key):
    base = ROOT / 'devdocs/xeen/briefs' / key / 'L1'
    read = lambda name: yaml.safe_load((base / name).read_text())
    return read('plan.yml'), read('sketch.yml'), read('project.yml')


def poly_mask(points, scale=RES, size=N):
    img = Image.new('L', (size * scale, size * scale), 0)
    ImageDraw.Draw(img).polygon([(x * scale, y * scale) for x, y in points], fill=255)
    return np.asarray(img) > 127


def line_mask(points, width_cells, scale=RES, size=N):
    img = Image.new('L', (size * scale, size * scale), 0)
    d = ImageDraw.Draw(img)
    pts = [(x * scale, y * scale) for x, y in points]
    w = max(1, int(width_cells * scale))
    d.line(pts, fill=255, width=w, joint='curve')
    for p in pts:
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=255)
    return np.asarray(img) > 127


def build_land(plan, sketch):
    """Height (map units) and space id per raster pixel, from the sketch's bands, points, ridges, cliffs and water."""
    size = N * RES
    height = np.full((size, size), 1000.0)
    bands = sketch['heights']['bands']
    for band in bands:
        if band['band'] == 'band:rim_sea':
            continue
        height[poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 4 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    # key heights pull the land towards them (a soft cone)
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 6.0 if point['h'] > 2400 else 4.0
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        w = np.clip(1 - d / r, 0, 1) ** 2 * (3 - 2 * np.clip(1 - d / r, 0, 1))
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        slope = ridge.get('slope', 3) + 1.5
        w = np.clip(1 - dist / slope, 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    # rolling swells and a little roughness, never in towns or water
    rng = np.random.default_rng(5)
    noise = ndimage.gaussian_filter(rng.normal(size=(size, size)), 3 * RES)
    noise = noise / (np.abs(noise).max() + 1e-6)
    rough = ndimage.gaussian_filter(rng.normal(size=(size, size)), 0.6 * RES)
    rough = rough / (np.abs(rough).max() + 1e-6)
    calm = np.zeros((size, size), bool)
    for d in sketch.get('districts', []):
        if d['space'].startswith('town:') or d['space'] in ('zone:halon_yard', 'zone:winterkill_square'):
            calm |= poly_mask(d['polygon'])
    calm = ndimage.binary_dilation(calm, iterations=2 * RES)
    steep = np.clip((height - 1500) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 260 + rough * (60 + 260 * steep))
    for d in sketch.get('districts', []):
        if d['space'].startswith('town:'):
            m = poly_mask(d['polygon'])
            level = np.median(height[m])
            target = {'town:winterkill': 1000, 'town:monastery': 1900, 'town:glom': 1350}.get(d['space'], level)
            soft = ndimage.gaussian_filter(m.astype(float), RES)
            height = height * (1 - soft) + target * soft
    water = np.zeros((size, size), bool)
    ice = np.zeros((size, size), bool)
    for body in sketch.get('water', {}).get('bodies', []):
        m = poly_mask(body['polygon'])
        if body['id'] == 'water:rim_sea':
            continue
        height[m] = body['level']
        (ice if body['id'] in ('water:mere', 'water:halon_pond') else water)[m] = True
    for river in sketch.get('water', {}).get('rivers', []):
        m = line_mask(river['line'], river.get('width_cells', 2))
        bank = ndimage.binary_dilation(m, iterations=2 * RES)
        fall = np.linspace(840, 800, len(river['line']))
        level = 820
        height[bank] = np.minimum(height[bank], np.maximum(height[bank] - 150, level + 40))
        height[m] = level
        frozen = m & (xx < 78)
        ice |= frozen
        water |= m & ~frozen
    rim = poly_mask([[0, 0], [24, 0], [24, 104], [128, 104], [128, 128], [0, 128]])
    height[rim] = 0
    return height, water, ice, rim


def space_masks(sketch):
    out = {}
    for d in sketch.get('districts', []):
        out.setdefault(d['space'], np.zeros((N * RES, N * RES), bool))
        out[d['space']] |= poly_mask(d['polygon'])
    return out


def colour_land(plan, sketch, height, water, ice, rim, ground):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = (238, 242, 248)
    masks = space_masks(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(size, size)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space in ['zone:steppe', 'zone:west_plateau', 'zone:snowfields', 'zone:ogre_hills', 'zone:troll_forest',
                  'zone:lagoon_marches', 'zone:arrival_meadow', 'zone:giants', 'zone:frostspine', 'zone:glacier',
                  'town:winterkill', 'town:monastery', 'town:glom']:
        if space in masks and space in ground:
            soft = ndimage.gaussian_filter(masks[space].astype(float), 2.5 * RES)
            soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
            rgb = rgb * (1 - soft) + np.array(ground[space]) * soft
    # rock where steep or high
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.45) * 2.2, 0, 1)
    rock = np.maximum(rock, np.clip((height - 2900) / 500, 0, 0.6))
    rgb = rgb * (1 - rock[..., None]) + np.array((118, 112, 110)) * rock[..., None]
    rgb[ice] = (205, 225, 238)
    rgb[water] = (52, 92, 112)
    # hillshade
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    shade = np.clip(0.55 + 0.6 * shade, 0.35, 1.15)
    rgb = rgb * shade[..., None]
    rgb[ice] = rgb[ice] * 0.85 + np.array((205, 225, 238)) * 0.15
    # stars below the rim
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    idx = rng.integers(0, size, size=(2200, 2))
    for y, x in idx:
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    # the cliff face (a band just outside the land, drawn as rock in shade)
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.2 * RES)) & rim
    rgb[cliff] = (96, 92, 104)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    # trees
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    for space, (density, colour) in TREES.items():
        if space not in masks:
            continue
        m = masks[space]
        ys, xs = np.nonzero(m[::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x = (cx + rng.random()) * RES
                y = (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or ice[hy, hx] or rim[hy, hx] or height[hy, hx] > 2600:
                    continue
                s = RES * (0.35 + 0.2 * rng.random())
                draw.polygon([(x, y - s * 1.3), (x + s * 0.7, y + s * 0.5), (x - s * 0.7, y + s * 0.5)],
                             fill=colour)
    return img


# ---------------------------------------------------------------- SVG plan

def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def pts(points, s):
    return ' '.join(f'{x * s:.1f},{y * s:.1f}' for x, y in points)


SYMBOLS = {
    'entrance': ('#0b6b3a', 'sq'), 'dungeon': ('#111', 'sq'), 'junction': ('#5a4630', 'dot'),
    'poi': ('#7a1f6a', 'dot'), 'chest': ('#b8860b', 'diamond'), 'npc': ('#1d5fa8', 'dot'),
    'camp': ('#b1361e', 'tri'), 'landmark': ('#c06000', 'star'),
}


def svg_plan(key, plan, sketch, project, labels, extra_svg='', scale=8):
    size = N * scale
    colour = Image.open(HERE / key / 'colour.png').resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    colour.save(buf, 'JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -30 {size + 60} {size + 60}" '
           f'width="{size + 60}" height="{size + 60}" font-family="DejaVu Sans, sans-serif">',
           f'<image href="data:image/jpeg;base64,{b64}" x="0" y="0" width="{size}" height="{size}"/>',
           '<defs><pattern id="quiet" width="10" height="10" patternUnits="userSpaceOnUse" '
           'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#2e8b57" '
           'stroke-width="2" stroke-opacity="0.55"/></pattern>'
           '<marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" '
           'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0b6b3a"/></marker></defs>']
    # grid every 16 cells
    for i in range(0, N + 1, 16):
        out.append(f'<line x1="{i * scale}" y1="0" x2="{i * scale}" y2="{size}" stroke="#000" '
                   'stroke-opacity="0.18" stroke-width="1"/>')
        out.append(f'<line x1="0" y1="{i * scale}" x2="{size}" y2="{i * scale}" stroke="#000" '
                   'stroke-opacity="0.18" stroke-width="1"/>')
        out.append(f'<text x="{i * scale}" y="-8" font-size="12" text-anchor="middle" fill="#ccc">{i}</text>')
        out.append(f'<text x="-8" y="{i * scale + 4}" font-size="12" text-anchor="end" fill="#ccc">{i}</text>')
    px, py, pw, ph = sketch['frame']['playable']
    out.append(f'<rect x="{px * scale}" y="{py * scale}" width="{pw * scale}" height="{ph * scale}" fill="none" '
               'stroke="#fff" stroke-opacity="0.7" stroke-dasharray="8 6" stroke-width="1.5"/>')
    # quiet and encounter areas
    enc_labels = labels.get('encounters', {})
    for area in sketch.get('areas', []):
        kind = area.get('kind', 'encounter')
        poly = area.get('polygon')
        if not poly:
            continue
        if kind in ('keep_clear', 'open'):
            out.append(f'<polygon points="{pts(poly, scale)}" fill="url(#quiet)" stroke="#2e8b57" '
                       'stroke-opacity="0.8" stroke-width="1.5" stroke-dasharray="4 3"/>')
        else:
            colour_e = enc_labels.get(area['id'], {}).get('colour', '#d0302a')
            out.append(f'<polygon points="{pts(poly, scale)}" fill="{colour_e}" fill-opacity="0.13" '
                       f'stroke="{colour_e}" stroke-width="2.2" stroke-opacity="0.9"/>')
    # roads
    for road in sketch.get('roads', []):
        lane = road.get('width') == 'lane'
        w = 3 if lane else 5
        out.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" stroke="#3b2a1a" '
                   f'stroke-width="{w + 2}" stroke-opacity="0.55" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" stroke="{"#d8c49a" if lane else "#c49a5a"}" '
                   f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'
                   f'{" stroke-dasharray=\"7 4\"" if lane else ""}/>')
    # plots
    buildings = {}
    for space in plan['spaces']:
        for b in space.get('buildings', []) or []:
            buildings[b['id']] = b
    for d in sketch.get('districts', []):
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            fp = b['footprint_cells'][(plot.get('index') or 1) - 1]
            front, depth = fp
            wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
            x, y = plot['at']
            service = b['service'] != 'residence'
            fill = '#6e3b2a' if service else '#8a6a52'
            out.append(f'<rect x="{x * scale:.1f}" y="{y * scale:.1f}" width="{wx * scale:.1f}" height="{wy * scale:.1f}" '
                       f'fill="{fill}" stroke="#2a1a10" stroke-width="1.2"/>')
            # door tick on the front side
            cx, cy = (x + wx / 2) * scale, (y + wy / 2) * scale
            f = plot['facing']
            tx, ty = {'n': (cx, y * scale), 's': (cx, (y + wy) * scale), 'e': ((x + wx) * scale, cy),
                      'w': (x * scale, cy)}[f]
            out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="2.2" fill="#ffd34d" stroke="#2a1a10" stroke-width="0.8"/>')
    # cameras
    for view in sketch.get('views', []):
        x, y = view['at']
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = math.hypot(lx - x, ly - y)
        half = math.radians(35)
        p1 = (x + math.cos(ang - half) * dist, y + math.sin(ang - half) * dist)
        p2 = (x + math.cos(ang + half) * dist, y + math.sin(ang + half) * dist)
        signature = 'glacier' in view['id'] or 'bridge' in view['id'] or 'arrival' in view['id']
        if not signature:
            continue
        col = '#1f6fd1' if signature else '#5b7fa8'
        out.append(f'<polygon points="{pts([(x + .5, y + .5), p1, p2], scale)}" fill="{col}" fill-opacity="0.12" '
                   f'stroke="{col}" stroke-width="1.5" stroke-dasharray="6 4"/>')
        out.append(f'<line x1="{(x + .5) * scale}" y1="{(y + .5) * scale}" x2="{(lx + .5) * scale}" '
                   f'y2="{(ly + .5) * scale}" stroke="{col}" stroke-width="2"/>')
        out.append(f'<circle cx="{(x + .5) * scale}" cy="{(y + .5) * scale}" r="6" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
    out.append(extra_svg)
    # points
    seen = set()
    for point in sketch.get('points', []):
        pid = point['id']
        x, y = point['at']
        cx, cy = (x + 0.5) * scale, (y + 0.5) * scale
        kind = labels['kinds'].get(pid, 'poi')
        colour_p, shape = SYMBOLS[kind]
        if shape == 'sq':
            out.append(f'<rect x="{cx - 6}" y="{cy - 6}" width="12" height="12" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'diamond':
            out.append(f'<polygon points="{cx},{cy - 7} {cx + 7},{cy} {cx},{cy + 7} {cx - 7},{cy}" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'tri':
            out.append(f'<polygon points="{cx},{cy - 8} {cx + 7},{cy + 6} {cx - 7},{cy + 6}" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'star':
            star = []
            for i in range(10):
                r = 9 if i % 2 == 0 else 4
                a = -math.pi / 2 + i * math.pi / 5
                star.append(f'{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}')
            out.append(f'<polygon points="{" ".join(star)}" fill="{colour_p}" stroke="#fff" stroke-width="1.2"/>')
        else:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{colour_p}" stroke="#fff" stroke-width="1.5"/>')
        if kind == 'entrance' and pid.startswith('entrance:') and point.get('facing') and \
                labels['arrows'].get(pid):
            dx, dy = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0)}[point['facing']]
            out.append(f'<line x1="{cx - dx * 26}" y1="{cy - dy * 26}" x2="{cx - dx * 9}" y2="{cy - dy * 9}" '
                       'stroke="#0b6b3a" stroke-width="4" marker-end="url(#arr)"/>')
        text = labels['names'].get(pid)
        if not text or (pid, text) in seen:
            continue
        seen.add((pid, text))
        dx, dy, anchor = labels['offsets'].get(pid, (9, 4, 'start'))
        out.append(f'<text x="{cx + dx}" y="{cy + dy}" font-size="12.5" text-anchor="{anchor}" fill="#111" '
                   f'stroke="#fff" stroke-width="3.2" paint-order="stroke" stroke-linejoin="round">{esc(text)}</text>')
    # area and zone captions
    for text, (x, y), size_t, colour_t in labels.get('captions', []):
        out.append(f'<text x="{x * scale}" y="{y * scale}" font-size="{size_t}" font-style="italic" '
                   f'text-anchor="middle" fill="{colour_t}" stroke="#fff" stroke-width="3" stroke-opacity="0.75" '
                   f'paint-order="stroke">{esc(text)}</text>')
    # scale bar: 10 cells = 5,120 units
    bx, by = 4 * scale, (N - 6) * scale
    out.append(f'<rect x="{bx - 6}" y="{by - 22}" width="{10 * scale + 120}" height="34" fill="#000" fill-opacity="0.55"/>')
    out.append(f'<line x1="{bx}" y1="{by}" x2="{bx + 10 * scale}" y2="{by}" stroke="#fff" stroke-width="4"/>')
    out.append(f'<text x="{bx + 10 * scale + 8}" y="{by + 5}" font-size="13" fill="#fff">5,120 units (10 cells)</text>')
    out.append(f'<text x="{bx}" y="{by - 8}" font-size="12" fill="#fff">grid: 16 cells = 8,192 units</text>')
    out.append('</svg>')
    return '\n'.join(out)


# ---------------------------------------------------------------- perspective blockout

def blockout(height, colour_img, view, models, out_path, w=1536, h=1024, fov=70.0, annotations=None):
    """A heightfield ray cast from the sketch's camera, with the plan's buildings as dark blocks: composition only."""
    size = height.shape[0]
    col = np.asarray(colour_img.convert('RGB')).astype(float)
    cx, cy = (view['at'][0] + 0.5) * RES, (view['at'][1] + 0.5) * RES
    ground = height[int(cy), int(cx)]
    eye = ground + view.get('height', 180)
    lx, ly = (view['look'][0] + 0.5) * RES, (view['look'][1] + 0.5) * RES
    yaw = math.atan2(ly - cy, lx - cx)
    look_h = height[int(min(ly, size - 1)), int(min(lx, size - 1))]
    dist_look = math.hypot(lx - cx, ly - cy) * 512 / RES
    pitch = math.radians(view.get('pitch', -4.0))
    unit = RES / 512.0                     # raster pixels per map unit
    img = np.zeros((h, w, 3))
    # sky gradient (winter overcast) and the stars below the horizon line
    for yy in range(h):
        t = yy / h
        img[yy, :] = (176 + 40 * t, 186 + 36 * t, 198 + 30 * t)
    focal = (w / 2) / math.tan(math.radians(fov / 2))
    horizon = h / 2 + focal * math.tan(pitch)
    max_d = 30000.0
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, max_d, 40.0)])
    for sx in range(w):
        a = yaw + math.atan2(sx - w / 2, focal)
        dx, dy = math.cos(a), math.sin(a)
        corr = math.cos(a - yaw)
        ybuf = h
        rx = cx + dx * zs * unit
        ry = cy + dy * zs * unit
        inside = (rx >= 0) & (rx < size - 1) & (ry >= 0) & (ry < size - 1)
        for k in np.nonzero(inside)[0]:
            ix, iy = int(rx[k]), int(ry[k])
            fx, fy = rx[k] - ix, ry[k] - iy
            hgt = (height[iy, ix] * (1 - fx) * (1 - fy) + height[iy, ix + 1] * fx * (1 - fy)
                   + height[iy + 1, ix] * (1 - fx) * fy + height[iy + 1, ix + 1] * fx * fy)
            z = zs[k] * corr
            sy = int(horizon - (hgt - eye) / z * focal)
            if sy < ybuf:
                c = col[iy, ix]
                if hgt <= 1:            # below the rim: the stars
                    c = np.array((14, 16, 32))
                fog = min(1.0, (zs[k] / 16000.0) ** 1.6) * 0.85
                c = c * (1 - fog) + np.array((190, 198, 210)) * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
        if ybuf > horizon:
            # below the rim line: void with stars
            img[int(max(horizon, 0)):ybuf, sx] = (14, 16, 32)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(out)
    # models: (cell x, cell y, base height, top height, half width cells, colour)
    order = []
    for m in models:
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        d = math.hypot(mx - cx, my - cy) / unit
        order.append((d, m))
    for d, m in sorted(order, reverse=True):
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        a = math.atan2(my - cy, mx - cx) - yaw
        a = (a + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2 + 5) or d < 200:
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(my), int(mx)] if m[2] is None else m[2]
        top = base + m[3]
        y0 = horizon - (top - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        fog = min(1.0, (d / 16000.0) ** 1.6) * 0.85
        c = tuple(int(v * (1 - fog) + f * fog) for v, f in zip(m[5], (190, 198, 210)))
        draw.rectangle((sx - half, y0, sx + half, y1), fill=c)
    # annotations: where the plan's named things fall in this view (a guide for the painter, not for the picture)
    for label, ax, ay, rise in annotations or []:
        mx, my = (ax + 0.5) * RES, (ay + 0.5) * RES
        a = math.atan2(my - cy, mx - cx) - yaw
        a = (a + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2):
            continue
        d = math.hypot(mx - cx, my - cy) / unit
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(min(my, size - 1)), int(min(mx, size - 1))] + rise
        sy = horizon - (base - eye) / z * focal
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=(220, 30, 30), width=4)
        draw.text((sx + 12, sy - 12), label, fill=(200, 20, 20), font=FONT)
    out.save(out_path)
    return out_path


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else 'x5'
    plan, sketch, project = load(key)
    folder = HERE / key
    folder.mkdir(exist_ok=True)
    height, water, ice, rim = build_land(plan, sketch)
    img = colour_land(plan, sketch, height, water, ice, rim, X5_GROUND)
    img.save(folder / 'colour.png')
    import labels_x5 as labels_mod
    svg = svg_plan(key, plan, sketch, project, labels_mod.LABELS, labels_mod.extra_svg(8))
    (folder / f'plan_{key}.svg').write_text(svg)
    for view in sketch.get('views', []):
        name = view['id'].split(':')[1]
        blockout(height, img, view, labels_mod.MODELS, folder / f'blockout_{name}.png', fov=view.get('fov', 80.0),
                 annotations=labels_mod.ANNOTATIONS.get(view['id']))
    print('heights', int(height.min()), int(height.max()), 'written to', folder)


if __name__ == '__main__':
    main()
