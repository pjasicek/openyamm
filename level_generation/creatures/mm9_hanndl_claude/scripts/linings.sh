#!/usr/bin/env bash
# Linings behind Hanndl's open garment rims (2026-11-02, see-through gate: the background through the belt band's rims and
# the collar, mostly on the lying corpse). PeasantDM2's neck_cap.py and rim_lining.py (copied), on the sleeve-tucked master
# work/master_v2.blend -> work/master_v3.blend. Geometry is added only: the paid paints and every UV stay valid.
# Annud's body has no open rim at the cuffs or the tunic hem (Meshy closed them), only the collar loops and the belt band.
# Usage (project folder): scripts/linings.sh
set -euo pipefail
P=$PWD; W=$P/work; T=$P/textures; V=$P/v2/textures
B() { /snap/bin/blender --background --factory-startup --python "$@" 2>&1 | grep -E "RIM_LINING|NECK_CAP|Error|Trace" | cut -c1-220; }
RL() { B scripts/rim_lining.py -- $W/$1.blend $W/$2.blend $W/$2.json $T/hanndl_lining_mask.png \
  $T/hanndl_basecolor_graded.png $T/hanndl_metal_rough_1k.png "${@:3}"; }
B scripts/neck_cap.py -- $W/master_v2.blend $W/lin_s1.blend $V/hanndl_head_basecolor.png
RL lin_s1 lin_s2 bones=Neck,Head band_bones=Neck,Head,Spine,Clavicle depth=0.30 region=R zmin=0.45 inner_offset=0.0005
RL lin_s2 master_v3 bones=Spine band_bones=Spine,Pelvis,Bone,Thigh depth=0.12 region=R zmin=0.10 zmax=0.26 min_edges=12 \
  inner_offset=0.0005
echo "LININGS done -> $W/master_v3.blend"
