#!/usr/bin/env bash
# Geometry chain on the painted master (positions/faces/weights only; the paid paints stay valid), repo root:
# cap_fix (cap_normals.py) -> cap_reshape.py (MM9's tall flat-topped skullcap) -> sleeve_tuck -> cuff_trim (-1.5 cm both
# sides) -> linings.sh (from work/tuck_trim.blend) -> head_rigid.py -> body_reweight.py -> stub_cap.py -> twin_patch.py (own-paint two-sided
# patches where the see-through gate found folds seen from behind) -> work/rigid_v3.blend -> neck-cap twins -> work/rigid_v3n.blend (the build default).
set -euo pipefail
P=level_generation/creatures/mm9_peasantdm4_claude; W=$PWD/$P/work; BL=$P/scripts/bl.sh
$BL "CAP_RESHAPE|Error|Trace" $P/scripts/cap_reshape.py $W/cap_fix.blend $W/cap_shape.blend 0.02 0.2 | cut -c1-200
$BL "TUCK|Error|Trace" $P/scripts/sleeve_tuck.py $W/cap_shape.blend $W/tuck.blend 0.7 0.004 1 | cut -c1-120
$BL "CUFF|Error|Trace" $P/scripts/cuff_trim.py $W/tuck.blend $W/tuck_trim.blend 0.01 L=-0.015,R=-0.015 | cut -c1-120
bash $P/scripts/linings.sh | grep -E "LININGS|Error|Trace" | cut -c1-120
$BL "HEAD_RIGID|Error|Trace" $P/scripts/head_rigid.py $W/linings_v1.blend $W/rigid_v1.blend
# chest/collar/collarbone weights (user, Talk: "twists his clothing on breast/collarbones"): no Ponytail1/Bone03/Head share on
# body vertices, upper-arm and clavicle shares fading out toward the midline
$BL "BODY_REWEIGHT|Error|Trace" $P/scripts/body_reweight.py $W/rigid_v1.blend $W/rigid_v1w.blend
$BL "STUB_CAP|Error|Trace" $P/scripts/stub_cap.py $W/rigid_v1w.blend $W/rigid_v2.blend | cut -c1-120
# twin patches (Blender rest frame; the export mirrors x and lifts 0.603 m): the +x shoulder top and upper back where the
# puffed sleeve folds against the vest (Death 110 px, X 74, Running 97), the skirt sides at the hips (Death 65), the boots'
# turned-down cuff undersides (14-18 px in every clip)
TP="0.19,0.08,0.352;0.194,0.1,0.345;0.165,0.06,0.359;0.20,0.072,0.334;0.178,0.146,0.311;0.137,0.161,0.295;0.104,0.16,0.313"
# (the mirrored left-shoulder points were tried and made the left sleeve worse, 18 -> 73 px: that side is not a mirror)
TP="$TP;0.183,0.052,0.066;-0.183,0.052,0.066"
TP="$TP;0.018,0.074,-0.432;0.023,0.097,-0.432;-0.165,0.198,-0.433;-0.043,0.119,-0.433;-0.018,0.074,-0.432;-0.023,0.097,-0.432;0.165,0.198,-0.433;0.043,0.119,-0.433"
$BL "TWIN_PATCH|Error|Trace" $P/scripts/twin_patch.py $W/rigid_v2.blend $W/rigid_v3.blend "$TP" 0.05
# (tried: an unflipped copy 3 mm under the -x shoulder crack, twin_patch.py flip 0 -> rigid_v4: the left sleeve went from
# 17 to 28 px, the copies at the fold landed outside the silhouette; not used)
# the neck cap under the beard, seen through the collar gap when the head turns (chest weights no longer drag the collar
# with the head): two-sided there
$BL "TWIN_PATCH|Error|Trace" $P/scripts/twin_patch.py $W/rigid_v3.blend $W/rigid_v3n.blend "-0.046,0.029,0.334;0.0,0.03,0.33;0.046,0.029,0.334" 0.06 0.0005 1 1
echo GEOM_CHAIN done
