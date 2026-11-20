#!/usr/bin/env python3
"""In-game comparison fixture and tours for the Crystal Walker v2 (copied from mm8_crystal_material_claude) (same cameras and spawn points as the m548 codex and
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
# the v2 walker's own measured strides (planted-sole speed per cycle): walk 0.70 m / 1.0 s, run 1.00 m / 0.75 s
text = data.decode()
head = text.index('- descriptor: Crystal Walker A'); tail = text.index('- descriptor: Crystal Walker C'); tail = text.index('- descriptor:', tail + 10)
block = text[head:tail].replace('stride_length: 0.9\n', 'stride_length: 0.7\n').replace('run_stride_length: 1.3\n', 'run_stride_length: 1.0\n')   # no-op once installed
manifest.write_text(text[:head] + block + text[tail:])

SPAWNS = {
    'out_walker': [(148, -4760, 3322, 1), (149, -4695, 3029, 1), (150, -4630, 2736, 1)],
    'in_walker': [(148, 900, -2935, -47), (149, 900, -2735, -47), (150, 900, -3135, -47)],
}
out = project / 'review' / 'ingame' / label; out.mkdir(parents=True, exist_ok=True)
# a hostile tier-A walker spawned close: it walks in and attacks the immortal party; captured every 0.2 s
att = [{'expect': 'gameplay'}, {'wait': 1}, {'key': '`'}, {'wait': 0.25},
       {'text': 'actor spawn 148 1 -4000 3170 1'}, {'key': 'Return'}, {'wait': 0.25}, {'key': '`'}, {'wait': 1.0}]
for k in range(40):
    att += [{'capture': f'a{k:02d}'}, {'wait': 0.2}]
(Path(__file__).resolve().parents[1] / 'review' / 'ingame' / label).mkdir(parents=True, exist_ok=True)
(Path(__file__).resolve().parents[1] / 'review' / 'ingame' / label / 'out_attack.yml').write_text(
    yaml.safe_dump({'output_dir': str(Path(__file__).resolve().parents[1] / 'review' / 'ingame' / label / 'out_attack'),
                    'exit': True, 'steps': att}, sort_keys=False))
for run, spawns in SPAWNS.items():
    steps = [{'expect': 'gameplay'}, {'wait': 1}, {'key': '`'}, {'wait': 0.25}]
    for m, x, y, z in spawns:
        steps += [{'text': f'actor spawn {m} 1 {x} {y} {z} friendly'}, {'key': 'Return'}, {'wait': 0.25}]
    steps += [{'key': '`'}, {'wait': 0.2}, {'capture': 'front'}, {'wait': 1.0}, {'capture': 'walk'},
              {'wait': 1.0}, {'capture': 'later'}]
    (out / f'{run}.yml').write_text(yaml.safe_dump({'output_dir': str(out / run), 'exit': True, 'steps': steps},
                                                   sort_keys=False))
print(target)
