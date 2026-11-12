#!/usr/bin/env bash
# Follow-up m190 (2026-11-11): spine-chain/beard reweight plus a stronger Hit. From the repository root:
#   level_generation/creatures/mm7_m190_animfix_claude/scripts/build_followup.sh
# Hit source: work/before_hit/mm7_m190.glb (the full humanoid-set Hit, before the anim stream's x0.3), the only clip
# that differs from the installed work/before_followup/mm7_m190.glb. Steps: every joint of Hit x0.7 toward its first
# frame (rotations and translations), then B_Spine/B_Spine1/B_Spine2 and both clavicles x0.6 more (0.42 in all: their
# 27 deg flex and 30-39 deg shrug stretch this 23 cm deep back), feet raised where Hit dips, then reweight_trunk.py.
set -euo pipefail
P=level_generation/creatures/mm7_m190_animfix_claude
T=level_generation/creatures/audit_mm678_20261111/fixes/anim_tools
W=$P/work/build
mkdir -p "$W" "$P/export"
python3 $T/scale_keys.py $P/work/before_hit/mm7_m190.glb $W/hit_a.glb --clip Hit --joints '*' --factor 0.7 --ref Hit \
    --translation-joints '*' --translation-factor 0.7
python3 $T/scale_keys.py $W/hit_a.glb $W/hit_b.glb --clip Hit --joints 'B_Spine,B_Spine1,B_Spine2,B_L_Clavicle,B_R_Clavicle' \
    --factor 0.6 --ref Hit
python3 level_generation/creatures/claude_shared/floor/floor_fix.py $W/hit_b.glb $W/hit_c.glb --raise Hit
python3 $P/scripts/reweight_trunk.py $W/hit_c.glb $P/export/mm7_m190.glb --labels $P/work/labels.npz
