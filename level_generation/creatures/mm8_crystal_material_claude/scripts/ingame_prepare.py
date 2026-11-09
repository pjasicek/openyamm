#!/usr/bin/env python3
"""In-game comparison fixture and tours for the crystal material (same cameras and spawn points as the m548 codex and
m596 comparison captures). The fixture is a hard-linked copy of assets_dev with the Crystal Dragon (112-114) and
Crystal Walker (148-150) families preloaded in 6d19 and oute3 (actor spawn needs the family loaded; production maps
unchanged), taken after the models to compare are installed: the installed runtime copies are new files, so each
fixture keeps the models of its moment. Usage: ingame_prepare.py <label>  -> work/fixture_<label>/assets and
review/ingame/<label>/<run>.yml"""
import copy
import os
import shutil
import sys
from pathlib import Path

import yaml

project = Path(__file__).resolve().parents[1]; root = project.parents[2]
label = sys.argv[1]
source = root / 'assets_dev'; target = project / 'work' / f'fixture_{label}' / 'assets'
if target.exists():
    shutil.rmtree(target.parent)
shutil.copytree(source, target, copy_function=os.link, symlinks=True)
for relative in map(Path, ['worlds/mm6/maps/6d19.scene.yml', 'worlds/mm6/maps/oute3.scene.yml']):
    scene = yaml.safe_load((source / relative).read_bytes()); actors = scene['initial_state']['actors']
    for monster in (112, 113, 114, 148, 149, 150):
        actor = copy.deepcopy(actors[0])
        actor.update(actor_index=len(actors), name='Crystal preload fixture', monster_info_id=monster,
                     monster_id=monster, unique_name_index=0, group=999, ally=999, hostility_type=0,
                     sprite_ids=[0, 0, 0, 0], immobile=True)
        actors.append(actor)
    (target / relative).unlink(); (target / relative).write_text(yaml.safe_dump(scene, sort_keys=False))
manifest = target / 'worlds/mm8/models/actors.yml'; data = manifest.read_bytes(); manifest.unlink()
manifest.write_bytes(data)

SPAWNS = {
    'out_dragon': [(112, -4760, 3322, 1), (113, -4695, 3029, 1), (114, -4630, 2736, 1)],
    'out_walker': [(148, -4760, 3322, 1), (149, -4695, 3029, 1), (150, -4630, 2736, 1)],
    'in_dragon': [(112, 500, -2935, -47), (113, 500, -2575, -47), (114, 500, -3295, -47)],
    'in_walker': [(148, 900, -2935, -47), (149, 900, -2735, -47), (150, 900, -3135, -47)],
}
out = project / 'review' / 'ingame' / label; out.mkdir(parents=True, exist_ok=True)
for run, spawns in SPAWNS.items():
    steps = [{'expect': 'gameplay'}, {'wait': 1}, {'key': '`'}, {'wait': 0.25}]
    for m, x, y, z in spawns:
        steps += [{'text': f'actor spawn {m} 1 {x} {y} {z} friendly'}, {'key': 'Return'}, {'wait': 0.25}]
    steps += [{'key': '`'}, {'wait': 0.2}, {'capture': 'front'}, {'wait': 1.0}, {'capture': 'walk'},
              {'wait': 1.0}, {'capture': 'later'}]
    (out / f'{run}.yml').write_text(yaml.safe_dump({'output_dir': str(out / run), 'exit': True, 'steps': steps},
                                                   sort_keys=False))
print(target)
