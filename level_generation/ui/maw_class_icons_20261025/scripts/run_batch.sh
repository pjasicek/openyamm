#!/bin/bash
# Generates the class icon masters in parallel Codex runs (the brief skips existing masters).
# Batches a and b made the four MAW class lines; batch c (2026-10-25, later) made the Peasant.
cd "$(dirname "$0")/../../../.."
D=level_generation/ui/maw_class_icons_20261025
run() {
    codex exec "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached image is its input 1. Do list positions $2 of classes.json (1-based)." \
        -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_$1_last_message.md" \
        -i "$D/refs_class_icons.png" < /dev/null > "$D/raw/batch_$1_run.log" 2>&1
}
run a "1, 2" &
run b "3, 4" &
run c "5" &
wait
ls "$D/masters"
