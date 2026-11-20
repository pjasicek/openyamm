#!/bin/bash
# Usage: scripts/codex_head.sh d1|d3|d4   (repo root)
P=level_generation/creatures/mm9_peasantdf_claude; R=$P/references_hd; O=$P/references_head/$1
case $1 in
  d1) inputs=(-i $R/mm9_head_views_pdf1a.png -i $R/d1/00_three_quarter.png -i $R/d1/01_front.png -i $R/mm9_skin_x4_pdf1a.png);;
  d3) inputs=(-i $R/mm9_head_views_pdf3a.png -i $R/d3/01_front.png -i $R/d3/03_left.png -i $R/mm9_skin_x4_pdf3a.png);;
  d4) inputs=(-i $R/mm9_head_views_pdf4a.png -i $R/d4/01_front.png -i $R/d4/03_left.png -i $R/mm9_skin_x4_pdf4a.png);;
esac
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md "${inputs[@]}" < /dev/null > $O/codex_run.log 2>&1
