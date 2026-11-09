#!/bin/bash
# Usage: scripts/codex_masters.sh 1|2|3|4   (from the repo root)
R=level_generation/creatures/mm9_troglodyte_claude/references_hd
run=$1
inputs=(-i $R/mm9_views_b.png -i $R/mm9_head_views_b.png -i $R/mm9_skin_x4_b.png)
if [ "$run" != 1 ]; then inputs+=(-i $R/00_three_quarter.png); fi
if [ "$run" = 3 ]; then inputs+=(-i $R/mm9_views_c.png -i $R/mm9_head_views_c.png -i $R/mm9_skin_x4_c.png -i $R/01_front.png -i $R/02_back.png -i $R/03_left.png -i $R/04_right.png); fi
if [ "$run" = 4 ]; then inputs+=(-i $R/01_front.png -i $R/03_left.png -i $R/mm9_mouth_views_b.png); fi
if [ "$run" = 5 ]; then inputs=(-i $R/mm9_views_a.png -i $R/mm9_head_views_a.png -i $R/mm9_skin_x4_a.png -i $R/01_front.png -i $R/03_left.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
