"""Retirement of the restored sprites that projectiles and their impacts no longer draw.

No projectile or impact draws its native sprite (models in engine/models/projectiles.yml, effects in
engine/effects/projectiles.yml; the regression case projectile_visuals_draw_no_native_sprites checks it). The
projectile objects are the unpickable ones that spells (display and impact objects, spells.txt), monster missiles
(monster_projectiles.txt objects and impacts) and the water splash (object 800) use. A texture of their sprites is
retirable when no other sprite of any sprite frame table (engine, worlds, monster frames), no other object (items,
placed objects) and no decoration (decoration_data.txt SpriteId) uses it. Reports the textures and their restored x2 files in assets_dev/engine/decorations_x2/;
--archive YYYYMMDD moves those files to assets_legacy/projectiles_x2_<date>/ (a missing x2 sprite falls back to the
native bitmap). decorations_x2/manifest.json keeps its entries as the approval record, as for the retired decoration
sprites.
Usage: python3 -I retire_sprites.py [--list] [--archive YYYYMMDD]"""
import argparse
import glob
import os
import re
import shutil

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DEV = os.path.join(REPO, 'assets_dev')
X2 = os.path.join(DEV, 'engine', 'decorations_x2')
NO_PICKUP = 'NoPickup'


def decoration_sprite_ids():
    ids = set()
    for row in table_rows('decoration_data.txt')[2:]:
        if len(row) > 12 and row[12].strip().isdigit():
            ids.add(int(row[12]))
    return ids


def sprite_tables():
    paths = [os.path.join(DEV, 'engine', 'rendering', 'sprite_frame_data_common.yml'),
             os.path.join(DEV, 'engine', 'rendering', 'sprite_frame_data_engine_items.yml')]
    paths += glob.glob(os.path.join(DEV, 'worlds', '*', 'rendering', 'sprite_frame_data*.yml'))
    paths += glob.glob(os.path.join(DEV, 'engine', 'rendering', 'sprite_frames', '**', '*.yml'), recursive=True)
    textures = {}
    names_by_id = {}
    for path in paths:
        document = yaml.safe_load(open(path)) or {}
        for sprite in document.get('sprites', []):
            name = str(sprite.get('sprite_name', '')).lower()
            if 'sprite_id' in sprite:
                names_by_id[int(sprite['sprite_id'])] = name
            for frame in sprite.get('frames', []):
                textures.setdefault(name, set()).add(str(frame.get('texture_name', '')).lower())
    return textures, names_by_id


def objects():
    rows = {}
    for line in open(os.path.join(DEV, 'engine', 'data_tables', 'object_list.txt'), encoding='utf-8', errors='replace'):
        fields = line.rstrip('\n').split('\t')
        if line.startswith('//') or len(fields) < 13 or not fields[2].lstrip('-').isdigit():
            continue
        rows[int(fields[2])] = (fields[1].lower(), NO_PICKUP in fields[12])
    return rows


WATER_SPLASH = 800


def table_rows(name):
    path = os.path.join(DEV, 'engine', 'data_tables', name)
    return [line.rstrip('\n').split('\t') for line in open(path, encoding='utf-8', errors='replace')]


def projectile_objects():
    """Object ids that spells, monster missiles and the water splash fly or leave as impacts."""
    ids = {WATER_SPLASH}
    for row in table_rows('spells.txt')[1:]:
        for column in (20, 21):
            if len(row) > column and row[column].strip().lstrip('-').isdigit():
                ids.add(int(row[column]))
    for row in table_rows('monster_projectiles.txt')[1:]:
        for column in (1, 2):
            if len(row) > column and row[column].strip().isdigit():
                ids.add(int(row[column]))
    ids.discard(0)
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', metavar='YYYYMMDD')
    parser.add_argument('--list', action='store_true', help='print the retirable files')
    args = parser.parse_args()
    table = objects()
    bound = {o for o in projectile_objects() if o in table}
    sprites, names_by_id = sprite_tables()
    retired = {table[o][0] for o in bound if o in table and table[o][1]}
    kept = {sprite for o, (sprite, _) in table.items() if o not in bound or not table[o][1]}
    kept |= {names_by_id[i] for i in decoration_sprite_ids() if i in names_by_id}
    needed = set()
    for sprite, textures in sprites.items():
        if sprite not in retired or sprite in kept:
            needed |= textures
    candidates = set()
    for sprite in sorted(retired - kept):
        textures = sprites.get(sprite, set())
        free = textures - needed
        print(f'{sprite}: {len(textures)} textures, {len(free)} retirable')
        candidates |= free
    files = []
    for name in sorted(os.listdir(X2)):
        stem = re.sub(r'_p\d+\.png$', '', name.lower())
        # Directional frames add a view digit to the texture name (sp391 -> sp3910 .. sp3914).
        if name.endswith('.png') and (stem in candidates or stem[:-1] in candidates):
            files.append(name)
    if args.list:
        print(' '.join(files))
    size = sum(os.path.getsize(os.path.join(X2, f)) for f in files)
    print(f'retirable x2 files: {len(files)} ({size / 1e6:.1f} MB)')
    if args.archive:
        target = os.path.join(REPO, 'assets_legacy', f'projectiles_x2_{args.archive}')
        os.makedirs(target, exist_ok=True)
        for name in files:
            shutil.move(os.path.join(X2, name), os.path.join(target, name))
        print('archived to', target)


main()
