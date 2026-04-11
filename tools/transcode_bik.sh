#!/usr/bin/env bash

set -euo pipefail

usage()
{
    cat <<'EOF'
Usage:
  transcode_bik.sh -i INPUT_DIR -o OUTPUT_DIR

Description:
  Transcodes all .bik files in INPUT_DIR to .ogv files in OUTPUT_DIR.
  The script probes video/audio end times and trims output to the shortest
  valid stream end so decoded Bink cutscenes do not overrun their media tail.
EOF
}

require_tool()
{
    local tool_name="$1"

    if ! command -v "$tool_name" >/dev/null 2>&1
    then
        echo "Missing required tool: $tool_name" >&2
        exit 1
    fi
}

is_number()
{
    local value="$1"
    [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]]
}

normalize_probe_value()
{
    local value="$1"
    value="${value//$'\r'/}"
    value="${value//$'\n'/}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"

    if [[ -z "$value" || "$value" == "N/A" ]]
    then
        return 1
    fi

    printf "%s\n" "$value"
}

packet_end_time()
{
    local stream_spec="$1"
    local input_path="$2"
    local last_packet

    last_packet="$(
        ffprobe -v error \
            -select_streams "$stream_spec" \
            -show_entries packet=pts_time,duration_time \
            -of csv=p=0 \
            "$input_path" 2>/dev/null < /dev/null | tail -n1
    )"

    if [[ -z "$last_packet" ]]
    then
        return 1
    fi

    local pts_time
    local duration_time

    IFS=',' read -r pts_time duration_time <<< "$last_packet"
    pts_time="$(normalize_probe_value "${pts_time:-}" || true)"
    duration_time="$(normalize_probe_value "${duration_time:-}" || true)"

    if ! is_number "$pts_time"
    then
        return 1
    fi

    if is_number "${duration_time:-}"
    then
        awk -v pts="$pts_time" -v dur="$duration_time" 'BEGIN { printf "%.6f\n", pts + dur }'
    else
        awk -v pts="$pts_time" 'BEGIN { printf "%.6f\n", pts }'
    fi
}

stream_duration()
{
    local stream_spec="$1"
    local input_path="$2"
    local value

    value="$(
        ffprobe -v error \
            -select_streams "$stream_spec" \
            -show_entries stream=duration \
            -of csv=p=0 \
            "$input_path" 2>/dev/null < /dev/null | head -n1
    )"
    value="$(normalize_probe_value "$value" || true)"

    if is_number "$value"
    then
        printf "%s\n" "$value"
        return 0
    fi

    return 1
}

format_duration()
{
    local input_path="$1"
    local value

    value="$(
        ffprobe -v error \
            -show_entries format=duration \
            -of csv=p=0 \
            "$input_path" 2>/dev/null < /dev/null | head -n1
    )"
    value="$(normalize_probe_value "$value" || true)"

    if is_number "$value"
    then
        printf "%s\n" "$value"
        return 0
    fi

    return 1
}

stream_property_or_default()
{
    local stream_spec="$1"
    local property_name="$2"
    local default_value="$3"
    local input_path="$4"
    local value

    value="$(
        ffprobe -v error \
            -select_streams "$stream_spec" \
            -show_entries "stream=${property_name}" \
            -of csv=p=0 \
            "$input_path" 2>/dev/null | head -n1
    )"

    if [[ -n "$value" && "$value" != "N/A" ]]
    then
        printf "%s\n" "$value"
    else
        printf "%s\n" "$default_value"
    fi
}

duration_hms_to_seconds()
{
    local value="$1"

    if [[ ! "$value" =~ ^([0-9]+):([0-9]+):([0-9]+([.][0-9]+)?)$ ]]
    then
        return 1
    fi

    awk \
        -v hours="${BASH_REMATCH[1]}" \
        -v minutes="${BASH_REMATCH[2]}" \
        -v seconds="${BASH_REMATCH[3]}" \
        'BEGIN { printf "%.6f\n", hours * 3600 + minutes * 60 + seconds }'
}

ffmpeg_reported_duration()
{
    local input_path="$1"
    local value

    value="$(
        ffmpeg -nostdin -i "$input_path" 2>&1 < /dev/null \
            | sed -n 's/.*Duration: \([0-9:.]*\),.*/\1/p' \
            | head -n1
    )"
    value="$(normalize_probe_value "$value" || true)"

    if [[ -z "$value" ]]
    then
        return 1
    fi

    duration_hms_to_seconds "$value"
}

has_stream()
{
    local stream_spec="$1"
    local input_path="$2"
    local value

    value="$(
        ffprobe -v error \
            -select_streams "$stream_spec" \
            -show_entries stream=index \
            -of csv=p=0 \
            "$input_path" 2>/dev/null < /dev/null | head -n1
    )"
    value="$(normalize_probe_value "$value" || true)"
    [[ -n "$value" ]]
}

