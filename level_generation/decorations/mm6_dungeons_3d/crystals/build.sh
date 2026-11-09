#!/usr/bin/env bash
# Build the crystal batch (README.md): textures -> Blender build -> review renders and sheet -> finish (link LODs,
# validate) [--install copies new GLBs to assets_dev/worlds/mm6/models]. Usage: build.sh [--install] [prop...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"
blender=/snap/bin/blender
install=; if [[ "${1:-}" == --install ]]; then install=--install; shift; fi
mkdir -p work/logs
python3 scripts/make_textures.py > work/logs/textures.log
python3 scripts/make_memory_crystal.py > work/logs/memory_crystal.log
# prop:builder:native first frame:review yaw
for entry in crystl0:build_crystals:crystl0_p549.png:0 crclstr:build_crystals:crclstr_p142.png:0 \
             crys6:build_crystals:crys6_p142.png:0 crys5:build_crystals:crys5_p142.png:0 \
             mcryst01:build_mcryst:mcryst01_p549.png:0 stlmite1:build_stalagmite:stlmite1_p142.png:0 \
             stlmite2:build_stalagmite:stlmite2_p142.png:0 stlmite3:build_stalagmite:stlmite3_p142.png:0 \
             corinth:build_corinth:corinth_p546.png:0; do
  IFS=: read -r prop builder native yaw <<< "$entry"
  if (( $# )) && [[ " $* " != *" $prop "* ]]; then continue; fi
  "$blender" --background --python "scripts/$builder.py" -- "$prop" > "work/logs/$prop.log" 2>&1
  tris=$(grep '^EXPORTED' "work/logs/$prop.log" | sed 's/.*tris \[\(.*\)\]/\1/' | tr -d ',')
  "$blender" --background --python scripts/review.py -- "$prop" "$yaw" > "work/logs/${prop}_review.log" 2>&1
  grep '^RENDER MEAN' "work/logs/${prop}_review.log" || true
  python3 scripts/sheet.py "$prop" "$native" $tris
  if [[ "$prop" == corinth ]]; then
    "$blender" --background --python scripts/detail.py -- corinth 0.8 1.0 0.0 0.27 > "work/logs/${prop}_detail.log" 2>&1
  fi
  python3 scripts/finish.py "$prop" $install
done
