#!/bin/bash
# scripts/codex_heads_v2.sh (repo root): head turnaround v2 (coif, soft creases, gentle smile) in one Codex run, 2026-11-04
R=level_generation/creatures/mm9_wyrdold_claude/references_hd; O=level_generation/creatures/mm9_wyrdold_claude/references_head
H=level_generation/creatures/mm9_wyrdold_claude/references_head_v2
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message.md -i $O/01_front.png -i $O/00_three_quarter.png -i $O/02_profile.png -i $O/03_back.png \
  -i $R/mm9_head_views.png < /dev/null > $H/codex_run.log 2>&1
