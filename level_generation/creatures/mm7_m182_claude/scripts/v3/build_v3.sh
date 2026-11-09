#!/bin/bash
# v3 full rebuild after the Meshy returns: geometry chain (scripts/v3/build_geometry.sh [step], default graft) ->
# compose (maps, masks, ramps) -> tier previews -> runtime GLB (scripts/v3/build_runtime_v3.sh) -> review viewer.
set -eo pipefail
cd "$(dirname "$0")/../.."
scripts/v3/build_geometry.sh "${1:-graft}"
python3 scripts/v3/compose_v3.py | cut -c1-300
python3 scripts/v3/tier_bake.py
scripts/v3/build_runtime_v3.sh
python3 scripts/viewer.py
