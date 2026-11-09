#!/bin/bash
# scripts/codex_heads.sh (repo root): head turnaround, face A
P=level_generation/creatures/mm9_peasantf6_claude; R=$P/references_hd; H=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message.md -i $R/mm9_head_views_a.png -i $R/00_three_quarter.png -i $R/mm9_skin_x4_a.png \
  -i $R/shape_head_clay.png < /dev/null > $H/codex_run.log 2>&1
