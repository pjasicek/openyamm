#!/bin/bash
# scripts/codex_face.sh (repo root): the face repaint of both women in one Codex run (references_face/CODEX_BRIEF.md)
F=level_generation/creatures/mm9_peasantf1_claude/references_face; H=level_generation/creatures/mm9_peasantf1_claude/references_head
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $F/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $F/codex_last_message.md -i $F/in_face_b.png -i $H/b_01_front.png -i $F/mm9_face_b.png -i $F/in_face_a.png -i $H/a_01_front.png \
  -i $F/mm9_face_a.png < /dev/null > $F/codex_run.log 2>&1
