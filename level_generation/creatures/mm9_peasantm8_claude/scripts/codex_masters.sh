#!/bin/bash
# Usage: scripts/codex_masters.sh <project> 1|2   (from the repo root). Shape authority: SHAPE=<approved project>.
P=$1; run=$2; R=$P/references_hd; F=level_generation/creatures/$SHAPE/references_hd
inputs=(-i $R/mm9_views.png -i $R/mm9_head_views.png -i $R/mm9_skin_x4.png -i $F/00_three_quarter.png)
if [ "$run" = 2 ]; then inputs+=(-i $R/00_three_quarter.png -i $F/01_front.png -i $F/03_left.png -i $F/02_back.png -i $F/04_right.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
