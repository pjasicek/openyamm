#!/usr/bin/env bash
# Converts every isle prop ABC to a raw GLB (rigid, LOD 0, MM9 skin as PNG) in work/raw/<prop>/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
HERE="$ROOT/level_generation/props/mm9_isleofashes_claude"
PY="$HERE/work/venv/bin/python"
M="$ROOT/mm9/extracted/MODELS/MODELS"
S="$ROOT/mm9/extracted/SKINS/SKINS"
conv() { # id model skin...  (MODE=full for deforming models)
    local id="$1" model="$2"; shift 2
    local args=()
    local i=0
    for skin in "$@"; do args+=(--texture "$i=$skin"); i=$((i+1)); done
    (cd "$ROOT/tools/mm9_import_discovery" && "$PY" convert_abc_model.py "$model" "$HERE/work/raw/$id" --id "$id" \
        --export-mode "${MODE:-rigid}" "${args[@]}")
    # the native LODs of the model (LOD n -> work/raw/<id>/lod<n>/<id>.glb), while the converter accepts the index
    for lod in 1 2 3; do
        (cd "$ROOT/tools/mm9_import_discovery" && "$PY" convert_abc_model.py "$model" "$HERE/work/raw/$id/lod$lod" \
            --id "$id" --lod "$lod" --export-mode "${MODE:-rigid}" "${args[@]}" 2>/dev/null) || break
    done
}
conv skull "$M/GIBS/SKELETON/BIP01 HEAD.abc" "$S/SKELETON1.dtx"
conv shipwreck "$M/PROPS/VIKINGSHIP-WRECK.abc" "$S/PROPS/VIKINGSHIP.dtx"
conv vikingship "$M/PROPS/VIKINGSHIP.abc" "$S/PROPS/VIKINGSHIP.dtx"
MODE=full conv book "$M/PROPS/BOOK.abc" "$S/PROPS/BOOK.dtx"
conv podium "$M/PROPS/PODIUM03.abc" "$S/PROPS/PODIUM03.dtx"
conv statstone "$M/PROPS/STATSTONE.abc" "$S/PROPS/STATSTONERED.dtx"
conv stonedebris02 "$M/PROPS/DEBRIS/STONEDEBRIS02.abc" "$S/PROPS/DEBRIS/LUMBERSTONEDEBRIS.dtx"
conv stonedebris03 "$M/PROPS/DEBRIS/STONEDEBRIS03.abc" "$S/PROPS/DEBRIS/LUMBERSTONEDEBRIS.dtx"
conv logsburning "$M/PROPS/LOGSBURNING.abc" "$S/PROPS/LOGSBURNING.dtx"
conv cot "$M/PROPS/BED_COT.abc" "$S/PROPS/BED_COT.dtx"
conv stool "$M/PROPS/STOOL03.abc" "$S/PROPS/STOOL03.dtx"
conv coatrack "$M/PROPS/COATRACK1.abc" "$S/PROPS/COATRACK1.dtx"
conv dresser "$M/PROPS/DRESSER.abc" "$S/PROPS/DRESSERPLAIN.dtx"
conv roundtable "$M/PROPS/TABLEROUND4.abc" "$S/PROPS/TABLEROUND4.dtx"
conv well "$M/PROPS/WELL.abc" "$S/PROPS/WELL.dtx"
conv cookpot "$M/PROPS/COOKPOT.abc" "$S/PROPS/COOKPOT.dtx"
# Trees: reference only (heights for the tree mapping), not installed.
conv ref_tree05 "$M/PROPS/PLANTSANDTREES/TREE05.abc"
conv ref_tree06 "$M/PROPS/PLANTSANDTREES/TREE06.abc"
