#!/bin/bash
# Usage: scripts/codex_head.sh a|b|c   (repo root)
P=level_generation/creatures/mm9_peasanthof_claude; R=$P/references_hd; O=$P/references_head/$1
case $1 in
  a) inputs=(-i $R/mm9_head_views_phof1a.png -i $R/a/00_three_quarter.png -i $R/a/01_front.png -i $R/mm9_skin_x4_phof1a.png);;
  b) inputs=(-i $R/mm9_head_views_phof1b.png -i $R/a/00_three_quarter.png -i $R/a/01_front.png -i $R/mm9_skin_x4_phof1b.png);;
  a2) inputs=(-i $R/mm9_head_views_phof1a.png -i $R/a/00_three_quarter.png -i $P/references_head/a/01_front.png -i $R/mm9_skin_x4_phof1a.png);;
  c) inputs=(-i $R/mm9_head_views_phof2c.png -i $R/c/01_front.png -i $R/c/03_left.png -i $R/mm9_skin_x4_phof2c.png);;
esac
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md "${inputs[@]}" < /dev/null > $O/codex_run.log 2>&1
