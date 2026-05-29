#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
cd "${repo_root}"

python_bin="${PYTHON:-python3}"
extracted_root="${MM9_EXTRACTED_ROOT:-mm9/extracted}"
dat_root="${MM9_WORLD_DAT_ROOT:-${extracted_root}/WORLDS/WORLDS}"
world_root="${MM9_WORLD_ROOT:-assets_dev/worlds/mm9}"
editor_world_root="${MM9_EDITOR_WORLD_ROOT:-assets_editor_dev/worlds/mm9}"
maps_root="${world_root}/maps"
editor_maps_root="${editor_world_root}/maps"
textures_root="${world_root}/textures"
audio_root="${world_root}/audio"
editor_textures_root="${editor_world_root}/textures"
editor_audio_root="${editor_world_root}/audio"
scripts_root="${MM9_SCRIPT_ROOT:-${extracted_root}/SCRIPTS/SCRIPTS}"
source_sounds_root="${MM9_SOURCE_SOUNDS_ROOT:-${extracted_root}/SOUNDS/SOUNDS}"
events_root="${world_root}/events"
editor_events_root="${editor_world_root}/events"
scale="${MM9_SCALE:-2.56}"
sector_mode="${MM9_SECTOR_MODE:-leaf_grid}"
sector_grid="${MM9_SECTOR_GRID:-4}"
compile_tool="${MM9_COMPILE_INDOOR_SOURCE:-build/tools/mm9_compile_indoor_source}"
copy_editor=1
compile_indoor=1
generate_events=1
editor_world_root_explicit=0
mode="curated"
outdoor_maps=("GUBERLAND")
indoor_maps=("DARKPASSAGEWAY")
classification_map_root="${MM9_CLASSIFICATION_MAP_ROOT:-assets_dev/worlds/mm9/maps}"

