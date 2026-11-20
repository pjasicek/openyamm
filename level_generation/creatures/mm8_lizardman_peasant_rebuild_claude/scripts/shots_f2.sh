#!/usr/bin/env bash
# Follow-up 2 viewer shots: fixed cameras (glTF metres), tiers given as $1 (comma list), into $2.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"; P=level_generation/creatures/$(basename "$here")
Q=-1.9,1.3,2.6:0,0.85,0.1; F=0,1.0,3.2:0,0.85,0; S=-3.2,1.0,0.3:0,0.85,0.1
SPECS="stand_front:Standing:0:front:body:$F stand_quarter:Standing:2.0:front:body:$Q stand_side:Standing:1.0:front:body:$S
walk_a:Walk:0.0:front:body:$S walk_b:Walk:0.26:front:body:$S walk_q:Walk:0.5:front:body:$Q
run_a:Run:0.0:front:body:$S run_b:Run:0.2:front:body:$S sprint:Sprint:0.15:front:body:$S
fidget_a:Fidget:0.15:front:body:$Q fidget_b:Fidget:0.35:front:body:$Q
attack_a:Attack:0.15:front:body:$Q attack_b:Attack:0.3:front:body:$Q attack_c:Attack:0.45:front:body:$Q attack_s:Attack:0.3:front:body:$S
hit_a:Hit:0.15:front:body:$Q hit_b:Hit:0.3:front:body:$Q death_a:Death:0.3:front:body:$Q death_b:Death:0.55:front:body:$Q
corpse:Corpse:0:front:body:1.07,1.59,1.91:-0.03,0.12,0.07
hands:Standing:0:front:body:0,0.9,1.5:0,0.8,0 hands_q:Standing:0:front:body:-1.0,0.95,1.1:0,0.8,0"
mkdir -p "$2"
[[ -n "${SKIP:-}" ]] && SPECS=$(tr ' ' '\n' <<<"$SPECS" | grep -vE "$SKIP" | tr '\n' ' ')
python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P "$2" "$1" $SPECS | tail -3
