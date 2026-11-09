"""How MM6, MM7 and MM8 populate their outdoor maps with hostile monsters, from the shipped scenes, ODMs, event
scripts and map_stats rows: spawn points (encounter slots and group sizes), placed hostile actors, and where they lie
relative to the towns, chests, dungeon entrances, roads, ground items and the map's edge.

    python3 level_generation/projects/hesper_out1/spawn_density.py    # prints the rows, writes review/spawn_density/

A spawn point spawns, on the first visit and every refill, a group of its slot's count range (map_stats `#`), of a
random tier by the slot's difficulty or of a fixed tier (index 4-12). "Expected" is the mean of that range. A placed
actor is hostile when its relation to the party (hostile.txt, the engine's rule) is hostile or it carries the
Aggressor bit or its group is set Hostile by the map's script; an invisible one waits for an event and is
counted apart. The town is the largest cluster of house doors (enter_house events, single linkage 2 000); "near" is
within 2 500 units (about 5 s of walking). Land excludes the water tiles. Hesper's Starport Reach is measured the same
way from its spawn data (spawns.yml through spawns.py).
"""
import csv
import json
import math
import re
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
DEV = ROOT / 'assets_dev'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

OUT = PROJECT / 'review/spawn_density'
NEAR = 2500
MAPS = [('mm6', 'oute3', 'New Sorpigal'), ('mm6', 'outd3', 'Castle Ironfist'), ('mm6', 'outd2', 'Bootleg Bay'),
        ('mm6', 'outb2', 'Blackshire'), ('mm6', 'outc1', 'Frozen Highlands'),
        ('mm7', '7out01', 'Emerald Island'), ('mm7', '7out02', 'Harmondale'), ('mm7', '7out03', 'Erathia'),
        ('mm7', '7out13', 'Tatalia'), ('mm7', 'out14', 'Avlee'),
        ('mm8', 'out01', 'Dagger Wound'), ('mm8', 'out02', 'Ravenshore'), ('mm8', 'out03', 'Alvar'),
        ('mm8', 'out04', 'Ironsand'), ('mm8', 'out05', 'Garrote Gorge')]
TILE_FILES = {'mm6': 'terrain_tile_data_3.txt', 'mm7': 'terrain_tile_data_2.txt', 'mm8': 'terrain_tile_data.txt'}
WATER = 5                                        # the water tileset; a road set has 'cros' (crossing) tiles
AGGRESSOR, INVISIBLE = 0x00080000, 0x00010000   # actor attributes; an invisible actor waits for an event
SCALE = 0.006                                    # plot pixels per world unit


def table(path):
    return list(csv.reader(open(path, encoding='utf-8', errors='replace'), delimiter='\t'))


MONSTERS = [r for r in table(DEV / 'engine/data_tables/monster_data.txt') if r and r[0].isdigit()]
BY_ID = {int(r[0]): r for r in MONSTERS}
BY_PICTURE = {r[2].strip().lower(): int(r[0]) for r in MONSTERS}
RELATIONS = [r for r in table(DEV / 'engine/data_tables/hostile.txt')[1:] if len(r) >= 2]
PARTY = [int(c) if c.strip() else 0 for c in RELATIONS[0][1:]]
STATS = {r[2].lower(): r for r in table(DEV / 'engine/data_tables/map_stats.txt') if len(r) > 27 and r[0].isdigit()}


def hostile_id(monster_id):
    index = (monster_id - 1) // 3 + 1 if monster_id > 0 else 0
    return index < len(PARTY) and PARTY[index] > 0


def count_range(text):
    text = text.strip()
    if not text or text == '0':
        return 0, 0
    low, _, high = text.partition('-')
    return int(low), int(high or low)


def slots(stats):
    """The map's three encounter slots: (picture, difficulty, min, max, hostile)."""
    result = {}
    for slot, column in ((1, 16), (2, 20), (3, 24)):
        picture = stats[column].strip()
        low, high = count_range(stats[column + 3])
        monster = BY_PICTURE.get(f'{picture} a'.lower())
        if picture in ('', '0') or monster is None:
            continue
        result[slot] = {'picture': picture, 'name': BY_ID[monster][1], 'difficulty': int(stats[column + 2] or 0),
                        'count': (low, high), 'hostile': hostile_id(monster)}
    return result


