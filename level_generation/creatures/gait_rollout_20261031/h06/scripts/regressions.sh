#!/usr/bin/env bash
# Headless actor regressions covering the package h06 models (installed GLBs, current actors.yml), one log per case
# in review/regression_<case>.log.   scripts/regressions.sh
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$root"
for c in mm6_demon_actor_models_keep_simulation_and_death_rules mm6_demon_actor_models_variants_share_asset_and_native_stats \
         mm6_demon_actor_models_sorpigal_crowd mm6_demon_actor_models_indoor_binding mm6_demon_actor_models_hive_placed_actors \
         mm6_gua_actor_models_bind_new_sorpigal_guards mm6_gob_actor_models_bind_sorpigal_goblins \
         mm6_skeleton_actor_fidget_clip_plays_past_the_native_fidget \
         mm6_skeleton_actor_model_tiers_follow_the_native_frame_scales \
         mm6_lizard_archer_actor_model_tiers_follow_sprite_scales mm6_ert_actor_model_tiers_clips_and_sockets \
         mm6_mm7_mm8_actor_models_build_every_binding; do
    OPENYAMM_REGRESSION_FILTER="$c" SDL_AUDIODRIVER=dummy ./build/game/openyamm --headless-run-regression-suite actors \
        > "$here/review/regression_$c.log" 2>&1
    echo "$c: exit $? $(grep -o 'passed=[0-9]* failed=[0-9]*' "$here/review/regression_$c.log" | tail -1)"
done