usage() {
    cat <<'EOF'
usage: regenerate_mm9_maps.sh [options]

Regenerates MM9 map geometry and scene sidecars from extracted WORLDS/*.dat.

Default mode regenerates the curated maps currently used by OpenYAMM:
  outdoor: GUBERLAND -> ODM
  indoor:  DARKPASSAGEWAY -> BLV prototype

Options:
  --all-odm              Convert every DAT under --dat-root as an outdoor ODM shell.
  --all-blv              Convert every DAT under --dat-root as an indoor BLV prototype.
  --all-classified       Convert outdoor-like DATs as ODM and every other DAT as BLV.
  --clear-defaults       Empty the curated default map lists.
  --outdoor NAME         Add one DAT stem to convert as ODM.
  --indoor NAME          Add one DAT stem to convert as BLV.
  --dat-root PATH        Directory containing extracted DAT files.
  --extracted-root PATH  Extracted MM9 REZ root. Default: mm9/extracted
  --world-root PATH      Development MM9 world root. Default: assets_dev/worlds/mm9
  --editor-world-root P  Editor MM9 world root. Default: assets_editor_dev/worlds/mm9
  --scripts-root PATH    Directory containing extracted MM9 .scr/.inc files.
  --source-sounds-root P Directory containing extracted MM9 WAV files.
  --classification-map-root P
                         Existing generated-map root used only by the classifier.
  --scale VALUE          LithTech-to-OpenYAMM coordinate scale. Default: 2.56
  --sector-mode MODE     BLV sector mode: one_room, spatial_grid, or leaf_grid.
  --sector-grid N        Grid size for spatial/leaf BLV layout. Default: 4
  --compile-tool PATH    Indoor source compiler. Default: build/tools/mm9_compile_indoor_source
  --no-compile           Do not compile indoor source GLBs into BLV files.
  --no-events            Do not generate MM9 .events.yml / generated Lua files.
  --no-editor-copy       Do not mirror generated map files into assets_editor_dev.
EOF
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        --all-odm)
            mode="all_odm"
            shift
            ;;
        --all-blv)
            mode="all_blv"
            shift
            ;;
        --all-classified)
            mode="all_classified"
            shift
            ;;
        --clear-defaults)
            outdoor_maps=()
            indoor_maps=()
            shift
            ;;
        --outdoor)
            outdoor_maps+=("$2")
            shift 2
            ;;
        --indoor)
            indoor_maps+=("$2")
            shift 2
            ;;
        --dat-root)
            dat_root="$2"
            shift 2
            ;;
        --extracted-root)
            extracted_root="$2"
            dat_root="${2}/WORLDS/WORLDS"
            scripts_root="${2}/SCRIPTS/SCRIPTS"
            source_sounds_root="${2}/SOUNDS/SOUNDS"
            shift 2
            ;;
        --world-root)
            world_root="$2"
            maps_root="${world_root}/maps"
            textures_root="${world_root}/textures"
            audio_root="${world_root}/audio"
            events_root="${world_root}/events"
            if [[ "${editor_world_root_explicit}" != 1 ]]
            then
                if [[ "${world_root}" == assets_dev/* ]]
                then
                    editor_world_root="assets_editor_dev/${world_root#assets_dev/}"
                else
                    editor_world_root="${world_root}"
                fi
                editor_maps_root="${editor_world_root}/maps"
                editor_textures_root="${editor_world_root}/textures"
                editor_audio_root="${editor_world_root}/audio"
                editor_events_root="${editor_world_root}/events"
            fi
            shift 2
            ;;
        --editor-world-root)
            editor_world_root="$2"
            editor_maps_root="${editor_world_root}/maps"
            editor_textures_root="${editor_world_root}/textures"
            editor_audio_root="${editor_world_root}/audio"
            editor_events_root="${editor_world_root}/events"
            editor_world_root_explicit=1
            shift 2
            ;;
        --scripts-root)
            scripts_root="$2"
            shift 2
            ;;
        --source-sounds-root)
            source_sounds_root="$2"
            shift 2
            ;;
        --classification-map-root)
            classification_map_root="$2"
            shift 2
            ;;
        --scale)
            scale="$2"
            shift 2
            ;;
        --sector-mode)
            sector_mode="$2"
            shift 2
            ;;
        --sector-grid)
            sector_grid="$2"
            shift 2
            ;;
        --compile-tool)
            compile_tool="$2"
            shift 2
            ;;
        --no-compile)
            compile_indoor=0
            shift
            ;;
        --no-events)
            generate_events=0
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

mkdir -p "${maps_root}"
mkdir -p "${events_root}"
mkdir -p "${textures_root}"
mkdir -p "${audio_root}"

lower_stem() {
    basename "$1" .dat | tr '[:upper:]' '[:lower:]'
}

dat_path_for() {
    local stem="$1"
    local candidate="${dat_root}/${stem}.dat"
    if [[ -f "${candidate}" ]]
    then
        printf '%s\n' "${candidate}"
        return 0
    fi

    candidate="${dat_root}/$(printf '%s' "${stem}" | tr '[:lower:]' '[:upper:]').dat"
    if [[ -f "${candidate}" ]]
    then
        printf '%s\n' "${candidate}"
        return 0
    fi

    echo "missing DAT for ${stem} under ${dat_root}" >&2
    return 1
}

copy_map_outputs_to_editor() {
    local name="$1"
    if [[ "${copy_editor}" != 1 ]]
    then
        return 0
    fi

    mkdir -p "${editor_maps_root}"
    shopt -s nullglob
    local outputs=("${maps_root}/${name}".*)
    shopt -u nullglob
    if [[ ${#outputs[@]} -gt 0 ]]
    then
        cp -a "${outputs[@]}" "${editor_maps_root}/"
    fi
}

copy_event_outputs_to_editor() {
    local name="$1"
    if [[ "${copy_editor}" != 1 ]]
    then
        return 0
    fi

    mkdir -p "${editor_events_root}"
    shopt -s nullglob
    local outputs=("${events_root}/${name}".*)
    shopt -u nullglob
    if [[ ${#outputs[@]} -gt 0 ]]
    then
        cp -a "${outputs[@]}" "${editor_events_root}/"
    fi
}

copy_texture_outputs_to_editor() {
    if [[ "${copy_editor}" != 1 ]]
    then
        return 0
    fi

    if [[ ! -d "${textures_root}" ]]
    then
        return 0
    fi

    mkdir -p "${editor_textures_root}"
    shopt -s nullglob
    local outputs=("${textures_root}"/*)
    shopt -u nullglob
    if [[ ${#outputs[@]} -gt 0 ]]
    then
        cp -a "${outputs[@]}" "${editor_textures_root}/"
    fi
}

copy_audio_outputs_to_editor() {
    if [[ "${copy_editor}" != 1 ]]
    then
        return 0
    fi

    if [[ ! -d "${audio_root}" ]]
    then
        return 0
    fi

    mkdir -p "${editor_audio_root}"
    cp -a "${audio_root}/." "${editor_audio_root}/"
}

remove_stale_odm_outputs() {
    local name="$1"
    rm -f "${maps_root}/${name}.odm" "${maps_root}/${name}.model_assets.yml"
    if [[ "${copy_editor}" == 1 ]]
    then
        rm -f "${editor_maps_root}/${name}.odm" "${editor_maps_root}/${name}.model_assets.yml"
    fi
}

remove_stale_blv_outputs() {
    local name="$1"
    rm -f \
        "${maps_root}/${name}.blv" \
        "${maps_root}/${name}.source.glb" \
        "${maps_root}/${name}.geometry.yml" \
        "${maps_root}/${name}.bsp.yml" \
        "${maps_root}/${name}.compiled_doors.yml"
    if [[ "${copy_editor}" == 1 ]]
    then
        rm -f \
            "${editor_maps_root}/${name}.blv" \
            "${editor_maps_root}/${name}.source.glb" \
            "${editor_maps_root}/${name}.geometry.yml" \
            "${editor_maps_root}/${name}.bsp.yml" \
            "${editor_maps_root}/${name}.compiled_doors.yml"
    fi
}

generate_map_events() {
    local name="$1"
    if [[ "${generate_events}" != 1 ]]
    then
        return 0
    fi

    "${python_bin}" tools/mm9_import_discovery/generate_mm9_events.py \
        --maps-root "${maps_root}" \
        --scripts-root "${scripts_root}" \
        --source-sounds-root "${source_sounds_root}" \
        --events-root "${events_root}" \
        --audio-root "${audio_root}" \
        --only-map "${name}" \
        || return $?
    copy_event_outputs_to_editor "${name}"
    copy_audio_outputs_to_editor
}

convert_odm() {
    local dat_path="$1"
    local name
    name="$(lower_stem "${dat_path}")"
    echo "MM9 ODM ${name}"
    remove_stale_blv_outputs "${name}"
    "${python_bin}" tools/mm9_import_discovery/transcode_mm9_dat_to_odm.py \
        --dat "${dat_path}" \
        --output-dir "${maps_root}" \
        --name "${name}" \
        --scale "${scale}" \
        --extracted-root "${extracted_root}" \
        --bitmap-dir "${textures_root}" \
        || return $?
    generate_map_events "${name}" || return $?
    copy_texture_outputs_to_editor
    copy_map_outputs_to_editor "${name}"
}

convert_blv() {
    local dat_path="$1"
    local name
    name="$(lower_stem "${dat_path}")"
    echo "MM9 BLV ${name}"
    remove_stale_odm_outputs "${name}"
    local args=(
        --dat "${dat_path}"
        --output-dir "${maps_root}"
        --name "${name}"
        --scale "${scale}"
        --extracted-root "${extracted_root}"
        --sector-mode "${sector_mode}"
        --sector-grid "${sector_grid}"
        --bitmap-dir "${textures_root}"
    )
    if [[ "${compile_indoor}" == 1 ]]
    then
        if [[ ! -x "${compile_tool}" ]]
        then
            echo "indoor compiler is not executable: ${compile_tool}" >&2
            echo "build it with: cmake --build build --target mm9_compile_indoor_source -j25" >&2
            exit 1
        fi
        args+=(--compile-tool "${compile_tool}")
    fi
    convert_blv_failure_stage="transcode_blv"
    "${python_bin}" tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py "${args[@]}" || return $?
    convert_blv_failure_stage="events"
    generate_map_events "${name}" || return $?
    convert_blv_failure_stage=""
    copy_texture_outputs_to_editor
    copy_map_outputs_to_editor "${name}"
}

convert_blv_with_odm_fallback() {
    local dat_path="$1"
    local name
    name="$(lower_stem "${dat_path}")"
    local log_path
    log_path="$(mktemp)"

    convert_blv_failure_stage=""
    if convert_blv "${dat_path}" >"${log_path}" 2>&1
    then
        cat "${log_path}"
        rm -f "${log_path}"
        return 0
    fi
    local status=$?
    cat "${log_path}" >&2
    if [[ "${convert_blv_failure_stage}" != "transcode_blv" ]]
    then
        rm -f "${log_path}"
        return "${status}"
    fi
    if ! grep -q "indoor source compiler exceeded 65535 faces" "${log_path}"
    then
        rm -f "${log_path}"
        return "${status}"
    fi
    rm -f "${log_path}"

    echo "MM9 BLV ${name} failed; falling back to ODM shell" >&2
    convert_odm "${dat_path}" || return $?
}

classify_dat_export_kind() {
    local dat_path="$1"
    "${python_bin}" - "${dat_path}" "${classification_map_root}" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path("tools/mm9_import_discovery").resolve()))
from classify_mm9_maps import collect_metrics

metrics = collect_metrics(Path(sys.argv[1]), Path(sys.argv[2]))
print("odm" if metrics.recommendation == "outdoor_like" else "blv")
PY
}

if [[ "${mode}" == "all_odm" || "${mode}" == "all_blv" || "${mode}" == "all_classified" ]]
then
    while IFS= read -r -d '' dat_path
    do
        if [[ "${mode}" == "all_odm" ]]
        then
            convert_odm "${dat_path}" || exit $?
        elif [[ "${mode}" == "all_blv" ]]
        then
            convert_blv "${dat_path}" || exit $?
        else
            export_kind="$(classify_dat_export_kind "${dat_path}")"
            if [[ "${export_kind}" == "odm" ]]
            then
                convert_odm "${dat_path}" || exit $?
            else
                convert_blv_with_odm_fallback "${dat_path}" || exit $?
            fi
        fi
    done < <(find "${dat_root}" -maxdepth 1 -type f -iname '*.dat' -print0 | sort -z)
    exit 0
fi

for map_name in "${outdoor_maps[@]}"
do
    convert_odm "$(dat_path_for "${map_name}")" || exit $?
done

for map_name in "${indoor_maps[@]}"
do
    convert_blv "$(dat_path_for "${map_name}")" || exit $?
done
