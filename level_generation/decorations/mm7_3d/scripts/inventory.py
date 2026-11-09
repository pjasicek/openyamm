#!/usr/bin/env python3
"""Inventory of the MM7 map decorations (outdoor scene entities and dungeon BLV entities), written to inventory.json.

Per decoration name: placements (outdoor, indoor), maps, decoration table hint/flags/light, native sprite frames and
loop (1/16 s units), first frame texture, DSFT scale, restored x2 file and logical size (assets_dev/engine/
decorations_x2), world height of the sprite frame (logical height x scale) and of its opaque art (art_height, with
art_bottom: world units of empty frame below the art, from the first restored frame's alpha), and the model already bound for it by another world's
manifest, if any. Invisible markers (DontDraw, no sprite) are listed with visible: false.
Usage: inventory.py"""
import json
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image
import yaml

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
ASSETS = REPO / 'assets_dev'
sys.path.insert(0, str(REPO / 'tools'))
import export_indoor_scene_yml as blv  # noqa: E402

ENTITY = re.compile(r'^  - entity_index:.*?\n    name: "(.*?)"', re.M)
# Variants of maps that are not separate places (the scene of a map after an event, the dimension-travel copy).
SKIP_SCENES = {'7d05_1', '7out04_1', '7out15_1', '7d29_dimension_travel'}


def blv_entity_names(path):
    reader = blv.ByteReader(path, path.read_bytes())
    layout = blv.detect_blv_layout(reader)
    face_data = reader.read_i32(blv.FACE_DATA_SIZE_OFFSET, 'face data size')
    sector_data = reader.read_i32(blv.SECTOR_R_DATA_SIZE_OFFSET, 'sector data size')
    sector_lights = reader.read_i32(blv.SECTOR_RL_DATA_SIZE_OFFSET, 'sector light data size')
    offset = blv.SECTION_OFFSET
    offset += 4 + reader.read_i32(offset, 'vertices') * blv.VERTEX_RECORD_SIZE
    faces = reader.read_i32(offset, 'faces')
    offset += 4 + faces * layout['face_record_size'] + face_data + faces * blv.TEXTURE_NAME_SIZE
    offset += 4 + reader.read_i32(offset, 'face params') * (blv.FACE_PARAM_RECORD_SIZE + blv.FACE_PARAM_NAME_SIZE)
    offset += 4 + reader.read_i32(offset, 'sectors') * layout['sector_record_size'] + sector_data + sector_lights
    offset += 4  # door count
    count = reader.read_i32(offset, 'entities')
    offset += 4 + count * layout['sprite_record_size']
    return [reader.read_fixed_string(offset + index * blv.SPRITE_NAME_SIZE, blv.SPRITE_NAME_SIZE, 'entity name')
            for index in range(count)]


def main():
    table = {}
    for line in (ASSETS / 'engine/data_tables/decoration_data.txt').read_text(encoding='latin-1').splitlines()[3:]:
        cells = line.split('\t')
        if len(cells) >= 13:
            table[cells[1].lower()] = cells
    sprites = {sprite['sprite_id']: sprite for sprite in
               yaml.safe_load((ASSETS / 'engine/rendering/sprite_frame_data_common.yml').read_text())['sprites']}
    x2 = {binding['name'].lower(): binding for binding in
          json.loads((ASSETS / 'engine/decorations_x2/manifest.json').read_text())['bindings']}
    bound = {}
    for manifest in sorted(ASSETS.glob('engine/models/*decorations.yml')) + sorted(
            ASSETS.glob('worlds/*/models/*decorations.yml')):
        for binding in yaml.safe_load(manifest.read_text()).get('decorations', []):
            bound.setdefault(binding['name'].lower(), binding['model'])

    rows = {}

    def add(name, map_name, outdoor):
        row = rows.setdefault(name.lower(), {'name': name.lower(), 'outdoor': 0, 'indoor': 0, 'maps': set()})
        row['outdoor' if outdoor else 'indoor'] += 1
        row['maps'].add(map_name)

    maps = ASSETS / 'worlds/mm7/maps'
    for scene in sorted(maps.glob('*.scene.yml')):
        name = scene.name[:-len('.scene.yml')]
        text = scene.read_text()
        if name in SKIP_SCENES or 'kind: "outdoor_scene"' not in text[:200]:
            continue
        begin = text.find('\nentities:')
        end = text.find('\nspawns:', begin)
        for entity in ENTITY.findall(text[begin:end]):
            add(entity, name + '.odm', True)
    for path in sorted(maps.glob('*.blv')):
        for entity in blv_entity_names(path):
            add(entity, path.name, False)

    out = []
    for name, row in rows.items():
        cells = table.get(name)
        sprite = sprites.get(int(cells[12])) if cells and cells[12].lstrip('-').isdigit() else None
        frames = (sprite or {}).get('frames', [])
        texture = frames[0]['texture_name'].lower() if frames else ''
        scale = frames[0].get('scale', 1.0) if frames else 0.0
        restored = x2.get(texture) or x2.get(texture + '0')  # directional sprites: view 0 (front)
        flags = cells[11] if cells else '?'
        visible = bool(texture) and texture != 'null' and 'DontDraw' not in flags
        logical = restored['logical_size'] if restored else None
        art_height = art_bottom = None
        if restored:
            alpha = np.asarray(Image.open(ASSETS / 'engine/decorations_x2' / restored['file']).convert('RGBA'))[..., 3]
            rows_with_art = np.nonzero((alpha > 32).any(axis=1))[0]
            if len(rows_with_art):
                per_pixel = logical[1] * scale / alpha.shape[0]
                art_height = round((rows_with_art[-1] + 1 - rows_with_art[0]) * per_pixel)
                art_bottom = round((alpha.shape[0] - 1 - rows_with_art[-1]) * per_pixel)
        out.append({
            'name': name, 'visible': visible, 'count': row['outdoor'] + row['indoor'],
            'outdoor': row['outdoor'], 'indoor': row['indoor'], 'maps': sorted(row['maps']),
            'hint': cells[2] if cells else '?', 'flags': flags, 'light_radius': int(cells[6]) if cells else 0,
            'frames': len(frames), 'loop': (sprite or {}).get('animation_length_raw'),
            'textures': [frame['texture_name'].lower() for frame in frames],
            'scale': scale, 'x2': restored['file'] if restored else None, 'logical': logical,
            'height': round(logical[1] * scale) if logical else None,
            'art_height': art_height, 'art_bottom': art_bottom,
            'bound_model': bound.get(name),
        })
    out.sort(key=lambda row: (-row['visible'], -row['count'], row['name']))
    (HERE / 'inventory.json').write_text(json.dumps(out, indent=1) + '\n')
    visible = [row for row in out if row['visible']]
    print(f"{len(visible)} visible decorations, {sum(row['count'] for row in visible)} placements "
          f"({sum(row['outdoor'] for row in visible)} outdoor, {sum(row['indoor'] for row in visible)} indoor)")


if __name__ == '__main__':
    main()
