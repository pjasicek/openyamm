#!/usr/bin/env python3
"""Inventory of every decoration placed in the MM8 maps (outdoor ODM and dungeon BLV), written to ../inventory.json.

Placements resolve to decoration table rows by name, as the game does (DecorationTable::resolveMapDecoration); the
raw ids in MM8 maps do not match the merged table. Per decoration: placements per map, native frames and loop
(1/16 s units), first frame texture and its restored x2 file, opaque native size and DSFT scale, world height (opaque
native pixel height x scale, the binding height), light radius, and the existing engine model of a decoration that
shows the same image (MM6 boulders, torch, campfires).
Usage: python3 scripts/inventory.py"""
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
ASSETS = REPO / 'assets_dev'
sys.path.insert(0, str(REPO / 'util'))
from map_export import parse_blv_file, parse_odm_file  # noqa: E402

LEGACY = ASSETS / '_legacy/sprites_original'
X2 = ASSETS / 'engine/decorations_x2'


def decoration_table():
    rows, by_name = {}, {}
    for line in (ASSETS / 'engine/data_tables/decoration_data.txt').read_text(encoding='latin1').splitlines():
        cells = line.split('\t')
        if len(cells) < 13 or not cells[0].strip().isdigit():
            continue
        index = int(cells[0])
        rows[index] = dict(name=cells[1].strip(), hint=cells[2].strip(), radius=int(cells[4] or 0),
                           light=int(cells[6] or 0), flags=cells[11].strip(),
                           sprite=int(cells[12]) if cells[12].strip().isdigit() else 0)
        by_name.setdefault(cells[1].strip().lower(), index)
    return rows, by_name


def main():
    rows, by_name = decoration_table()
    sprites = {s['sprite_id']: s for s in
               yaml.safe_load((ASSETS / 'engine/rendering/sprite_frame_data_common.yml').read_text())['sprites']}
    legacy = {name.lower(): name for name in os.listdir(LEGACY)}
    x2 = defaultdict(list)
    for name in os.listdir(X2):
        if name.endswith('.png') and '_p' in name:
            x2[name.rsplit('_p', 1)[0].lower()].append(name)

    # Engine manifests (every world) plus any world extension files.
    bound = defaultdict(list)
    manifests = [('engine', ASSETS / 'engine/models')] + [(w, ASSETS / 'worlds' / w / 'models')
                                                           for w in sorted(os.listdir(ASSETS / 'worlds'))]
    for scope, folder in manifests:
        for manifest in ('decorations.yml', 'indoor_decorations.yml'):
            path = folder / manifest
            if not path.exists():
                continue
            for binding in (yaml.safe_load(path.read_text()) or {}).get('decorations', []):
                index = by_name.get(binding['name'].lower())
                if index is not None and binding.get('model'):
                    bound[rows[index]['sprite']].append(f"{scope}:{binding['name']}:{binding['model']}")

    placements = defaultdict(lambda: dict(outdoor=0, dungeon=0, maps=Counter()))
    maps = ASSETS / 'worlds/mm8/maps'
    for path in sorted(maps.glob('*.odm')) + sorted(maps.glob('*.blv')):
        outdoor = path.suffix == '.odm'
        for entity in (parse_odm_file(path) if outdoor else parse_blv_file(path))['payload']['entities']:
            name = entity['name'].strip().lower()
            if not name:
                continue
            index = by_name.get(name, entity['decoration_list_id'])
            entry = placements[index]
            entry['outdoor' if outdoor else 'dungeon'] += 1
            entry['maps'][path.name] += 1

    out = []
    for index, entry in placements.items():
        row = rows.get(index)
        sprite = sprites.get(row['sprite']) if row else None
        frames = (sprite or {}).get('frames', [])
        texture = frames[0]['texture_name'] if frames else ''
        if not row or not texture or texture == 'null' or 'DontDraw' in row['flags']:
            continue
        bmp = legacy.get(texture.lower() + '.bmp') or legacy.get(texture.lower() + '0.bmp')
        size = opaque = None
        if bmp:
            image = Image.open(LEGACY / bmp)
            size = list(image.size)
            box = image.point([0] + [255] * 255).getbbox() if image.mode == 'P' else image.getbbox()
            opaque = [box[2] - box[0], box[3] - box[1]] if box else None
        scale = frames[0].get('scale', 1.0)
        out.append(dict(
            name=row['name'], hint=row['hint'], outdoor=entry['outdoor'], dungeon=entry['dungeon'],
            maps=dict(entry['maps'].most_common()), light=row['light'], flags=row['flags'],
            sprite=sprite.get('sprite_name'), frames=len(frames), anim=sprite.get('animation_length_raw'),
            frame_textures=[f['texture_name'] for f in frames], tex=texture,
            files=sorted({f for t in frames for key in x2 if key == t['texture_name'].lower()
                          or (key[:-1] == t['texture_name'].lower() and key[-1].isdigit()) for f in x2[key]}), native_size=size, opaque_size=opaque, scale=scale,
            height=round(opaque[1] * scale) if opaque else None,
            width=round(opaque[0] * scale) if opaque else None,
            same_image_bound=bound.get(row['sprite'], [])))
    out.sort(key=lambda r: -(r['outdoor'] + r['dungeon']))
    (HERE / 'inventory.json').write_text(json.dumps(out, indent=1) + '\n')
    print(len(out), 'types', sum(r['outdoor'] for r in out), 'outdoor', sum(r['dungeon'] for r in out), 'dungeon')


if __name__ == '__main__':
    main()
