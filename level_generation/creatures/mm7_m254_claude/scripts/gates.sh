#!/usr/bin/env bash
# m254 gate batch on the final gated chain (work/rig_v5.blend): G4 arm weights at extremes, G5 hand stretch, G6 hand and
# forearm contacts (closed skin inside test), arms into the torso, soles, flat feet, jerk, strides and standing height.
# Writes review/gates_final.txt. Token: CREATURE_3D_TOKEN.
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
P=level_generation/creatures/mm7_m254_claude; B=${BLEND:-$repo/$P/work/rig_v5.blend}; OUT=$repo/$P/review/gates_final.txt
CLIPS="Standing Walking Running Attack Hit Death Fidget"
run() { local out log; out=$(env "${ENVS[@]}" tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1)
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO|Saved|Warning)' | cut -c1-260
        grep -A6 Traceback "$log" | head -8; }
ENVS=(X=1)
{
echo "# m254 gates on $(basename "$B") ($(date -u +%F))"
run g4_weights.py "$B" final Attack:17 Attack:25 Attack:29 Fidget:60 Fidget:80 Death:60 Hit:8 Walking:8 Standing:0
run g5_hand_stretch.py "$B" $CLIPS
run g6_contacts.py "$B" $CLIPS
run arm_torso_probe.py "$B" $CLIPS
ENVS=(STEP=0.5); run sole_probe.py "$B" Standing Walking Running Attack Hit Fidget
ENVS=(X=1); run foot_flat.py "$B" Standing Walking Attack Hit Fidget
run jerk_probe.py "$B" $CLIPS
run g6_skirt_poke.py "$B" Walking Running Attack Fidget
run stride.py "$B" Walking Running Standing
run stand_height.py "$B"
} > "$OUT" 2>&1
cat "$OUT"
