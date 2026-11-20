#!/bin/bash
# The creature's see-through gate (../mm9_peasantdf_claude/scripts/see_through_gate.py, copied as see_through_gate_df.py so it
# runs under this project's lease; defaults step 3, px 3 mm, 16 views) on the candidates. Baseline: the creature's job 7 runs
# on the installed files (review/gates/job7/see_through_d<n>/st.json).
# Usage (project folder): scripts/see_through_df.sh <tag> [designs] -> review/gates_<tag>/see_through_d<n>/st.json
cd "$(dirname "$0")/.."; R=/home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_peasantdf_reduce_claude; tag=$1; shift
for n in ${@:-1 2 3 4}; do
  out=$R/$P/review/gates_$tag/see_through_d$n; mkdir -p $out
  (cd $R && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $(cat $R/$P/LEASE_TOKEN.txt) \
    $P/scripts/see_through_gate_df.py $R/$P/${SRCDIR:-export}/mm9_peasantdf$n.glb $out/st.json > $out/log.txt 2>&1); echo SEEDONE d$n $?
done
