#!/bin/bash
# Usage: scripts/codex_head.sh 1|2|3   (from the repo root)
B=level_generation/creatures/mm9_banshee_claude
R=$B/references_head
H=$B/references_hd
run=$1
inputs=(-i $H/mm9_views_head_A.png -i $H/mm9_views_head_E.png -i $H/mm9_skin_x4_E.png -i $H/mm9_skin_x4_A.png)
if [ "$run" != 1 ]; then inputs+=(-i $R/a/00_three_quarter.png); fi
if [ "$run" = 3 ]; then inputs+=(-i $R/a/01_front.png -i $R/a/02_back.png -i $R/a/03_left.png -i $R/a/04_right.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
