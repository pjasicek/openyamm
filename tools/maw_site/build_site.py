#!/usr/bin/env python3
"""Builds the MAW guide website into output/maw_site (see README.md).

    python3 tools/maw_site/build_site.py [--out DIR] [--skip-images]

Chedian's maps and teachers come from the MM9 guide's data (output/mm9_site/data/guide.js): build that first.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / 'tools' / 'maw'))
import classes  # noqa: E402
import dungeon_plans  # noqa: E402
import mm9_balance  # noqa: E402
import teachers  # noqa: E402
import world_maps  # noqa: E402

MM9_SITE = REPO / 'output' / 'mm9_site'
MM9_BALANCE = REPO / 'assets_dev' / 'engine' / 'rulesets' / 'maw' / 'worlds' / 'mm9' / 'balance.yml'
# MAW's rows on MM9 people: the Hag's skill reset and Dimensional Maps, the Jarls' bounty offices.
MM9_MAW_DIALOGUE = REPO / 'assets_dev' / 'engine' / 'rulesets' / 'maw' / 'worlds' / 'mm9' / 'dialogue.yml'
CONTENT = HERE / 'content'

CONTINENTS = [
    {'id': 'enroth', 'name': 'Enroth', 'world': 'mm6', 'game': 'Might and Magic VI'},
    {'id': 'antagarich', 'name': 'Antagarich', 'world': 'mm7', 'game': 'Might and Magic VII'},
    {'id': 'jadame', 'name': 'Jadame', 'world': 'mm8', 'game': 'Might and Magic VIII'},
    {'id': 'chedian', 'name': 'Chedian', 'world': 'mm9', 'game': 'Might and Magic IX'},
]

# Marker types: the MM9 guide's, plus the MM6-MM8 house kinds. Order is the legend order.
POI_TYPES = {
    'teacher': {'name': 'Teacher', 'color': '#4f8ff7', 'glyph': 'T', 'shown': True},
    'promoter': {'name': 'Promotion', 'color': '#b07cf0', 'glyph': 'P', 'shown': True},
    'entrance': {'name': 'Dungeon entrance', 'color': '#e2543f', 'glyph': '▼', 'shown': True},
    'exit': {'name': 'Exit', 'color': '#e879a6', 'glyph': '→', 'shown': True},
    'vendor': {'name': 'Shop', 'color': '#3fbf6a', 'glyph': '$', 'shown': True},
    'guild': {'name': 'Guild', 'color': '#2bb3a8', 'glyph': 'G', 'shown': True},
    'service': {'name': 'Temple, tavern, bank, training', 'color': '#d9a441', 'glyph': '+', 'shown': True},
    'transport': {'name': 'Boats and stables', 'color': '#2f9fd6', 'glyph': '⚓', 'shown': True},
    'castle': {'name': 'Castle and throne room', 'color': '#c9b37a', 'glyph': '♜', 'shown': True},
    'bonus': {'name': 'Well, fountain, shrine', 'color': '#5cc8e0', 'glyph': '◆', 'shown': True},
    'quest': {'name': 'Quest NPC', 'color': '#eab308', 'glyph': '!', 'shown': True},
    'objective': {'name': 'Quest object', 'color': '#f59e0b', 'glyph': '★', 'shown': False},
    'hint': {'name': 'Obelisk and hint', 'color': '#94a3b8', 'glyph': '?', 'shown': False},
    'hireling': {'name': 'Hireling', 'color': '#84cc16', 'glyph': 'H', 'shown': False},
    'house': {'name': 'Home', 'color': '#9aa3ad', 'glyph': '⌂', 'shown': False},
    'npc': {'name': 'NPC', 'color': '#9aa3ad', 'glyph': '•', 'shown': False},
    'teleporter': {'name': 'Teleporter', 'color': '#a78bfa', 'glyph': '◎', 'shown': False},
    'chest': {'name': 'Chest', 'color': '#c08a3e', 'glyph': '▣', 'shown': False},
    'lever': {'name': 'Lever and switch', 'color': '#f97316', 'glyph': '⊸', 'shown': False},
    'secret': {'name': 'Secret', 'color': '#f43f5e', 'glyph': 'S', 'shown': False},
    'ladder': {'name': 'Ladder', 'color': '#a3a3a3', 'glyph': 'H', 'shown': False},
}
# Chedian markers the MAW guide leaves out: monster levels and loot follow MAW, not MM9.
MM9_DROPPED = {'monster', 'loot', 'breakable', 'trap', 'door'}
MM9_GUIDE_URL = 'https://jasicek.net/openyamm/mm9-guide/'

# Class ids whose icon file has a shorter name.
CLASS_ICONS = {'assassinthiefline': 'assassin'}

SECTIONS = ['start', 'progression', 'chedian', 'promotions', 'classes', 'crafting', 'tips', 'combat', 'loot', 'spells',
            'deviations']


def load_mm9_guide():
    path = MM9_SITE / 'data' / 'guide.js'
    if not path.exists():
        sys.exit(f'{path.relative_to(REPO)} is missing: run python3 tools/mm9_site/build_site.py first')
    text = path.read_text()
    return json.loads(text[text.index('{'):text.rindex('}') + 1])


def chedian_levels():
    """Chedian's MAW map levels from balance.yml, in map_levels.yml's shape."""
    data = yaml.safe_load(MM9_BALANCE.read_text())
    bands, starters, madness, madness_start = {}, [], {}, []
    for file_name, entry in (data.get('maps') or {}).items():
        if entry.get('band'):
            bands[file_name] = entry['band']
        if entry.get('horizontal_starter'):
            starters.append(file_name)
        if entry.get('madness_level'):
            madness[file_name] = entry['madness_level']
        if entry.get('madness_start'):
            madness_start.append(file_name)
    return {'bands': bands, 'horizontal_starter_maps': starters,
            'madness': {'levels': madness, 'starting_maps': madness_start}}


def chedian_maps(mm9, out, skip_images):
    """The MM9 guide's maps for Chedian: its images, regions and markers, without MM9's monster levels."""
    levels_data = chedian_levels()
    regions = {region['id']: region for region in mm9['regions']}
    dialogue = yaml.safe_load(MM9_MAW_DIALOGUE.read_text())
    topics = {}
    for topic in dialogue.get('topics') or []:
        topics.setdefault(topic['npc'], []).append(topic['label'])
    map_names = {m['id']: m['name'] for m in mm9['maps']}
    bounties = {entry['npc']: map_names.get(Path(entry['map']).stem, entry['map'])
                for entry in dialogue.get('bounties') or []}
    maps = []
    for m in mm9['maps']:
        entry = {key: m[key] for key in ('id', 'name', 'kind', 'floors', 'floorNames', 'thumb') if key in m}
        entry.update({'continent': 'chedian', 'world': 'mm9', 'file': f'{m["id"]}.blv',
                      'region': regions[m['region']]['name'] if m.get('region') in regions else ''})
        levels = world_maps.map_levels(entry['file'], levels_data)
        if levels:
            entry['levels'] = levels
        pois = []
        for poi in m['pois']:
            if poi['t'] in MM9_DROPPED or poi['t'] not in POI_TYPES:
                continue
            keep = {key: poi[key] for key in ('id', 't', 'n', 'd', 'u', 'v', 'f', 'map') if key in poi}
            if poi.get('promo'):
                keep['k'] = f'{poi["promo"]} promotion'
            if poi.get('rude') in topics:
                keep['t'] = 'service'
                keep['k'] = 'MAW: ' + ', '.join(t for t in topics[poi['rude']] if t != 'Reset skills')
            if poi.get('rude') in bounties:
                keep['k'] = f'MAW bounty office for {bounties[poi["rude"]]}'
            pois.append(keep)
        entry['pois'] = pois
        entry['mm9'] = f'{MM9_GUIDE_URL}#map-{m["id"]}'
        maps.append(entry)
        if not skip_images:
            for floor in entry['floors']:
                copy_asset(MM9_SITE / floor['img'], out / floor['img'])
            if entry.get('thumb'):
                copy_asset(MM9_SITE / entry['thumb'], out / entry['thumb'])
    return maps


def copy_asset(source, target):
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def one_floor(entry):
    """An MM6-MM8 map in the MM9 guide's multi-floor shape: one floor, every marker on it."""
    if entry.get('img'):
        entry['floors'] = [{'img': entry.pop('img'), 'w': entry.pop('w'), 'h': entry.pop('h')}]
        entry['floorNames'] = ['']
    else:
        entry['floors'] = []
        entry['floorNames'] = []
    for poi in entry.get('pois', []):
        poi['f'] = 0
    return entry


