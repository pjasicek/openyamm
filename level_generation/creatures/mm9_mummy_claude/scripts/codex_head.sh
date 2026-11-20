#!/bin/bash
# Usage: scripts/codex_head.sh   (from the repo root)
P=level_generation/creatures/mm9_mummy_claude; R=$P/references_hd; H=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message.md -i $H/mm9_head_t1.png -i $H/mm9_head_t2.png -i $H/mm9_head_t3.png -i $R/mm9_skin_x4_t1.png -i $R/mm9_skin_x4_t2.png -i $R/mm9_skin_x4_t3.png \
  -i $R/00_three_quarter.png -i $R/01_front.png -i $R/02_back.png -i $R/03_left.png < /dev/null > $H/codex_run.log 2>&1
