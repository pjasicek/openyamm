#!/usr/bin/env bash
set -euo pipefail
demo_root="${OPENYAMM_PMN2_DEMO:-/tmp/openyamm-pmn2-playtest}"
case "${1:-mages}" in
    mages|town) demo_start="${1:-mages}" ;;
    *) echo 'Usage: play.sh [mages|town]' >&2; exit 2 ;;
esac
if [[ ! -f "$demo_root/playtest_snapshot.json" ]]; then
    echo 'Prepare the demo first: python3 level_generation/creatures/mm6_pmn2/prepare_playtest.py' >&2
    exit 1
fi
cd -- "$demo_root/$demo_start"
exec ../openyamm --world mm8
