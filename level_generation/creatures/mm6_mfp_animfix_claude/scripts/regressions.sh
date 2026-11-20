#!/usr/bin/env bash
# Headless actor regressions covering the package h05 models (installed GLBs, current actors.yml), one log per case
# in review/regression_<case>.log.   scripts/regressions.sh
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$root"
for c in mm6_peasant_m4_actor_model_tiers_share_the_native_height mm6_merchant_actor_model_tiers_share_the_native_height \
         mm6_peasant_f3_actor_model_tiers_share_the_native_height mm6_peasant_f4_actor_model_tiers_share_the_native_height \
         mm6_swordsman_actor_model_tiers_share_one_size; do
    OPENYAMM_REGRESSION_FILTER="$c" SDL_AUDIODRIVER=dummy ./build/game/openyamm --headless-run-regression-suite actors \
        > "$here/review/regression_$c.log" 2>&1
    echo "$c: exit $? $(grep -o 'passed=[0-9]* failed=[0-9]*' "$here/review/regression_$c.log" | tail -1)"
done
