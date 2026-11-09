#!/usr/bin/env bash
# Headless actor regressions covering the package h03 models (installed GLBs, current actors.yml), one log per case
# in review/regression_<case>.log.   scripts/regressions.sh
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$root"
for c in mm6_cleric_actor_model_tiers_share_the_native_height mm6_cleric_actor_spell_charge_glows_at_right_palm \
         mm6_cleric_actor_marked_attack_fits_the_action_and_follows_through \
         mm6_cleric_actor_ranged_attack_launches_from_staff_head mm6_cleric_actor_air_attack_lights_the_staff_head \
         mm6_cleric_actor_head_turns_toward_the_party mm6_lich_actor_model_tiers_share_the_native_height \
         mm6_sorcerer_actor_model_tiers_share_the_native_height mm6_archer_actor_model_tiers_share_the_native_height \
         mm6_druidess_actor_model_tiers_share_one_size mm6_mm7_mm8_actor_models_build_every_binding; do
    OPENYAMM_REGRESSION_FILTER="$c" SDL_AUDIODRIVER=dummy ./build/game/openyamm --headless-run-regression-suite actors \
        > "$here/review/regression_$c.log" 2>&1
    echo "$c: exit $? $(grep -o 'passed=[0-9]* failed=[0-9]*' "$here/review/regression_$c.log" | tail -1)"
done
