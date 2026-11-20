#!/bin/bash
# Step 6. Tables from the game data through the harness: class skill caps and HP/SP per level (caps.yml: the final
# classes; caps2.yml: the base and first-promotion classes the class ladder uses) and the monster table with attacks,
# spells and resistances (monsters.json, for the real-group fights).
set -e
P="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$P/../../../.." && pwd)"
S="${SOLO_SIM_DIR:-$REPO/output/maw_solo_sim}"
cd "$S"
SOLO_SPEC="$P/caps.yml" ./solo_harness --test-case="solo caps" | grep -E "^CAPS|^HPSP" > caps.txt
SOLO_SPEC="$P/caps2.yml" ./solo_harness --test-case="solo caps" | grep -E "^CAPS|^HPSP" > caps2.txt
MON_OUT="$S/monsters.json" ./solo_harness --test-case="solo monsters" > /dev/null
wc -l caps.txt caps2.txt monsters.json
