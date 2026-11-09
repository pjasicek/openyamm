#!/bin/bash
R=level_generation/creatures/mm9_evilsorcerer_claude; P=$R/references_paint; H=$R/references_hd
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/CODEX_BRIEF_A.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $P/codex_last_message_a.md -i $P/paint_01_front_clean.png -i $P/paint_03_left_clean.png -i $P/paint_02_back_clean.png -i $P/paint_04_right_clean.png -i $P/clay_01_front.png -i $P/clay_03_left.png -i $P/clay_02_back.png -i $P/clay_04_right.png -i $H/mm9_views_a.png -i $H/mm9_waist_views_a.png -i $H/mm9_chest_views_a.png -i $H/mm9_skin_x4_a.png < /dev/null > $P/codex_run_a.log 2>&1
