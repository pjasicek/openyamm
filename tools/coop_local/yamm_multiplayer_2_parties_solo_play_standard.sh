#!/usr/bin/env bash
# Starts the co-op session "2_parties_solo_play_standard" on this PC, every game joined and ready (tools/coop_local/README.md).
exec python3 "$(dirname -- "${BASH_SOURCE[0]}")/run.py" 2_parties_solo_play_standard "$@"
