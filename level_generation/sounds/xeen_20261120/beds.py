#!/usr/bin/env python3
"""Lay out the outdoor ambience beds of the Xeen maps (lane AU, devdocs/xeen/AUDIO.md "Outdoor beds").

    python3 level_generation/sounds/xeen_20261120/beds.py [maps...]

Reads beds.yml: per map, the fields of one bed each (a sound over the union of some of the sketch's districts, less
others), with a hex lattice spacing in cells, the radii in game units, the volume and day/night. Writes:

- review/beds/<map>.png: the map's minimap with each emitter's inner and outer circle, by bed;
- review/beds/<map>.yml: the sketch.yml `sounds:` entries, ready to paste (the map lanes own the sketches); every bed
  emitter carries `pan: false` (D-48: heard centred, by distance only), a field's `pan: true` keeps panning, and the
  `extra` point sounds (sand-falls, Kalindra's shimmer) are written as given, panned;
- a coverage line per field: the share of the field's cells whose summed bed level (power sum of the emitters' linear
  falloff, devdocs/AMBIENT_SOUNDS.md) lies within 3 dB of one emitter heard at full volume, and the lowest and highest.

The engine's falloff is linear in amplitude from the inner to the outer radius (engine/AudioSystem.cpp), so a hex
lattice with spacing about the outer radius and an inner radius of about 0.4 of it keeps the bed within about 2 dB.
"""
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BRIEFS = REPO / 'devdocs/xeen/briefs'
MINIMAPS = REPO / 'assets_dev/worlds/xeen/icons_x2'
OUT = HERE / 'review/beds'
CELL = 512.0
COLOURS = {'xeen_amb_meadow': (255, 230, 60), 'xeen_amb_lagoon': (60, 220, 255), 'xeen_amb_tundra': (255, 255, 255),
           'xeen_amb_savannah': (255, 150, 40), 'xeen_amb_desert': (255, 90, 200), 'xeen_amb_darkside': (180, 120, 255),
           'xeen_sandfall_loop': (255, 0, 0), 'xeen_phase_loop': (0, 255, 120), 'xeen_amb_aspen': (120, 255, 120),
           'xeen_amb_necropolis': (200, 200, 255), 'xeen_lavafall_loop': (255, 60, 0), 'lava loop': (255, 140, 0),
           'humming': (0, 255, 255)}


def inside(point, polygon):
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def region_test(districts, zones, exclude, playable):
    x0, y0, w, h = playable
    polys = [districts[z] for z in zones if z != '*']
    cuts = [districts[z] for z in exclude]

    def test(point):
        if not (x0 <= point[0] <= x0 + w and y0 <= point[1] <= y0 + h):
            return False
        whole = zones == ['*']
        return (whole or any(inside(point, p) for p in polys)) and not any(inside(point, p) for p in cuts)
    return test


def lattice(spacing, playable, offset):
    x0, y0, w, h = playable
    dy = spacing * math.sqrt(3) / 2
    row = 0
    y = y0 + offset[1]
    while y <= y0 + h:
        x = x0 + offset[0] + (spacing / 2 if row % 2 else 0)
        while x <= x0 + w:
            yield (round(x * 2) / 2, round(y * 2) / 2)
            x += spacing
        y += dy
        row += 1


def gain(distance, inner, outer):
    return np.clip(1.0 - (distance - inner) / (outer - inner), 0.0, 1.0)


