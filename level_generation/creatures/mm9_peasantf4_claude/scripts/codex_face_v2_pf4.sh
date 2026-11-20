#!/bin/bash
# scripts/codex_face_v2_pf4.sh a|b (repo root): the v2 face repaint (warmer, relaxed eyes, lifted smile) for one woman
P=level_generation/creatures/mm9_peasantf4_claude; F=$P/references_face; V=$F/v2; t=$1
if [ "$t" = a ]; then IN=(-i $V/in_face_a.png -i $F/mm9_face_a_small.png -i $F/ref_portrait_a_small.png); EX='the original game render of woman A (smaller copy), the approved HD portrait of woman A (smaller copy)'; else IN=(-i $V/in_face_b.png -i $F/mm9_face_b_small.png); EX='the original game render of woman B (smaller copy)'; fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $V/CODEX_BRIEF.md for woman $t only and save $V/out_face_$t.png (1254x1254). The attached images are, in order: in_face_$t.png (the render to repaint), $EX. Produce the image with your built-in image generation tool." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $V/codex_last_message_$t.md "${IN[@]}" < /dev/null > $V/codex_run_$t.log 2>&1
