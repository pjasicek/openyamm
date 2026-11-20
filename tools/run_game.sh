#!/usr/bin/env bash
# Launch the normal development build on the current desktop display.
# --isolated selects reproducible private runs; other arguments go directly to the game.
# The window starts minimized unless --visible is given (see tools/RUN_GAME.md).
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
cd -- "$repo_root"
if [[ "${1-}" == "--isolated" ]]; then
    shift
    exec python3 "$script_dir/run_game.py" "$@"
fi
# Agent runs start minimized so they do not cover the desktop; a leading --visible shows the window
# (FPS measurements, or watching the run).
if [[ "${1-}" == "--visible" ]]; then
    shift
    unset OPENYAMM_START_MINIMIZED
else
    export OPENYAMM_START_MINIMIZED="${OPENYAMM_START_MINIMIZED:-1}"
fi
exec ./build/game/openyamm "$@"
