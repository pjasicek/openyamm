#!/bin/bash
# Generates the study's art in parallel Codex runs (the brief skips existing masters, so a rerun resumes).
cd "$(dirname "$0")/../../../.."
D=level_generation/ui/maw_class_spellbooks_20261108
run() {
    codex exec "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached images are its inputs 1-3 in order. Do list positions $2 of $D/art.json (1-based)." \
        -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_$1_last_message.md" \
        -i "$D/refs/refs_vignettes.png" -i "$D/refs/refs_medallions.png" -i "$D/refs/refs_tabs.png" \
        < /dev/null > "$D/raw/batch_$1_run.log" 2>&1
}
run a "1-7" &
run b "8-14" &
run c "15-20" &
run d "21-27" &
run e "28-34" &
wait
ls "$D/masters"
