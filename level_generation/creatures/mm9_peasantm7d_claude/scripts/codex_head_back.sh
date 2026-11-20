#!/bin/bash
# Resume of codex_head.sh d (the first run stopped at "model at capacity" after 01/00/02): the back view only. Repo root.
P=level_generation/creatures/mm9_peasantm7d_claude
H=level_generation/creatures/mm9_peasantm7_claude/references_head
R=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/references_head/CODEX_BRIEF.md exactly, for person D, but generate ONLY the missing view 03_back.png (01, 00 and 02 are already selected in $R/; do not change them) and then write generation_runs.json and selected_views_review.png for all four. The attached images are the brief's inputs 1-7 in order, then the selected 01_front.png of person D as the identity input. Save into $R/." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $P/references_hd/mm9_head_views_d.png -i $P/references_hd/mm9_skin_x4_d.png \
  -i $P/references_head/ear_shape_views.png -i $H/01_front.png -i $H/00_three_quarter.png -i $H/02_profile.png \
  -i $H/03_back.png -i $R/01_front.png < /dev/null > $R/codex_run_back.log 2>&1
