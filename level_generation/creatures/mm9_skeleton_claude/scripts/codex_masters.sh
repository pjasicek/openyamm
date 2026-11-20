#!/usr/bin/env bash
# Codex HD masters. Usage: scripts/codex_masters.sh 1|2 (from the repo root)
set -u
P=level_generation/creatures/mm9_skeleton_claude; R=$P/references_hd; run=$1
msg1="Follow the brief in $R/CODEX_BRIEF.md exactly, RUN 1 ONLY: generate 00_three_quarter.png, then stop. The attached images are its inputs in order. Use your built-in image generation tool and save as specified."
msg2="Follow the brief in $R/CODEX_BRIEF.md exactly, RUN 2: generate 01_front.png, 02_back.png, 03_left.png and 04_right.png with the attached selected 00_three_quarter.png (input 5) as the same figure. The attached images are its inputs in order. Use your built-in image generation tool and save as specified."
extra=(); msg="$msg1"; if [ "$run" = 2 ]; then extra=(-i $R/00_three_quarter.png); msg="$msg2"; fi
level_generation/creatures/claude_shared/codex_slot.sh codex exec "$msg" \
  -c model_reasoning_effort=medium -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_run$run.md -i $R/mm9_views_skel2.png -i $R/mm9_head_views_skel2.png -i $R/mm9_torso_views_skel2.png -i $R/mm9_skin_x4.png "${extra[@]}" \
  < /dev/null > $R/codex_run$run.log 2>&1
echo codex run $run exit $?
