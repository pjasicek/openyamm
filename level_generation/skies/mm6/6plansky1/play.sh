#!/usr/bin/env bash
set -euo pipefail
pilot_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
pilot_tier="${1:-x2}"
case "$pilot_tier" in x1|x2) ;; *) echo 'Usage: play.sh [x1|x2]' >&2; exit 2 ;; esac
python3 "$pilot_dir/prepare_review.py" --play
pilot_stage="/tmp/openyamm-mm6-6plansky1-pilot/$pilot_tier"
cd "$pilot_stage"
exec ../openyamm --world mm6
