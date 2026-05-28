#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
cd "${repo_root}"

python_bin="${PYTHON:-python3}"
extracted_root="${MM9_EXTRACTED_ROOT:-mm9/extracted}"
world_root="${MM9_WORLD_ROOT:-assets_dev/worlds/mm9}"
editor_world_root="${MM9_EDITOR_WORLD_ROOT:-assets_editor_dev/worlds/mm9}"
scale="${MM9_SCALE:-2.56}"
run_skins=1
run_actors=1
run_collections=1
run_registry=1
run_rewrite=1
copy_editor=1
clean_outputs=1

usage() {
    cat <<'EOF'
usage: regenerate_mm9_models.sh [options]

Regenerates source-shaped MM9 model assets, runtime DTX skin copies, PNG previews,
model_registry.yml, and scene model_asset resolutions.

Options:
  --extracted-root PATH     Extracted MM9 REZ root. Default: mm9/extracted
  --world-root PATH         Development MM9 world root. Default: assets_dev/worlds/mm9
  --editor-world-root PATH  Editor MM9 world root. Default: assets_editor_dev/worlds/mm9
  --scale VALUE            LithTech-to-OpenYAMM coordinate scale. Default: 2.56
  --skip-skins             Skip shared SKINS/*.dtx copy and PNG preview generation.
  --skip-actors            Skip actor model conversion.
  --skip-collections       Skip non-actor model collection conversion.
  --skip-registry          Skip model_registry.yml generation.
  --skip-rewrite-scenes    Skip scene/model_assets model_asset rewrite.
  --no-clean               Do not delete generated models/skins/skin previews before regeneration.
  --no-editor-copy         Do not mirror models, skins, and maps into assets_editor_dev.
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
        --skip-skins)
            run_skins=0
            shift
            ;;
        --skip-actors)
            run_actors=0
            shift
            ;;
        --skip-collections)
            run_collections=0
            shift
            ;;
        --skip-registry)
            run_registry=0
            shift
            ;;
        --skip-rewrite-scenes)
            run_rewrite=0
            shift
            ;;
        --no-clean)
            clean_outputs=0
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

models_root="${extracted_root}/MODELS/MODELS"
skins_root="${extracted_root}/SKINS/SKINS"
data_root="${extracted_root}/DATA/DATA"
world_models_root="${world_root}/models"
world_skins_root="${world_root}/skins"
world_skins_preview_root="${world_root}/skins_preview"
world_maps_root="${world_root}/maps"

if [[ "${clean_outputs}" == 1 ]]
then
    cmake -E rm -rf "${world_models_root}" "${world_skins_root}" "${world_skins_preview_root}"
fi

if [[ "${run_skins}" == 1 ]]
then
    "${python_bin}" tools/mm9_import_discovery/convert_skin_library.py \
        --source-root "${skins_root}" \
        --output-root "${world_skins_root}" \
        --preview-root "${world_skins_preview_root}" \
        --report "${world_root}/import/skin_library_report.yml"
fi

if [[ "${run_actors}" == 1 ]]
then
    "${python_bin}" tools/mm9_import_discovery/batch_convert_actor_models.py \
        --table "${data_root}/ACTOR.txt" \
        --table "${data_root}/MONSTERS.txt" \
        --models-root "${models_root}" \
        --skins-root "${skins_root}" \
        --output-root "${world_models_root}" \
        --world-root "${world_root}" \
        --shared-skins-dir "${world_skins_root}" \
        --report "${world_models_root}/import/actor_batch_report.yml" \
        --scale "${scale}"
fi

if [[ "${run_collections}" == 1 ]]
then
    "${python_bin}" tools/mm9_import_discovery/batch_convert_model_collection.py \
        --models-root "${models_root}" \
        --skins-root "${skins_root}" \
        --map-root "${world_maps_root}" \
        --output-root "${world_models_root}" \
        --world-root "${world_root}" \
        --shared-skins-dir "${world_skins_root}" \
        --report "${world_models_root}/import/model_collection_batch_report.yml" \
        --scale "${scale}"
fi

if [[ "${run_registry}" == 1 ]]
then
    "${python_bin}" tools/mm9_import_discovery/generate_model_registry.py \
        --models-root "${world_models_root}" \
        --output "${world_models_root}/model_registry.yml"
fi

if [[ "${run_rewrite}" == 1 ]]
then
    "${python_bin}" tools/mm9_import_discovery/rewrite_scene_model_assets.py \
        --maps-root "${world_maps_root}" \
        --registry "${world_models_root}/model_registry.yml"
fi

if [[ "${copy_editor}" == 1 ]]
then
    mkdir -p "${editor_world_root}/models" "${editor_world_root}/skins" "${editor_world_root}/skins_preview" \
        "${editor_world_root}/maps"
    if [[ "${clean_outputs}" == 1 ]]
    then
        cmake -E rm -rf "${editor_world_root}/models" "${editor_world_root}/skins" \
            "${editor_world_root}/skins_preview"
        mkdir -p "${editor_world_root}/models" "${editor_world_root}/skins" "${editor_world_root}/skins_preview"
    fi
    if [[ -d "${world_models_root}" ]]
    then
        cp -a "${world_models_root}/." "${editor_world_root}/models/"
    fi
    if [[ -d "${world_skins_root}" ]]
    then
        cp -a "${world_skins_root}/." "${editor_world_root}/skins/"
    fi
    if [[ -d "${world_skins_preview_root}" ]]
    then
        cp -a "${world_skins_preview_root}/." "${editor_world_root}/skins_preview/"
    fi
    if [[ -d "${world_maps_root}" ]]
    then
        cp -a "${world_maps_root}/." "${editor_world_root}/maps/"
    fi
fi
