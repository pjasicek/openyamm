#!/usr/bin/env bash
# Rebuilds the m362 texture pass (no paid step) on the pre-pass GLB (work/before_texpass/mm7_m362.glb, the install of
# 2026-10-31) and checks it against both that GLB and the currently installed one (the installed file is this pass
# itself after the first install; a diff against it catches any later layer by another project, which would then need
# merging); with --install also installs it through the shared texture-pass install lock. apply_layout.py keeps every
# clip, node and material of its input and refuses an input whose LOD0 differs from the mesh the paid layout belongs
# to.
# Usage (repository root): build_install.sh [--install]
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm7_m362_texpass_claude
INSTALL=${1:-}
python3 $P/scripts/compose.py $P/textures/m362_tp
python3 $P/scripts/face_features.py $P/textures/m362_tp
python3 $P/scripts/apply_layout.py $P/work/before_texpass/mm7_m362.glb $P/work/uv_final.npz $P/textures/m362_tp \
    $P/export/mm7_m362_tp.glb
python3 $P/scripts/glb_diff.py $P/work/before_texpass/mm7_m362.glb $P/export/mm7_m362_tp.glb
python3 $P/scripts/glb_diff.py assets_source/worlds/mm7/models/mm7_m362.glb $P/export/mm7_m362_tp.glb
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $P/export/mm7_m362_tp.glb
python3 level_generation/creatures/claude_shared/flat_shading_check.py $P/export/mm7_m362_tp.glb
python3 level_generation/creatures/claude_shared/texture_quality.py $P/export/mm7_m362_tp.glb | grep -v '^    '
python3 $P/scripts/lod1_check.py $P/export/mm7_m362_tp.glb
if [[ "$INSTALL" == --install ]]; then
    flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py $P/export/mm7_m362_tp.glb \
        --world mm7 --name mm7_m362.glb
fi
