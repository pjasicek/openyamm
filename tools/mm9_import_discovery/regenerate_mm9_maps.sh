#!/usr/bin/env bash
set -euo pipefail

# Retired 2026-11-06: the old MM9 import (45 ODMs) is no longer the runtime world. assets_dev/worlds/mm9 holds the
# rebuilt BLVs (devdocs/mm9_rework/README.md), the old import's inputs live in assets_editor_dev/worlds/mm9/maps and
# its original tables in level_generation/projects/mm9r_common/original_tables. Running this script would write old
# ODM maps, map Lua and old-frame exit rows over the rework. Set MM9_OLD_IMPORT=1 only to rebuild the old import into
# a separate MM9_WORLD_ROOT.
if [[ "${MM9_OLD_IMPORT:-}" != "1" ]]; then
    echo "regenerate_mm9_maps.sh is retired (the MM9 rework replaced the old import); see the comment at its top" >&2
    exit 2
fi

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
music_root="${world_root}/music"
editor_textures_root="${editor_world_root}/textures"
editor_audio_root="${editor_world_root}/audio"
editor_music_root="${editor_world_root}/music"
scripts_root="${MM9_SCRIPT_ROOT:-${extracted_root}/SCRIPTS/SCRIPTS}"
source_sounds_root="${MM9_SOURCE_SOUNDS_ROOT:-${extracted_root}/SOUNDS/SOUNDS}"
source_voices_root="${MM9_SOURCE_VOICES_ROOT:-${extracted_root}/VOICES/VOICES}"
source_music_root="${MM9_SOURCE_MUSIC_ROOT:-mm9/game/music}"
events_root="${world_root}/events/maps"
editor_events_root="${editor_world_root}/events/maps"
events_common_root="${world_root}/events/common"
editor_events_common_root="${editor_world_root}/events/common"
scale="${MM9_SCALE:-2.56}"
sector_mode="${MM9_SECTOR_MODE:-leaf_grid}"
sector_grid="${MM9_SECTOR_GRID:-4}"
compile_tool="${MM9_COMPILE_INDOOR_SOURCE:-build/tools/mm9_compile_indoor_source}"
copy_editor=1
compile_indoor=1
generate_events=1
editor_world_root_explicit=0
defer_shared_editor_copy=0
mode="curated"
outdoor_maps=("GUBERLAND")
indoor_maps=("DARKPASSAGEWAY")
classification_map_root="${MM9_CLASSIFICATION_MAP_ROOT:-assets_dev/worlds/mm9/maps}"
item_source_audit_output="${MM9_ITEM_SOURCE_AUDIT_OUTPUT:-MM9_ITEM_SOURCE_AUDIT.md}"

