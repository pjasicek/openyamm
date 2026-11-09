#!/usr/bin/env bash
# Candidate from work/ladder.blend -> export/mm6_wel.glb (LODs, shadow LODs, variant mappings) + viewer tiers.
# Usage: build_cand.sh Cand_62 r62
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
REA_CAND=$1 REA_NODE=Body blender -b -P scripts/export_cand.py 2>&1 | grep -E "EXPORTED|Error"
python3 scripts/swap_lod0.py "$ROOT/assets_source/worlds/mm6/models/mm6_wel.glb" work/cand_export.glb export/mm6_wel_lod0.glb Body
blender -b -P scripts/build_lods_ratios.py -- export/mm6_wel_lod0.glb export/mm6_wel_lods.glb Body 2>&1 | grep "LOD tri"
python3 ../mm6_med_claude/scripts/shrink_shadow_lods.py export/mm6_wel_lods.glb export/mm6_wel.glb > /dev/null
python3 scripts/carry_variants.py export/mm6_wel.glb
python3 scripts/viewer_variants.py export/mm6_wel.glb "$2" > /dev/null
