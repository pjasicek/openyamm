#!/bin/bash
# scripts/codex_masters_pf4.sh (repo root): PF4 skin A body masters (4) and head turnaround (4) in one Codex run, brief references_hd/CODEX_BRIEF.md
P=level_generation/creatures/mm9_peasantf4_claude; R=$P/references_hd; H=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/mm9_views_a.png -i $R/mm9_chest_views_a.png -i $R/mm9_head_views_a.png -i $R/mm9_skin_x4_a.png \
  -i $R/f1_shape/01_front_clean.png -i $R/f1_shape/03_left_clean.png -i $R/f1_shape/02_back_clean.png -i $R/f1_shape/04_right_clean.png \
  -i $H/f1_shape/b_01_front.png -i $H/f1_shape/b_00_three_quarter.png -i $H/f1_shape/b_02_profile.png -i $H/f1_shape/b_03_back.png \
  < /dev/null > $R/codex_run.log 2>&1
