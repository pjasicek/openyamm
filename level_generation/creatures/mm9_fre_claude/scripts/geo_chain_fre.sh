#!/bin/bash
# Fre: positions-only chain on a uv npz (F4's order: tweak_pf1 -> chin_pf4 -> under_hood_pf4 (the cap) -> puff_pf4 -> bust_pf4 -> eyelid_pf4).
# Run BEFORE the head upload so the paint is made on the final face geometry, and in every rebuild (deterministic). Project folder.
# Usage: scripts/geo_chain_fre.sh <in uv npz> <out uv npz>
set -e
IN=$1; OUT=$2
python3 scripts/tweak_pf1.py work/asm_frozen.npz $IN work/geo_tw.npz 0.012 8 > /dev/null
python3 scripts/chin_pf4.py work/geo_tw.npz work/geo_chin.npz 16 0.005 | tail -1
# pass 4: PeasantF2's hair ('hair2') replaces the cap and braid: under_hair2_fre.py instead of under_hood_pf4.py, no braid turn, no cap hem
HAIR2=$(python3 -c "import numpy as np; print(int('hair2' in [str(x) for x in np.load('work/asm_frozen.npz')['names']]))")
if [ "$HAIR2" = 1 ]; then python3 scripts/under_hair2_fre.py work/geo_chin.npz work/geo_uh0.npz | tail -1
  # pass 5: the bare temples / ear plates / old-hood teeth relaxed (folded faces drew lit panels), then the hair clearance again
  python3 scripts/smooth_side_fre.py work/geo_uh0.npz work/geo_uh1.npz | tail -1
  python3 scripts/under_hair2_fre.py work/geo_uh1.npz work/geo_uh.npz | tail -1
else python3 scripts/under_hood_pf4.py work/geo_chin.npz work/geo_uh.npz work/asm_frozen.npz | tail -1; fi
python3 scripts/puff_pf4.py work/geo_uh.npz work/geo_puff.npz work/rig.json ${PUFFKEEP:-0.0} | tail -1
python3 scripts/bust_pf4.py work/geo_puff.npz work/geo_bust.npz | tail -1
python3 scripts/eyelid_pf4.py work/geo_bust.npz work/geo_lid.npz | tail -1
# PeasantF4 job 8 (2026-11-04, snapshot of ../mm9_peasantf4_claude/scripts/bodice_fix_pf4.py): F1's bodice eyelet holes filled, lacing chevrons and
# peplum spikes dropped
python3 scripts/bodice_fix_pf4.py work/geo_lid.npz $OUT | tail -1
if [ "$HAIR2" != 1 ]; then
python3 scripts/braid_pose_fre.py $OUT $OUT ${BRAID_DEG:-0} | tail -1
python3 scripts/cap_hem_fre.py $OUT $OUT ${CAPHEM:-0.022 0.006} | tail -1
fi
