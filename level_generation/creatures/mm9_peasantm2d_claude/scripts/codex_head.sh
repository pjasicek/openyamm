#!/bin/bash
# Elf head turnaround for person D (repo root): PeasantM2's clean-shaven tier-B head views as edit targets.
P=level_generation/creatures/mm9_peasantm2d_claude
H=level_generation/creatures/mm9_peasantm2_claude/references_head
R=$P/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $P/references_head/CODEX_BRIEF.md exactly; write the outputs into $R/. The attached images are its inputs in order. Produce the four head images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message.md -i $P/references_hd/mm9_head_views_d.png -i $P/references_hd/mm9_skin_x4_d.png \
  -i $P/references_head/ear_shape_views.png -i $H/b_01_front.png -i $H/b_00_three_quarter.png -i $H/b_02_profile.png \
  -i $H/b_03_back.png < /dev/null > $R/codex_run.log 2>&1
