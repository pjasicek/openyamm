#!/bin/bash
# The power curve from the routes: cases for every stage (solo builds and the party reference), the harness on every
# spec shard, the real-group fights and the curve table. Needs route/out_<dk>.jsonl and route/out_<dk>_party.jsonl
# (README "Running it"). About 40 minutes on 24 cores. The shard files (pool_<dk>[_party]_s<seed>.yml and their
# outputs) are overwritten by name; a work directory used with fewer seeds before should be emptied by hand first.
set -e
D="$(cd "$(dirname "$0")" && pwd)"
S="${SOLO_SIM_DIR:-$(cd "$D/../../../.." && pwd)/output/maw_solo_sim}"
export SOLO_SIM_DIR="$S"
cd "$S"
python3 "$D"/gen_pool.py
ls pool_*_s[0-9].yml | sed 's/^pool_//; s/\.yml$//' | xargs -P "${JOBS:-24}" -I{} sh -c \
  'SOLO_SPEC=$PWD/pool_{}.yml SOLO_OUT=$PWD/pool_out_{}.jsonl ./solo_harness --test-case="solo harness" > pool_run_{}.log 2>&1'
grep -h Status pool_run_*_s[0-9].log | sort | uniq -c
for dk in normal maw hard hell nightmare doom insanity madness; do
  cat pool_out_${dk}_s[0-9].jsonl > pool_out_$dk.jsonl
  cat pool_out_${dk}_party_s[0-9].jsonl > pool_out_${dk}_party.jsonl
  python3 "$D"/realfight.py "$S" pool_out_$dk.jsonl
  python3 "$D"/realfight.py "$S" pool_out_${dk}_party.jsonl
done
python3 "$D"/agg_curve.py
