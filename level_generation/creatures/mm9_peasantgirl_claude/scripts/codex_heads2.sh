#!/bin/bash
# scripts/codex_heads2.sh (repo root): paint-over face masters of the current head, three girls
P=level_generation/creatures/mm9_peasantgirl_claude; H=$P/references_head2
in=()
for t in g2 g3 g1e; do for v in front q34l right; do in+=(-i $H/cur_pg_${t}_${v}.png); done; done
for t in g2 g3 g1e; do in+=(-i $P/references_head/${t}_01_front.png); done
for t in g2 g3 g1e; do in+=(-i $P/references_hd/mm9_head_views_${t}.png); done
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec \
  "Follow the brief in $H/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the images with your built-in image generation tool and save them as specified." \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images \
  -o $H/codex_last_message.md "${in[@]}" < /dev/null > $H/codex_run.log 2>&1
