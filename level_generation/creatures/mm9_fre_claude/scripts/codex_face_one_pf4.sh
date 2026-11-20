#!/bin/bash
# scripts/codex_face_one_pf4.sh a|b (repo root): one woman's face repaint per Codex run (smaller requests; the joint run kept reconnecting)
P=level_generation/creatures/mm9_peasantf4_claude; F=$P/references_face; t=$1
if [ "$t" = a ]; then IN=(-i $F/in_face_a.png -i $F/ref_portrait_a_small.png -i $F/mm9_face_a_small.png); else IN=(-i $F/in_face_b.png -i $F/mm9_face_b_small.png); fi
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $F/CODEX_BRIEF.md, but produce ONLY out_face_$t.png (woman $t) in this run. The attached images are, in order: in_face_$t.png (the render to fix)$( [ $t = a ] && echo ', the approved HD portrait of woman A (smaller copy), the original game render of woman A (smaller copy)' || echo ', the original game render of woman B (smaller copy)'). Produce the image with your built-in image generation tool and save it as specified, 1254x1254." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $F/codex_last_message_$t.md "${IN[@]}" < /dev/null > $F/codex_run_$t.log 2>&1
