#!/usr/bin/env bash
set -euo pipefail
lab_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-ai2x}" in
    native|smooth2x|ai2x) lab_variant="${1:-ai2x}" ;;
    *) echo 'Usage: play.sh [native|smooth2x|ai2x]' >&2; exit 2 ;;
esac
if [[ ! -f "$lab_root/variants/$lab_variant/settings.ini" ]]; then
    echo 'Run python3 prepare.py first.' >&2
    exit 1
fi
cd -- "$lab_root/variants/$lab_variant"
exec "$lab_root/playtest/openyamm" --world mm8
