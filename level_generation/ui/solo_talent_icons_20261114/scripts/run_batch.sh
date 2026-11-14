#!/bin/bash
# Generates the talent icon masters in four parallel Codex runs (the brief skips existing masters).
# Usage: scripts/run_batch.sh               all four batches (positions of icons.json, 1-based)
#        scripts/run_batch.sh <tag> "<positions>" ["<extra instruction>"]   one run, e.g. a retry
cd "$(dirname "$0")/../../../.."
D=level_generation/ui/solo_talent_icons_20261114
run() {
    codex exec "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached image is its input 1. Do list positions $2 of icons.json (1-based). $3" \
        -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_$1_last_message.md" \
        -i "$D/refs_spell_icons.png" < /dev/null > "$D/raw/batch_$1_run.log" 2>&1
}
if [ $# -ge 2 ]; then
    run "$1" "$2" "$3"
else
    run a "1, 2, 3, 4, 5" &
    run b "6, 7, 8, 9, 10" &
    run c "11, 12, 13, 14, 15" &
    run d "16, 17, 18, 19, 20, 21" &
    wait
fi
ls "$D/masters"
