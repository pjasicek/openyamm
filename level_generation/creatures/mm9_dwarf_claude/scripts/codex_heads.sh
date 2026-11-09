#!/bin/bash
# scripts/codex_heads.sh (repo root)
R=level_generation/creatures/mm9_dwarf_claude/references_head; H=level_generation/creatures/mm9_dwarf_claude/references_hd
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/CODEX_BRIEF_PAINT.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/codex_last_message_paint_a.md -i $R/clay_01_front.png -i $R/clay_03_left.png -i $R/clay_02_back.png -i $R/clay_04_right.png -i $R/clay_05_top.png -i $R/clay_06_q34r.png -i $R/clay_07_q34l.png -i $H/mm9_head_views.png -i $H/mm9_skin_x4.png -i $R/in_body_head.png < /dev/null > $R/codex_paint_a.log 2>&1
