"""How MM7 and MM8 populate their towns, and Landfall beside them: placed peasants and guards per million square units
of the houses' bounding box, from the shipped scenes (initial actors, spawn points) and ODMs (BModels with a clickable
face, under 6 000 across, stand for the houses).

    python3 level_generation/projects/hesper_out1/town_density.py     # prints the rows, writes review/density/

A town is a cluster of peasants and guards (single linkage, 3 000), its box the houses within 1 500 of the cluster;
people count within 600 of that box. Writes one top-down plot per town at a common scale (grey houses, green
peasants, red guards, grey other actors, purple crosses the encounter spawn points) and a sheet.
"""
import csv
import json
import math
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

OUT = PROJECT / 'review/density'
rows = list(csv.reader(open(ROOT / 'assets_dev/engine/data_tables/monster_data.txt'), delimiter='\t'))
NAMES = {int(r[0]): r[1] for r in rows if r and r[0].isdigit()}
for line in (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines():
    cells = line.split('\t')
    if cells[0].isdigit():
        NAMES[int(cells[0])] = cells[1]
PEASANT = ('peasant', 'farmer', 'villager')
# The towns' armed friendly actors, read from each map's roster.
GUARD = {'Guard', 'Elven Defender', 'Brass Golem', 'Bowman', 'Lizardman Sergeant', 'Dark Elven Defender',
         'Troll Warrior', 'Necromancer', 'Landfall Guard', 'Guard Sergeant', "Warden's Guard"}
MAPS = [('mm7', 'worlds/mm7/maps/7out01', 'Emerald Island'), ('mm7', 'worlds/mm7/maps/7out02', 'Harmondale'),
        ('mm7', 'worlds/mm7/maps/7out04', 'Tularean Forest'), ('mm7', 'worlds/mm7/maps/7out05', 'Deyja'),
        ('mm7', 'worlds/mm7/maps/7out13', 'Tatalia'), ('mm7', 'worlds/mm7/maps/out14', 'Avlee'),
        ('mm8', 'worlds/mm8/maps/out01', 'Dagger Wound'), ('mm8', 'worlds/mm8/maps/out02', 'Ravenshore'),
        ('mm8', 'worlds/mm8/maps/out03', 'Alvar'), ('mm8', 'worlds/mm8/maps/out04', 'Ironsand'),
        ('mm8', 'worlds/mm8/maps/out06', 'Shadowspire'),
        ('hesper', 'runtime/worlds/hesper/maps/hes_out1', 'Landfall')]
SCALE = 0.025                                    # pixels per world unit in the plots


def load(world, stem):
    base = (PROJECT / stem) if world == 'hesper' else (ROOT / 'assets_dev' / stem)
    scene = yaml.load(open(f'{base}.scene.yml'), Loader=yaml.CSafeLoader)
    odm = parse_odm_file(Path(f'{base}.odm'))['payload']
    people = []
    for a in scene['initial_state']['actors']:
        name = NAMES.get(a['monster_info_id'] or a['monster_id'], '?')
        kind = 'peasant' if any(k in name.lower() for k in PEASANT) else 'guard' if name in GUARD else 'other'
        people.append((a['position']['x'], a['position']['y'], kind))
    houses = []
    for b in odm['bmodels']:
        xs, ys = [v['x'] for v in b['vertices']], [v['y'] for v in b['vertices']]
        if xs and any(f['cog_triggered_number'] for f in b['faces']) and max(xs) - min(xs) < 6000 \
                and max(ys) - min(ys) < 6000:
            houses.append((min(xs), min(ys), max(xs), max(ys)))
    spawns = [(s['position']['x'], s['position']['y']) for s in scene.get('spawns', []) if s['type_id'] == 3]
    return people, houses, spawns


def towns(people, houses):
    members = [p for p in people if p[2] != 'other']
    parent = list(range(len(members)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            if math.hypot(members[i][0] - members[j][0], members[i][1] - members[j][1]) < 3000:
                parent[find(i)] = find(j)
    groups = {}
    for i, member in enumerate(members):
        groups.setdefault(find(i), []).append(member)
    for group in groups.values():
        if len(group) < 6:
            continue
        x0, x1 = min(p[0] for p in group) - 1500, max(p[0] for p in group) + 1500
        y0, y1 = min(p[1] for p in group) - 1500, max(p[1] for p in group) + 1500
        found = [h for h in houses if x0 < (h[0] + h[2]) / 2 < x1 and y0 < (h[1] + h[3]) / 2 < y1]
        if len(found) >= 4:
            yield (min(h[0] for h in found), min(h[1] for h in found), max(h[2] for h in found),
                   max(h[3] for h in found)), len(found)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results, plots = [], []
    for world, stem, title in MAPS:
        people, houses, spawns = load(world, stem)
        boxes = sorted(towns(people, houses), key=lambda t: -t[1])[:1]          # the main town of the map
        for (x0, y0, x1, y1), count in boxes:
            def inside(p, pad=600):
                return x0 - pad < p[0] < x1 + pad and y0 - pad < p[1] < y1 + pad
            peasants = sum(p[2] == 'peasant' and inside(p) for p in people)
            guards = [p for p in people if p[2] == 'guard' and inside(p)]
            paired = sum(any(0 < math.hypot(g[0] - h[0], g[1] - h[1]) < 700 for h in guards) for g in guards)
            area = (x1 - x0) * (y1 - y0) / 1e6
            results.append({'world': world, 'town': title, 'size': [x1 - x0, y1 - y0], 'houses': count,
                            'peasants': peasants, 'guards': len(guards), 'guards_paired': paired,
                            'spawns_in_town': sum(inside(s) for s in spawns),
                            'peasants_per_million': round(peasants / area, 2),
                            'guards_per_million': round(len(guards) / area, 3)})
            pad = 2500
            image = Image.new('RGB', (int((x1 - x0 + 2 * pad) * SCALE), int((y1 - y0 + 2 * pad) * SCALE) + 16),
                              'white')
            draw = ImageDraw.Draw(image)

            def at(x, y):
                return (x - x0 + pad) * SCALE, (y1 + pad - y) * SCALE + 16
            for hx0, hy0, hx1, hy1 in houses:
                draw.rectangle([at(hx0, hy1), at(hx1, hy0)], fill=(160, 160, 160))
            draw.rectangle([at(x0, y1), at(x1, y0)], outline=(0, 0, 0))
            for x, y in spawns:
                cx, cy = at(x, y)
                draw.line([cx - 3, cy - 3, cx + 3, cy + 3], fill=(140, 0, 200))
                draw.line([cx - 3, cy + 3, cx + 3, cy - 3], fill=(140, 0, 200))
            for x, y, kind in people:
                cx, cy = at(x, y)
                colour = {'peasant': (0, 150, 0), 'guard': (220, 0, 0), 'other': (130, 130, 130)}[kind]
                draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=colour)
            draw.text((4, 2), f'{title}: {peasants} peasants, {len(guards)} guards, {x1 - x0}x{y1 - y0}',
                      fill=(0, 0, 0))
            name = title.lower().replace(' ', '_')
            image.save(OUT / f'{name}.png')
            plots.append(image)
    columns = 4
    rows_ = [plots[i:i + columns] for i in range(0, len(plots), columns)]
    sheet = Image.new('RGB', (sum(p.width for p in max(rows_, key=lambda r: sum(p.width for p in r))) + 10 * columns,
                              sum(max(p.height for p in r) + 10 for r in rows_)), 'white')
    y = 0
    for row in rows_:
        x = 0
        for plot in row:
            sheet.paste(plot, (x, y))
            x += plot.width + 10
        y += max(p.height for p in row) + 10
    sheet.save(OUT / 'sheet.png')
    (OUT / 'density.json').write_text(json.dumps(results, indent=1) + '\n')
    for r in results:
        print(json.dumps(r))


main()
