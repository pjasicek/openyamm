#!/usr/bin/env bash
# One Blender at a time for this agent: wait for a PID (the gates run that ends in its own sleeve gate), then run the given
# Blender jobs in order. Usage: blender_queue.sh <pid or 0> "<label>:<glb>:lod|sleeve" ...
cd "$(dirname "$0")/.."
pid=$1; shift
if [[ "$pid" != 0 ]]; then while kill -0 $pid 2>/dev/null; do sleep 10; done; fi
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
F=/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_honkmale_claude
for job in "$@"; do
  IFS=: read -r label glb kind <<< "$job"; glb=$(realpath $glb)
  if [[ $kind == lod ]]; then
    REA_NODE=HonkM $BL -P scripts/lod_check.py -- $glb $label > work/lod_check_$label.log 2>&1
  else
    mkdir -p review/gates_$label
    $BL --python $F/v2/scripts/sleeve_gate.py -- $glb $PWD/review/gates_$label/sleeve_gate.json Bip01 24 front,above34,below,q34 > review/gates_$label/sleeve.txt 2>&1
  fi
  echo "DONE $job" >> work/blender_queue.log
done
