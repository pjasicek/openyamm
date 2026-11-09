#!/bin/bash
# scripts/codex_masters_fre.sh (repo root): Fre body masters (4, on PeasantF4's masters) and head paint-overs (4, on renders of our head)
# in one Codex run, brief references_hd/CODEX_BRIEF.md
P=level_generation/creatures/mm9_fre_claude; R=$P/references_hd; H=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/mm9_views.png -i $R/mm9_chest_views.png -i $R/mm9_head_views.png -i $R/mm9_skin_x4.png \
  -i $R/f4_shape/01_front_clean.png -i $R/f4_shape/03_left_clean.png -i $R/f4_shape/02_back_clean.png -i $R/f4_shape/04_right_clean.png \
  -i $H/cur_front.png -i $H/cur_q34.png -i $H/cur_left.png -i $H/cur_back.png \
  < /dev/null > $R/codex_run.log 2>&1
