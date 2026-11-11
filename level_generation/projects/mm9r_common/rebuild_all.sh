#!/usr/bin/env bash
# Rebuild MM9 maps into their review roots, as the final rebuild did (devdocs/mm9_rework/FINAL_REBUILD_WORK.md R1):
# per map convert.py, then its lighting base (dungeon/lighting.py --layout-only) and MM9's lightmaps over it
# (lightmap_transfer.py --install). The twelve open-air maps (the regions, Afterworld, Boot Camp) build into
# output/mm9_rework/isleofashes_blv_root, the rest into output/mm9_rework/assets_dev. Up to JOBS maps at once, each
# through lane.sh's map lock and slots; one log per map in LOGS; promote into assets_dev afterwards
# (output/mm9_rework/promotion_*/promote.py).
#
#   level_generation/projects/mm9r_common/rebuild_all.sh LOGS [stem ...]     (default: all 44 maps)
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../../.." && pwd)"
logs="${1:?usage: rebuild_all.sh LOGS [stem ...]}"
shift
mkdir -p "$logs"
B_MAPS="afterworld lindisfarne thronheim frosgard bootcamp mountainpass guberland drangheim thjorgard sturmford isleofashes yorwick"
A_MAPS="1000terrors anskramkeep arslegardcity bathhouse beethoven chasmofthedead connectingtunnels darkpassageway
dookscastle dragonstadium drangheimcity drangheimprison dungeonofsecrets frosgardcity guberlandcity hallofthegods
inventastorca klusoshouse lichlab lindisfarnemonastery ruinedtemple sturmfordcity tasaracademy templeofhonk thearena
thjoradmine thjorgardcity thronheimcity traininghall verhoffinruins wizardslab yanmirsfort"
stems=("$@")
if [ ${#stems[@]} -eq 0 ]; then
    read -r -a stems <<< "$(echo $A_MAPS $B_MAPS)"
fi

one() {
    local stem="$1" project root_args=()
    if [[ " $B_MAPS " == *" $stem "* ]]; then
        project="level_generation/projects/mm9r_${stem}_blv"
        root_args=(--root "$repo/output/mm9_rework/isleofashes_blv_root")
    else
        project="level_generation/projects/mm9r_${stem}"
    fi
    local log="$logs/$stem.log"
    local started=$SECONDS
    {
        echo "== $stem ($project) $(date +%T)"
        python3 "$project/convert.py" &&
            python3 level_generation/projects/mm9r_common/dungeon/lighting.py "$project" --layout-only "${root_args[@]}" &&
            python3 level_generation/projects/mm9r_common/lightmap_transfer.py "$project" --install "${root_args[@]}"
    } > "$log" 2>&1
    local status=$?
    echo "$stem $([ $status -eq 0 ] && echo ok || echo FAILED) $((SECONDS - started))s" | tee -a "$logs/summary.txt"
    return $status
}
export -f one
export repo logs B_MAPS

cd "$repo"
: > "$logs/summary.txt"
printf '%s\n' "${stems[@]}" | xargs -P "${JOBS:-6}" -I{} \
    "$here/lane.sh" map {} bash -c 'one "$1"' _ {}
echo "done: $(grep -c ' ok ' "$logs/summary.txt") ok, $(grep -c FAILED "$logs/summary.txt") failed"
