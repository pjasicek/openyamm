#!/usr/bin/env python3
"""Composes worldtables/engine/data_tables/{monster_data,monster_descriptors,items,map_stats}.txt: the engine table
plus the Xeen world's tableContributions rows, as the studio's readWorldTable (openyamm-studio/core/Project.cpp) and
the game compose them. Passed to oymap validate/build as --mount, because the indoor build of build-xeen's oymap
(IndoorBuild.cpp loweringOptionsOf/dataTable) reads only engine/data_tables and so refuses the world's monster rows.
Rerun after A2 regenerates the world's tables. Remove once the studio's indoor build reads world tables."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path
import yaml
R = Path(_REPO_ROOT + '/assets_dev')
W = pathlib.Path(_REPO_ROOT, 'output/studio_cal/xd21') / 'worldtables/engine/data_tables'
W.mkdir(parents=True, exist_ok=True)
manifest = yaml.safe_load((R / 'worlds/xeen/world.yml').read_text())
for name, table in [('monster_data.txt', 'monster_data'), ('monster_descriptors.txt', 'monster_descriptors'),
                    ('items.txt', 'items'), ('map_stats.txt', 'map_stats')]:
    text = (R / 'engine/data_tables' / name).read_text(errors='surrogateescape')
    for c in manifest['tableContributions']:
        if c['table'] == table and c['mode'] == 'append':
            text += '\n' + (R / 'worlds/xeen' / c['path']).read_text(errors='surrogateescape')
    (W / name).write_text(text, errors='surrogateescape')
print('composed', W)
