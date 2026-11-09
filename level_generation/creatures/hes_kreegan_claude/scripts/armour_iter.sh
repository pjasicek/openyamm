#!/usr/bin/env bash
# Armour iteration loop (not part of the chain): the pieces rebuilt from armour_spec_v4.py on the final clips
# (work/it.blend = work/rig_v3t.blend with the helper bones re-baked and the bulk), the shell skinned, optionally the Running gun
# push (CLEAR=1, as in the chain), then shell stretch, shell leak and the armour gate on every FSTEP-th frame of the
# living clips (about a minute). Confirm with rebuild.sh tail: the chain's other pose fixes are not rerun here.
# Usage: TOK=<lease> [HELPERS=1] [CLEAR=1] [FSTEP=2] scripts/armour_iter.sh <tag>
set -uo pipefail
cd "$(dirname "$0")/.."
P=$PWD; S=scripts/step.sh; T=${1:-it}; L="Standing Walking Running Attack Hit Fidget"; SPEC=$P/scripts/armour_trooper.json
if [ "${HELPERS:-0}" = 1 ] || [ ! -f work/it.blend ]; then
  $S leg_limit.py "$P/work/rig_v3t.blend" "$P/work/it.blend" Running
  $S helper_bones.py "$P/work/it.blend" "$P/work/it.blend" > /dev/null; $S bulk_body.py "$P/work/it.blend" "$P/work/it.blend"; fi
python3 scripts/armour_spec_v4.py > /dev/null
$S make_armour.py "$P/work/it.blend" "$SPEC" "$P/work/it_a.blend" | grep -v "^PLATE"
$S skin_shell.py "$P/work/it_a.blend" "$SPEC" "$P/work/it_s.blend" | grep SHELLHIDE
if [ "${CLEAR:-0}" = 1 ]; then LEFT=1 MARGIN=0.02 PASSES=5 $S armour_clear.py "$P/work/it_s.blend" "$P/work/it_s.blend" $L; fi
$S shell_stretch.py "$P/work/it_s.blend" "$SPEC" $T $L | tail -1 | cut -c1-400
$S shell_leak.py "$P/work/it_s.blend" "$SPEC" $T $L | grep -v "PASS\|candidates"
FSTEP=${FSTEP:-2} $S armour_gate.py "$P/work/it_s.blend" $T "$SPEC" $L > /dev/null
python3 scripts/gate_worst.py $T ${TOLV:-0.3}
