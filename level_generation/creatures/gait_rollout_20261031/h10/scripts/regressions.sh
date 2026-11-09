#!/usr/bin/env bash
# Headless actor regressions covering the package h10 models (installed GLBs, current actors.yml), one log per case
# in review/regression_<case>.log. No case names these MM7 models; the shared binding build covers them.
#   scripts/regressions.sh
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$root"
for c in mm6_mm7_mm8_actor_models_build_every_binding; do
    OPENYAMM_REGRESSION_FILTER="$c" SDL_AUDIODRIVER=dummy ./build/game/openyamm --world mm7 \
        --headless-run-regression-suite actors > "$here/review/regression_$c.log" 2>&1
    echo "$c: exit $? $(grep -o 'passed=[0-9]* failed=[0-9]*' "$here/review/regression_$c.log" | tail -1)"
done
