#!/bin/bash
# Usage: scripts/codex_tiers.sh b|c  (from the repo root)
R=level_generation/creatures/mm9_highwayman_claude; H=$R/references_hd; t=$1
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/references_tiers/CODEX_BRIEF.md exactly, tier ${t^^} only (write generation_runs_$t.json and selected_views_review_$t.png). The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/references_tiers/codex_last_message_$t.md -i $H/01_front_clean.png -i $H/03_left_clean.png -i $H/02_back_clean.png -i $H/04_right_clean.png -i $H/mm9_views_$t.png -i $H/mm9_waist_views_$t.png -i $H/mm9_head_views_$t.png -i $H/mm9_skin_x4_$t.png < /dev/null > $R/references_tiers/codex_run_$t.log 2>&1
