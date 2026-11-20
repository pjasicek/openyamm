#!/bin/bash
# Written by portraits.py: one Codex image job, retried on transient Codex failures (model at capacity, rate limits,
# dropped connections), which parallel runs hit often. Run it in the background; it exits 0 once level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/raw_A.png exists.
cd /home/pjasicek/github/OpenYAMM || exit 1
for attempt in 1 2 3 4 5 6; do
  codex exec "Follow the brief in level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/brief_A.md exactly. The attached images are its inputs in order. Produce the sheet with your built-in image generation tool and save it as specified." -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images -o level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/codex_last_message_A.md -i level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/template_A.png level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/source_A.png level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/identity.png < /dev/null > level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/codex_run_A.log 2>&1
  [ -f level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/raw_A.png ] && exit 0
  if ! grep -qE "at capacity|Reconnecting|stream disconnected|error sending request|429|Too Many Requests|rate limit" level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/codex_run_A.log; then
    echo "Codex failed without output; see level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/codex_run_A.log"; exit 1
  fi
  cp level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/codex_run_A.log level_generation/ui/hud_inventory/mm9_pc_portraits/npc09/codex_run_A.log.retry_$attempt
  sleep $((60 * attempt))
done
echo "Codex still failing after 6 attempts"; exit 1
