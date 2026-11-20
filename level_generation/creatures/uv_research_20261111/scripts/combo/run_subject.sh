#!/usr/bin/env bash
# Combined-layout study (uv_research_20261111/combo, 2026-11-11): one subject through
#   export (the seam trial's prepared mesh) -> PartUV with the skin-weight part tree (licence-clean, no PartField)
#   -> variants:  p0_t<thr>  PartUV charts as they are (merge_below=0, no seam pass)
#                 p1_t<thr>  PartUV charts + small-chart merge (max_stretch 1.25) + seam pass (6 rounds, p90 <= 1.25)
#   -> unpacked charts (packer=none) -> sparrow (4-texel gap, one scale, 5 x 60 s) -> upload + measurement GLB
#   -> texture_quality.py.
# The xatlas -> seam pass -> sparrow variant is layout/winners/ (made with the same scripts and settings).
#
#   CREATURE_3D_TOKEN=<lease token> scripts/combo/run_subject.sh <subject> <stage> <src> <trial args...>
# stage: export | partuv | unwrap | sparrow | apply | pack (= sparrow + apply) | all.  Runs from the repository root.
set -euo pipefail
cd /home/pjasicek/github/OpenYAMM
U=level_generation/creatures/uv_research_20261111
SUBJ="$1"; STAGE="$2"; SRC="$3"; shift 3
ARGS=("$@")
OUT="$U/combo/$SUBJ"
mkdir -p "$OUT"
SP="$U/../claude_shared/sparrow_venv"
P0="${P0_THRESHOLDS:-1.1 1.25 1.5}"
P1="${P1_THRESHOLDS:-1.1 1.25}"

blender() {   # <name> <script> <args...>: lease-checked Blender, log kept next to the outputs; waits while another
    # operation of this lease (a Meshy call, another Blender run) holds the write lock
    local name="$1" script="$2"; shift 2
    local out log
    for attempt in $(seq 1 60); do
        if out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$script" "$@" 2>&1); then
            cp "$(echo "$out" | sed -n 's/^Blender log: //p')" "$OUT/$name.log"
            return 0
        fi
        log="$(echo "$out" | sed -n 's/^Blender log: //p')"
        if grep -q "Another creature operation is running" "$log" 2>/dev/null; then
            sleep 10
            continue
        fi
        echo "$out"; cp "$log" "$OUT/$name.log" 2>/dev/null; return 1
    done
    return 1
}

variants() {
    for t in $P0; do echo "p0_t$t"; done
    for t in $P1; do echo "p1_t$t"; done
}

if [[ $STAGE == export || $STAGE == all ]]; then
    blender prep "$U/scripts/layout/uv_seam_trial.py" "$SRC" "$OUT" prep mode=export "${ARGS[@]}"
    grep EXPORTED "$OUT/prep.log"
fi
if [[ $STAGE == partuv || $STAGE == all ]]; then
    # python -I from an unrelated directory against the installed partuv wheel (as partuv/RESULTS.md)
    ( cd "$U/partuv/weights" && "$PWD/../venv/bin/python" -I "/home/pjasicek/github/OpenYAMM/$U/scripts/partuv_run.py" \
        "/home/pjasicek/github/OpenYAMM/$OUT/prep_mesh.npz" "/home/pjasicek/github/OpenYAMM/$OUT/partuv" bones \
        $(echo $P0 $P1 | tr ' ' '\n' | sort -u) ) > "$OUT/partuv.log" 2>&1
    grep PARTUV "$OUT/partuv.log"
fi
if [[ $STAGE == unwrap || $STAGE == all ]]; then
    for t in $P0; do
        blender "p0_t$t" "$U/scripts/layout/uv_seam_trial.py" "$SRC" "$OUT" "p0_t$t" "${ARGS[@]}" \
            "charts_npz=$OUT/partuv/partuv_t$t.npz" merge_below=0 packer=none
    done
    for t in $P1; do
        blender "p1_t$t" "$U/scripts/layout/uv_seam_trial.py" "$SRC" "$OUT" "p1_t$t" "${ARGS[@]}" \
            "charts_npz=$OUT/partuv/partuv_t$t.npz" max_stretch=1.25 seam_rounds=6 seam_stretch=1.25 packer=none
    done
fi
if [[ $STAGE == pack || $STAGE == sparrow || $STAGE == all ]]; then
    pack_one() {
        local v="$1"
        "$SP/py/bin/python" "$U/scripts/layout/faces2layout.py" "$OUT/${v}_faces.npz" "$OUT/${v}_layout.npz"
        "$SP/py/bin/python" "$U/scripts/layout/sparrow_pack.py" "$OUT/${v}_layout.npz" "$OUT/${v}_sparrow.npz" \
            --sep 4 --rotation continuous --seconds 60 --runs 5 --fill 0.66 > "$OUT/sparrow_${v}.log" 2>&1
    }
    # two sparrow runs at a time, as layout/pack/queue.sh did for the winners
    vs=($(variants))
    for ((i = 0; i < ${#vs[@]}; i += 2)); do
        pack_one "${vs[i]}" &
        if ((i + 1 < ${#vs[@]})); then pack_one "${vs[i + 1]}" & fi
        wait
    done
fi
if [[ $STAGE == pack || $STAGE == apply || $STAGE == all ]]; then
    vs=($(variants))
    mkdir -p "$OUT/final"
    for v in "${vs[@]}"; do
        blender "apply_$v" "$U/scripts/layout/apply_layout.py" "$OUT/$v.blend" "$OUT/${v}_sparrow.npz" "$OUT/final" "$v"
        # the exporter drops the material on imported installed creatures: placeholder material as layout/ did
        "$SP/py/bin/python" "$U/scripts/layout/glb_add_material.py" "$OUT/final/${v}_measure.glb" "$OUT/final/${v}_measure.glb"
        python3 "$U/../claude_shared/texture_quality.py" "$OUT/final/${v}_measure.glb" --by-bone \
            --heatmap "$OUT/final/${v}_heat" --json "$OUT/final/${v}_quality.json" > "$OUT/final/${v}_quality.log" 2>&1
        tail -1 "$OUT/sparrow_${v}.log"
    done
fi
echo "DONE $SUBJ $STAGE"
