"""Inventory native New Sorpigal decoration art, including script-selected states; no asset edits."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import sys

import numpy as np
from PIL import Image, ImageDraw
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'util'))
from map_export import parse_odm_file


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    for directory in ('native', 'references', 'prompts', 'raw', 'review', 'enhanced', 'sheets'):
        (HERE / directory).mkdir(exist_ok=True)
    map_path = REPO / 'assets_dev/worlds/mm6/maps/oute3.odm'
    scene_path = map_path.with_suffix('.scene.yml')
    table_path = REPO / 'assets_dev/engine/data_tables/decoration_data.txt'
    frames_path = REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
    events_path = REPO / 'assets_dev/worlds/mm6/events/maps/oute3.lua'
    entities = parse_odm_file(map_path)['payload']['entities']
    scene = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader)
    overrides = {e['entity_index']: e for e in scene.get('entities', [])}
    for entity in entities:
        entity.update(overrides.get(entity['index'], {}))
    counts = collections.Counter(e['name'].lower() for e in entities)
    script_states = set(re.findall(r'evt\.SetSprite\([^\n]*?"([^"]+)"', events_path.read_text()))
    rows = {r[1].lower(): r for r in csv.reader(table_path.open(), delimiter='\t') if r and r[0].isdigit()}
    groups = {s['sprite_id']: s for s in yaml.load(frames_path.read_text(), Loader=yaml.CSafeLoader)['sprites']}
    roots = [REPO / 'assets_dev/worlds/mm6', REPO / 'assets_dev/engine']
    sprite_paths = {}
    for root in roots:
        for path in (root / 'sprites').glob('*'):
            if path.suffix.lower() == '.bmp':
                sprite_paths.setdefault(path.stem.lower(), path)
    sources = {}
    records = []
    for name in sorted(set(counts) | script_states):
        row = rows[name]
        sprite_id = int(row[12])
        entry = {'name': name, 'hint': row[2], 'placed_count': counts[name],
                 'selected_by_map_script': name in script_states, 'sprite_id': sprite_id,
                 'descriptor_id': int(row[0]) - 1, 'flags': row[11],
                 'collision_radius': int(row[4]), 'collision_height': int(row[5]),
                 'light_radius': int(row[6]), 'light_rgb': list(map(int, row[7:10]))}
        if sprite_id == 0:
            entry.update(policy='marker_no_art', frames=[], unique_images=[])
            records.append(entry)
            continue
        group = groups[sprite_id]
        entry['native_group'] = group
        entry['frames'] = []
        entry['policy'] = 'keep_native_animation' if len(group['frames']) > 1 else 'enhance'
        unique = []
        for frame in group['frames']:
            texture = frame['texture_name'].lower()
            names = [texture] if 'Image1' in frame['flags'] else [texture + str(i) for i in range(5)]
            entry['frames'].append({'images': names, 'duration_ms': frame.get('frame_length_raw', 0) * 62.5,
                                    'scale': frame.get('scale', 1), 'flags': frame['flags'],
                                    'palette_id': frame['palette_id']})
            for image_name in names:
                if image_name not in unique:
                    unique.append(image_name)
                if image_name in sources:
                    assert sources[image_name]['palette_id'] == frame['palette_id']
                    continue
                image_path = sprite_paths[image_name]
                image = Image.open(image_path)
                assert image.mode == 'P', (image_name, image.mode)
                palette_name = f"pal{frame['palette_id']:03d}.act"
                palette = next(root / 'textures' / palette_name for root in roots
                               if (root / 'textures' / palette_name).exists())
                indices = np.array(image)
                colors = np.frombuffer(palette.read_bytes()[:768], np.uint8).reshape(256, 3)
                rgba = Image.fromarray(np.dstack([colors[indices], (indices != 0).astype(np.uint8) * 255]))
                rgba.save(HERE / 'native' / (image_name + '.png'))
                sources[image_name] = {'path': str(image_path.relative_to(REPO)), 'sha256': digest(image_path),
                                      'palette': str(palette.relative_to(REPO)), 'palette_sha256': digest(palette),
                                      'palette_id': frame['palette_id'], 'size': list(image.size),
                                      'visible_bounds': rgba.getbbox()}
        entry['unique_images'] = unique
        records.append(entry)
    inventory = {'world': 'mm6', 'map': 'oute3.odm', 'placed_entities': len(entities),
                 'records': records, 'sources': sources,
                 'provenance': {str(p.relative_to(REPO)): digest(p)
                                for p in (map_path, scene_path, table_path, frames_path, events_path)}}
    (HERE / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    visible = [r for r in records if r['unique_images']]
    contact = Image.new('RGB', (5 * 320, ((len(visible) + 4) // 5) * 340), (47, 51, 48))
    draw = ImageDraw.Draw(contact)
    for i, entry in enumerate(visible):
        im = Image.open(HERE / 'native' / (entry['unique_images'][0] + '.png'))
        im.thumbnail((296, 285), Image.Resampling.NEAREST)
        x, y = i % 5 * 320, i // 5 * 340
        contact.paste(im, (x + (320 - im.width) // 2, y + 35 + (285 - im.height)), im)
        draw.text((x + 8, y + 5), entry['name'] + f"  x{entry['placed_count']}", fill='white')
        draw.text((x + 8, y + 20), f"{entry['hint']}; {len(entry['frames'])} frames", fill='white')
    contact.save(HERE / 'references/native_catalogue.png')
    for entry in visible:
        if entry['policy'] == 'keep_native_animation':
            names = entry['unique_images']
            ims = [Image.open(HERE / 'native' / (n + '.png')) for n in names]
            w, h = max(im.width for im in ims), max(im.height for im in ims)
            sheet = Image.new('RGB', (3 * (w + 20), ((len(ims) + 2) // 3) * (h + 35)), (47, 51, 48))
            draw = ImageDraw.Draw(sheet)
            for i, im in enumerate(ims):
                x, y = i % 3 * (w + 20), i // 3 * (h + 35)
                sheet.paste(im, (x + (w - im.width) // 2 + 10, y + h - im.height + 25), im)
                draw.text((x + 5, y + 5), names[i], fill='white')
            sheet.save(HERE / 'references' / (entry['name'] + '_animation.png'))
    print(json.dumps({'placed_entities': len(entities), 'decoration_types': len(counts),
                      'including_script_states': len(records), 'unique_images': len(sources),
                      'policies': dict(collections.Counter(r['policy'] for r in records))}, indent=2))


if __name__ == '__main__':
    run()
