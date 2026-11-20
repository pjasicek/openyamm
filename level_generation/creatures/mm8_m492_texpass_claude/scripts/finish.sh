#!/usr/bin/env bash
# Checks (and with --install installs) the texture-pass export of every texpass.json target: glb_diff against the
# claimed GLB, winding, flat shading, texture_quality, LOD colour check; with --install also install_model.py, the
# actor-binding regression and the floor audit (texpass.json floor_match descriptor glob).
# Usage (any directory): scripts/finish.sh [--install]
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"
cd "$P/../../.."
INSTALL=${1:-}
mapfile -t TARGETS < <(python3 -c "import json;[print(w,s) for w,s in json.load(open('$P/texpass.json'))['targets']]")
for pair in "${TARGETS[@]}"; do
    read -r world stem <<< "$pair"
    python3 "$P/scripts/glb_diff.py" "$P/work/before_texpass/$stem.glb" "$P/export/$stem.glb"
    python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$P/export/$stem.glb" | tail -1
    python3 level_generation/creatures/claude_shared/flat_shading_check.py "$P/export/$stem.glb" | tail -1
    python3 level_generation/creatures/claude_shared/texture_quality.py "$P/export/$stem.glb" --by-bone \
        --json "$P/work/quality_after_$stem.json" | grep -v '^    '
    (cd "$P/scripts" && python3 lod_check.py "$P/work/before_texpass/$stem.glb" "$P/export/$stem.glb")
    if [[ "$INSTALL" == --install ]]; then
        cmp -s "assets_source/worlds/$world/models/$stem.glb" "$P/work/before_texpass/$stem.glb" \
            || { echo "installed $stem changed since the claim: re-run apply on it first" >&2; exit 1; }
        python3 tools/install_model.py "$P/export/$stem.glb" --world "$world" | tail -1
    fi
done
if [[ "$INSTALL" == --install ]]; then
    OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding timeout 900 ./build/game/openyamm \
        --world mm6 --headless-run-regression-suite actors 2>&1 | tail -3
    for pair in "${TARGETS[@]}"; do
        read -r world stem <<< "$pair"
        match=$(python3 -c "import json;print(json.load(open('$P/texpass.json')).get('floor_match', {}).get('$stem', '*'))")
        timeout 900 python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world "$world" \
            --match "$match" | tail -4
    done
fi
