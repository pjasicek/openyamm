#!/usr/bin/env bash
# Install and check one attacks-2 re-animated attack (copy of anim_tools/finish_model.sh, before_attacks backup;
# MODEL_CASE=<substring> also runs that model's own actors-suite regression case).
#   finish_model.sh <project dir> <world> <stem> '<descriptor glob for floor/gait audits>' "<name>" [binding key=value ...]
# Expects <project>/export/<stem>.glb and <project>/work/before_attacks/<stem>.glb. Steps: winding, glb_diff summary,
# motion audit compared with the audit's measurement, install, bindings (binding_set.py), floor audit, gait audit
# (Standard and MAW), the every-binding regression, the review viewer and its check. Output: <project>/review/finish.txt
set -uo pipefail
P=$1; W=$2; S=$3; GLOB=$4; NAME=$5; shift 5
A=level_generation/creatures/audit_mm678_20261111
T=level_generation/creatures/claude_shared
TOOLS=$A/fixes/anim_tools
OUT=$P/review/finish.txt
mkdir -p "$P/review"
{
echo "## winding"; python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$P/export/$S.glb" | tail -1
echo "## changed samplers (glb_diff)"
python3 level_generation/creatures/mm8_m480_texpass_claude/scripts/glb_diff.py "$P/work/before_attacks/$S.glb" \
    "$P/export/$S.glb" | tr ',' '\n' | awk '{print $1}' | sort | uniq -c
echo "## motion audit vs audit (changed clips)"
python3 $T/motion_audit.py "$P/export/$S.glb" --out "$P/audit_export" > /dev/null
python3 "$TOOLS/cmp_audit.py" "$A/motion/$S.json" "$P/audit_export/$S.json"
echo "## install"; python3 tools/install_model.py "$P/export/$S.glb" --world "$W" 2>&1 | tail -1
if [ $# -gt 0 ]; then echo "## bindings"; python3 "$TOOLS/binding_set.py" --world "$W" --model "$S.glb" "$@"; fi
echo "## floor"; python3 $T/floor/floor_audit.py --world "$W" --match "$GLOB" | tail -4
echo "## gait standard"; python3 $T/postprocess/gait_audit.py --world "$W" --match "$GLOB" | tail -4
echo "## gait maw"; python3 $T/postprocess/gait_audit.py --world "$W" --match "$GLOB" --ruleset maw | tail -4
echo "## regression"
OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding ./build/game/openyamm --world mm6 \
    --headless-run-regression-suite actors 2>&1 | grep -E "descriptors|PASS|FAIL" | tail -2
if [ -n "${MODEL_CASE:-}" ]; then
    OPENYAMM_REGRESSION_FILTER=$MODEL_CASE ./build/game/openyamm --world mm6 --headless-run-regression-suite actors 2>&1 \
        | grep -E "PASS|FAIL|passed|failed" | tail -4
fi
echo "## viewer"
python3 "$TOOLS/anim_viewer.py" --project "$P" --name "$NAME" --before "$P/work/before_attacks/$S.glb" \
    --after "assets_source/worlds/$W/models/$S.glb" --world "$W" --stem "$S"
python3 tools/run_creature_review.py --project "$P" check 2>&1 | grep -A3 consoleErrors
} > "$OUT" 2>&1
cat "$OUT"
