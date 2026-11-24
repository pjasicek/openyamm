#!/bin/bash
# Lane A5 (2026-11-20, fifth session): a map's terrain material weights and the world's shared liquid edge masks,
# written in a private root and swapped into assets_dev file by file (new file + rename), so no game that is loading
# a Xeen map reads a half-written mask (X1 once failed to load while `edges` rewrote them in place).
#   level_generation/projects/xeen/common/install/terrain_swap.sh <stem>      e.g. xeen_x3
# Held under locks/terrain.lock (one swap at a time in the lane). The private root: a real copy of
# worlds/xeen/terrain_materials, hard links (read only) of the maps and the engine's data tables.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../../../.."
stem=$1
here=output/studio_cal/a5
exec {lock}>"$here/locks/terrain.lock"
flock "$lock"
tmp=$here/tm_root_$$
mkdir -p $tmp/worlds/xeen $tmp/engine
cp -r assets_dev/worlds/xeen/terrain_materials $tmp/worlds/xeen/terrain_materials
# the ground plants (F5, 2026-11-21): `weights` writes the map's terrain_decorations/<stem>.yml and the transition
# masks from the hand-written terrain_decorations/plants.yml; swapped back like the weights
cp -r assets_dev/worlds/xeen/terrain_decorations $tmp/worlds/xeen/terrain_decorations
cp -al assets_dev/worlds/xeen/maps $tmp/worlds/xeen/maps
cp -al assets_dev/engine/data_tables $tmp/engine/data_tables
# terrain_materials.py reads the material library and the liquids table from the root it is given (--assets): real
# copies of those two files (2026-11-24: without them `weights` stopped at a missing library.yml, nothing swapped)
mkdir -p $tmp/engine/terrain_materials $tmp/engine/liquids
cp assets_dev/engine/terrain_materials/library.yml $tmp/engine/terrain_materials/library.yml
cp assets_dev/engine/liquids/liquids.yml $tmp/engine/liquids/liquids.yml
# the world's terrainTileset (mm7): without world.yml terrain_materials.py reads MM8's tile names (X7's lava rows, 21:39)
ln assets_dev/worlds/xeen/world.yml $tmp/worlds/xeen/world.yml
# open-air BLVs' ground files (oymap build writes <stem>_blv.yml, XD-17 2026-11-21) are not ODMs: `edges` would open
# <stem>_blv.odm and fail, so the private root leaves them out (the swap below copies only what the root holds)
rm -f $tmp/worlds/xeen/terrain_materials/*_blv.yml $tmp/worlds/xeen/terrain_materials/*_blv_weights*.png
# what the root held before the tools ran: the swap copies back only files the tools wrote or changed, never an
# untouched copy (A6, 2026-11-21: terrain_materials/world.yml edited during a swap was overwritten by the old copy)
for sub in terrain_materials terrain_decorations; do
python3 - $tmp/worlds/xeen/$sub > $tmp/before_$sub.txt <<'PY'
import hashlib, os, sys
for d, _, fs in os.walk(sys.argv[1]):
    for f in fs:
        p = os.path.join(d, f)
        print(hashlib.sha1(open(p, 'rb').read()).hexdigest(), os.path.relpath(p, sys.argv[1]))
PY
done
tools/heavy.sh 8 python3 tools/terrain_materials.py weights --world xeen --map $stem.odm --assets $tmp
tools/heavy.sh 8 python3 tools/terrain_materials.py edges --world xeen --assets $tmp
# F11 (2026-11-21): no swap of weights with texels that do not sum to one or a straight run of hard switches
tools/heavy.sh 8 python3 tools/terrain_materials.py check --world xeen --map $stem.odm --assets $tmp
for sub in terrain_materials terrain_decorations; do
python3 - "$tmp/worlds/xeen/$sub" assets_dev/worlds/xeen/$sub "$tmp/before_$sub.txt" <<'PY'
import filecmp, hashlib, os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
before = dict(reversed(l.split(' ', 1)) for l in open(sys.argv[3]).read().splitlines())
changed = removed = 0
for d, _, files in os.walk(src):
    rel = os.path.relpath(d, src)
    os.makedirs(os.path.join(dst, rel), exist_ok=True)
    for f in files:
        s, t = os.path.join(d, f), os.path.join(dst, rel, f)
        if f in ('world.yml', 'plants.yml') or before.get(os.path.normpath(os.path.join(rel, f))) == \
                hashlib.sha1(open(s, 'rb').read()).hexdigest():
            continue   # not written by this run (world.yml is A6's; never copied back)
        if os.path.exists(t) and filecmp.cmp(s, t, shallow=False):
            continue
        shutil.copyfile(s, t + '.new')
        os.chmod(t + '.new', 0o644)
        os.replace(t + '.new', t)
        changed += 1
# masks the private run removed as stale go too
if os.path.isdir(os.path.join(dst, 'liquid_edges')):
    for f in os.listdir(os.path.join(dst, 'liquid_edges')):
        if f.endswith('.png') and not os.path.exists(os.path.join(src, 'liquid_edges', f)):
            os.remove(os.path.join(dst, 'liquid_edges', f))
            removed += 1
print(f'{os.path.basename(dst)}: swapped {changed} files, removed {removed} stale masks')
PY
done
python3 - "$tmp" <<'PY'
import os, shutil, sys
t = os.path.realpath(sys.argv[1])
assert os.path.basename(t).startswith('tm_root_') and t.startswith(os.path.realpath('output/studio_cal/a5') + '/')
shutil.rmtree(t)
PY
