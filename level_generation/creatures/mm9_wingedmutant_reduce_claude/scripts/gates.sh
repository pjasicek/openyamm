#!/usr/bin/env bash
# Gates the Winged Mutant ran (README: gates.py stretch/floor/loop seams, winding, flat shading, detached parts) plus bone
# lengths, texture quality, symmetry and every LOD's height/stretch, on one GLB -> review/gates_<label>/.
# Usage (project folder): scripts/gates.sh <glb> <label> [noblender]
set -euo pipefail
cd "$(dirname "$0")/.."; glb=$1; out=review/gates_$2; mkdir -p $out
repo=/home/pjasicek/github/OpenYAMM; S=$repo/level_generation/creatures/claude_shared
C="scripts/cap.sh python3"
$C scripts/gates.py $glb $out/gates.json > $out/gates.log 2>&1
$C $S/detached_parts_audit.py $glb --json $out/detached.json > $out/detached.log 2>&1 || true
$C $S/flat_shading_check.py $glb > $out/flat.log 2>&1 || true
$C $S/bone_length_audit.py $glb > $out/bones.log 2>&1 || true
$C $S/texture_quality.py $glb --json $out/texq.json > $out/texq.log 2>&1 || true
$C $repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.log 2>&1 || true
if [[ "${3:-}" != noblender ]]; then
  BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4"
  $BL -P scripts/measure_symmetry.py -- $PWD/$glb 2>&1 | grep SYM > $out/symmetry.log || true
  REA_NODE=Wmut $BL -P scripts/lod_check.py -- $PWD/$glb $2 > $out/lod_check.log 2>&1 || true
fi
tail -n 3 $out/*.log | cut -c1-220
