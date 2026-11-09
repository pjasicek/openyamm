#!/bin/bash
P=level_generation/creatures/mm9_peasantdm3_claude; O=$P/references_head
mkdir -p $O/profile_fix/raw
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $O/profile_fix/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $O/profile_fix/codex_last_message.md -i $O/silhouette/sil_left_white.png -i $O/01_front.png -i $O/02_profile.png \
  -i $O/profile_fix_input_overlay.png < /dev/null > $O/profile_fix/codex_run.log 2>&1
