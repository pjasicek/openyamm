#!/usr/bin/env bash
# MM6 male peasant fix on the original install (work/orig_mm6_pman_v2.glb, the source before this project): shoulders held.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/shoulder_fix.py work/orig_mm6_pman_v2.glb export/mm6_pman_v2.glb \
  --bones L/B_L_Clavicle/B_L_UpperArm R/B_R_Clavicle/B_R_UpperArm --clips Standing Walking Fidget
