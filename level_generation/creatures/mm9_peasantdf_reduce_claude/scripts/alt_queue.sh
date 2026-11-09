#!/bin/bash
# after the see-through queue (PID in work/see_queue.pid): build the forearms-whole fallback (mp_xf_r55) for DF1 into work/alt_xf/
# and run its see-through gate (review/gates_xf/see_through_d1)
cd "$(dirname "$0")/.."
while kill -0 $(cat work/see_queue.pid) 2>/dev/null; do sleep 20; done
OUTDIR=work/alt_xf scripts/build_df.sh mp_xf_r55 1
SRCDIR=work/alt_xf scripts/see_through_df.sh xf 1
echo ALTDONE
