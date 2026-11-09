#!/usr/bin/env bash
# Rebuild the one-handed Attack/Cast into the export and the tier viewer files. Usage: oh_build.sh <tag>
set -euo pipefail; cd "$(dirname "$0")/.."; tag=$1
python3 scripts/front_onehand.py work/mm8_m484_r73_pre_attack.glb work/oh_$tag.npz > /dev/null
python3 scripts/ship_onehand.py work/mm8_m484_r73_pre_attack.glb work/oh_$tag.npz work/oh_export_$tag.glb
for t in a b c; do
  python3 scripts/front_onehand.py review/viewer/mm8_m484_${t}_r73.glb work/oh_view_${t}.npz > /dev/null
  python3 scripts/ship_onehand.py review/viewer/mm8_m484_${t}_r73.glb work/oh_view_${t}.npz work/oh_${t}_$tag.glb > /dev/null
done
