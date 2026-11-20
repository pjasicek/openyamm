#!/bin/bash
# repo root. scripts/codex_paint.sh ebora|siren
R=level_generation/creatures/mm9_ebora_claude; P=$R/references_paint; H=$R/references_hd
clay=(-i $P/clay_01_front.png -i $P/clay_03_left.png -i $P/clay_02_back.png -i $P/clay_04_right.png)
if [ "$1" = siren ]; then
  brief=CODEX_BRIEF_SIREN.md; extra=(-i $H/mm9_body_views_siren1.png -i $H/mm9_head_views_siren1.png -i $H/mm9_chest_views_siren1.png -i $H/mm9_legs_views_siren1.png -i $H/mm9_skin_x4_siren1.png)
else
  brief=CODEX_BRIEF.md; extra=(-i $H/01_front.png -i $H/03_left.png -i $H/02_back.png -i $H/04_right.png -i $H/mm9_chest_views_ebora.png -i $H/mm9_legs_views_ebora.png -i $H/mm9_head_views_ebora.png)
fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/$brief exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $P/codex_last_message_$1.md "${clay[@]}" "${extra[@]}" < /dev/null > $P/codex_run_$1.log 2>&1
