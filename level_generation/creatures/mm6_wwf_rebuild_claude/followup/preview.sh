#!/usr/bin/env bash
# preview.sh <basecolor png> <tag> [shots...]: patch the pre-follow-up GLB's base colour, viewer GLBs per tier, shots of tier A
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
png=$(realpath "$1"); tag=$2; shift 2; out=${OUT:-$here/review/followup/shots}
cd "$here"; mkdir -p "$out"
python3 followup/patch_image.py work/before_followup/mm6_wwf.glb work/prev_$tag.glb wwf_basecolor=$png >/dev/null
python3 scripts/viewer_variants.py work/prev_$tag.glb $tag >/dev/null
python3 followup/viewer_manifest.py work/before_followup/mm6_wwf.glb $tag cur >/dev/null
cd "$repo"; P=level_generation/creatures/$(basename "$here")
python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P "$out" ${TIERS:-wwf_a_$tag} $(python3 $P/scripts/shot_specs.py "$@") | tail -1
