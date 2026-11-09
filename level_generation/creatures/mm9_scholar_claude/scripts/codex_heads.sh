#!/bin/bash
# scripts/codex_heads.sh (repo root): both head turnarounds in one Codex run
R=level_generation/creatures/mm9_scholar_claude/references_hd; H=level_generation/creatures/mm9_scholar_claude/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message.md -i $R/mm9_head_views_1.png -i $R/00_three_quarter_clean.png -i $R/01_front_clean.png -i $R/mm9_skin_x4_1.png \
  -i $R/mm9_head_views_3.png -i $R/mm9_skin_x4_3.png < /dev/null > $H/codex_run.log 2>&1