def mark_people(maps, teacher_data, class_data):
    """Teachers and promoters on their houses' markers."""
    by_map = {m['id']: {p['id']: p for p in m.get('pois', [])} for m in maps}
    for teacher in teacher_data['teachers']:
        if teacher['continent'] == 'Chedian' or not teacher.get('house_id'):
            continue
        for map_file in (teacher.get('map'), teacher.get('marker_map')):
            poi = by_map.get(Path(map_file or '').stem, {}).get(f'h{teacher["house_id"]}')
            if poi is not None:
                lesson = f'{teacher["mastery"]} {teacher["skill"]}'
                poi.setdefault('teach', [])
                if lesson not in poi['teach']:
                    poi['teach'].append(lesson)
                if poi['t'] == 'house':
                    poi['t'] = 'teacher'
                teacher.setdefault('at', []).append({'map': Path(map_file).stem, 'poi': poi['id']})
                break
    for cls in class_data['classes']:
        for step in cls.get('promotions', []):
            if not step.get('house_id') or not step.get('map'):
                continue
            poi = by_map.get(Path(step['map']).stem, {}).get(f'h{step["house_id"]}')
            if poi is not None:
                if poi['t'] in ('house', 'castle', 'teacher'):
                    poi['t'] = 'promoter'
                promo = f'{cls["name"]}: {step["tier"]}'
                poi.setdefault('promos', [])
                if promo not in poi['promos']:
                    poi['promos'].append(promo)
                step['at'] = {'map': Path(step['map']).stem, 'poi': poi['id']}


