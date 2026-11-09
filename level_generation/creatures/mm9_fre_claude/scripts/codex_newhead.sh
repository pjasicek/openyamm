#!/bin/bash
# scripts/codex_newhead.sh <run 1|2> (repo root): pass 7 new-head HD masters, brief references_newhead/CODEX_BRIEF.md.
# Run 1: 00_three_quarter only. Run 2: 01-04 with the selected 00 as an extra input.
P=level_generation/creatures/mm9_fre_claude; N=$P/references_newhead
if [ "$1" = 1 ]; then
  MSG="Follow the brief in $N/CODEX_BRIEF.md exactly. This is RUN 1: produce ONLY 00_three_quarter.png (the primary). The attached images are inputs 1-5 of the brief, in order. Use your built-in image generation tool and save as specified."
  EXTRA=""
else
  MSG="Follow the brief in $N/CODEX_BRIEF.md exactly. This is RUN 2: 00_three_quarter.png is FROZEN (do not regenerate it); produce 01_front.png, 02_back.png, 03_left.png and 04_right.png. The attached images are inputs 1-5 of the brief, in order, then input 6 = $N/00_three_quarter.png: the SAME person, hair, circlet, proportions and framing must appear in every view. Use your built-in image generation tool and save as specified, then write the contact sheet."
  EXTRA="-i $N/00_three_quarter.png"
fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec "$MSG" \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $N/codex_last_message_run$1.md -i $P/references_hd/mm9_head_views.png -i $P/references_head/01_front.png \
  -i $P/references_head/00_three_quarter.png -i $P/references_head/02_profile.png -i $P/references_head/03_back.png $EXTRA \
  < /dev/null > $N/codex_run$1.log 2>&1
