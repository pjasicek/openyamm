#!/bin/bash
# Usage: scripts/codex_masters.sh 1|2   (from the repo root). Body HD masters, skin A design, PeasantF5's masters as shape authority, our clay head.
P=level_generation/creatures/mm9_peasantf6_claude; run=$1; R=$P/references_hd; F=level_generation/creatures/mm9_peasantf5_claude/references_hd
inputs=(-i $R/mm9_views_a.png -i $R/mm9_chest_views_a.png -i $R/mm9_head_views_a.png -i $R/mm9_skin_x4_a.png -i $F/00_three_quarter_clean.png -i $R/shape_head_clay.png)
if [ "$run" = 2 ]; then inputs+=(-i $R/00_three_quarter.png -i $F/01_front_clean.png -i $F/03_left_clean.png -i $F/02_back_clean.png -i $F/04_right_clean.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
