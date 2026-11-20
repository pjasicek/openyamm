#!/bin/bash
# Accessory texture sheet (staff + crown) for the Codex brief in references_acc/ (repo root).
R=level_generation/creatures/mm9_yanmir_claude/references_acc
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/mm9_staff_views.png -i $R/mm9_skin_x2.png -i $R/crown_master_crop.png < /dev/null > $R/codex_run.log 2>&1
