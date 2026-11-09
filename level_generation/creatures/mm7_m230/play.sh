#!/usr/bin/env bash
set -euo pipefail
creature_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$creature_root/../../.." && pwd)"
demo_root="${OPENYAMM_CRUSADER_DEMO:-/tmp/openyamm-crusader-playtest}"
if [[ ! -f "$demo_root/settings.ini" ]]; then
    echo "Prepare the demo first: python3 $creature_root/prepare_playtest.py" >&2
    exit 1
fi
cd -- "$demo_root"
exec "$repo_root/build/game/openyamm" --world mm8
