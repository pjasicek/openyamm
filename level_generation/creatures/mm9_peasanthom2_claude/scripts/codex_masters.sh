#!/bin/bash
# HD body masters for PeasantHOM2 (repo root). Edit targets: mm9_peasanthom1_claude's accepted clean masters.
R=level_generation/creatures/mm9_peasanthom2_claude/references_hd
H=level_generation/creatures/mm9_peasanthom1_claude/references_hd/clean
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the five images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/mm9_views_h2.png -i $R/mm9_head_views_h2.png -i $R/mm9_skin_x4_h2.png \
  -i $H/00_three_quarter.png -i $H/01_front.png -i $H/02_back.png -i $H/03_left.png -i $H/04_right.png < /dev/null > $R/codex_run.log 2>&1
