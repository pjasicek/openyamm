#!/bin/bash
# head_prep -> reduce -> head_build -> fit -> join. Project folder.
. scripts/env.sh
$G scripts/head_prep.py | tail -1 | cut -c1-100
scripts/run.sh reduce_mesh.py $P/work/head_half.npz $P/work/head_half_r.npz ${HT:-1900} 2>&1 | grep -E "REDUCED|rror"
$G scripts/head_build.py | tail -3 | cut -c1-160
$G scripts/fit_liz.py | tail -1 | cut -c1-120
$G scripts/join_liz.py | cut -c1-160
