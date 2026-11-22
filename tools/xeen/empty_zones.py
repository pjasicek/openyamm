#!/usr/bin/env python3
"""Empty outdoor land: how far walkable land lies from the nearest hostile (F10, 2026-11-21).

The user: "this area ultra empty, no mobs in radius" (Mount Firestone). For every outdoor map this measures, on a grid
of terrain tiles (512 x 512), the distance from each walkable land tile to the nearest monster source: a monster
spawn marker (`spawns`, type 3, index 1-12) or a placed hostile actor (townsfolk, named characters and rows friendly
to the party left out, as tools/xeen/balance.py counts them). It reports per map the largest empty radius on land, the
share of land farther than the threshold from any monster, and every empty zone (a connected patch of land past the
threshold) with its deepest point.

Walkable land: inside the play square (|x|, |y| < 22,528, tiles 20-107), not water or lava (tile flag 2 without the
shore bit), neither terrain triangle of the tile steeper than the game's slope limit (a rise of more than 512 over a
tile, OutdoorMovementController terrainSlopeTooHigh), on Xeen not below z 256 (the rim's stars), and in a connected walkable
piece of at least 64 tiles (peaks, ledges and islets left out).

Left out of the empty zones (not of the distances):
- towns: land within 2,500 of a house door that has two more house doors within 3,000 (MM6-MM8 towns are quiet too);
- the map's exemptions in tools/xeen/empty_zones.yml (a centre, a radius and the decision that keeps it quiet).

Calibration (`--calibrate`, 37 shipped maps: MM6's 15, MM7's 13, MM8's 9, 2026-11-21): the largest empty radius on
land outside towns has a median of 12,400 (p25 9,600, p75 16,800); land farther than 6,000 from any monster is a
median 17 % of a map (p75 25 %); road tiles lie a median 3,400 from a monster (map medians; p75 4,600). An empty
zone is a connected patch of land farther than ZONE (6,000) from every monster. The shipped maps' largest zone is a
median 228 tiles (p75 522, mostly at a map's edge). A zone deeper than LIMIT (12,000, the shipped median largest
radius) or larger than AREA_LIMIT (520 tiles, the shipped p75) is larger than a typical MM6-MM8 one: it is reported,
and `--check` fails on it. A share of land past 6,000 above SHARE_LIMIT (the shipped p75) is a warning.

    python3 tools/xeen/empty_zones.py                      every installed Xeen outdoor map
    python3 tools/xeen/empty_zones.py xeen_x7 [--zones]    one map, and each of its zones
    python3 tools/xeen/empty_zones.py --scene <scene.yml> --odm <odm>   a build folder's map (the map pipelines)
    python3 tools/xeen/empty_zones.py --calibrate           the MM6-MM8 maps, measured the same way
    python3 tools/xeen/empty_zones.py --check               exit 1 when an Xeen zone is past the threshold
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'util'))

import balance  # noqa: E402
import xeenlib  # noqa: E402
from map_export import parse_odm_file  # noqa: E402

TILE = 512
PLAY = (20, 108)              # tiles 20-107: |x|, |y| < 22,528
MIN_PIECE = 64                # walkable pieces smaller than this (16 M units^2) are not land the party walks
TOWN_RADIUS = 2500
TOWN_DOORS_NEAR = 3000
ZONE = 6000                   # an empty zone: land farther than this from every monster
LIMIT = 12000                 # a zone deeper than this is larger than the shipped maps' median largest (12,400)
AREA_LIMIT = 520              # or a zone of more tiles than the shipped maps' p75 largest (median 228, p75 522)
SHARE_LIMIT = 0.25            # the shipped maps' p75 share of land farther than ZONE (a warning)
ENGINE_TILES = {'mm6': 'terrain_tile_data_3.txt', 'mm7': 'terrain_tile_data_2.txt', 'mm8': 'terrain_tile_data.txt',
                'xeen': 'terrain_tile_data_2.txt'}
CALIBRATION = {
    'mm6': ['outa1', 'outa2', 'outa3', 'outb1', 'outb2', 'outb3', 'outc1', 'outc2', 'outc3', 'outd1', 'outd2',
            'outd3', 'oute1', 'oute2', 'oute3'],
    'mm7': ['7out01', '7out02', '7out03', '7out04', '7out05', '7out06', '7out13', '7out15', 'out09', 'out10',
            'out11', 'out12', 'out14'],
    'mm8': ['out01', 'out02', 'out03', 'out04', 'out05', 'out06', 'out07', 'out08', 'out13'],
}
EXEMPTIONS = Path(__file__).resolve().with_name('empty_zones.yml')


def tile_flag_table(world):
    rows = [line.split('\t') for line in
            (xeenlib.ENGINE_TABLES / ENGINE_TILES[world]).read_text(encoding='latin-1').splitlines()[1:]]
    return rows


def tile_flags(payload, world, rows, tile):
    if tile >= 234:
        return 0
    if tile >= 90:
        index = payload['tile_set_lookup_indices'][(tile - 90) // 36] + (tile - 90) % 36
    else:
        index = tile + ([0, 450, 630][payload['master_tile']] if world == 'mm8' and tile else 0)
    if index >= len(rows):
        return 0
    return int(rows[index][6], 0)


def land_mask(payload, world):
    """Walkable land tiles (128 x 128, [row, col]) and the heights."""
    rows = tile_flag_table(world)
    tiles = np.array(payload['tile_map']).reshape(128, 128)
    heights = np.array(payload['height_map'], dtype=np.int32).reshape(128, 128) * 32
    flags = {t: tile_flags(payload, world, rows, t) for t in np.unique(tiles)}
    wet = np.vectorize(lambda t: bool(flags[t] & 2 and not flags[t] & 0x100))(tiles)
    z00 = heights[:-1, :-1]
    z10 = heights[:-1, 1:]
    z01 = heights[1:, :-1]
    z11 = heights[1:, 1:]
    tri1 = np.maximum.reduce([z00, z10, z11]) - np.minimum.reduce([z00, z10, z11])
    tri2 = np.maximum.reduce([z00, z01, z11]) - np.minimum.reduce([z00, z01, z11])
    low = np.minimum.reduce([z00, z10, z01, z11])
    walk = np.zeros((128, 128), bool)
    walk[:-1, :-1] = (tri1 <= TILE) & (tri2 <= TILE)
    if world == 'xeen':
        walk[:-1, :-1] &= low >= 256    # the rim cliff and the stars below it (the Xeen maps' edge)
    walk &= ~wet
    box = np.zeros_like(walk)
    box[PLAY[0]:PLAY[1], PLAY[0]:PLAY[1]] = True
    walk &= box
    labels, count = ndimage.label(walk, structure=np.ones((3, 3)))
    sizes = ndimage.sum(walk, labels, range(1, count + 1))
    keep = np.isin(labels, [i + 1 for i, size in enumerate(sizes) if size >= MIN_PIECE])
    return keep


def tile_centres():
    cols, rows = np.meshgrid(np.arange(128), np.arange(128))
    return (cols + 0.5 - 64) * TILE, (64 - rows - 0.5) * TILE


def world_to_tile(x, y):
    return int(64 - y / TILE), int(x / TILE + 64)


def lua_house_events(path):
    """Event ids whose handler enters a house (a door)."""
    doors = set()
    for lua in [path] + sorted(path.parent.glob(path.stem + '_*.lua')):
        if not lua.exists():
            continue
        text = lua.read_text(encoding='latin-1')
        regs = list(re.finditer(r'^Register(?:NoOp)?Event\((\d+)', text, re.M))
        for i, match in enumerate(regs):
            block = text[match.start(): regs[i + 1].start() if i + 1 < len(regs) else len(text)]
            if 'EnterHouse(' in block:
                doors.add(int(match.group(1)))
    return doors


def house_doors(payload, scene, lua_path):
    events = lua_house_events(lua_path)
    points = defaultdict(list)
    faces = ((scene.get('bmodel_faces') or {}).get('interactive_faces')) or []
    by_face = {(f['bmodel_index'], f['face_index']): f.get('cog_triggered_number') for f in faces}
    for bi, model in enumerate(payload['bmodels']):
        verts = np.array([[q['x'], q['y']] if isinstance(q, dict) else q[:2] for q in model['vertices']], float)
        for fi, face in enumerate(model['faces']):
            event = by_face.get((bi, fi), face['cog_triggered_number'])
            if event in events and len(face['vertex_indices']):
                points[event].append(verts[face['vertex_indices']].mean(axis=0))
    for entity in scene.get('entities') or []:
        event = entity.get('event_id_secondary') or entity.get('event_id_primary')
        if event in events:
            points[event].append(np.array([entity['position']['x'], entity['position']['y']], float))
    return [np.mean(p, axis=0) for p in points.values()]


def town_mask(doors):
    mask = np.zeros((128, 128), bool)
    if not doors:
        return mask
    pts = np.array(doors)
    cx, cy = tile_centres()
    for p in pts:
        near = np.hypot(pts[:, 0] - p[0], pts[:, 1] - p[1]) <= TOWN_DOORS_NEAR
        if near.sum() >= 3:
            mask |= np.hypot(cx - p[0], cy - p[1]) <= TOWN_RADIUS
    return mask


def monster_sources(scene, by_id, friendly):
    """(x, y, kind) of every monster spawn marker and placed hostile."""
    out = []
    for spawn in scene.get('spawns') or []:
        if spawn.get('type_id') == 3 and 1 <= spawn.get('index', 0) <= 12:
            out.append((spawn['position']['x'], spawn['position']['y'], 'marker'))
    for actor in (scene.get('initial_state') or {}).get('actors') or []:
        info = by_id.get(actor.get('monster_info_id') or actor.get('monster_id'))
        if info is None or balance.TOWNSFOLK.match(info['picture']) or balance.TOWNSFOLK_NAMES.match(info['name']):
            continue
        if actor.get('npc_id') or info['id'] in friendly:
            continue
        out.append((actor['position']['x'], actor['position']['y'], 'placed'))
    return out


def load_exemptions():
    data = xeenlib.load_yaml(EXEMPTIONS) if EXEMPTIONS.exists() else None
    return (data or {}).get('maps') or {}


def measure(stem, world, scene_path, odm_path, lua_path, by_id, friendly, exempt=()):
    import yaml
    payload = parse_odm_file(Path(odm_path))['payload']
    scene = yaml.load(Path(scene_path).read_text(), Loader=yaml.CSafeLoader)
    land = land_mask(payload, world)
    sources = monster_sources(scene, by_id, friendly)
    cx, cy = tile_centres()
    if sources:
        pts = np.array([(s[0], s[1]) for s in sources], float)
        dist = np.full((128, 128), np.inf)
        for x, y in pts:
            dist = np.minimum(dist, np.hypot(cx - x, cy - y))
    else:
        dist = np.full((128, 128), 1e6)
    town = town_mask(house_doors(payload, scene, Path(lua_path)))
    quiet = np.zeros_like(land)
    for item in exempt:
        quiet |= np.hypot(cx - item['at'][0], cy - item['at'][1]) <= item['radius']
    counted = land & ~town & ~quiet
    zones = []
    labels, count = ndimage.label(counted & (dist > ZONE), structure=np.ones((3, 3)))
    for i in range(1, count + 1):
        cells = labels == i
        deepest = np.where(cells, dist, -1)
        r, c = np.unravel_index(np.argmax(deepest), deepest.shape)
        zones.append({'deepest': float(dist[r, c]), 'at': (float(cx[r, c]), float(cy[r, c])), 'tile': (int(c), int(r)),
                      'tiles': int(cells.sum())})
    zones.sort(key=lambda z: -z['deepest'])
    vals = dist[counted]
    tiles = np.array(payload['tile_map']).reshape(128, 128)
    road = counted & (tiles >= 198) & (tiles < 234)
    return {
        'stem': stem, 'world': world, 'sources': len(sources), 'land_tiles': int(land.sum()),
        'left_out': int((land & (town | quiet)).sum()),
        'largest': float(vals.max()) if vals.size else 0.0,
        'median': float(np.median(vals)) if vals.size else 0.0,
        'share': float((vals > ZONE).mean()) if vals.size else 0.0,
        'road': float(np.median(dist[road])) if road.any() else None,
        'zones': zones, 'dist': dist, 'counted': counted,
    }


def too_large(zone):
    return zone['deepest'] > LIMIT or zone['tiles'] > AREA_LIMIT


def row(m):
    past = [z for z in m['zones'] if too_large(z)]
    flag = ' **past %d**' % LIMIT if m['largest'] > LIMIT else ''
    share = ' **over %.2f**' % SHARE_LIMIT if m['share'] > SHARE_LIMIT else ''
    road = '%.0f' % m['road'] if m['road'] is not None else '-'
    area = max([z['tiles'] for z in m['zones']] or [0])
    big = ' **over %d**' % AREA_LIMIT if area > AREA_LIMIT else ''
    return '| %s | %d | %d | %d | %.0f | %s | %.0f%s | %d%s | %.2f%s | %d |' % (
        m['stem'], m['sources'], m['land_tiles'], m['left_out'], m['median'], road, m['largest'], flag, area, big,
        m['share'], share, len(past))


HEADER = ('| Map | Monster sources | Land tiles | Town/exempt tiles | Median distance | On roads (median) | '
          'Largest empty radius | Largest zone (tiles) | Land > %d | Zones too large |\n'
          '| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |' % ZONE)


def xeen_maps():
    return sorted(p.stem for p in (xeenlib.WORLD / 'maps').glob('xeen_*.odm'))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('maps', nargs='*')
    parser.add_argument('--calibrate', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--scene')
    parser.add_argument('--odm')
    parser.add_argument('--lua')
    args = parser.parse_args()
    by_id, _ = balance.monster_rows()
    if args.calibrate:
        results = []
        print(HEADER)
        for world, stems in CALIBRATION.items():
            for stem in stems:
                base = xeenlib.WORLDS / world / 'maps' / stem
                m = measure(stem, world, base.with_suffix('.scene.yml'), base.with_suffix('.odm'),
                            xeenlib.WORLDS / world / 'events' / 'maps' / (stem + '.lua'), by_id, set())
                results.append(m)
                print(row(m))
        largest = np.array([m['largest'] for m in results])
        share = np.array([m['share'] for m in results])
        road = np.array([m['road'] for m in results if m['road'] is not None])
        area = np.array([max([z['tiles'] for z in m['zones']] or [0]) for m in results])
        print('\n%d maps. Largest empty radius: p25 %.0f, median %.0f, p75 %.0f. Land > %d: median %.2f, p75 %.2f. '
              'On roads: median %.0f, p75 %.0f. Largest zone: median %.0f tiles, p75 %.0f.' % (
                  len(results), np.percentile(largest, 25), np.median(largest), np.percentile(largest, 75), ZONE,
                  np.median(share), np.percentile(share, 75), np.median(road), np.percentile(road, 75),
                  np.median(area), np.percentile(area, 75)))
        return 0
    friendly = balance.friendly_rows()
    exemptions = load_exemptions()
    if args.scene:
        scene = Path(args.scene)
        stem = scene.name.split('.')[0]
        lua = Path(args.lua) if args.lua else scene.with_name(stem + '.lua')
        todo = [(stem, scene, Path(args.odm or scene.with_name(stem + '.odm')), lua)]
    else:
        todo = []
        for stem in args.maps or xeen_maps():
            base = xeenlib.WORLD / 'maps' / stem
            todo.append((stem, base.with_suffix('.scene.yml'), base.with_suffix('.odm'),
                         xeenlib.WORLD / 'events' / 'maps' / (stem + '.lua')))
    print(HEADER)
    failed = []
    results = []
    for stem, scene, odm, lua in todo:
        m = measure(stem, 'xeen', scene, odm, lua, by_id, friendly, exemptions.get(stem) or [])
        results.append(m)
        print(row(m))
        if any(too_large(z) for z in m['zones']):
            failed.append(stem)
    for m in results:
        if not m['zones']:
            continue
        print('\n%s: empty zones (land farther than %d from every monster)' % (m['stem'], ZONE))
        for z in m['zones']:
            if z['tiles'] < 4 and not too_large(z):
                continue
            print('  deepest %5.0f at (%6.0f, %6.0f) tile [%d, %d], %d tiles%s'
                  % (z['deepest'], z['at'][0], z['at'][1], z['tile'][0], z['tile'][1], z['tiles'],
                     '  TOO LARGE' if too_large(z) else ''))
    if args.check and failed:
        print('\nempty zones deeper than %d or larger than %d tiles: %s' % (LIMIT, AREA_LIMIT, ', '.join(failed)))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
