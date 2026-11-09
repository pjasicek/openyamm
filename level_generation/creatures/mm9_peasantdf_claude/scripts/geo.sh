#!/bin/bash
# Geometry chain after fit + reduce (repo root): bracelets dropped -> MPFB hands -> level neck cut -> head split ->
# eye sockets filled, cups dropped, socket holes closed -> ears tucked -> wrist rings trimmed -> work/eyes_trim.blend
set -e
P=level_generation/creatures/mm9_peasantdf_claude; W=$PWD/$P/work; S=$P/scripts
$S/bl.sh "BRACELETS|Error|Trace" $S/drop_bracelets.py $W/rig_v1.blend $W/rig_v2.blend
$S/bl.sh "^GRAFT|Error|Trace" $S/graft_hands.py $PWD/$S/graft_pdf.json | cut -c1-200
$S/bl.sh "NECKCUT|Error|Trace" $S/neck_bisect.py $W/hands_v1.blend $W/hands_v3.blend
$S/bl.sh "HEADSPLIT|Error|Trace" $S/head_split.py $PWD/$S/head_pdf.json | cut -c1-200
$S/bl.sh "EYEFILL|Error|Trace" $S/eye_fill.py $W/head_v1.blend $W/eyes_v0.blend 2,5 | cut -c1-120
$S/bl.sh "Error|Trace" $S/loose_parts.py $W/eyes_v0.blend $W/eyes_v1.blend 70 0.03 | grep -v '^PART' || true
FILL_NEAR="0.018,-0.087,0.438;-0.028,-0.087,0.436" $S/bl.sh "FILLED|Error|Trace" $S/fill_holes.py $W/eyes_v1.blend $W/eyes_v2.blend 8
$S/bl.sh "EARTUCK|Error|Trace" $S/ear_tuck.py $W/eyes_v2.blend $W/eyes_v3.blend
$S/bl.sh "CUFF|Error|Trace" $S/cuff_trim.py $W/eyes_v3.blend $W/eyes_trim.blend -0.03 | cut -c1-200
$S/bl.sh "WRISTCLAMP|Error|Trace" $S/stub_clamp.py $W/eyes_trim.blend $W/eyes_trim2.blend
$S/bl.sh "TRIANGULATED|Error|Trace" $S/triangulate.py $W/eyes_trim2.blend $W/eyes_tri.blend  # (stub_clamp v2 ring cap was run later on work/master_v1.blend -> master_v1b.blend, positions only)
echo GEODONE
