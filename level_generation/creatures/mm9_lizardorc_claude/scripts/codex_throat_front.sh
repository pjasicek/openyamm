#!/bin/bash
# run 2: Codex edit of the below view of the jaw underside and throat (references_head/throat/CODEX_BRIEF_THROAT_FRONT.md). Repo root.
R=level_generation/creatures/mm9_lizardorc_claude
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $R/references_head/throat/CODEX_BRIEF_THROAT_FRONT.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $R/references_head/throat/codex_last_message_front.md -i $R/references_head/throat/throat_front.png -i $R/references_head/throat/throat_front_overlay.png -i $R/references_hd/01_front_clean.png < /dev/null > $R/references_head/throat/codex_run_front.log 2>&1
