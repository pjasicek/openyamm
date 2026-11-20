#!/usr/bin/env bash
set -euo pipefail
ship_project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ship_repo="$(cd -- "$ship_project/../../.." && pwd)"
cd -- "$ship_repo"
exec ./tools/run_game.sh --isolated mm6_sorpigal_ship --world mm6 --map oute3.odm \
    --assets "$ship_project/playtest/assets_dev" \
    --position -1100 -10208 160 --yaw-radians 0 --pitch-degrees 8 \
    --warmup 2 --seconds 0 "$@"
