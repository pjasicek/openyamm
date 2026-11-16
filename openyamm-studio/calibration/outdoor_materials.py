#!/usr/bin/env python3
"""Makes the terrain material file of a built outdoor project and puts it where the game finds it.

  outdoor_materials.py <project> (--root <scratch asset root> | --mount <mount folder>)
                       [--build <build folder>] [--preview <file.png>]

The game draws the ground of an outdoor map only from its material file (worlds/<world>/terrain_materials/<map>.yml
with its weight and shore images; level_generation/terrain/materials/README.md), which tools/terrain_materials.py
makes from the map's tiles. That tool writes beside the maps of the asset root it is given, and rewrites the
world's liquid edge masks in place. A scratch root is a hard-link copy of assets_dev, so it must never be that
root: this script lays out a small root of its own (<build>/materials_root: the built map and its scene, the tile
tables, the world's world.yml, all as copies), runs the tool there and copies the three results into the target
as new files (written beside and renamed over, never opened in place).

The project must be built (`oymap build`); its build folder is <project>/build unless --build names another.
--preview also writes the tool's picture of the weights, to check against `oymap render`.
Headless game runs and oymap do not need the material file; a game window does."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
assets = repo / 'assets_dev'


def take_option(arguments, name, default=None):
    if name in arguments:
        at = arguments.index(name)
        value = arguments[at + 1]
        del arguments[at:at + 2]
        return value
    return default


def make_materials(project, target, build=None, preview=None):
    """The material files of the built map, copied under target/worlds/<world>/terrain_materials. Returns their
    names."""
    project = Path(project)
    build = Path(build) if build else project / 'build'
    card = yaml.safe_load((project / 'project.yml').read_text())
    world, stem = card['world'], card['id'].lower()
    if not (build / f'{stem}.odm').is_file():
        sys.exit(f'{build} has no {stem}.odm: build the project first (oymap build)')
    work = build / 'materials_root'
    shutil.rmtree(work, ignore_errors=True)
    maps = work / 'worlds' / world / 'maps'
    materials = work / 'worlds' / world / 'terrain_materials'
    tables = work / 'engine' / 'data_tables'
    for folder in (maps, materials, tables):
        folder.mkdir(parents=True)
    for name in (f'{stem}.odm', f'{stem}.scene.yml'):
        shutil.copyfile(build / name, maps / name)
    shutil.copyfile(assets / 'worlds' / world / 'terrain_materials' / 'world.yml', materials / 'world.yml')
    # The reference map's own shades and shore (world.yml `maps`: Shadowspire's beach of grey dust) for the rebuild,
    # in this copy only.
    reference = str((card.get('map_stats') or {}).get('reference', '')).lower()
    rules = yaml.safe_load((materials / 'world.yml').read_text())
    if reference and reference in (rules.get('maps') or {}):
        rules['maps'][f'{stem}.odm'] = rules['maps'][reference]
        (materials / 'world.yml').write_text(yaml.safe_dump(rules, sort_keys=False))
    for table in sorted((assets / 'engine' / 'data_tables').glob('terrain_tile_data*.txt')):
        shutil.copyfile(table, tables / table.name)
    command = [sys.executable, str(repo / 'tools/terrain_materials.py'), 'weights', '--world', world,
               '--map', f'{stem}.odm', '--assets', str(work)]
    if preview:
        command += ['--preview', str(preview)]
    done = subprocess.run(command, capture_output=True, text=True)
    if done.returncode != 0:
        sys.exit(f'tools/terrain_materials.py failed:\n{done.stdout}{done.stderr}')
    made = sorted(path for path in materials.iterdir() if path.is_file() and path.name != 'world.yml')
    if not any(path.name == f'{stem}.yml' for path in made):
        sys.exit(f'tools/terrain_materials.py wrote no {stem}.yml:\n{done.stdout}{done.stderr}')
    destination = Path(target) / 'worlds' / world / 'terrain_materials'
    destination.mkdir(parents=True, exist_ok=True)
    for path in made:
        # Beside and renamed over: a file of that name in a hard-link root is replaced, not written into.
        beside = destination / (path.name + '.new')
        shutil.copyfile(path, beside)
        os.replace(beside, destination / path.name)
    return [path.name for path in made]


def main():
    arguments = sys.argv[1:]
    root = take_option(arguments, '--root')
    mount = take_option(arguments, '--mount')
    build = take_option(arguments, '--build')
    preview = take_option(arguments, '--preview')
    if len(arguments) != 1 or (root is None) == (mount is None):
        sys.exit(__doc__)
    target = Path(root or mount).resolve()
    if target == assets.resolve():
        sys.exit('the target is assets_dev itself: name a scratch root or a mount folder')
    names = make_materials(arguments[0], target, build, preview)
    print(f'wrote {", ".join(names)} under {target}/worlds/.../terrain_materials')


if __name__ == '__main__':
    main()
