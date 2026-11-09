#!/bin/bash
P=level_generation/creatures/mm9_greenman_claude; O=$P/references_staff
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md -i $P/source/mm9/skins/greenmanstaff.png -i $P/references_head/03_back.png < /dev/null > $O/codex_run.log 2>&1
