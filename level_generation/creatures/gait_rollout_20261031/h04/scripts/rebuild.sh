#!/usr/bin/env bash
# Rebuild the package h04 exports from the pre-gait copies in work/ (the sources as installed before this package,
# 2026-10-31) and run the gates. The Mixamo rigs (pfem, pmn2) are composed on a B_-renamed copy and renamed back.
#   scripts/rebuild.sh [model ...]     (default: pman_v2 fmp pfem pmn2 mep)
# Install afterwards: python3 tools/install_model.py <export> --world mm6 --name mm6_<m>.glb (from the repo root).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
models=("$@")
[[ ${#models[@]} -eq 0 ]] && models=(pman_v2 fmp pfem pmn2 mep)
for m in "${models[@]}"; do
    pre="work/mm6_${m}_pre_gait.glb"
    case $m in
        pman_v2) jobs=(jobs/pman_v2_jog.json); sets=(--set run=Jog --set run_stride_length=2.03);
                 old=Walking; new=Jog; scale=104.502737; node=- ;;
        fmp)     jobs=(jobs/fmp_jog.json); sets=(--set run=Jog --set run_stride_length=1.6);
                 old=Walking,Run; new=Jog; scale=105.656395358897; node=- ;;
        pfem)    jobs=(jobs/pfem_jog.json); sets=(--set run=Jog --set run_stride_length=1.54);
                 old=Walking; new=Jog; scale=111.6; node=- ;;
        pmn2)    jobs=(jobs/pmn2_jog.json); sets=(--set run=Jog --set run_stride_length=1.87);
                 old=Walking,Running; new=Jog; scale=105.8; node=Staff ;;
        mep)     jobs=(jobs/mep_walk2.json jobs/mep_jog.json jobs/mep_sprint.json);
                 sets=(--set walking=Walk2 --set stride_length=1.374 --set run=Jog --set run_stride_length=2.205
                       --set sprint=Sprint --set sprint_stride_length=4.098);
                 old=Walking,Running; new=Walk2,Jog,Sprint; scale=103.127492; node=Staff ;;
        *) echo "unknown model $m"; exit 1 ;;
    esac
    if [[ $m == pfem || $m == pmn2 ]]; then
        python3 scripts/rename_mixamo.py "$pre" "work/mm6_${m}_pre_gait_B.glb" to_b > /dev/null
        python3 scripts/compose_gait.py "work/mm6_${m}_pre_gait_B.glb" "work/mm6_${m}_jog_B.glb" "${jobs[@]}" \
            > "work/${m}_compose.log"
        python3 scripts/rename_mixamo.py "work/mm6_${m}_jog_B.glb" "export/mm6_${m}.glb" from_b > /dev/null
        cp "work/mm6_${m}_jog_B.compose.json" "review/mm6_${m}.compose.json"
    else
        python3 scripts/compose_gait.py "$pre" "export/mm6_${m}.glb" "${jobs[@]}" > "work/${m}_compose.log"
        cp "export/mm6_${m}.compose.json" "review/mm6_${m}.compose.json"
    fi
    bash scripts/gates.sh "$m" "$node" "$old" "$new" "$scale" "${sets[@]}"
done
