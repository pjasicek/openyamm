#!/bin/bash
# Usage: scripts/codex_heads.sh a|b|c  (from the repo root)
R=level_generation/creatures/mm9_thrall_claude; H=$R/references_head; t=$1
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/references_head/CODEX_BRIEF_PAINT.md exactly, tier ${t^^} only. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message_$t.md -i $H/clay_01_front.png -i $H/clay_03_left.png -i $H/clay_02_back.png -i $H/clay_04_right.png -i $H/clay_05_top.png -i $H/clay_06_q34r.png -i $H/clay_07_q34l.png -i $R/references_hd/mm9_head_views_$t.png -i $R/references_hd/mm9_skin_x4_$t.png < /dev/null > $H/codex_run_$t.log 2>&1
