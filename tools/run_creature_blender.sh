#!/usr/bin/env bash
# Reusable approval entry point for creature and assigned item authoring/export/review scripts.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
creature_token="${CREATURE_3D_TOKEN:-}"
if [[ ${1:-} == --token ]]; then
    creature_token="${2:?Expected a creature lease token}"
    shift 2
fi
if [[ $# -lt 1 ]]; then
    echo "Usage: tools/run_creature_blender.sh [--token TOKEN] <project/script.py> [script arguments...]" >&2
    exit 2
fi
script_path="$(realpath -- "$repo_root/$1")"
shift
case "$script_path" in
    "$repo_root"/level_generation/creatures/*.py)
        relative_path="${script_path#"$repo_root"/level_generation/creatures/}"
        [[ "$relative_path" == */* ]] || { echo "Choose a script inside one creature project." >&2; exit 2; }
        project_path="$repo_root/level_generation/creatures/${relative_path%%/*}"
        ;;
    "$repo_root"/level_generation/props/items_wip_*/*.py)
        relative_path="${script_path#"$repo_root"/level_generation/props/}"
        project_path="$repo_root/level_generation/props/${relative_path%%/*}"
        # Item workers keep their paid-job leases and receipts in their own meshy directory.
        if [[ -f "$project_path/meshy/creature_3d_progress.json" ]]; then
            project_path="$project_path/meshy"
        fi
        ;;
    *) echo "Expected a Python script inside a creature or props/items_wip_* project." >&2; exit 2 ;;
esac
[[ -f "$script_path" ]] || { echo "Script does not exist: $script_path" >&2; exit 2; }
log_path="$(mktemp /tmp/openyamm-creature-blender-XXXXXXXX.log)"
echo "Blender log: $log_path"
cd -- "$repo_root"
script_arguments=()
if [[ $# -gt 0 ]]; then
    script_arguments=(-- "$@")
fi
exec python3 "$repo_root/tools/creature_workspace.py" run --project "$project_path" --token "$creature_token" -- \
    /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$script_path" "${script_arguments[@]}" > "$log_path" 2>&1
