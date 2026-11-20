#!/usr/bin/env bash
# m286 gate run on the gated master (work/rig_v5.blend) -> review/gates_final.txt: G6 prop/arm contacts (the modelled
# axe on its export frame, axe_attach.py), G5 hand stretch, G4 arm stretch at clip extremes, soles, foot flatness, jerk,
# stride and standing height. Token: CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
P=level_generation/creatures/mm7_m286_claude; W="$repo/$P/work"; OUT="$repo/$P/review/gates_final.txt"
CLIPS="Standing Walking Running Attack Hit Fidget Death"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(G6|HANDSTRETCH|SOLE|JERK|G4|FLAT|STRIDE|STAND|AXEATTACH)' "$log" | cut -c1-400 || true; }
{
run axe_attach.py "$W/rig_v5.blend" "$W/rig_v5_axe.blend"
PROP_HAND=R run g6_prop.py "$W/rig_v5_axe.blend" $CLIPS
run g5_hand_stretch.py "$W/rig_v5.blend" $CLIPS
run g4_weights.py "$W/rig_v5.blend" final Attack:15 Attack:25 Attack:30 Fidget:30 Hit:6 Death:40 Running:10 Walking:10 Standing:0
STEP=0.5 run sole_probe.py "$W/rig_v5.blend" $CLIPS
run foot_flat.py "$W/rig_v5.blend" Standing Walking Running Attack Fidget
run jerk_probe.py "$W/rig_v5.blend" $CLIPS
run stride.py "$W/rig_v5.blend" Walking Running Standing
run stand_height.py "$W/rig_v5.blend"
} | tee "$OUT"
