#!/usr/bin/env bash
# Reusable approval entry point for creature authoring/export/review scripts.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
creature_token="${CREATURE_3D_TOKEN:-}"
if [[ ${1:-} == --token ]]; then
    creature_token="${2:?Expected a creature lease token}"
    shift 2
fi
if [[ $# != 1 ]]; then
    echo "Usage: tools/run_creature_blender.sh [--token TOKEN] level_generation/creatures/<package>/<script>.py" >&2
    exit 2
fi
script_path="$(realpath -- "$repo_root/$1")"
case "$script_path" in
    "$repo_root"/level_generation/creatures/*.py) ;;
    *) echo "Expected a Python script under level_generation/creatures/." >&2; exit 2 ;;
esac
[[ -f "$script_path" ]] || { echo "Script does not exist: $script_path" >&2; exit 2; }
relative_path="${script_path#"$repo_root"/level_generation/creatures/}"
[[ "$relative_path" == */* ]] || { echo "Choose a script inside one creature project." >&2; exit 2; }
project_path="$repo_root/level_generation/creatures/${relative_path%%/*}"
log_path="$(mktemp /tmp/openyamm-creature-blender-XXXXXXXX.log)"
echo "Blender log: $log_path"
cd -- "$repo_root"
exec python3 "$repo_root/tools/creature_workspace.py" run --project "$project_path" --token "$creature_token" -- \
    /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$script_path" > "$log_path" 2>&1
