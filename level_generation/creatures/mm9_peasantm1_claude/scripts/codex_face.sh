#!/bin/bash
# Usage: scripts/codex_face.sh   (from the repo root) - eye-area repaint of the albedo face renders (face fix)
P=level_generation/creatures/mm9_peasantm1_claude
O=$P/references_face
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md -i $O/in_face_a.png -i $P/references_head/01_front.png -i $O/in_face_b.png -i $P/references_head_b/01_front.png \
  < /dev/null > $O/codex_run.log 2>&1
