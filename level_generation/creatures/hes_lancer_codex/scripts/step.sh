#!/usr/bin/env bash
set -euo pipefail
project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$project/../../.." && pwd)"
: "${CREATURE_3D_TOKEN:?set CREATURE_3D_TOKEN to the project lease}"
cd "$repo"
tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" \
    "level_generation/creatures/hes_lancer_codex/scripts/$1" "${@:2}"
