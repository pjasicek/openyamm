#!/usr/bin/env bash
# Private HUD review fixture; ordinary settings, saves and launchers remain untouched.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd -- "$repo_root"
preview_mode="${1:-restored}"
if [[ $# -gt 0 ]]; then shift; fi
prepare_args=()
case "$preview_mode" in
    restored) ;;
    original) prepare_args+=(--original) ;;
    *) echo 'Usage: play.sh [restored|original] [isolated run options]' >&2; exit 2 ;;
esac
preview_metadata="$(mktemp /tmp/openyamm-hud-launch-XXXXXX.json)"
python3 level_generation/ui/hud_inventory/prepare_preview.py "${prepare_args[@]}" > "$preview_metadata"
preview_dir="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["stage"])' "$preview_metadata")"
echo "HUD preview: $preview_dir"
exec ./tools/run_game.sh --isolated hud_restoration --world mm6 \
    --settings "$preview_dir/settings.ini" --assets "$preview_dir/assets" \
    --save "$preview_dir/tmp/openyamm_scenario_saves/hud_artwork_preview/preview.oysav" \
    --warmup 2 --seconds 0 "$@"
