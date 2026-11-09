#!/bin/bash
# Usage: scripts/codex_runs.sh body|head   (from the repo root). Codex only through codex_slot.sh.
P=level_generation/creatures/mm9_peasantdm3_claude
D1=level_generation/creatures/mm9_peasantdm1_claude
if [ "$1" = body ]; then
  O=$P/references_hd
  inputs=(-i $O/mm9_views_b.png -i $O/mm9_torso_views_b.png -i $O/mm9_skin_x4_b.png -i $O/mm9_views_b.png
          -i $D1/references_hd/00_three_quarter.png -i $D1/references_hd/01_front.png -i $D1/references_hd/02_back.png
          -i $D1/references_hd/03_left.png -i $D1/references_hd/04_right.png)
else
  O=$P/references_head
  inputs=(-i $O/silhouette/sil_front_white.png -i $O/silhouette/sil_q34_white.png -i $O/silhouette/sil_left_white.png
          -i $O/silhouette/sil_back_white.png -i $P/references_hd/mm9_head_views_b.png -i $P/references_hd/mm9_skin_x4_b.png
          -i $D1/references_head/01_front.png)
fi
mkdir -p $O/raw
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md "${inputs[@]}" < /dev/null > $O/codex_run.log 2>&1
