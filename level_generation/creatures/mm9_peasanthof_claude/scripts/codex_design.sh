#!/bin/bash
# Usage: scripts/codex_design.sh c phof2c   (repo root): retexture views of design C on the clay silhouettes references_hd/c/sil_*
P=level_generation/creatures/mm9_peasanthof_claude
R=$P/references_hd; D=$R/$1; s=$2
inputs=(-i $R/mm9_views_$s.png -i $R/mm9_head_views_$s.png -i $R/mm9_skin_x4_$s.png -i $D/sil_front.png -i $D/sil_left.png -i $D/sil_back.png -i $D/sil_right.png)
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $D/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $D/codex_last_message.md "${inputs[@]}" < /dev/null > $D/codex_run.log 2>&1
