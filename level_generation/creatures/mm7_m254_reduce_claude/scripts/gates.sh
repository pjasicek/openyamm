#!/usr/bin/env bash
# Humanoid gates of the source project (../mm7_m254_claude/scripts, copied as gate_*.py) on a gate scene built from a
# runtime GLB by gate_blend.py, so the source GLB and the reduced GLB go through the same path. G4 arm stretch at the
# source's extreme frames plus every 4th frame of every clip, G5 hand stretch, G6 contacts, arms into the torso, soles,
# flat feet. Usage: TOKEN=<lease> gates.sh <glb> <label>  -> review/gates_<label>.txt
set -uo pipefail
cd "$(dirname "$0")/.."; P=$PWD; ROOT=$(cd ../../.. && pwd); glb=$1; label=$2; OUT=review/gates_$label.txt
CLIPS="Standing Walking Running Attack Hit Death Fidget"
run() { local out log; out=$(env "${ENVS[@]}" "$ROOT/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m254_reduce_claude/scripts/$1" "${@:2}" 2>&1)
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO|Saved|Warning)' | cut -c1-260
        grep -A6 Traceback "$log" | head -8; }
ENVS=(X=1); run gate_blend.py "$P/$glb" "$P/work/gate_$label.blend" >/dev/null
B=$P/work/gate_$label.blend
G4F="Attack:17 Attack:25 Attack:29 Fidget:60 Fidget:80 Death:60 Hit:8 Walking:8 Standing:0"
for c in $CLIPS; do for f in $(seq 0 4 112); do G4F="$G4F $c:$f"; done; done
{
echo "# m254 gates on $glb ($(date -u +%F))"
run gate_g4_weights.py "$B" "$label" $G4F
run gate_g5_hand_stretch.py "$B" $CLIPS
run gate_g6_contacts.py "$B" $CLIPS
run gate_arm_torso_probe.py "$B" $CLIPS
ENVS=(STEP=0.5); run gate_sole_probe.py "$B" Standing Walking Running Attack Hit Fidget
ENVS=(X=1); run gate_foot_flat.py "$B" Standing Walking Attack Hit Fidget
} > "$OUT" 2>&1
cat "$OUT" | cut -c1-200
