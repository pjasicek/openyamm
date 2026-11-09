#!/bin/bash
R=level_generation/creatures/mm9_trellborg_claude/references_club
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached image is its input 1. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=low -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/mm9_wood_x16.png < /dev/null > $R/codex_run.log 2>&1
