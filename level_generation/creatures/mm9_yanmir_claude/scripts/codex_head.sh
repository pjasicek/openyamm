#!/bin/bash
# Head sculpt for the head-only Meshy model (repo root).
R=level_generation/creatures/mm9_yanmir_claude
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/references_head/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/references_head/codex_last_message.md -i $R/references_hd/mm9_head_views.png -i $R/references_head/in_body_head.png < /dev/null > $R/references_head/codex_run.log 2>&1
