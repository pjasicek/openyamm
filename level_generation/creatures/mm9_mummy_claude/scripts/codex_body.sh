#!/bin/bash
# Usage: scripts/codex_body.sh 1|2|3   (from the repo root)
P=level_generation/creatures/mm9_mummy_claude; R=$P/references_hd; run=$1
case $run in
 1) inputs=(-i $R/mm9_views_t1.png -i $R/mm9_skin_x4_t1.png -i $P/references_head/mm9_head_t1.png);;
 2) inputs=(-i $R/mm9_views_t1.png -i $R/mm9_skin_x4_t1.png -i $P/references_head/mm9_head_t1.png -i $R/00_three_quarter.png);;
 3) inputs=(-i $R/mm9_views_t2.png -i $R/mm9_skin_x4_t2.png -i $R/mm9_views_t3.png -i $R/mm9_skin_x4_t3.png -i $R/01_front.png -i $R/02_back.png -i $R/03_left.png -i $R/04_right.png);;
esac
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $R/codex_run$run.log 2>&1
