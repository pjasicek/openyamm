#!/usr/bin/env python3
"""Coverage of the 3D decoration bindings and retirement of the restored decoration sprites they replace
(level_generation/MM6_2D_RETIREMENT.md).

Bindings are engine content (engine/models/decorations.yml for outdoor maps, indoor_decorations.yml for dungeons),
which a world may extend with worlds/<world>/models/ manifests of the same names (an entry replaces every engine entry
of its name; model: null keeps the sprite). For every world with maps, the script collects the decoration placements
(outdoor scene entities, dungeon BLV entities) and the event SetSprite string targets of its map scripts, and reports
each drawn decoration (visible sprite) that no binding covers on that map.

A restored sprite in assets_dev/engine/decorations_x2 retires when every decoration showing it is bound wherever it
is placed or switched to, and no other engine table names it. Without --archive nothing moves; the candidates are
written to decoration_sprite_retirement.json beside this script. --archive moves them to
assets_legacy/decorations_x2_<date>/ (one literal move per file, after the listing).
Usage: retire_decoration_sprites.py [--archive YYYYMMDD]"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import yaml

REPO = Path(__file__).resolve().parents[3]
ASSETS = REPO / 'assets_dev'
X2 = ASSETS / 'engine/decorations_x2'
sys.path.insert(0, str(REPO / 'level_generation/decorations/mm7_3d/scripts'))
sys.path.insert(0, str(REPO / 'tools'))
from inventory import blv_entity_names, ENTITY  # noqa: E402

WORLDS = ['mm6', 'mm7', 'mm8', 'mm9']
SET_SPRITE = re.compile(r'SetSprite\(\s*[^,\n]+,\s*[^,\n]+,\s*"([^"]+)"', re.I)


def decoration_table():
    table = {}
    for line in (ASSETS / 'engine/data_tables/decoration_data.txt').read_text(encoding='latin-1').splitlines()[3:]:
        cells = line.split('\t')
        if len(cells) >= 13:
            table.setdefault(cells[1].lower(), cells)
    return table


def manifest_entries(world, file_name):
    """Effective entries of a world (engine entries with the world's replacements)."""
    entries = []
    for index, path in enumerate([ASSETS / 'engine/models' / file_name, ASSETS / 'worlds' / world / 'models' / file_name]):
        if not path.exists():
            continue
        added = yaml.safe_load(path.read_text()).get('decorations') or []
        if index:
            names = {entry['name'].lower() for entry in added}
            entries = [entry for entry in entries if entry['name'].lower() not in names]
        entries += [entry for entry in added if entry.get('model') is not None]
    return entries


def bound_on(world, map_name):
    entries = manifest_entries(world, 'indoor_decorations.yml' if map_name.endswith('.blv') else 'decorations.yml')
    return {entry['name'].lower() for entry in entries
            if not entry.get('maps') or map_name in {name.lower() for name in entry['maps']}}


def map_uses(world):
    """(map file, decoration names placed, SetSprite target names) of every map of a world."""
    maps = ASSETS / 'worlds' / world / 'maps'
    scripts = ASSETS / 'worlds' / world / 'events/maps'
    for scene in sorted(maps.glob('*.scene.yml')):
        text = scene.read_text()
        if 'kind: "outdoor_scene"' not in text[:200]:
            continue
        stem = scene.name[:-len('.scene.yml')]
        if not (maps / (stem + '.odm')).exists():
            continue  # a scene variant (after an event), not a separate map
        entities = text[text.find('\nentities:'):text.find('\nspawns:')]
        yield stem + '.odm', [name.lower() for name in ENTITY.findall(entities)], switch_targets(scripts, stem)
    for path in sorted(maps.glob('*.blv')):
        yield path.name, [name.lower() for name in blv_entity_names(path)], switch_targets(scripts, path.stem)


def switch_targets(scripts, stem):
    names = set()
    for script in sorted(scripts.glob('*.lua')) if scripts.exists() else []:
        lower = script.name.lower()
        if lower == stem.lower() + '.lua' or lower.startswith(stem.lower() + '_'):
            names |= {name.lower() for name in SET_SPRITE.findall(script.read_text(errors='ignore')) if name != '0'}
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--archive', metavar='YYYYMMDD', help='move the retired sprites to assets_legacy')
    args = parser.parse_args()
    table = decoration_table()
    sprites = {sprite['sprite_id']: sprite for sprite in
               yaml.safe_load((ASSETS / 'engine/rendering/sprite_frame_data_common.yml').read_text())['sprites']}
    files_by_texture = {}
    for binding in json.loads((X2 / 'manifest.json').read_text())['bindings']:
        if (X2 / binding['file']).exists():
            files_by_texture.setdefault(binding['name'].lower(), []).append(binding['file'])

    def textures(name):
        cells = table.get(name)
        if not cells or not cells[12].lstrip('-').isdigit():
            return set()
        found = set()
        for frame in (sprites.get(int(cells[12])) or {}).get('frames', []):
            texture = frame['texture_name'].lower()
            # Directional sprites store one file per view (texture + digit).
            found |= {key for key in files_by_texture
                      if key == texture or (key[:-1] == texture and key[-1].isdigit())}
        return found

    def drawn(name):
        # A visible sprite: not DontDraw, and a sprite whose frames name a texture (emitters show "null").
        cells = table.get(name)
        if not cells or 'DontDraw' in cells[11] or not cells[12].lstrip('-').isdigit():
            return False
        frames = (sprites.get(int(cells[12])) or {}).get('frames', [])
        return any(frame['texture_name'].lower() not in ('', 'null') for frame in frames)

    unbound = {}   # (world, name) -> maps
    bound_uses = set()
    for world in WORLDS:
        for map_name, placed, targets in map_uses(world):
            bound = bound_on(world, map_name)
            for name in set(placed) | targets:
                if not drawn(name):
                    continue
                if name in bound:
                    bound_uses.add(name)
                else:
                    unbound.setdefault((world, name), set()).add(map_name + (':SetSprite' if name not in placed else ''))
    unbound_names = {name for _, name in unbound}
    users = {}
    for name in table:
        for texture in textures(name):
            users.setdefault(texture, set()).add(name)
    other_tables = [path.read_text(encoding='latin-1', errors='ignore').lower()
                    for path in list((ASSETS / 'engine/data_tables').glob('*.txt')) + list(ASSETS.glob('engine/*.yml'))
                    if path.name != 'decoration_data.txt']
    retire, kept = [], {}
    for texture in sorted({texture for name in bound_uses for texture in textures(name)}):
        blockers = sorted(users.get(texture, set()) & unbound_names)
        named = any(re.search(r'(?<![a-z0-9])' + re.escape(texture) + r'(?![a-z0-9])', text) for text in other_tables)
        if blockers or named:
            kept[texture] = blockers or ['named by another engine table']
        else:
            retire.append(texture)
    files = sorted(file for texture in retire for file in files_by_texture[texture])
    size = sum((X2 / file).stat().st_size for file in files)
    report = {'unbound': {f'{world}:{name}': sorted(maps) for (world, name), maps in sorted(unbound.items())},
              'retire_files': files, 'bytes': size, 'kept': kept}
    (Path(__file__).with_name('decoration_sprite_retirement.json')).write_text(json.dumps(report, indent=1) + '\n')
    print(f'unbound drawn decorations: {len(unbound)}')
    for (world, name), maps in sorted(unbound.items()):
        print(f'  {world} {name}: {", ".join(sorted(maps)[:6])}{" ..." if len(maps) > 6 else ""}')
    print(f'retirable sprite files: {len(files)} ({size / 1e6:.1f} MB); kept textures of bound decorations: {len(kept)}')
    if args.archive:
        target = REPO / 'assets_legacy' / f'decorations_x2_{args.archive}'
        target.mkdir(parents=True, exist_ok=True)
        for file in files:
            shutil.move(str(X2 / file), str(target / file))
        print(f'moved {len(files)} files to {target.relative_to(REPO)}')


if __name__ == '__main__':
    main()
