#!/bin/bash
# Rebuild both GLBs from the paid paints after a texture, weight or clip change (project folder):
#   scripts/rebuild.sh <viewer revision> [--install]
# human: head default g2, tiers pg_g2 / pg_g3, the elf ears left out; elf: head g1e, tier pg_g1e, ears kept.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/head_fix3_pg.py g2 g3 g1e | grep -E "HEADFIX|Error"      # r27: fresh head paint on the final mouth (head_fix2_pg.py was for the r24 paint)
python3 scripts/tiers_pg.py | grep -E "TIERS|Error"
for side in human elf; do
  if [[ $side == human ]]; then T=g2; S=_h; DP=ears; else T=g1e; S=_e; DP=; fi
  HEAD_TIER=$T python3 scripts/finish_pg.py | tail -1 | cut -c1-40
  python3 scripts/add_cap.py work/uv_tex.npz work/uv_tex.npz | tail -1
  python3 scripts/fill_holes.py work/uv_tex.npz work/uv_tex.npz | tail -1
  python3 scripts/tweak_pg.py work/uv_tex.npz work/uv_tex2.npz | tail -1
  DROP_PARTS=$DP OUTSUF=$S scripts/rig.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace|HALF"
  scripts/build_runtime.sh $side ${2:-} 2>&1 | grep -E "Error|Trace|WINDING|inverted|Installed|installed|mm9_peasantgirl"
done
[ -x scripts/viewer_update.sh ] && scripts/viewer_update.sh $1 | tail -1 || true
