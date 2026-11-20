#!/usr/bin/env bash
# One per-region ladder on work/groups_a.npy (make_groups.py) and a keep set (KEEP, default work/keep_b.npy): head,
# left hand, right hand and armour pieces at their own ratios, the rest of the body at each listed ratio (converted
# to whole-mesh ladder ratios). Usage: [KEEP=...] run_groups.sh <label> <head> <right hand> <left hand> <armour> <rest> [rest ...]
set -euo pipefail
cd "$(dirname "$0")/.."
label=$1 head=$2 rhand=$3 lhand=$4 armour=$5; shift 5
keep=${KEEP:-work/keep_b.npy}
ratios=$(python3 -c "
import sys, numpy as np
g, k = np.load('work/groups_a.npy'), np.load(sys.argv[1]); r = dict(zip((1, 3, 2, 4), map(float, sys.argv[2:6])))
b = int(k.sum()) + sum(int(((g == i) & ~k).sum() * x) for i, x in r.items()); rest = ((g == 0) & ~k).sum()
print(','.join(f'{(b + rest * float(x)) / len(g):.4f}' for x in sys.argv[6:]))" "$keep" "$head" "$rhand" "$lhand" "$armour" "$@")
REA_GROUPS=work/groups_a.npy REA_KEEP_FACES=$keep REA_GROUP_RATIOS=1:$head,2:$lhand,3:$rhand,4:$armour \
    bash scripts/run_ladder.sh "$label" "$ratios" | grep -v DECIMATED
