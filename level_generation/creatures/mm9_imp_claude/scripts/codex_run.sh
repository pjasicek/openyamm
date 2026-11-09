#!/bin/bash
# Usage: codex_run.sh <run name> <prompt> <image>...   (run from the repository root)
P=level_generation/creatures/mm9_imp_claude/references_hd
name=$1; prompt=$2; shift 2
args=(); for i in "$@"; do args+=(-i "$i"); done
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec "$prompt" \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write \
  --add-dir "$HOME/.codex/generated_images" -o "$P/codex_last_message_$name.md" "${args[@]}" \
  < /dev/null > "$P/codex_$name.log" 2>&1