def tiers(values: dict[str, float]) -> dict[str, int]:
    """1-5 by quintile among the given maps."""
    ordered = sorted(values, key=lambda k: values[k])
    return {key: 1 + min(4, index * 5 // max(len(ordered), 1)) for index, key in enumerate(ordered)}


def map_stats(maps: list[dict], cache_path: Path) -> None:
    """Monsters at MAW and Nightmare (tools/maw/mm9_balance.py counts them as the game resolves them), the indoor
    floor area, and three tiers: monsters, loot (kills x the middle family's level) and crowding (monsters per floor
    area, among indoor maps only: outdoors the party can keep its distance). MM9's rebuilt maps are in the same units
    (its converters scale MM9 by 2.56), so their roomier dungeons rank as less crowded."""
    balance = yaml.safe_load(MM9_BALANCE.read_text())
    counts = {**mm9_balance.mm68_encounters(), **mm9_balance.mm9_encounters(balance)}
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    loot, crowd = {}, {}
    for m in maps:
        count = counts.get(m['file'])
        if not count or not m.get('levels') or m['levels'].get('arena'):
            continue
        stats = {'n': count['maw'], 'n_nm': count['nightmare']}
        indoor = m['kind'] not in ('outdoor', 'city')
        if indoor:
            path = world_maps.WORLDS / m['world'] / 'maps' / m['file']
            key = f'{m["file"]}:{path.stat().st_mtime_ns}'
            if key not in cache:
                cache[key] = dungeon_plans.floor_area(path) / (512 * 512)
            stats['area'] = round(cache[key], 1)
        m['stats'] = stats
        if count['maw'] > 0:
            loot[m['id']] = count['maw'] * m['levels']['band'][1]
            if indoor and stats.get('area'):
                crowd[m['id']] = count['maw'] / stats['area']
                stats['crowd'] = round(count['maw'] / stats['area'] * 100, 1)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache))
    loot_tier, crowd_tier, count_tier = tiers(loot), tiers(crowd), tiers({k: v for k, v in
                                                                          ((m['id'], m.get('stats', {}).get('n', 0))
                                                                           for m in maps) if v > 0})
    for m in maps:
        if 'stats' in m:
            for key, table in (('loot_tier', loot_tier), ('crowd_tier', crowd_tier), ('n_tier', count_tier)):
                if m['id'] in table:
                    m['stats'][key] = table[m['id']]


