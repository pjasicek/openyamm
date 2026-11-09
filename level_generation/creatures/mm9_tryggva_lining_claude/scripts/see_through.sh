#!/bin/bash
# The see-through gate (scripts/see_through_gate.py, PeasantDM2's plus the per-face dump) on one GLB, sweep settings
# (step 4, 4 mm pixels, 16 views, every clip) unless overridden.
# Usage (any folder): scripts/see_through.sh <glb> <out json> [key=value ...]
set -u
P=/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_tryggva_lining_claude
glb=$(realpath $1); out=$(realpath -m $2); shift 2; mkdir -p $(dirname $out)
$P/scripts/bl.sh "SEE_THROUGH_SUMMARY|Error|Trace" level_generation/creatures/mm9_tryggva_lining_claude/scripts/see_through_gate.py \
  $glb $out step=4 px_mm=4 shots=2 extra= faces=1 "$@"
