#!/bin/bash
# Tier B face repaint (repo root).
P=level_generation/creatures/mm9_peasantm5_claude; R=$P/references_face
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/in_face_b.png -i $R/mm9_face_b.png -i $P/references_hd/mm9_head_views_b.png < /dev/null > $R/codex_run.log 2>&1
