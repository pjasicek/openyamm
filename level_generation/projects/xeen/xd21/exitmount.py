#!/usr/bin/env python3
"""Compose output/studio_cal/xd21/mount_exit: this map's mount plus the X2 agent's current mount (output/studio_cal/x2/
mount), so the quay door's exit can be walked onto X2. Worlds files are hard links (never written); the engine tables
are fresh files: X2's, with this map's map_stats and bolster_maps rows added."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os, shutil, subprocess, sys
X = _REPO_ROOT + '/output/studio_cal'
OUT = f'{X}/xd21/mount_exit'
if os.path.exists(OUT):
    sys.exit(f'{OUT} exists: remove it first (rm -r with its literal path)')
os.makedirs(f'{OUT}/engine/data_tables')
subprocess.run(['cp', '-al', f'{X}/x2/mount/worlds', f'{OUT}/worlds'], check=True)
for sub in ('maps', 'events/maps'):
    os.makedirs(f'{OUT}/worlds/mm7/{sub}', exist_ok=True)
    for f in os.listdir(f'{X}/xd21/mount/worlds/mm7/{sub}'):
        os.link(f'{X}/xd21/mount/worlds/mm7/{sub}/{f}', f'{OUT}/worlds/mm7/{sub}/{f}')
shutil.copyfile(f'{X}/x2/mount/engine/data_tables/outdoor_travels.txt', f'{OUT}/engine/data_tables/outdoor_travels.txt')
mine_b = [l for l in open(f'{X}/xd21/mount/engine/data_tables/bolster_maps.txt', encoding='latin-1') if l.startswith('9137\t')]
rows_b = [l for l in open(f'{X}/x2/mount/engine/data_tables/bolster_maps.txt', encoding='latin-1') if not l.startswith('9137\t')]
open(f'{OUT}/engine/data_tables/bolster_maps.txt', 'w', encoding='latin-1').write(''.join(rows_b + mine_b))
mine = [l for l in open(f'{X}/xd21/mount/engine/data_tables/map_stats.txt', encoding='latin-1') if l.startswith('9137\t')]
rows = [l for l in open(f'{X}/x2/mount/engine/data_tables/map_stats.txt', encoding='latin-1') if not l.startswith('9137\t')]
open(f'{OUT}/engine/data_tables/map_stats.txt', 'w', encoding='latin-1').write(''.join(rows + mine))
print('composed', OUT)
