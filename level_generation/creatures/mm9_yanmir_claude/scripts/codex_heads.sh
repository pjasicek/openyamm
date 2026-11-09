#!/bin/bash
# Head paints on our clay (repo root).
R=level_generation/creatures/mm9_yanmir_claude; H=$R/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF_PAINT.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message_a.md -i $H/clay_01_front.png -i $H/clay_03_left.png -i $H/clay_02_back.png -i $H/clay_04_right.png -i $H/clay_05_top.png -i $R/references_hd/mm9_head_views.png -i $R/references_hd/mm9_skin_x4.png -i $H/in_body_head.png < /dev/null > $H/codex_run_a.log 2>&1
