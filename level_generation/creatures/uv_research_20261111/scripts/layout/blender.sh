#!/usr/bin/env bash
# Same Blender invocation as tools/run_creature_blender.sh, without its project lock: the PartUV agent holds the
# uv_research_20261111 lease (whole folder) and this agent writes only under layout/. Log next to the outputs.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
script="$1"; shift
log="$1"; shift
cd "$repo_root"
exec /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$script" -- "$@" > "$log" 2>&1
