#!/bin/bash
# Lane A8 lighting bake of one Xeen dungeon: a8_bake.sh <key> <asset root>; output output/studio_cal/<key>/a8_bake/bake,
# then installed beside the map in assets_dev by temp file and rename (A7's bake_map.sh and install_bake.py, A8 paths).
set -e
k=$1; root=$2; shift 2
cd "$(dirname "$(readlink -f "$0")")/../../../../.."
out=output/studio_cal/$k/a8_bake/bake
mkdir -p $out
tools/heavy.sh 16 \
  blender --background --factory-startup --python-exit-code 1 --python tools/lighting/bake_indoor.py -- \
  --profile tools/lighting/baked_indoors/profiles/xeen_$k.yml --output $out --assets $root \
  --game-binary "$PWD/build-xeen/game/openyamm" --sources "$PWD/assets_source" "$@"
python3 - "$k" <<'PY'
import os, shutil, sys
from pathlib import Path
n = sys.argv[1]
src = Path(f'output/studio_cal/{n}/a8_bake/bake')
dst = Path('assets_dev/worlds/xeen/maps')
for name in (f'xeen_{n}.lighting', f'xeen_{n}.bake.json'):
    tmp = dst / (name + '.a8tmp')
    shutil.copyfile(src / name, tmp)
    os.chmod(tmp, 0o644)
    os.replace(tmp, dst / name)
    print('installed', dst / name, (dst / name).stat().st_size)
PY
