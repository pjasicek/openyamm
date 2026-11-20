#!/bin/bash
# Generates the boss badges in four parallel Codex runs (the brief skips existing masters).
cd "$(dirname "$0")/../../.."
D=level_generation/ui/maw_boss_badges_20261024
run() {
    codex exec "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached image is its input 1. Do list positions $2 of items.json (1-based)." \
        -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_$1_last_message.md" \
        -i "$D/refs_obsidian_hud.png" < /dev/null > "$D/raw/batch_$1_run.log" 2>&1
}
run a "1, 2, 3, 4" &
run b "5, 6, 7, 8" &
run c "9, 10, 11, 12" &
run d "13, 14, 15" &
wait
ls "$D/masters" | wc -l
