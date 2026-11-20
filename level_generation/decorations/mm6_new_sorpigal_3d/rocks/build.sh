#!/usr/bin/env bash
# Rebuild the MM6 scan rocks (rock03..rock14, see README.md): ../scripts/build_prop.py with rocks.json -> review
# renders and sheets -> link LODs -> validate [--install copies them to assets_dev/worlds/mm6/models].
# Usage: build.sh [--install] [rock...]   (no rock names: all of them)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project="$(dirname "$here")"
models="$project/../../../assets_dev/worlds/mm6/models"
blender=/snap/bin/blender
cd "$project"
mkdir -p rocks/work/logs
install=; if [[ "${1:-}" == --install ]]; then install=1; shift; fi
for pair in rock07:rok7:315 rock14:rok14:330 rock03:rok3:65 rock04:rok4:300 rock05:rok5:315 rock06:rok6:300 \
            rock08:rok8:150 rock09:rok9:120 rock12:rok12:90 rock13:rok13:225; do
  IFS=: read -r rock sprite yaw <<< "$pair"
  if (( $# )) && [[ " $* " != *" $rock "* ]]; then continue; fi
  PROPS_JSON="$here/rocks.json" PROP_ROOT="$here/$rock" \
    "$blender" --background --python scripts/build_prop.py -- "$rock" > "rocks/work/logs/$rock.log" 2>&1
  "$blender" --background --python scripts/review_render.py -- "rocks/$rock" "rocks/$rock/work/${rock}_export.glb" \
    "$yaw" > /dev/null 2>&1
  python3 scripts/review_sheet.py "rocks/$rock" "$sprite" 2400 960 290 96
  python3 ../../../tools/link_static_model_lods.py "rocks/$rock/work/${rock}_export.glb" \
    "rocks/$rock/work/${rock}_linked.glb"
  python3 scripts/validate_glb.py "rocks/$rock/work/${rock}_linked.glb" 2500 1000 300 100
  if [[ -n "$install" ]]; then
    install -m 0664 "rocks/$rock/work/${rock}_linked.glb" "$models/mm6_deco_${rock}.glb"
  fi
done
