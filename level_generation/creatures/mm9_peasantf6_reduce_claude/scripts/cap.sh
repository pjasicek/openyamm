#!/usr/bin/env bash
# Run a command in a memory-capped user scope (MemoryMax CAP, default 12G, no swap) so a runaway allocation is killed
# alone instead of exhausting the shared machine (2026-10-20: an unguarded full SVD of 79k points took 88 GB).
exec systemd-run --user --scope -q -p MemoryMax="${CAP:-12G}" -p MemorySwapMax=0 "$@"
