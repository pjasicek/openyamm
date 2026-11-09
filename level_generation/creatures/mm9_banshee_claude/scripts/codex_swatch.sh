#!/bin/bash
R=level_generation/creatures/mm9_banshee_claude/references_swatch
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order: cloth patch, hair E, hair A. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/mm9_cloth_patch_x7.png -i $R/mm9_hair_E_x10.png -i $R/mm9_hair_A_x10.png < /dev/null > $R/codex_run.log 2>&1
