#!/bin/bash
# Usage: scripts/codex_shield.sh a|b|c (repo root)
R=level_generation/creatures/mm9_clansoldier_claude/references_shield; t=$1
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, tier ${t^^} only. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_$t.md -i $R/outline.png -i $R/mm9_shield_x4_$t.png < /dev/null > $R/codex_$t.log 2>&1
