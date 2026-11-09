#!/usr/bin/env bash
set -euo pipefail
trial_root="${OPENYAMM_SORPIGAL_DIRT_TRIAL:-/tmp/openyamm-sorpigal-dirt-fidelity}"
trial_mode="${1:-candidate}"
case "$trial_mode" in
    original|current|candidate|transitions) ;;
    *) echo 'Usage: play.sh [transitions|candidate|current|original]' >&2; exit 2 ;;
esac
if [[ $# -gt 1 ]]; then
    echo 'Usage: play.sh [transitions|candidate|current|original]' >&2
    exit 2
fi
if [[ ! -f "$trial_root/dirt_trial.json" ]]; then
    echo 'Prepare first: python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/prepare_trial.py' >&2
    exit 1
fi
if [[ ! -d "$trial_root/$trial_mode" ]]; then
    echo 'Prepare transitions: python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/prepare_playtest.py' >&2
    exit 1
fi
echo "Separate dirt trial: $trial_mode. Choose Load Game and 'Terrain camera reference'."
cd -- "$trial_root/$trial_mode"
if [[ "$trial_mode" == transitions ]]; then
    exec ./openyamm --world mm6
fi
exec ../openyamm --world mm6
