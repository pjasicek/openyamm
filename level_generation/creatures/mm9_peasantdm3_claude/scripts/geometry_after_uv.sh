#!/usr/bin/env bash
# Geometry steps after the head UV pass (positions/faces/weights only; the paid paints stay valid). Repo root.
#   work/texpass_head.blend -> ear_flatten (ears under the hair) -> curtain_close (hair curtain onto the cheek/jaw, out of
#   the tunic) -> rigid_beard (face/beard 100 % Head) -> hair_twin (hair thickness at the nape) -> linings.sh (neck cap,
#   collar, belt, boots, sleeves) -> cuff_lining (the folded linen cuffs) -> work/linings_v2.blend (build default).
# The head UV pass (uv_pass.sh) must NEVER re-run: the head retexture belongs to work/texpass_head.blend's layout.
set -euo pipefail
P=level_generation/creatures/mm9_peasantdm3_claude; W=$PWD/$P/work; BL=$P/scripts/bl.sh
$BL "EARFLAT|rror" $P/scripts/ear_flatten.py $W/texpass_head.blend $W/ears_v2.blend 0.1 0.066
$BL "CURTAIN|rror|Trace" $P/scripts/curtain_close.py $W/ears_v2.blend $W/curtain_v2.blend 0.003 0.006 3.5 | cut -c1-300
$BL "RIGIDBEARD|rror" $P/scripts/rigid_beard.py $W/curtain_v2.blend $W/rigid_v1.blend
$BL "HAIRTWIN|rror|Trace" $P/scripts/hair_twin.py $W/rigid_v1.blend $W/hairtwin_v1.blend
$P/scripts/linings.sh | grep -o 'RIM_LINING {"loops": \[[^]]\{0,100\}\|LININGS.*'
$BL "CUFF_LINING|rror|Trace" $P/scripts/cuff_lining.py $W/linings_v1.blend $W/linings_v2.blend 0.020 0.003 \
  $PWD/$P/textures/pdm3_tp_basecolor_graded.png force 0.0
