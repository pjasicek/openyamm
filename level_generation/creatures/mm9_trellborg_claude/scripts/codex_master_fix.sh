#!/bin/bash
R=level_generation/creatures/mm9_trellborg_claude/references_hd
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md, section 'Correction to run 1 (run 1b)' only. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run1b.md -i $R/mm9_views_a.png -i $R/mm9_torso_views_a.png -i $R/mm9_legs_views_a.png -i $R/mm9_head_views_a.png -i $R/mm9_skin_x4_a.png -i $R/raw/00_three_quarter_first.png < /dev/null > $R/codex_run1b.log 2>&1
