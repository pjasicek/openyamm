#!/bin/bash
cd "$(dirname "$0")/.."
export REA_HEIGHT_M=1.855 REA_KEEP_FACES=work/keep_${K:-a}.npy REA_GROUPS=work/groups_${K:-a}.npy REA_DROP_FACES=work/drop_a.npy REA_RELINE=work/lined_a.npy
export REA_SRC_OPEN=1382
export REA_GROUP_RATIOS=${REA_GROUP_RATIOS:-1:0.7,2:0.7,3:0.75,4:0.7}
scripts/run_ladder.sh ${1:-a} ${2:-0.72,0.68,0.64,0.60}
