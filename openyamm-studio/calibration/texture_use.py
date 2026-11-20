#!/usr/bin/env python3
"""Which shipped dungeons use a texture, and which textures a shipped dungeon is built from.

A new dungeon should take each area's textures from one coherent family of a shipped map whose purpose fits, not
pick textures one by one by name from many maps (the user's finding on XD-01, 2026-11-13). This answers the two
questions that needs:

    texture_use.py <texture> [...]        the shipped dungeons that use each texture, most faces first
    texture_use.py --map mm8/d06.blv      the textures a dungeon is built from, most faces first
    texture_use.py --project <folder>     every texture a project uses, with where each comes from; textures
                                          from more than a few maps, or from no shipped dungeon, are flagged
    texture_use.py --rebuild-index        rebuild the index from assets_dev (oymap export of every MM6-8 BLV)

The index lives in output/studio_lead/ (blv_texture_use.json: texture to {"world/map.blv": faces};
blv_names.json: map file to its name in map_stats.txt).
"""
import collections
import glob
import json
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INDEX = os.path.join(REPO, 'output', 'studio_lead', 'blv_texture_use.json')
NAMES = os.path.join(REPO, 'output', 'studio_lead', 'blv_names.json')


def rebuild():
    oymap = os.path.join(REPO, 'openyamm-studio', 'build', 'oymap')
    index = collections.defaultdict(collections.Counter)
    names = {}
    with open(os.path.join(REPO, 'assets_dev', 'engine', 'data_tables', 'map_stats.txt'), encoding='latin-1') as stats:
        for line in stats:
            fields = line.split('\t')
            if len(fields) > 2 and fields[2].lower().endswith('.blv'):
                names.setdefault(fields[2].lower(), fields[1])
    for world in ('mm6', 'mm7', 'mm8'):
        for path in sorted(glob.glob(os.path.join(REPO, 'assets_dev', 'worlds', world, 'maps', '*.blv'))):
            out = subprocess.run([oymap, 'export', path], capture_output=True, text=True).stdout
            try:
                faces = json.loads(out)['map']['faces']
            except (ValueError, KeyError):
                continue
            key = f'{world}/{os.path.basename(path)}'
            for face in faces:
                if not face.get('is_portal'):
                    index[face['texture'].lower()][key] += 1
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, 'w') as out_file:
        json.dump({texture: dict(use) for texture, use in index.items()}, out_file)
    with open(NAMES, 'w') as out_file:
        json.dump(names, out_file)
    print(f'{len(index)} textures indexed')


def load():
    with open(INDEX) as index_file, open(NAMES) as names_file:
        return json.load(index_file), json.load(names_file)


def label(key, names):
    return f'{key} ({names.get(key.split("/")[1], "?")})'


def project_textures(folder):
    import yaml
    found = collections.Counter()

    def walk(node):
        if isinstance(node, dict):
            texture = node.get('texture')
            if isinstance(texture, str):
                found[texture.lower()] += 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for name in ('rooms.yml', 'objects.yml', 'project.yml'):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            with open(path) as project_file:
                walk(yaml.safe_load(project_file))
    return found


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv[0] == '--rebuild-index':
        rebuild()
        return 0
    index, names = load()
    if argv[0] == '--map':
        key = argv[1]
        use = collections.Counter({texture: maps[key] for texture, maps in index.items() if key in maps})
        print(label(key, names))
        for texture, count in use.most_common():
            print(f'  {texture:14s} {count:5d} faces; also in {len(index[texture]) - 1} other dungeons')
        return 0
    if argv[0] == '--project':
        found = project_textures(argv[1])
        sources = collections.Counter()
        for texture in sorted(found):
            maps = index.get(texture, {})
            top = sorted(maps.items(), key=lambda kv: -kv[1])[:2]
            if top:
                sources[top[0][0]] += 1
            flag = '  NOT IN ANY SHIPPED DUNGEON' if not maps else ''
            print(f'{texture:14s} {", ".join(label(k, names) + f" {n}" for k, n in top)}{flag}')
        print(f'\n{len(found)} textures; their main source maps: {len(sources)}')
        for key, count in sources.most_common():
            print(f'  {count:3d}  {label(key, names)}')
        return 0
    for texture in argv:
        maps = index.get(texture.lower(), {})
        print(texture, '(in no shipped dungeon)' if not maps else '')
        for key, count in sorted(maps.items(), key=lambda kv: -kv[1])[:8]:
            print(f'  {count:5d}  {label(key, names)}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
