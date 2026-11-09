#!/bin/bash
# Usage: scripts/codex_head.sh a|b   (from the repo root)
P=level_generation/creatures/mm9_peasantm3_claude
if [ "$1" = a ]; then
  O=$P/references_head
  inputs=(-i $P/references_hd/mm9_head_views_a.png -i $P/references_hd/00_three_quarter.png -i $P/references_hd/01_front.png -i $P/references_hd/mm9_skin_x4_a.png)
else
  O=$P/references_head_b
  inputs=(-i $P/references_hd/mm9_head_views_b.png -i $P/references_head/01_front.png -i $P/references_head/00_three_quarter.png -i $P/references_head/02_profile.png -i $P/references_head/03_back.png -i $P/references_hd/mm9_skin_x4_b.png)
fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md "${inputs[@]}" < /dev/null > $O/codex_run.log 2>&1
