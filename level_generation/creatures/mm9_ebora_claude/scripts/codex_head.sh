#!/bin/bash
# repo root: scripts/codex_head.sh ebora|siren
R=level_generation/creatures/mm9_ebora_claude; P=$R/references_head; H=$R/references_hd
clay=(); for v in 08_face 01_front 06_q34r 07_q34l 03_left 04_right 02_back 05_top; do clay+=(-i $P/clay_$v.png); done
if [ "$1" = siren ]; then b=CODEX_BRIEF_HEAD_SIREN.md; ex=(-i $H/mm9_head_views_siren1.png -i $H/mm9_skin_x4_siren1.png); else b=CODEX_BRIEF_HEAD.md; ex=(-i $H/mm9_head_views_ebora.png -i $H/01_front.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/$b exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $P/codex_last_message_$1.md "${clay[@]}" "${ex[@]}" < /dev/null > $P/codex_run_$1.log 2>&1
