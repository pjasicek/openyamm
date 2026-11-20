#!/usr/bin/env bash
# Headless actor regressions covering the package h17 models (installed GLBs, current actors.yml), one log per case
# in review/regression_<case>.log.   scripts/regressions.sh
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$root"
for c in mm8_pirate_actor_models_keep_native_roles mm8_female_crossbow_pirate_actor_models_keep_tiers_equipment_and_release \
         mm8_pirate_mage_actor_models_keep_palettes_staff_cast_and_simulation \
         mm8_mercenary_actor_models_keep_tiers_equipment_and_simulation \
         mm8_bedraggled_human_actor_models_keep_civilian_roles mm6_mm7_mm8_actor_models_build_every_binding; do
    OPENYAMM_REGRESSION_FILTER="$c" SDL_AUDIODRIVER=dummy ./build/game/openyamm --headless-run-regression-suite actors \
        > "$here/review/regression_$c.log" 2>&1
    echo "$c: exit $? $(grep -o 'passed=[0-9]* failed=[0-9]*' "$here/review/regression_$c.log" | tail -1)"
done
