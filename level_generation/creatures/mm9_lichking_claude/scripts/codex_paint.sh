#!/bin/bash
# repo root
R=level_generation/creatures/mm9_lichking_claude; P=$R/references_paint; H=$R/references_hd
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $P/codex_last_message.md -i $P/clay_01_front.png -i $P/clay_03_left.png -i $P/clay_02_back.png -i $P/clay_04_right.png -i $H/01_front.png -i $H/03_left.png -i $H/02_back.png -i $H/04_right.png -i $H/mm9_chest.png -i $H/mm9_waist.png -i $H/mm9_skin_x4.png < /dev/null > $P/codex_run.log 2>&1
