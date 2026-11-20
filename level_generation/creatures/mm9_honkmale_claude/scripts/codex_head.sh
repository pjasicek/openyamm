#!/usr/bin/env bash
# Usage: scripts/codex_head.sh <project dir name>   (from the repo root). Runs through the 16 shared slots.
set -u
P=level_generation/creatures/$1; D=$P/references_hd; H=$P/v2/references_head
PROMPT="Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Generate 01_front.png first, then the other three views with it as an extra input. Produce the images with your built-in image generation tool and save them as specified."
level_generation/creatures/claude_shared/codex_slot.sh codex exec "$PROMPT" -c model_reasoning_effort=medium \
  -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o "$H/codex_last_message.md" -i "$D/mm9_head_views.png" -i "$D/00_three_quarter.png" -i "$D/01_front.png" -i "$D/mm9_skin_x4.png" \
  < /dev/null > "$H/codex_run.log" 2>&1
echo "codex head $1 exit $?"
