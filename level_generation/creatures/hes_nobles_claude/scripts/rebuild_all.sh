#!/usr/bin/env bash
# The whole Nobles chain from the rig: sockets -> carapace -> the five clip sets -> assembly -> export -> runtime -> events,
# strides -> bindings. Usage: LOD_REPAIR_PYTHON=<venv python> scripts/rebuild_all.sh [clips]  (without `clips` the clip
# blends are reused)
set -euo pipefail
cd "$(dirname "$0")/.."
B="timeout 1800 /snap/blender/current/blender --background --factory-startup -noaudio --python"
$B scripts/add_sockets.py 2>&1 | grep -E "^SOCKETS|Error" || true
scripts/carapace.sh
if [ "${1:-}" = clips ]; then
  for s in noble ssekh mraal xith gate; do $B scripts/build_clips.py -- $s > work/clips_$s.log 2>&1 & done; wait
  grep -h CLIPS_DONE work/clips_*.log
  [ "$(grep -h -c CLIPS_DONE work/clips_*.log | paste -sd+ | bc)" -eq 5 ] || { echo "a clip set failed"; exit 1; }
fi
$B scripts/assemble.py -- noble,ssekh,mraal,xith,gate all noble_fang noble_sidearm ssekh_fang_r ssekh_fang_l phase_cleaver \
  storm_rifle lancer_carbine bastion_emitter gorget_seal 2>&1 | grep -E "^ASSEMBLED|Error" | cut -c1-60 || true
$B scripts/probe_events.py 2>&1 | grep -E "^EVENTS|Error" || true
$B scripts/stride.py -- Mraal_Walking Mraal_Running 2>&1 | grep -E "^STRIDE|Error" || true
$B scripts/export_noble.py -- all hes_noble 2>&1 | grep -E "^EXPORTED|Error" | cut -c1-200 || true
scripts/build_runtime.sh hes_noble
python3 scripts/publish.py