usage() {
    cat <<'EOF'
usage: regenerate_mm9_maps.sh [options]

Regenerates MM9 map geometry and scene sidecars from extracted WORLDS/*.dat.

Default mode regenerates the curated maps currently used by OpenYAMM as ODM BModel worlds:
  exterior: GUBERLAND
  enclosed: DARKPASSAGEWAY

Options:
  --all-odm              Convert every DAT under --dat-root as an outdoor ODM shell.
  --all-blv              Convert every DAT under --dat-root as an indoor BLV prototype.
  --all-classified       Convert every DAT as ODM and classify exterior/enclosed semantics.
  --clear-defaults       Empty the curated default map lists.
  --outdoor NAME         Add one DAT stem to convert as ODM.
  --indoor NAME          Add one DAT stem to convert as an enclosed ODM BModel world.
  --dat-root PATH        Directory containing extracted DAT files.
  --extracted-root PATH  Extracted MM9 REZ root. Default: mm9/extracted
  --world-root PATH      Development MM9 world root. Default: assets_dev/worlds/mm9
  --editor-world-root P  Editor MM9 world root. Default: assets_editor_dev/worlds/mm9
  --scripts-root PATH    Directory containing extracted MM9 .scr/.inc files.
  --source-sounds-root P Directory containing extracted MM9 WAV files.
  --source-voices-root P Directory containing extracted MM9 voice WAV files.
  --source-music-root P Directory containing the original MM9-Song*.mp3 files.
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
            source_voices_root="${2}/VOICES/VOICES"
            shift 2
            ;;
        --world-root)
            world_root="$2"
            maps_root="${world_root}/maps"
            textures_root="${world_root}/textures"
            audio_root="${world_root}/audio"
            music_root="${world_root}/music"
            events_root="${world_root}/events/maps"
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
                editor_music_root="${editor_world_root}/music"
                editor_events_root="${editor_world_root}/events/maps"
            fi
            shift 2
            ;;
        --editor-world-root)
            editor_world_root="$2"
            editor_maps_root="${editor_world_root}/maps"
            editor_textures_root="${editor_world_root}/textures"
            editor_audio_root="${editor_world_root}/audio"
            editor_music_root="${editor_world_root}/music"
            editor_events_root="${editor_world_root}/events/maps"
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
        --source-voices-root)
            source_voices_root="$2"
            shift 2
            ;;
        --source-music-root)
            source_music_root="$2"
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

map_image_args=(
    --dat-root "${dat_root}"
    --source-image-root "${extracted_root}/ART/ART/INTERFACESCREENS/MAPSCREENS/MAPS"
    --world-root "${world_root}"
    --editor-world-root "${editor_world_root}"
    --scale "${scale}"
)
if [[ "${copy_editor}" != 1 ]]
then
    map_image_args+=(--no-editor-copy)
fi
"${python_bin}" tools/mm9_import_discovery/promote_mm9_map_images.py "${map_image_args[@]}"

"${python_bin}" tools/mm9_import_discovery/generate_mm9_item_source_audit.py \
    --dat-root "${dat_root}" \
    --item-id-map "${world_root}/state/item_ids.yml" \
    --output "${item_source_audit_output}"

"${python_bin}" tools/mm9_import_discovery/generate_mm9_monster_tables.py \
    --source-monsters "${extracted_root}/DATA/DATA/MONSTERS.txt" \
    --output-dir "${world_root}/data_tables"
if [[ "${copy_editor}" == 1 ]]
then
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_monster_tables.py \
        --source-monsters "${extracted_root}/DATA/DATA/MONSTERS.txt" \
        --output-dir "${editor_world_root}/data_tables"
fi
engine_map_stats="${world_root%/worlds/mm9}/engine/data_tables/map_stats.txt"
if [[ -f "${engine_map_stats}" ]]
then
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_map_stats_encounters.py \
        --source-monsters "${extracted_root}/DATA/DATA/MONSTERS.txt" \
        --source-map-stats "${extracted_root}/DATA/DATA/MAPSTATS.txt" \
        --map-stats "${engine_map_stats}"
fi

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

    if [[ -d "${events_common_root}" ]]
    then
        mkdir -p "${editor_events_common_root}"
        shopt -s nullglob
        local common_outputs=("${events_common_root}"/*.lua)
        shopt -u nullglob
        if [[ ${#common_outputs[@]} -gt 0 ]]
        then
            cp -a "${common_outputs[@]}" "${editor_events_common_root}/"
        fi
    fi
}

copy_texture_outputs_to_editor() {
    if [[ "${copy_editor}" != 1 || "${defer_shared_editor_copy}" == 1 ]]
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
    if [[ "${copy_editor}" != 1 || "${defer_shared_editor_copy}" == 1 ]]
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

copy_music_outputs_to_editor() {
    if [[ "${copy_editor}" != 1 || "${defer_shared_editor_copy}" == 1 ]]
    then
        return 0
    fi

    if [[ ! -d "${music_root}" ]]
    then
        return 0
    fi

    mkdir -p "${editor_music_root}"
    cp -a "${music_root}/." "${editor_music_root}/"
}

generate_world_content() {
    local quest_overlay="${world_root}/data_tables/english/quests_overlay.txt"
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_quest_overlay.py \
        --source "${world_root}/dialogue/rude/NPC997.rude" \
        --output "${quest_overlay}" \
        || return $?
    "${python_bin}" tools/mm9_import_discovery/import_mm9_world_audio.py \
        --sounds-root "${source_sounds_root}" \
        --voices-root "${source_voices_root}" \
        --engine-audio-root "assets_dev/engine/audio" \
        --output-root "${audio_root}" \
        || return $?
    "${python_bin}" tools/mm9_import_discovery/import_mm9_world_music.py \
        --source-root "${source_music_root}" \
        --output-root "${music_root}" \
        || return $?

    if [[ "${copy_editor}" == 1 ]]
    then
        local editor_quest_overlay="${editor_world_root}/data_tables/english/quests_overlay.txt"
        mkdir -p "$(dirname "${editor_quest_overlay}")"
        cp -a "${quest_overlay}" "${editor_quest_overlay}"
        copy_audio_outputs_to_editor
        copy_music_outputs_to_editor
    fi
}

generate_quest_interactions() {
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_quest_interactions.py \
        --rude-root "${world_root}/dialogue/rude" \
        --maps-root "${maps_root}" \
        --raw-maps-root "${editor_maps_root}" \
        --events-root "${maps_root}" \
        --scripts-root "${scripts_root}" \
        --output "${world_root}/state/quest_interactions.yml" \
        --report "${world_root}/state/quest_interaction_coverage.yml"
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

    rm -f \
        "${world_root}/events/${name}.lua" \
        "${world_root}/events/${name}.script_ir.yml"
    if [[ "${copy_editor}" == 1 ]]
    then
        rm -f \
            "${editor_world_root}/events/${name}.lua" \
            "${editor_world_root}/events/${name}.script_ir.yml"
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
    local location_type="${2:-exterior}"
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
        --location-type "${location_type}" \
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
    "${python_bin}" tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py "${args[@]}" || return $?
    generate_map_events "${name}" || return $?
    copy_texture_outputs_to_editor
    copy_map_outputs_to_editor "${name}"
}

classify_dat_location_type() {
    local dat_path="$1"
    "${python_bin}" - "${dat_path}" "${classification_map_root}" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path("tools/mm9_import_discovery").resolve()))
from classify_mm9_maps import collect_metrics

metrics = collect_metrics(Path(sys.argv[1]), Path(sys.argv[2]))
print("exterior" if metrics.recommendation == "outdoor_like" else "enclosed")
PY
}

generate_transition_contribution() {
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_transitions.py \
        --maps-dir "${editor_maps_root}" \
        --output "${world_root}/data_tables/map_transitions.txt" \
        --audit "${world_root}/import/map_transition_audit.yml"
}

generate_skill_trainer_contribution() {
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_skill_trainers.py \
        --rude-dir "${world_root}/dialogue/rude" \
        --maps-dir "${maps_root}" \
        --scripts-dir "${scripts_root}" \
        --output "${world_root}/data_tables/skill_trainers.txt" \
        --audit "${world_root}/import/skill_trainer_audit.yml"
}

generate_transport_route_contribution() {
    "${python_bin}" tools/mm9_import_discovery/generate_mm9_transport_routes.py \
        --shops "${extracted_root}/DATA/DATA/MMIXSHOPS.txt" \
        --rude-dir "${extracted_root}/RUDE/RUDE" \
        --books "${extracted_root}/DATA/DATA/BOOK AND SCROLL TEXT.csv" \
        --maps-dir "${maps_root}" \
        --output "${world_root}/data_tables/transport_routes.txt" \
        --audit "${world_root}/import/transport_route_audit.yml"
}

generate_world_content || exit $?

if [[ "${mode}" == "all_odm" || "${mode}" == "all_blv" || "${mode}" == "all_classified" ]]
then
    defer_shared_editor_copy=1
    while IFS= read -r -d '' dat_path
    do
        if [[ "${mode}" == "all_odm" ]]
        then
            location_type="$(classify_dat_location_type "${dat_path}")"
            convert_odm "${dat_path}" "${location_type}" || exit $?
        elif [[ "${mode}" == "all_blv" ]]
        then
            convert_blv "${dat_path}" || exit $?
        else
            location_type="$(classify_dat_location_type "${dat_path}")"
            convert_odm "${dat_path}" "${location_type}" || exit $?
        fi
    done < <(find "${dat_root}" -maxdepth 1 -type f -iname '*.dat' -print0 | sort -z)
    defer_shared_editor_copy=0
    copy_texture_outputs_to_editor
    copy_audio_outputs_to_editor
    generate_quest_interactions || exit $?
    generate_transition_contribution || exit $?
    generate_transport_route_contribution || exit $?
    generate_skill_trainer_contribution || exit $?
    exit 0
fi

for map_name in "${outdoor_maps[@]}"
do
    convert_odm "$(dat_path_for "${map_name}")" exterior || exit $?
done

for map_name in "${indoor_maps[@]}"
do
    convert_odm "$(dat_path_for "${map_name}")" enclosed || exit $?
done

generate_quest_interactions || exit $?
generate_transition_contribution || exit $?
generate_transport_route_contribution || exit $?
generate_skill_trainer_contribution || exit $?
