#!/usr/bin/env bash
# Blender (background, factory startup) under this project's creature lease, run from the project directory.
# Usage: TOKEN=<lease> scripts/bl.sh <script.py> [-- args...]   (environment variables pass through)
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
script=$1; shift
exec python3 "$ROOT/tools/creature_workspace.py" run --project "$P" --token "$TOKEN" -- \
    bash -c 'cd "$0" && exec /snap/bin/blender -b --factory-startup --python-exit-code 1 -P "$@"' "$P" "$script" "$@"
