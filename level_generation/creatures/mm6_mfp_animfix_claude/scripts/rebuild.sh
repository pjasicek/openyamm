#!/usr/bin/env bash
# Rebuild the package h05 exports from the pre-gait copies in work/ (the sources as installed before this package,
# assets_source commit d285bdd, 2026-10-31; also the rollback) and run the gates (scripts/gates.sh).
#   scripts/rebuild.sh [model ...]     (default: natm mer1 mfp natf nobl)
# Install afterwards: python3 tools/install_model.py <export> --world mm6 --name mm6_<m>.glb (from the repo root).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
models=("$@")
[[ ${#models[@]} -eq 0 ]] && models=(natm mer1 mfp natf nobl)
for m in "${models[@]}"; do
    case $m in
        natm) jobs=(walk2 jog sprint); scale=107.0; props=Spear=mm6_natm_spear.glb,Buckler=mm6_natm_buckler.glb
              sets=(--set walking=Walk2 --set stride_length=1.80 --set run=Jog --set run_stride_length=2.9
                    --set sprint=Sprint --set sprint_stride_length=4.11) ;;
        mer1) jobs=(jog); scale=107; props=Club=mm6_mer1_club.glb
              sets=(--set run=Jog --set run_stride_length=1.88) ;;
        mfp)  jobs=(walk2 jog sprint); scale=107.5; props=Knife=mm6_mfp_knife.glb
              sets=(--set walking=Walk2 --set stride_length=1.6 --set run=Jog --set run_stride_length=2.41
                    --set sprint=Sprint --set sprint_stride_length=3.41) ;;
        natf) jobs=(walk2 jog sprint); scale=107.9; props=ForearmBlade=mm6_natf_blade.glb,LeafShield=mm6_natf_shield.glb
              sets=(--set walking=Walk2 --set stride_length=1.8 --set run=Jog --set run_stride_length=2.85
                    --set sprint=Sprint --set sprint_stride_length=4.11) ;;
        nobl) jobs=(walk2 jog sprint); scale=109.874; props=Sword=mm6_nobl_sword.glb
              sets=(--set walking=Walk2 --set stride_length=1.75 --set run=Jog --set run_stride_length=2.8
                    --set sprint=Sprint --set sprint_stride_length=4.1) ;;
        *) echo "unknown model $m"; exit 1 ;;
    esac
    files=(); new=()
    for j in "${jobs[@]}"; do
        files+=("jobs/${m}_$j.json")
        case $j in walk2) new+=(Walk2) ;; jog) new+=(Jog) ;; sprint) new+=(Sprint) ;; esac
    done
    python3 scripts/compose_gait.py "work/mm6_${m}_pre_gait.glb" "export/mm6_$m.glb" "${files[@]}" > "work/${m}_compose.log"
    cp "export/mm6_$m.compose.json" "review/mm6_$m.compose.json"
    new_csv=$(IFS=,; echo "${new[*]}")
    bash scripts/gates.sh "$m" Walking,Running "$new_csv" "$scale" "$props" "${sets[@]}"
done
