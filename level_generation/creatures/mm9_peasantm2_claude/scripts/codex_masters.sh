#!/bin/bash
# Usage: scripts/codex_masters.sh 1|2   (from the repo root)
R=level_generation/creatures/mm9_peasantm2_claude/references_hd
run=$1
inputs=(-i $R/mm9_full_views_a_half.png -i $R/mm9_waist_views_a_half.png -i $R/mm9_head_views_a_half.png -i $R/mm9_skin_x4_a.png)
if [ "$run" = 2 ]; then inputs+=(-i $R/00_three_quarter_clean.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
