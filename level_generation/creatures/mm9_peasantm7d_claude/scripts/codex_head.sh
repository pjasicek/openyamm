#!/bin/bash
# Elf head turnarounds (repo root). Usage: scripts/codex_head.sh d|c
P=level_generation/creatures/mm9_peasantm7d_claude
H=level_generation/creatures/mm9_peasantm7_claude/references_head
t=$1
if [ "$t" = d ]; then R=$P/references_head; else R=$P/references_head_c; fi
mkdir -p $R
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/references_head/CODEX_BRIEF.md exactly, for person $(echo $t | tr a-z A-Z); write the outputs into $R/. The attached images are its inputs in order. Produce the four head images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $P/references_hd/mm9_head_views_$t.png -i $P/references_hd/mm9_skin_x4_$t.png \
  -i $P/references_head/ear_shape_views.png -i $H/01_front.png -i $H/00_three_quarter.png -i $H/02_profile.png \
  -i $H/03_back.png < /dev/null > $R/codex_run.log 2>&1
