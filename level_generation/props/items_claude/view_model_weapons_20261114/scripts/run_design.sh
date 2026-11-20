#!/bin/sh
# Codex design masters, three sessions at a time. Usage: scripts/run_design.sh <kind>...
cd "$(dirname "$0")/.." || exit 1
run() { python3 -I scripts/codex_design.py run "$1"; }
set -- "$@"
while [ $# -gt 0 ]; do
  a=$1; shift; b=${1:-}; [ $# -gt 0 ] && shift; c=${1:-}; [ $# -gt 0 ] && shift
  run "$a" & [ -n "$b" ] && run "$b" & [ -n "$c" ] && run "$c" & wait
done
