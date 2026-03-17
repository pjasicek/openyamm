#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "--build" ]]; then
    cmake --build "$repo_root/build" -j4 --target openyamm
fi

"$repo_root/build/game/openyamm" --headless-run-regression-suite dialogue
