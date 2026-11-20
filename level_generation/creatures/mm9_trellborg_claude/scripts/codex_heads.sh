#!/bin/bash
# from the repo root
R=level_generation/creatures/mm9_trellborg_claude; H=$R/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/references_head/CODEX_BRIEF_PAINT.md exactly. The attached images are its inputs in order. Your image tool accepts five references per call: use the clay of the view being painted, the head master, the skin, and the selected front paint. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message_a.md -i $H/clay_01_front.png -i $H/clay_03_left.png -i $H/clay_02_back.png -i $H/clay_04_right.png -i $H/clay_05_top.png -i $H/in_body_head.png -i $R/references_hd/mm9_skin_x4_a.png < /dev/null > $H/codex_run_a.log 2>&1
