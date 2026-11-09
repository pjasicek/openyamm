#!/usr/bin/env bash
# Headless actor regressions covering the package h22 models (MM8 Plane Guardian, Crystal Walker) on the installed GLBs
# and the current actors.yml, one log per case in review/regression_<case>.log.
#   scripts/regressions.sh
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$root"
for c in mm8_plane_guardian_actor_models_keep_tiers_scale_and_claw_roles \
         mm8_crystal_walker_actor_models_keep_native_tiers_and_skinning \
         mm6_mm7_mm8_actor_models_build_every_binding; do
    OPENYAMM_REGRESSION_FILTER="$c" SDL_AUDIODRIVER=dummy ./build/game/openyamm --world mm8 \
        --headless-run-regression-suite actors > "$here/review/regression_$c.log" 2>&1
    echo "$c: exit $? $(grep -o 'passed=[0-9]* failed=[0-9]*' "$here/review/regression_$c.log" | tail -1)"
done