def main():
    config = yaml.safe_load((HERE / 'beds.yml').read_text())
    wanted = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    for name, spec in config['maps'].items():
        if wanted and name not in wanted:
            continue
        sketch = yaml.safe_load((BRIEFS / name / 'L4/sketch.yml').read_text())
        playable = sketch['frame']['playable']
        districts = {d['space']: [tuple(p) for p in d['polygon']] for d in sketch.get('districts') or []
                     if d.get('polygon')}
        entries, lines = [], []
        for field in spec['fields']:
            test = region_test(districts, field['zones'], field.get('exclude', []), playable)
            points = [p for p in lattice(field['spacing'], playable, field.get('offset', [0, 0])) if test(p)]
            points = [p for p in points if list(p) not in field.get('drop', [])]
            points += [tuple(p) for p in field.get('add', [])]
            for index, point in enumerate(points, 1):
                entry = {'id': f"sound:{field['id']}_{index}", 'at': list(point), 'sound': field['sound'],
                         'radius': field['radius'], 'inner_radius': field['inner']}
                if field['volume'] != 1:
                    entry['volume'] = field['volume']
                for flag in ('day_only', 'night_only'):
                    if field.get(flag):
                        entry[flag] = True
                # D-48: a bed surrounds the party, so it is heard centred (its falloff stays); point sounds pan.
                if not field.get('pan', False):
                    entry['pan'] = False
                if 'wait' in field:
                    entry['wait'] = field['wait']
                entries.append((field, entry))
            # Coverage over the field's cells: the summed level of this field's emitters, relative to one at full.
            cells = [(x + 0.5, y + 0.5) for x in range(128) for y in range(128) if test((x + 0.5, y + 0.5))]
            if cells and points:
                c = np.array(cells) * CELL
                e = np.array(points) * CELL
                d = np.sqrt(((c[:, None, :] - e[None, :, :]) ** 2).sum(-1))
                power = (gain(d, field['inner'], field['radius']) ** 2).sum(1)
                level = 10 * np.log10(np.maximum(power, 1e-6))
                ok = float(np.mean((level >= -3) & (level <= 3))) * 100
                lines.append(f"{name} {field['id']}: {len(points)} emitters, {len(cells)} cells, within 3 dB "
                             f"{ok:.0f} %, lowest {level.min():.1f} dB, highest {level.max():.1f} dB")
            else:
                lines.append(f"{name} {field['id']}: {len(points)} emitters over {len(cells)} cells")
        for extra in spec.get('extra', []):
            entries.append(({'sound': extra['sound']}, extra))
        draw_map(name, entries, districts)
        write_entries(name, entries)
        print('\n'.join(lines))


def draw_map(name, entries, districts):
    scale = 768 / 128
    minimap = MINIMAPS / f'xeen_{name}.png'
    if minimap.exists():
        image = Image.open(minimap).convert('RGB').resize((768, 768))
    else:
        # A map not installed yet (D5, D6 in session 4): the sketch's district outlines on grey.
        image = Image.new('RGB', (768, 768), (60, 60, 60))
        lines = ImageDraw.Draw(image)
        for polygon in districts.values():
            lines.polygon([(x * scale, y * scale) for x, y in polygon], outline=(150, 150, 150))
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for field, entry in entries:
        colour = COLOURS.get(field['sound'], (255, 255, 255))
        x, y = entry['at'][0] * scale, entry['at'][1] * scale
        for radius, alpha, width in ((entry['radius'], 110, 1), (entry['inner_radius'], 255, 2)):
            r = radius / CELL * scale
            draw.ellipse([x - r, y - r, x + r, y + r], outline=colour + (alpha,), width=width)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=colour + (255,))
    Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB').save(OUT / f'{name}.png')


def write_entries(name, entries):
    text = []
    for _, entry in entries:
        parts = []
        for key in ('id', 'at', 'sound', 'radius', 'inner_radius', 'volume', 'height', 'wait', 'loop', 'day_only',
                    'night_only', 'on', 'pan'):
            if key in entry:
                value = entry[key]
                if isinstance(value, list):
                    value = '[' + ', '.join(f'{v:g}' if isinstance(v, float) else str(v) for v in value) + ']'
                elif isinstance(value, bool):
                    value = 'true' if value else 'false'
                parts.append(f'{key}: {value}')
        text.append('  - {' + ', '.join(parts) + '}')
    (OUT / f'{name}.yml').write_text('sounds:\n' + '\n'.join(text) + '\n')


if __name__ == '__main__':
    main()
