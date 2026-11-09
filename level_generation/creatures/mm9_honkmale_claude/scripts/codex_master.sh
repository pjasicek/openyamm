#!/usr/bin/env bash
# Usage: scripts/codex_master.sh <project dir name> <run: 1|2>   (from the repo root). Runs through the 16 shared slots.
set -u
P=level_generation/creatures/$1; R=$2; D=$P/references_hd
PROMPT="Follow the brief in $D/CODEX_BRIEF.md exactly. The attached images are its inputs in order. This is run $R of the brief: "
if [[ $R == 1 ]]; then PROMPT+="generate 00_three_quarter.png only, then stop."; EX=(); else PROMPT+="generate 01_front, 02_back, 03_left and 04_right with the selected 00_three_quarter.png as an extra input."; EX=(-i "$D/00_three_quarter.png"); fi
PROMPT+=" Produce the images with your built-in image generation tool and save them as specified."
level_generation/creatures/claude_shared/codex_slot.sh codex exec "$PROMPT" -c model_reasoning_effort=medium \
  -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o "$D/codex_last_message_run$R.md" -i "$D/mm9_views.png" -i "$D/mm9_head_views.png" -i "$D/mm9_skin_x4.png" "${EX[@]}" \
  < /dev/null > "$D/codex_run$R.log" 2>&1
echo "codex $1 run $R exit $?"
