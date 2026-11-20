#!/usr/bin/env bash
# Puts the texture pass on the CURRENTLY installed Troll GLBs (MM8 mm8_m480, MM7 mm7_m461) and checks them; with
# --install also installs both. Run after any later layer on the installed files (the gait rollout's Sprint clips):
# apply_layout.py keeps every clip, node and material of its input and refuses an input whose LOD0 differs from the
# mesh the paid layout belongs to. Usage (repository root): merge_install.sh [--install]
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm8_m480_texpass_claude
INSTALL=${1:-}
for pair in "mm8 mm8_m480" "mm7 mm7_m461"; do
    read -r world stem <<< "$pair"
    cp "assets_source/worlds/$world/models/$stem.glb" "$P/work/merge_src_$stem.glb"
    python3 "$P/scripts/apply_layout.py" "$P/work/merge_src_$stem.glb" "$P/work/uv_fine.npz" "$P/textures/m480_tp" \
        "$P/export/$stem.glb"
    python3 "$P/scripts/glb_diff.py" "$P/work/merge_src_$stem.glb" "$P/export/$stem.glb"
    python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$P/export/$stem.glb"
    python3 level_generation/creatures/claude_shared/flat_shading_check.py "$P/export/$stem.glb"
    python3 level_generation/creatures/claude_shared/texture_quality.py "$P/export/$stem.glb" | grep -v '^    '
    python3 "$P/scripts/lod1_check.py" "$P/export/$stem.glb"
    if [[ "$INSTALL" == --install ]]; then
        python3 tools/install_model.py "$P/export/$stem.glb" --world "$world"
    fi
done
