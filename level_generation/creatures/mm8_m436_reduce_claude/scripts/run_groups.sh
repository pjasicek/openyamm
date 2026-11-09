#!/usr/bin/env bash
# Per-region ladder: group ratios fixed (REA_GROUP_RATIOS), the body-skin rest (group 0) at each of the given ratios,
# converted to the ladder's whole-mesh ratio. Usage: REA_GROUP_RATIOS=1:0.7,... run_groups.sh <label> <rest ratios>
set -euo pipefail
label=$1; cd "$(dirname "$0")/.."
R=$(python3 - "$2" <<'PY'
import os, sys, numpy as np
g = np.load('work/groups.npy'); k = np.load('work/keep.npy'); n = len(g)
gr = {int(a): float(b) for a, b in (kv.split(':') for kv in os.environ['REA_GROUP_RATIOS'].split(','))}
fixed = k.sum() + sum(int(((g == j) & ~k).sum() * r) for j, r in gr.items())
rest = ((g == 0) & ~k).sum()
print(','.join(f'{(fixed + rest * float(x)) / n:.4f}' for x in sys.argv[1].split(',')))
PY
)
echo "ladder ratios $R"
REA_GROUPS=work/groups.npy REA_KEEP_FACES=work/keep.npy scripts/run_ladder.sh "$label" "$R"
