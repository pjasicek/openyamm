#!/usr/bin/env bash
# Rebuild the package h15 exports (MM7 goblin peasants, MM8 Earth Elemental and Gog, both bound in MM7 too) from their
# pre-gait sources (work/<name>_pre_gait.glb: the installed sources before this package, also the rollback) and run the
# gates (gait_gate.py in every world and tier group the bindings change, check_winding.py).
#   scripts/rebuild.sh [model ...]   (models: mm7_7m452 mm7_m442 mm8_m504 mm8_m612; default all)
# Library loops in work/sources/ (copied from ../h08 and ../h16 work/sources: library-derived, never commit).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
cd "$here"
gate="$root/level_generation/creatures/claude_shared/postprocess/gait_gate.py"
only="$here/../q2/scripts/gate_only.py"
declare -A JOBS=([mm7_7m452]="7m452_jog" [mm7_m442]="m442_jog" [mm8_m504]="m504_walk2 m504_jog m504_run"
                 [mm8_m612]="m612_walk2")
models=("$@"); [[ ${#models[@]} -gt 0 ]] || models=(mm7_7m452 mm7_m442 mm8_m504 mm8_m612)
for m in "${models[@]}"; do
    jobs=(); for j in ${JOBS[$m]}; do jobs+=("jobs/$j.json"); done
    python3 scripts/compose_gait.py "work/${m}_pre_gait.glb" "export/$m.glb" "${jobs[@]}" > "work/${m}_compose.log"
    mv "export/$m.compose.json" "review/$m.compose.json"
    case $m in
        mm7_7m452|mm7_m442)
            python3 "$gate" --world mm7 --model "$m.glb" --candidate "export/$m.glb" --set run=Jog \
                > "review/${m}_mm7_gait_gate.txt" || true ;;
        mm8_m504)
            python3 "$gate" --world mm7 --model "$m.glb" --candidate "export/$m.glb" --set run=Run \
                > "review/${m}_mm7_gait_gate.txt" || true
            python3 "$only" --only "Earth Elemental A,Earth Elemental B" --world mm8 --model "$m.glb" \
                --candidate "export/$m.glb" --set walking=Walk2 > "review/${m}_mm8_AB_gait_gate.txt" || true
            python3 "$only" --only "Earth Elemental C" --world mm8 --model "$m.glb" --candidate "export/$m.glb" \
                --set walking=Walk2 --set run=Jog --set sprint=Run > "review/${m}_mm8_C_gait_gate.txt" || true ;;
        mm8_m612)
            python3 "$only" --only "AGog C" --world mm7 --model "$m.glb" --candidate "export/$m.glb" \
                --set walking=Walk2 > "review/${m}_mm7_C_gait_gate.txt" || true ;;
    esac
    python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "export/$m.glb" \
        | tail -1 > "review/${m}_winding.txt"
    for f in review/${m}_*gait_gate.txt; do echo "$f: $(tail -1 "$f")"; done
    cat "review/${m}_winding.txt"
done