def lua_events(path):
    """Event ids by kind from the map's event script: chests (openedChestIds and OpenChest), dungeon entrances
    (enter_dungeon actions and MoveToMap to a .blv) and houses (enter_house)."""
    text = path.read_text(errors='replace') if path.exists() else ''
    kinds = {'chest': set(), 'dungeon': set(), 'house': set()}
    for match in re.finditer(r'\[(\d+)\]\s*=\s*\{\s*kind\s*=\s*"(enter_dungeon|enter_house)"', text):
        kinds['dungeon' if match.group(2) == 'enter_dungeon' else 'house'].add(int(match.group(1)))
    block = re.search(r'openedChestIds\s*=\s*\{(.*?)\n\s*\},', text, re.S)
    if block:
        kinds['chest'].update(int(k) for k in re.findall(r'\[(\d+)\]\s*=', block.group(1)))
    for match in re.finditer(r'Register\w*Event\((\d+),(.*?)(?=\nRegister|\Z)', text, re.S):
        body = match.group(2)
        if 'OpenChest(' in body:
            kinds['chest'].add(int(match.group(1)))
        if re.search(r'MoveToMap\([^)]*\.blv"', body, re.I):
            kinds['dungeon'].add(int(match.group(1)))
    return kinds


def event_points(scene, odm, events):
    """One point per (event, model or decoration) carrying it: face centroids of the BModels, decoration spots."""
    points = []
    for model in odm['bmodels']:
        seen = set()
        for face in model['faces']:
            event = face['cog_triggered_number']
            if event in events and event not in seen:
                seen.add(event)
                vs = [model['vertices'][i] for i in face['vertex_indices']]
                points.append((sum(v['x'] for v in vs) / len(vs), sum(v['y'] for v in vs) / len(vs)))
    for entity in scene['entities']:
        if {entity['event_id_primary'], entity['event_id_secondary']} & events:
            points.append((entity['position']['x'], entity['position']['y']))
    return points


def clusters(points, link):
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if math.dist(points[i], points[j]) < link:
                parent[find(i)] = find(j)
    groups = {}
    for i, p in enumerate(points):
        groups.setdefault(find(i), []).append(p)
    return sorted(groups.values(), key=len, reverse=True)


def box_distance(p, box):
    dx = max(box[0] - p[0], 0, p[0] - box[2])
    dy = max(box[1] - p[1], 0, p[1] - box[3])
    return math.hypot(dx, dy)


def nearest(p, points):
    return min((math.dist(p, q) for q in points), default=float('inf'))


