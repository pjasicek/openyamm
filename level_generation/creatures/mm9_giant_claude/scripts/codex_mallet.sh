#!/bin/bash
# Usage: scripts/codex_mallet.sh 1|2   (from the repo root). Third pass: HD master views of MM9's mallet.
R=level_generation/creatures/mm9_giant_claude/references_mallet
run=$1
inputs=(-i $R/mm9_mallet_views_a.png -i $R/mm9_mallet_heads.png -i $R/mm9_mallet_skin_x4_a.png -i $R/mm9_mallet_skin_x4_b.png -i $R/proportion_template_front.png -i $R/superseded/00_three_quarter_v1.png)
if [ "$run" = 2 ]; then inputs+=(-i $R/00_three_quarter.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
