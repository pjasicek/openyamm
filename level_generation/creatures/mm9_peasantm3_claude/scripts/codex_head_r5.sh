#!/bin/bash
# r5 head turnarounds (repo root): fresh head masters for tier a|b on the final mouth geometry. Usage: codex_head_r5.sh a|b
P=level_generation/creatures/mm9_peasantm3_claude
t=$1; O=$P/references_head_r5$t
if [ "$t" = a ]; then ref=$P/references_head_a2/01_front.png; else ref=$P/references_head_b/01_front.png; fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/codex_last_message.md -i $O/viewer_head_$t.png -i $P/references_hd/mm9_head_views_$t.png -i $ref \
  -i $P/references_hd/mm9_skin_x4_$t.png < /dev/null > $O/codex_run.log 2>&1
