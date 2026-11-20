"""Builds data/finder.json and data/maps_web/*.jpg for the trainer finder mockup from data/trainers.json.

Run from the repository root: python3 -I level_generation/ui/journal_trainers_20261105/data/scripts/build_finder.py
MAW's extra houses (npc_extra_houses.yml) get their own rows, marked on the map whose script enters the house.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent
sys.path.insert(0, str(HERE))

import build_trainers as bt  # noqa: E402
from PIL import Image  # noqa: E402

WEB_SIZE = 768
CONTINENT_ORDER = ['Jadame', 'Antagarich', 'Enroth']


def house_doors(scripts):
    """house id -> list of (map stem, event ids) whose script enters it."""
    doors = {}
    for stem, events in scripts.items():
        for event, info in events.items():
            for house in info['houses']:
                doors.setdefault(house, {}).setdefault(stem, set()).add(event)
    return doors


def requirement_text(requirements):
    if not requirements:
        return ''
    parts = [f"skill {requirements['skillLevel']}"]
    if requirements.get('gold'):
        parts.append(f"{requirements['gold']:,} gold".replace(',', ' '))
    for extra in requirements.get('extra') or []:
        parts.append(str(extra))
    return ', '.join(parts)


def main():
    source = json.loads((DATA / 'trainers.json').read_text())
    _, _, houses, maps, _, _, _ = bt.load_tables()
    map_names = {entry['file']: entry['name'] for entry in maps.values()}
    scripts = bt.load_scripts()
    doors = house_doors(scripts)
    rows = []
    used_maps = set()

    def place(row):
        if row.get('outdoorMapFile') and row.get('marker'):
            used_maps.add(row['outdoorMapFile'])
        return {
            'houseName': row.get('houseName'),
            'mapName': row.get('mapName'),
            'townName': row.get('outdoorMapName') if row.get('markerKind') == 'house' else row.get('mapName'),
            'outdoorMapFile': row.get('outdoorMapFile'),
            'outdoorMapName': row.get('outdoorMapName'),
            'marker': {'x': row['marker']['x'], 'y': row['marker']['y']} if row.get('marker') else None,
            'imageSize': row.get('mapImageSize'),
            'markerKind': row.get('markerKind'),
        }

    for index, row in enumerate(source['trainers']):
        entry = {
            'id': f't{index}',
            'skill': row['skill'],
            'mastery': row['mastery'],
            'npcName': row['npcName'],
            'continent': row['continent'],
            'requirement': requirement_text(row.get('requirements')),
            'autonoteId': row.get('autonoteId'),
            **place(row),
        }
        rows.append(entry)

        # MAW also stands the teacher in other houses: one row each, MAW only.
        for extra in row.get('mawExtraHouses') or []:
            stem = Path(extra['mapFile']).stem
            events = doors.get(extra['houseId'], {}).get(stem, set())
            marker = bt.event_marker(extra['mapFile'], events) if events else None
            image = bt.map_image_source(extra['mapFile'])
            size = list(Image.open(image).size) if image else None
            pixel = bt.world_to_pixel(marker['worldX'], marker['worldY'], *size) if marker and size else None
            outdoor = extra['mapFile'] if extra['mapFile'].endswith('.odm') and pixel else None
            if outdoor:
                used_maps.add(outdoor)
            rows.append({
                'id': f't{index}m{len(rows)}',
                'skill': row['skill'],
                'mastery': row['mastery'],
                'npcName': row['npcName'],
                'continent': extra['continent'],
                'requirement': requirement_text(row.get('requirements')),
                'autonoteId': row.get('autonoteId'),
                'mawOnly': True,
                'houseName': extra['houseName'],
                'mapName': map_names.get(extra['mapFile'], extra['mapFile']),
                'townName': map_names.get(extra['mapFile'], extra['mapFile']),
                'outdoorMapFile': outdoor,
                'outdoorMapName': map_names.get(extra['mapFile']),
                'marker': {'x': pixel[0], 'y': pixel[1]} if pixel else None,
                'imageSize': size,
                'markerKind': 'house' if pixel else None,
            })

    # MAW's self-taught skills gain their masteries at these skill levels, with no trainer (mawSkillMasteryLadder,
    # outside Road to Insanity and Beyond Madness).
    ladders = {'Cover': (6, 12, 20), 'Mana Shield': (6, 12, 20), 'Enlightenment': (6, 12, 20),
               'Retaliation': (10, 24, 40)}
    for continent in CONTINENT_ORDER:
        for skill, levels in ladders.items():
            for mastery, level in zip(('Expert', 'Master', 'Grand Master'), levels):
                rows.append({'id': f'auto-{continent}-{skill}-{mastery}'.replace(' ', '_'), 'skill': skill,
                             'mastery': mastery, 'npcName': '', 'continent': continent, 'requirement': '',
                             'mawOnly': True, 'mawAuto': level, 'houseName': None, 'mapName': None,
                             'townName': None, 'outdoorMapFile': None, 'outdoorMapName': None, 'marker': None,
                             'imageSize': None, 'markerKind': None})

    web = DATA / 'maps_web'
    web.mkdir(exist_ok=True)
    for map_file in sorted(used_maps):
        stem = Path(map_file).stem
        image = Image.open(DATA / 'maps' / f'{stem}.png').convert('RGB')
        image.thumbnail((WEB_SIZE, WEB_SIZE), Image.LANCZOS)
        image.save(web / f'{stem}.jpg', quality=86, optimize=True)

    rows.sort(key=lambda r: (CONTINENT_ORDER.index(r['continent']) if r['continent'] in CONTINENT_ORDER else 9,
                             r['skill'], r['mastery'], r['npcName']))
    out = {'startContinent': 'Enroth', 'continents': CONTINENT_ORDER, 'trainers': rows}
    (DATA / 'finder.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    maw_rows = sum(1 for r in rows if r.get('mawOnly'))
    unmarked = [r for r in rows if not r['marker'] and not r.get('mawAuto')]
    print(f'{len(rows)} rows ({maw_rows} MAW-only), {len(unmarked)} without a marker, {len(used_maps)} maps')
    for r in unmarked:
        print('  no marker:', r['npcName'], r['skill'], r['mastery'], r['houseName'], r['mapName'])


if __name__ == '__main__':
    main()
