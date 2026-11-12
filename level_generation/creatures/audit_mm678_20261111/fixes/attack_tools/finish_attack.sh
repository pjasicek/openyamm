#!/usr/bin/env bash
# Install and check one attacks-stream model (MM6-MM8 audit fixes, 2026-11-11). From the repository root:
#   finish_attack.sh <project dir> <world> <stem> '<descriptor glob>' "<name>" <clips,checked> [binding key=value ...]
# Expects <project>/export/<stem>.glb and <project>/work/before_attacks/<stem>.glb. Steps: winding, glb_diff summary,
# motion audit compared with the audit's measurement, ratio and gates of the changed clips, install, bindings
# (anim_tools/binding_set.py), floor audit, the every-binding regression, the review viewer and its check.
# ALIAS='Attack=Cast' (env): viewer_alias.py gives the "before" models the new clip name as a copy of the old slot clip.
# Adapted from anim_tools/finish_model.sh (no gait audit: walks and runs are not touched). Output: <project>/review/finish.txt
set -uo pipefail
P=$1; W=$2; S=$3; GLOB=$4; NAME=$5; CLIPS=$6; shift 6
A=level_generation/creatures/audit_mm678_20261111
T=level_generation/creatures/claude_shared
AT=$A/fixes/attack_tools
NT=$A/fixes/anim_tools
OUT=$P/review/finish.txt
mkdir -p "$P/review"
{
echo "## winding"; python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$P/export/$S.glb" | tail -1
echo "## changed samplers (glb_diff)"
python3 level_generation/creatures/mm8_m480_texpass_claude/scripts/glb_diff.py "$P/work/before_attacks/$S.glb" \
    "$P/export/$S.glb" | tr ',' '\n' | awk '{print $1}' | sort | uniq -c
echo "## motion audit vs audit (changed clips)"
python3 $T/motion_audit.py "$P/export/$S.glb" --out "$P/audit_export" > /dev/null
python3 "$NT/cmp_audit.py" "$A/motion/$S.json" "$P/audit_export/$S.json"
echo "## ratio and gates"
python3 "$AT/ratio.py" "$P/export/$S.glb" "$CLIPS"
python3 "$AT/wrist_probe.py" "$P/export/$S.glb" "$CLIPS"
python3 level_generation/creatures/mm9_guard_claude/scripts/arm_hand_gate.py "$P/export/$S.glb" "$P/review/gate.json" \
    --side L=_L_ --side R=_R_ --clips "$CLIPS" 2>&1 | grep -v CHAINS
python3 $T/new_clip_measure.py "$P/export/$S.glb" "$CLIPS,Standing" 2>&1 | tail -n +1
echo "## install"; python3 tools/install_model.py "$P/export/$S.glb" --world "$W" 2>&1 | tail -1
if [ $# -gt 0 ]; then echo "## bindings"; python3 "$NT/binding_set.py" --world "$W" --model "$S.glb" "$@"; fi
echo "## floor"; python3 $T/floor/floor_audit.py --world "$W" --match "$GLOB" | tail -4
echo "## regression"
OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding ./build/game/openyamm --world mm6 \
    --headless-run-regression-suite actors 2>&1 | grep -E "descriptors|PASS|FAIL" | tail -2
echo "## viewer"
python3 "$NT/anim_viewer.py" --project "$P" --name "$NAME" --before "$P/work/before_attacks/$S.glb" \
    --after "assets_source/worlds/$W/models/$S.glb" --world "$W" --stem "$S"
if [ -n "${ALIAS:-}" ]; then python3 "$AT/viewer_alias.py" "$P/review/viewer" $ALIAS; fi
python3 tools/run_creature_review.py --project "$P" check 2>&1 | grep -A3 consoleErrors
} > "$OUT" 2>&1
cat "$OUT"
