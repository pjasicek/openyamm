#!/bin/bash
# Generates the remaining crafting icons in four parallel Codex runs (the brief skips existing masters).
cd "$(dirname "$0")/../../.."
D=level_generation/ui/maw_crafting_icons_20261023
run() {
    codex exec "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached image is its input 1. Do list positions $2 of items.json (1-based)." \
        -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_$1_last_message.md" \
        -i "$D/refs_mm_icons.png" < /dev/null > "$D/raw/batch_$1_run.log" 2>&1
}
run a "2, 3, 4, 5, 12, 13, 14" &
run b "6, 7, 8, 9, 15, 16, 17" &
run c "10, 18, 19, 20, 22, 23, 24" &
run d "25, 26, 27, 28, 29, 30" &
wait
ls "$D/masters" | wc -l
