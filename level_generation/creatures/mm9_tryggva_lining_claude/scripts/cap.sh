#!/usr/bin/env bash
# A command in a memory-capped user scope (MemoryMax CAP, default 12G, no swap).
exec systemd-run --user --scope -q -p MemoryMax="${CAP:-12G}" -p MemorySwapMax=0 "$@"
