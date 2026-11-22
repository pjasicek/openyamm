#!/usr/bin/env python3
"""XD-27: a play mount with this map and X2's current build (output/studio_cal/x2/mount, the X2 agent's scratch
install), so the exit can be walked onto X2. The game takes one --extra-mount; this merges the two (map_stats rows of
both). Run after every install. Writes output/studio_cal/xd27/mount_play (scratch)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import shutil
from pathlib import Path
R = Path(_REPO_ROOT)
X = R / 'output/studio_cal/xd27'
MINE, X2, OUT = X / 'mount', R / 'output/studio_cal/x2/mount', X / 'mount_play'
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(MINE, OUT)
for f in X2.rglob('*'):
    if f.is_file():
        rel = f.relative_to(X2)
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel.as_posix() in ('engine/data_tables/map_stats.txt', 'engine/data_tables/bolster_maps.txt') \
                and (OUT / rel).exists():
            continue
        shutil.copy2(f, dst)
# map_stats and bolster_maps: mine plus X2's row (9136)
n = 0
for table in ('map_stats.txt', 'bolster_maps.txt'):
    mine_f, x2_f = OUT / 'engine/data_tables' / table, X2 / 'engine/data_tables' / table
    if not x2_f.exists():
        continue
    mine = mine_f.read_text(encoding='latin-1').split('\n')
    x2rows = [l for l in x2_f.read_text(encoding='latin-1').split('\n') if l.startswith('9136\t')]
    mine = [l for l in mine if not l.startswith('9136\t')]
    while mine and mine[-1] == '':
        mine.pop()
    mine_f.write_text('\n'.join(mine + x2rows) + '\n', encoding='latin-1')
    n += len(x2rows)
print('mount_play: X2 rows', n)
