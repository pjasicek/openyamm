#!/bin/bash
# Audit every named MM9 reduction (installed GLB vs the project's before/ rollback source) and render close-ups of
# models whose LOD0 has escaping faces. Usage: reduction_uv_audit_batch.sh <name> [...]  (mm9_<name>_reduce_claude)
# -> mm9_<name>_reduce_claude/review/uv_audit/{audit.txt,audit.json,closeups.png}
cd "$(dirname "$0")/.."
S="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
for n in "$@"; do
  d=mm9_${n}_reduce_claude; mkdir -p $d/review/uv_audit
  $S python3 claude_shared/reduction_uv_audit.py ../../assets_source/worlds/mm9/models/mm9_$n.glb $d/before/mm9_$n.glb \
    --json $d/review/uv_audit/audit.json > $d/review/uv_audit/audit.txt 2>&1 || { echo "AUDIT FAIL $n"; continue; }
  if awk '$2=="LOD0" && $8>0 {f=1} END {exit !f}' $d/review/uv_audit/audit.txt; then
    $S python3 claude_shared/reduction_uv_closeups.py $d/review/uv_audit/audit.json $d/review/uv_audit 2>&1 | tail -1
  else
    echo "clean $n"
  fi
done
