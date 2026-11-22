#!/bin/bash
# A5: put X7's current build into the scratch root made by root.sh (its own new files) and its terrain weights.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -euo pipefail
cd "$OYR"
R=$OYR/output/studio_cal/x7/root
P=devdocs/xeen/briefs/x7/L4
[ -e output/studio_cal/x7/l4_check/sketch.yml ] && P=output/studio_cal/x7/l4_check
openyamm-studio/build-xeen/oymap install $P --build output/studio_cal/x7/build_w --root $R \
  > output/studio_cal/x7/run/root_install.log 2>&1
python3 tools/terrain_materials.py weights --world xeen --map xeen_x7.odm --assets $R \
  > output/studio_cal/x7/run/root_weights.log 2>&1
echo "root refreshed (project $P)"
