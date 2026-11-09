#!/usr/bin/env bash
# Build the pass GLB from the installed one, bake viewer skins and capture head/upper-body shots of the given skins.
# Usage (repository root): quick_view.sh <tag> <skin>...   e.g. quick_view.sh pass ba ab
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm7_m372_texpass_claude
T=$(awk '{print $3}' "$P/work/LEASE.txt")
tag=$1; shift
python3 "$P/scripts/apply_layout.py" "$P/work/before_texpass/mm7_m372.glb" "$P/work/uv_v2e.npz" "$P/textures/m372_final" \
    "$P/export/mm7_m372.glb" > /dev/null
python3 "$P/scripts/viewer_variants.py" "$P/export/mm7_m372.glb" "$tag" > /dev/null
python3 "$P/scripts/viewer_manifest.py" m372_aa_before before=installed "$tag=texture pass" > /dev/null
for k in "$@"; do
    python3 tools/run_creature_review.py --project "$P" --token "$T" --tier "m372_${k}_${tag}" shots \
        "${k}_${tag}_hf:Standing:0:front:head" "${k}_${tag}_hq:Standing:0:quarter:head" \
        "${k}_${tag}_ub:Standing:0:front:shoulders" | tail -1
done