def load_mm(world, stem):
    base = DEV / f'worlds/{world}/maps/{stem}'
    scene = yaml.load(open(f'{base}.scene.yml'), Loader=yaml.CSafeLoader)
    odm = parse_odm_file(Path(f'{base}.odm'))['payload']
    stats = STATS[f'{stem}.odm']
    tiles = [r for r in table(DEV / 'engine/data_tables' / TILE_FILES[world])[1:] if r and r[0].isdigit()]
    tileset = {int(r[0]): int(r[4]) for r in tiles}
    road_sets = {int(r[4]) for r in tiles if 'cros' in r[1].lower()}
    lookups = odm['tile_set_lookup_indices']
    bases = {0: 0, 1: 450, 2: 630}

    def kind(t):
        if t < 90:
            index = t if t == 0 or world == 'mm6' else bases.get(odm['master_tile'], 0) + t   # MM6: no remap
        elif t < 234:
            index = lookups[(t - 90) // 36] + (t - 90) % 36
        else:
            return None
        return tileset.get(index)
    sets = [kind(t) for t in odm['tile_map']]
    roads = [cell_point(i) for i, s in enumerate(sets) if s in road_sets]
    script = DEV / f'worlds/{world}/events/maps/{stem}.lua'
    events = lua_events(script)
    # Groups the map's script turns hostile (MM7 sets spawn groups Hostile on load, some after a quest).
    hostile_groups = {int(g) for g in re.findall(r'SetMonGroupBit\((\d+),\s*MonsterBits\.Hostile,\s*1\)',
                                                 script.read_text(errors='replace'))}
    encounter = slots(stats)
    spawns = []
    for s in scene['spawns']:
        if s['type_id'] != 3:
            continue
        index = s['index']
        slot = index if index <= 3 else (index - 4) % 3 + 1 if index <= 12 else 0
        if slot not in encounter:
            continue
        tier = None if index <= 3 else 'ABC'[(index - 4) // 3]
        spawns.append({'x': s['position']['x'], 'y': s['position']['y'], 'slot': slot, 'tier': tier,
                       'count': encounter[slot]['count'],
                       'hostile': encounter[slot]['hostile'] or s['group'] in hostile_groups})
    placed, hidden = [], 0
    for a in scene['initial_state']['actors']:
        if a['attributes'] & INVISIBLE:
            hidden += 1
            continue
        monster = a['monster_info_id'] or a['monster_id']
        hostile = bool(a['attributes'] & AGGRESSOR) or hostile_id(monster) or a['group'] in hostile_groups
        placed.append({'x': a['position']['x'], 'y': a['position']['y'], 'hostile': hostile,
                       'name': BY_ID.get(monster, ['', '?'])[1]})
    items = [(o['position']['x'], o['position']['y']) for o in scene['initial_state']['sprite_objects']
             if o.get('raw_containing_item_hex', '00000000')[:8] != '00000000']
    return {'scene': scene, 'odm': odm, 'stats': stats, 'sets': sets, 'roads': roads, 'slots': encounter,
            'spawns': spawns,
            'placed': placed, 'hidden': hidden, 'items': items,
            'chests': event_points(scene, odm, events['chest']),
            'dungeons': event_points(scene, odm, events['dungeon']),
            'houses': event_points(scene, odm, events['house']),
            'start': next(((e['position']['x'], e['position']['y']) for e in scene['entities']
                           if e['name'].lower() == 'party start'), None),
            'refill': int(stats[6] or 0)}


def load_hesper():
    """Starport Reach from its built scene and the placement data (spawns.py writes `work/spawns_plan.json`)."""
    plan = json.loads((PROJECT / 'work/spawns_plan.json').read_text())
    base = PROJECT / 'runtime/worlds/hesper/maps/hes_out1'
    scene = yaml.load(open(f'{base}.scene.yml'), Loader=yaml.CSafeLoader)
    odm = parse_odm_file(Path(f'{base}.odm'))['payload']
    hostile_ids = set(plan['hostile_monsters'])
    placed = [{'x': a['position']['x'], 'y': a['position']['y'], 'hostile': a['monster_id'] in hostile_ids,
               'name': str(a['monster_id'])} for a in scene['initial_state']['actors']
              if not a['attributes'] & INVISIBLE]
    spawns = [{'x': s['position'][0], 'y': s['position'][1], 'slot': s['slot'], 'tier': s['tier'],
               'count': tuple(plan['slots'][str(s['slot'])]['count']), 'hostile': True} for s in plan['spawns']]
    # Land: below the Ash Sea's dune walls and Landfall's cliff tops (spawns.py GROUND_MAX_Z), Hesper's water edge.
    return {'scene': scene, 'odm': odm, 'sets': [0 if h * 32 < 4200 else None for h in odm['height_map']],
            'slots': {int(k): v for k, v in plan['slots'].items()}, 'spawns': spawns, 'placed': placed,
            'items': [tuple(p) for p in plan['features']['items']],
            'chests': [tuple(p) for p in plan['features']['chests']],
            'dungeons': [tuple(p) for p in plan['features']['dungeons']],
            'houses': [tuple(p) for p in plan['features']['houses']], 'start': tuple(plan['features']['start']),
            'roads': [tuple(p) for p in plan['features']['roads']], 'refill': plan['refill_days']}


def cell_point(i):
    gx, gy = i % 128, i // 128
    return (gx - 64) * 512 + 256, (64 - gy) * 512 - 256


def measure(title, m):
    land = [cell_point(i) for i, s in enumerate(m['sets']) if s is not None and s != WATER
            and abs(cell_point(i)[0]) < 22528 and abs(cell_point(i)[1]) < 22528]
    roads = m['roads']
    town_groups = clusters(m['houses'], 2000) if m['houses'] else []
    town = town_groups[0] if town_groups and len(town_groups[0]) >= 4 else []
    if town:
        box = (min(p[0] for p in town) - 800, min(p[1] for p in town) - 800,
               max(p[0] for p in town) + 800, max(p[1] for p in town) + 800)
        centre = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    else:
        box, centre = None, m['start'] or (0, 0)

    def in_town(p):
        return box is not None and box[0] < p[0] < box[2] and box[1] < p[1] < box[3]
    hostile_spawns = [s for s in m['spawns'] if s['hostile']]
    groups = [((s['x'], s['y']), (s['count'][0] + s['count'][1]) / 2) for s in hostile_spawns]
    hostile_placed = [p for p in m['placed'] if p['hostile']]
    placed_groups = clusters([(p['x'], p['y']) for p in hostile_placed], 1200)
    everything = groups + [((sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)), len(g))
                           for g in placed_groups]
    expected = sum(n for _, n in groups) + len(hostile_placed)
    area = len(land) * 512 * 512 / 1e6
    spots = [p for p, _ in everything]

    def share(points, test):
        return round(sum(test(p) for p in points) / len(points), 2) if points else None
    # The ramp: hostile monsters per million square units of land by distance from the town (or start).
    bands = [(0, 6000), (6000, 12000), (12000, 20000), (20000, 99999)]
    ramp = []
    for lo, hi in bands:
        band_land = sum(lo <= math.dist(c, centre) < hi for c in land) * 512 * 512 / 1e6
        monsters = sum(n for p, n in everything if lo <= math.dist(p, centre) < hi)
        ramp.append(round(monsters / band_land, 2) if band_land > 20 else None)
    sizes = sorted(s['count'] for s in hostile_spawns)
    spacing = sorted(nearest(p, [q for q in spots if q is not p]) for p in spots)
    result = {
        'map': title, 'refill_days': m['refill'],
        'slots': {k: f"{v['name']} d{v['difficulty']} {v['count'][0]}-{v['count'][1]}" for k, v in m['slots'].items()},
        'spawn_points': len(hostile_spawns),
        'peaceful_spawn_points': len(m['spawns']) - len(hostile_spawns),
        'fixed_tier_points': sum(s['tier'] is not None for s in hostile_spawns),
        'group_size': f'{sizes[0][0]}-{sizes[-1][1]}' if sizes else '-',
        'placed_hostile': len(hostile_placed), 'placed_groups': len(placed_groups),
        'placed_hidden': m.get('hidden', 0),
        'expected_hostile': round(expected), 'land_million': round(area),
        'per_million': round(expected / area, 3) if area else None,
        'in_town': sum(n for p, n in everything if in_town(p)),
        'chests': len(m['chests']), 'chests_guarded': share(m['chests'], lambda c: nearest(c, spots) < NEAR),
        'dungeons': len(m['dungeons']),
        'dungeons_guarded': share(m['dungeons'], lambda d: nearest(d, spots) < NEAR),
        'items': len(m['items']), 'items_guarded': share(m['items'], lambda i: nearest(i, spots) < NEAR),
        'groups_on_road': share(spots, lambda p: nearest(p, roads) < 1024),
        'groups_near_chest': share(spots, lambda p: nearest(p, m['chests']) < NEAR),
        'groups_near_edge': share(spots, lambda p: 22528 - max(abs(p[0]), abs(p[1])) < 3000),
        'median_spacing': round(spacing[len(spacing) // 2]) if spacing else None,
        'quiet_radius': round(min((box_distance(p, box) for p in spots), default=0)) if box else None,
        'ramp_per_million': ramp,
    }
    return result, (box, centre, roads, everything, hostile_placed)


def plot(title, m, extra):
    box, centre, roads, everything, hostile_placed = extra
    size = int(45056 * SCALE)
    image = Image.new('RGB', (size, size + 16), 'white')
    draw = ImageDraw.Draw(image)

    def at(x, y):
        return (x + 22528) * SCALE, (22528 - y) * SCALE + 16
    for i, s in enumerate(m['sets']):
        if s == WATER:
            x, y = cell_point(i)
            draw.rectangle([at(x - 256, y + 256), at(x + 256, y - 256)], fill=(200, 220, 245))
    for x, y in roads:
        draw.rectangle([at(x - 256, y + 256), at(x + 256, y - 256)], fill=(215, 200, 170))
    if box:
        draw.rectangle([at(box[0], box[3]), at(box[2], box[1])], outline=(0, 150, 0))
    for x, y in m['houses']:
        cx, cy = at(x, y)
        draw.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=(90, 90, 90))
    for (x, y), n in everything:
        cx, cy = at(x, y)
        r = 2 + 1.2 * n
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(220, 0, 0))
    for p in hostile_placed:
        cx, cy = at(p['x'], p['y'])
        draw.ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5], fill=(220, 0, 0))
    for x, y in m['chests']:
        cx, cy = at(x, y)
        draw.rectangle([cx - 3, cy - 3, cx + 3, cy + 3], outline=(200, 140, 0), width=2)
    for x, y in m['dungeons']:
        cx, cy = at(x, y)
        draw.polygon([(cx, cy - 5), (cx + 5, cy + 4), (cx - 5, cy + 4)], outline=(120, 0, 200), width=2)
    for x, y in m['items']:
        cx, cy = at(x, y)
        draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(0, 140, 200))
    draw.text((4, 2), title, fill=(0, 0, 0))
    return image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results, plots = [], []
    maps = [(title, load_mm(world, stem)) for world, stem, title in MAPS]
    if (PROJECT / 'work/spawns_plan.json').exists():
        maps.append(('Starport Reach', load_hesper()))
    for title, m in maps:
        result, extra = measure(title, m)
        results.append(result)
        image = plot(f"{title}: {result['expected_hostile']} hostile", m, extra)
        image.save(OUT / f"{title.lower().replace(' ', '_')}.png")
        plots.append(image)
        print(json.dumps(result))
    columns = 4
    w, h = plots[0].size
    sheet = Image.new('RGB', (columns * (w + 8), math.ceil(len(plots) / columns) * (h + 8)), 'white')
    for k, image in enumerate(plots):
        sheet.paste(image, ((k % columns) * (w + 8), (k // columns) * (h + 8)))
    sheet.save(OUT / 'sheet.png')
    (OUT / 'density.json').write_text(json.dumps(results, indent=1) + '\n')


if __name__ == '__main__':
    main()
