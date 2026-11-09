#!/usr/bin/env bash
# PeasantHOM2 tier on the approved PeasantHOM1 runtime GLB (project folder). Append only: add_tier.py, then the proof
# (verify_append.py, glb_diff.py) and the review GLBs. [--install] installs export/mm9_phom1.glb with tools/install_model.py.
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
SRC=work/rollback/mm9_phom1_installed_before_phom2.glb      # copy of the installed approved GLB (sha256 0692f374...)
$V scripts/add_tier.py $SRC export/mm9_phom1.glb phom2_a \
  PHOM1_A=textures/phom2_basecolor_graded.png,textures/phom2_normal_1k.png \
  PHOM1Head_A=v2/textures/phom2_head_basecolor.png,v2/textures/phom2_head_normal_1k.png 2>&1 | grep -v Warn
$V scripts/verify_append.py $SRC export/mm9_phom1.glb 2>&1 | grep -v Warn | cut -c1-300
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm9_phom1.glb | tail -1
$V scripts/variant_glb.py export/mm9_phom1.glb review/viewer/phom2_a.glb phom2_a 2>&1 | grep -v Warn
if [[ "${1:-}" == "--install" ]]; then
  (cd ../../.. && python3 tools/install_model.py level_generation/creatures/mm9_peasanthom2_claude/export/mm9_phom1.glb --world mm9)
fi
