#!/usr/bin/env bash
# Starts the co-op session "maw_2_parties_full" on this PC, every game joined and ready (tools/coop_local/README.md).
exec python3 "$(dirname -- "${BASH_SOURCE[0]}")/run.py" maw_2_parties_full "$@"
