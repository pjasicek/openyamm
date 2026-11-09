#!/bin/bash
# Usage: scripts/codex_tiers.sh b|c   (from the repo root)
P=level_generation/creatures/mm9_zombie_claude; R=$P/references_tiers
run=$1
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_$run.md -i $R/input_a_views.png -i $P/references_hd/mm9_views_$run.png -i $P/references_hd/mm9_skin_x4_$run.png < /dev/null > $R/codex_run_$run.log 2>&1
