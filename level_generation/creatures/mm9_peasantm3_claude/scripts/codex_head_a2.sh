#!/bin/bash
# r3 head turnaround for tier A (repo root): fresh head masters from viewer renders of the current head + MM9 skin A.
P=level_generation/creatures/mm9_peasantm3_claude
O=$P/references_head_a2
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md -i $O/viewer_head_a.png -i $P/references_hd/mm9_head_views_a.png -i $P/references_head/01_front.png \
  -i $P/references_hd/mm9_skin_x4_a.png < /dev/null > $O/codex_run.log 2>&1
