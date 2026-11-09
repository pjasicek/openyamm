#!/bin/bash
# Written by portraits.py: one Codex image job, retried on transient Codex failures (model at capacity, rate limits,
# dropped connections), which parallel runs hit often. Run it in the background; it exits 0 once level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/raw.png exists.
cd /home/pjasicek/github/OpenYAMM || exit 1
for attempt in 1 2 3 4 5 6; do
  codex exec "Follow the brief in level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/CODEX_BRIEF.md exactly. The attached images are its inputs in order. Produce the image with your built-in image generation tool and save it as specified." -c model_reasoning_effort=medium -C /home/pjasicek/github/OpenYAMM -s workspace-write --add-dir ~/.codex/generated_images -o level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/codex_last_message.md -i level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/template.png level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/consensus_05.png level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/consensus_12.png level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/consensus_22.png level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/consensus_39.png level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/raw_A.png level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/raw_B.png < /dev/null > level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/codex_run.log 2>&1
  [ -f level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/raw.png ] && exit 0
  if ! grep -qE "at capacity|Reconnecting|stream disconnected|error sending request|429|Too Many Requests|rate limit" level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/codex_run.log; then
    echo "Codex failed without output; see level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/codex_run.log"; exit 1
  fi
  cp level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/codex_run.log level_generation/ui/hud_inventory/mm9_pc_portraits/pc12/repair_05_12_22_39/codex_run.log.retry_$attempt
  sleep $((60 * attempt))
done
echo "Codex still failing after 6 attempts"; exit 1
