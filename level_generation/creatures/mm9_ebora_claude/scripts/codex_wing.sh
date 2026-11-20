#!/bin/bash
R=level_generation/creatures/mm9_ebora_claude; P=$R/references_paint
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/CODEX_BRIEF_WING.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $P/codex_last_message_wing.md -i $P/wing_template.png -i $P/mm9_wing_views.png < /dev/null > $P/codex_run_wing.log 2>&1