def load_content():
    """The prose sections, keyed by name; images they use are listed for copying."""
    sections, images = {}, set()
    for name in SECTIONS:
        path = CONTENT / f'{name}.html'
        if not path.exists():
            continue
        html = path.read_text()
        sections[name] = html
        images.update(re.findall(r'src="(img/[^"]+)"', html))
    return sections, images


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--out', type=Path, default=REPO / 'output' / 'maw_site')
    parser.add_argument('--skip-images', action='store_true', help='reuse the map images already in the output')
    args = parser.parse_args()
    out = args.out
    started = time.time()

    mm9 = load_mm9_guide()
    maps = [one_floor(entry) for entry in world_maps.build(out, skip_images=args.skip_images)]
    maps += chedian_maps(mm9, out, args.skip_images)
    map_stats(maps, out / 'work' / 'floor_areas.json')
    teacher_data = teachers.build()
    class_data = classes.build()
    mark_people(maps, teacher_data, class_data)
    for cls in class_data['classes']:
        icon = CONTENT / 'img' / f'class_{CLASS_ICONS.get(cls["id"], cls["id"])}.png'
        if icon.exists():
            cls['icon'] = f'img/{icon.name}'
    sections, images = load_content()
    for image in sorted(images):
        copy_asset(CONTENT / image, out / image)
    for icon in sorted((CONTENT / 'img').glob('class_*.png')):
        copy_asset(icon, out / 'img' / icon.name)

    chedian_regions = [{'id': r['id'], 'name': r['name'], 'maps': r['maps']} for r in mm9['regions']]
    guide = {
        'generated': time.strftime('%Y-%m-%d'),
        'continents': CONTINENTS,
        'chedianRegions': chedian_regions,
        'poiTypes': POI_TYPES,
        'maps': maps,
        'mm9Guide': MM9_GUIDE_URL,
        **teacher_data,
        **class_data,
        'content': sections,
    }
    data_dir = out / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / 'guide.js').write_text('window.GUIDE = ' + json.dumps(guide, ensure_ascii=False, separators=(',', ':'))
                                       + ';\n')
    web = HERE / 'web'
    for name in ('app.js', 'style.css', 'page.html'):
        shutil.copy2(web / name, out / name)
    # Each file's content hash in its URL: a browser fetches what a deploy changed instead of its cached copy.
    page = (web / 'page.html').read_text()
    for name in ('data/guide.js', 'app.js', 'style.css'):
        digest = hashlib.sha256((out / name).read_bytes()).hexdigest()[:10]
        page = page.replace(f'"{name}"', f'"{name}?v={digest}"')
    (out / 'index.html').write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                                    '<meta name="viewport" content="width=device-width, initial-scale=1, '
                                    'viewport-fit=cover">\n</head>\n<body>\n' + page + '</body>\n</html>\n')

    pois = sum(len(m.get('pois', [])) for m in maps)
    print(f'wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(maps)} maps, {pois} markers, '
          f'{len(teacher_data["teachers"])} lessons, {len(class_data["classes"])} classes, '
          f'{len(sections)} sections in {time.time() - started:.0f} s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
