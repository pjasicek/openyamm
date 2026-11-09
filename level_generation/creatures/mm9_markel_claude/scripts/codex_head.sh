#!/bin/bash
# Head turnaround (from the repo root)
P=level_generation/creatures/mm9_markel_claude
O=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the four head images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md -i $P/references_hd/mm9_head_views.png -i $P/references_hd/00_three_quarter.png \
  -i $P/references_hd/01_front.png -i $P/references_hd/mm9_skin_x4.png < /dev/null > $O/codex_run.log 2>&1
