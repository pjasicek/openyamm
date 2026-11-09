#!/usr/bin/env bash
# Puts the m372 texture pass on the pre-pass installed GLB and checks it; with --install also installs it (under the
# shared texture-pass install lock: a concurrent full cook once deleted a freshly cooked texture).
# Source: work/merge_src_mm7_m372.glb, the installed file before the pass (sha256 4b05594e…, the gait-h14 build). After
# a later layer reinstalls the model without the pass, copy that file there first (FRESH=1 does it): its LOD0 must
# still be the pre-pass mesh.
# apply_layout.py keeps every clip, node and material of its input and refuses an input whose LOD0 differs from the
# mesh the paid layout belongs to. Usage (repository root): merge_install.sh [--install]
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm7_m372_texpass_claude
INSTALL=${1:-}
if [[ "${FRESH:-}" == 1 ]]; then
    cp assets_source/worlds/mm7/models/mm7_m372.glb "$P/work/merge_src_mm7_m372.glb"
fi
# round 3: the robe hangs straight in the idle clips (arms out 6 deg, no hand push on the robe chains; see README)
python3 "$P/scripts/dress_fix.py" "$P/work/merge_src_mm7_m372.glb" "$P/work/mm7_m372_dressed.glb" 6
python3 "$P/scripts/apply_layout.py" "$P/work/mm7_m372_dressed.glb" "$P/work/uv_v2e.npz" "$P/textures/m372_final" \
    "$P/work/mm7_m372_prefix.glb"
A="Standing:Robe_*,B_L_UpperArm,B_R_UpperArm Fidget:Robe_*,B_L_UpperArm,B_R_UpperArm Hit:Robe_*,B_L_UpperArm,B_R_UpperArm"
python3 "$P/scripts/glb_diff.py" "$P/work/merge_src_mm7_m372.glb" "$P/work/mm7_m372_prefix.glb" $A
# face follow-up: the spike removed, the cheek hole and the mouth opening filled (LOD0, LOD1 and shadow copies)
FILL=$(python3 -c "import json; print(','.join(map(str, json.load(open('$P/textures/m372_tp_report.json'))['mouth_fill_srgb'])))")
python3 "$P/scripts/fix_mesh.py" "$P/work/mm7_m372_prefix.glb" "$P/export/mm7_m372.glb" "$FILL"
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$P/export/mm7_m372.glb"
python3 level_generation/creatures/claude_shared/flat_shading_check.py "$P/export/mm7_m372.glb"
python3 level_generation/creatures/claude_shared/texture_quality.py "$P/export/mm7_m372.glb" | grep -v '^    '
python3 "$P/scripts/lod1_check.py" "$P/work/merge_src_mm7_m372.glb" "$P/export/mm7_m372.glb"
if [[ "$INSTALL" == --install ]]; then
    flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py "$P/export/mm7_m372.glb" --world mm7
fi
