#!/bin/bash
# scripts/codex_heads.sh 1|2 (repo root): skull turnaround
P=level_generation/creatures/mm9_skraelos_claude; R=$P/references_hd; H=$P/references_head; run=$1
inputs=(-i $R/01_front_clean.png -i $R/00_three_quarter_clean.png -i $R/03_left_clean.png -i $R/mm9_head_views.png -i $R/mm9_skin_x4.png)
if [ "$run" = 2 ]; then inputs+=(-i $H/00_three_quarter.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $H/codex_run$run.log 2>&1
