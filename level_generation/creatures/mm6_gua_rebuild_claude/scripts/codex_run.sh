#!/bin/bash
# Usage: scripts/codex_run.sh <dir under the project> <run name> <prompt> <image>...   (from the repository root)
P=level_generation/creatures/mm9_guard_claude; R=$P/$1; name=$2; prompt=$3; shift 3
args=(); for i in "$@"; do args+=(-i "$R/$i"); done
exec level_generation/creatures/claude_shared/codex_slot.sh codex exec "$prompt" \
  -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write \
  --add-dir "$HOME/.codex/generated_images" -o "$R/codex_last_message_$name.md" "${args[@]}" \
  < /dev/null > "$R/codex_$name.log" 2>&1
