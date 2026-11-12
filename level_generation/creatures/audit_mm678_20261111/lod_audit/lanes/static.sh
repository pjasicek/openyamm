#!/usr/bin/env bash
# Static checks of after and before GLBs, two processes.
d=$(cd "$(dirname "$0")/.." && pwd); root=$(cd "$d/../../../.." && pwd); cd "$root"
cut -f4 "$d/models.tsv" | xargs -P 2 -n 6 python3 "$d/lod_static.py" > "$d/static_after.jsonl" 2> "$d/static_after.err"
cut -f5 "$d/models.tsv" | xargs -P 2 -n 6 python3 "$d/lod_static.py" > "$d/static_before.jsonl" 2> "$d/static_before.err"
echo STATIC_DONE > "$d/lanes/STATIC_DONE"
