#!/bin/bash
# Generates the art in two parallel Codex runs (the brief skips existing masters, so a rerun resumes).
# run <name> <art.json positions> <brief input numbers> <image args...>
cd "$(dirname "$0")/../../../.."
D=level_generation/ui/mm9_fleet_foot_20261109
mkdir -p "$D/raw" "$D/masters"
run() {
    local name=$1 positions=$2 inputs=$3
    shift 3
    codex exec "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached images are, in order, its inputs $inputs. Do list positions $positions of $D/art.json (1-based)." \
        -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_${name}_last_message.md" \
        "$@" < /dev/null > "$D/raw/batch_${name}_run.log" 2>&1
}
run vignette 1 "1-2" -i "$D/refs/refs_air_vignettes.png" -i "$D/refs/refs_mm9_fleetfoot.png" &
run hud "2-3" "3-4" -i "$D/refs/refs_hud.png" -i "$D/refs/refs_mm9_fleetfoot.png" &
wait
ls "$D/masters"
