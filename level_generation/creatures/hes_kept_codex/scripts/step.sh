#!/usr/bin/env bash
# Owned, bounded Blender process with the host's immediate-exit runner.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(cd -- "$here/../../.." && pwd)
: "${CREATURE_3D_TOKEN:?claim this creature workspace first}"
step=$1; shift
cd "$repo"
exec python3 tools/creature_workspace.py run --project "$here" --token "$CREATURE_3D_TOKEN" -- \
 timeout -k 5 300 /snap/blender/current/blender --background --factory-startup -noaudio --disable-autoexec \
 --threads 4 --python-exit-code 1 --python "$here/scripts/run_step.py" -- "$here/scripts/$step.py" "$@"
