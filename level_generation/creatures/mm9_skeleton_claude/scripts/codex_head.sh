#!/usr/bin/env bash
# Codex skull and bust views (from the repo root)
set -u
P=level_generation/creatures/mm9_skeleton_claude; H=$P/references_hd; R=$P/references_head
level_generation/creatures/claude_shared/codex_slot.sh codex exec "Follow the brief in $R/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the five images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $H/01_front.png -i $H/00_three_quarter.png -i $H/03_left.png -i $H/02_back.png -i $H/mm9_head_views_skel2.png \
  < /dev/null > $R/codex_run.log 2>&1
echo codex head exit $?
