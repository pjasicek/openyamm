#!/bin/bash
# Usage: scripts/codex_masters.sh <design dir d1..d4> <skin pdfNx> 1|2   (from the repo root)
P=level_generation/creatures/mm9_peasantdf_claude
R=$P/references_hd
D=$R/$1; s=$2; run=$3
inputs=(-i $R/mm9_views_$s.png -i $R/mm9_head_views_$s.png -i $R/mm9_skin_x4_$s.png)
if [ "$run" = 2 ]; then inputs+=(-i $D/00_three_quarter.png); fi
if [ -n "$EXTRA" ]; then for e in $EXTRA; do inputs+=(-i $e); done; fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $D/CODEX_BRIEF.md exactly, run $run. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $D/codex_last_message_run$run.md "${inputs[@]}" < /dev/null > $D/codex_run$run.log 2>&1
