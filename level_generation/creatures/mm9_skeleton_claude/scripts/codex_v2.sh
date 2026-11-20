#!/usr/bin/env bash
set -u
P=level_generation/creatures/mm9_skeleton_claude; H=$P/references_hd; R=$H/v2
level_generation/creatures/claude_shared/codex_slot.sh codex exec "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the four images with your built-in image generation tool, one per clay view with that clay view as the edit base, and save them as specified." \
  -c model_reasoning_effort=medium -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $R/clay_01_front.png -i $R/clay_02_back.png -i $R/clay_03_left.png -i $R/clay_04_right.png -i $P/references_head/bust_front.png -i $H/mm9_torso_views_skel2.png -i $H/mm9_skin_x4.png \
  < /dev/null > $R/codex_run.log 2>&1
echo codex v2 exit $?
