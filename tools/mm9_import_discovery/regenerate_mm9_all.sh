#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

extracted_root="${MM9_EXTRACTED_ROOT:-mm9/extracted}"
world_root="${MM9_WORLD_ROOT:-assets_dev/worlds/mm9}"
editor_world_root="${MM9_EDITOR_WORLD_ROOT:-assets_editor_dev/worlds/mm9}"
scale="${MM9_SCALE:-2.56}"
map_mode="curated"
copy_editor=1
compile_indoor=1

usage() {
    cat <<'EOF'
usage: regenerate_mm9_all.sh [options]

Runs the MM9 static asset, map, and model regeneration wrappers in order.

Options:
  --extracted-root PATH     Extracted MM9 REZ root. Default: mm9/extracted
  --world-root PATH         Development MM9 world root. Default: assets_dev/worlds/mm9
  --editor-world-root PATH  Editor MM9 world root. Default: assets_editor_dev/worlds/mm9
  --scale VALUE            LithTech-to-OpenYAMM coordinate scale. Default: 2.56
  --map-mode MODE          curated, all-odm, or all-blv. Default: curated
  --no-compile             Do not compile indoor source GLBs into BLV files.
  --no-editor-copy         Do not mirror outputs into assets_editor_dev.
EOF
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        --extracted-root)
            extracted_root="$2"
            shift 2
            ;;
        --world-root)
            world_root="$2"
            shift 2
            ;;
        --editor-world-root)
            editor_world_root="$2"
            shift 2
            ;;
        --scale)
            scale="$2"
            shift 2
            ;;
        --map-mode)
            map_mode="$2"
            shift 2
            ;;
        --no-compile)
            compile_indoor=0
            shift
            ;;
        --no-editor-copy)
            copy_editor=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

common_args=(
    --extracted-root "${extracted_root}"
    --world-root "${world_root}"
)

map_args=(
    "${common_args[@]}"
    --editor-world-root "${editor_world_root}"
    --scale "${scale}"
)
model_args=(
    "${common_args[@]}"
    --editor-world-root "${editor_world_root}"
    --scale "${scale}"
)
static_args=("${common_args[@]}")

case "${map_mode}" in
    curated)
        ;;
    all-odm)
        map_args+=(--all-odm)
        ;;
    all-blv)
        map_args+=(--all-blv)
        ;;
    *)
        echo "invalid --map-mode: ${map_mode}" >&2
        exit 2
        ;;
esac

if [[ "${compile_indoor}" != 1 ]]
then
    map_args+=(--no-compile)
fi

if [[ "${copy_editor}" != 1 ]]
then
    map_args+=(--no-editor-copy)
    model_args+=(--no-editor-copy)
else
    static_args+=(--add-world-root "${editor_world_root}")
fi

"${script_dir}/regenerate_mm9_static_assets.sh" "${static_args[@]}"
"${script_dir}/regenerate_mm9_maps.sh" "${map_args[@]}"
"${script_dir}/regenerate_mm9_models.sh" "${model_args[@]}"
