#!/bin/bash
# Usage: scripts/codex_heads.sh   (from the repo root)
R=level_generation/creatures/mm9_peasantm2_claude
H=$R/references_head
python3 -c "
from PIL import Image
im=Image.open('$R/references_hd/mm9_head_views_b.png'); im.resize((im.width//2,im.height//2),Image.LANCZOS).save('$R/references_hd/mm9_head_views_b_half.png')"
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs 1-4 in order; use your own selected returns as the extra inputs the brief names. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message.md -i $R/references_hd/mm9_head_views_a_half.png -i $R/references_hd/mm9_head_views_b_half.png \
  -i $R/references_hd/00_three_quarter_clean.png -i $R/references_hd/01_front.png < /dev/null > $H/codex_run.log 2>&1
