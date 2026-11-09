#!/bin/bash
# Head turnaround (from the repo root)
P=level_generation/creatures/mm9_peasantm1d_claude
R=$P/v2/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the four head images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $P/references_hd/mm9_head_views_c.png -i $P/references_hd/00_three_quarter.png \
  -i $P/references_hd/mm9_skin_x4_c.png < /dev/null > $R/codex_run.log 2>&1