fps_to_gop()
{
    local fps_value="$1"
    local fps_numeric="15"

    if [[ "$fps_value" =~ ^([0-9]+)\/([0-9]+)$ ]]
    then
        local fps_num="${BASH_REMATCH[1]}"
        local fps_den="${BASH_REMATCH[2]}"

        if [[ "$fps_den" != "0" ]]
        then
            fps_numeric="$(awk -v num="$fps_num" -v den="$fps_den" 'BEGIN { printf "%.6f\n", num / den }')"
        fi
    elif is_number "$fps_value"
    then
        fps_numeric="$fps_value"
    fi

    awk -v fps="$fps_numeric" 'BEGIN { gop = int(fps + 0.5); if (gop < 1) { gop = 15 } print gop }'
}

input_dir=""
output_dir=""

while getopts ":hi:o:" option
do
    case "$option" in
        h)
            usage
            exit 0
            ;;
        i)
            input_dir="$OPTARG"
            ;;
        o)
            output_dir="$OPTARG"
            ;;
        :)
            echo "Missing value for -$OPTARG" >&2
            usage >&2
            exit 1
            ;;
        \?)
            echo "Unknown option: -$OPTARG" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "$input_dir" || -z "$output_dir" ]]
then
    usage >&2
    exit 1
fi

require_tool ffmpeg
require_tool ffprobe

if [[ ! -d "$input_dir" ]]
then
    echo "Input directory does not exist: $input_dir" >&2
    exit 1
fi

mkdir -p "$output_dir"

processed_count=0
written_count=0
skipped_count=0

while IFS= read -r -d '' input_path
do
    processed_count=$((processed_count + 1))
    input_name="$(basename "$input_path")"
    stem="${input_name%.*}"
    output_path="${output_dir}/${stem}.ogv"

    video_end="$(packet_end_time v:0 "$input_path" || true)"
    audio_end="$(packet_end_time a:0 "$input_path" || true)"

    if ! is_number "$video_end"
    then
        video_end="$(stream_duration v:0 "$input_path" || true)"
    fi

    if ! is_number "$audio_end"
    then
        audio_end="$(stream_duration a:0 "$input_path" || true)"
    fi

    if ! is_number "$video_end"
    then
        video_end="$(format_duration "$input_path" || true)"
    fi

    if ! is_number "$video_end"
    then
        video_end="$(ffmpeg_reported_duration "$input_path" || true)"
    fi

    trim_duration="$video_end"

    if ! is_number "$trim_duration"
    then
        echo "Warning: ${input_name}: could not determine trim duration, transcoding without trim" >&2
    fi

    source_fps="$(stream_property_or_default v:0 r_frame_rate 15/1 "$input_path")"
    source_rate="$(stream_property_or_default a:0 sample_rate 22050 "$input_path")"
    source_channels="$(stream_property_or_default a:0 channels 1 "$input_path")"
    gop_size="$(fps_to_gop "$source_fps")"
    has_audio="0"

    if has_stream a:0 "$input_path"
    then
        has_audio="1"
    fi

    echo "Transcoding ${input_name}"
    echo "  video_end=${video_end:-N/A} audio_end=${audio_end:-N/A} trim=${trim_duration}"
    echo "  fps=${source_fps} sample_rate=${source_rate} channels=${source_channels} gop=${gop_size}"

    if [[ "$has_audio" == "1" ]] && is_number "$audio_end" && is_number "$trim_duration"
    then
        ffmpeg -y \
            -nostdin \
            -i "$input_path" \
            -vf "fps=${source_fps},format=yuv420p" \
            -af "atrim=end=${trim_duration},asetpts=N/SR/TB" \
            -c:v libtheora -q:v 7 -g "$gop_size" \
            -c:a libvorbis -q:a 3 -ar "$source_rate" -ac "$source_channels" \
            -t "$trim_duration" \
            "$output_path"
    elif is_number "$trim_duration"
    then
        ffmpeg -y \
            -nostdin \
            -i "$input_path" \
            -vf "fps=${source_fps},format=yuv420p" \
            -c:v libtheora -q:v 7 -g "$gop_size" \
            -an \
            -t "$trim_duration" \
            "$output_path"
    elif [[ "$has_audio" == "0" ]] && ! is_number "$trim_duration"
    then
        ffmpeg -y \
            -nostdin \
            -i "$input_path" \
            -vf "fps=${source_fps},format=yuv420p" \
            -c:v libtheora -q:v 7 -g "$gop_size" \
            -an \
            "$output_path"
    else
        ffmpeg -y \
            -nostdin \
            -i "$input_path" \
            -vf "fps=${source_fps},format=yuv420p" \
            -c:v libtheora -q:v 7 -g "$gop_size" \
            -c:a libvorbis -q:a 3 -ar "$source_rate" -ac "$source_channels" \
            "$output_path"
    fi

    if [[ -f "$output_path" ]]
    then
        written_count=$((written_count + 1))
    else
        skipped_count=$((skipped_count + 1))
    fi
done < <(find "$input_dir" -maxdepth 1 -type f \( -iname '*.bik' \) -print0 | sort -z)

if [[ "$processed_count" -eq 0 ]]
then
    echo "No .bik files found in: $input_dir" >&2
    exit 1
fi

echo "Done. Processed ${processed_count} file(s), wrote ${written_count}, skipped ${skipped_count} to ${output_dir}."
