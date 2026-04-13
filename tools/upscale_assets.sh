#!/usr/bin/env bash
set -euo pipefail

usage()
{
    cat <<'EOF'
Usage: upscale_assets.sh [--quantize-8bit] [--only-pcx] [--key-transparency <auto|magenta|teal|none>] <input_dir> <scale> <output_dir>

Recursively finds all .bmp/.BMP/.pcx/.PCX files under <input_dir> and writes
upscaled copies to the matching relative paths under <output_dir> using xbrz.

Arguments:
  --quantize-8bit  Convert xbrz output to uncompressed 8-bit BMP using ImageMagick.
  --only-pcx       Process only .pcx/.PCX files.
  --key-transparency
                   Preserve chroma-key transparency by separating the key mask,
                   bleeding neighboring colors into transparent pixels before xbrz,
                   upscaling the mask with nearest-neighbor, and writing the final
                   keyed output as BMP/PCX. Accepted values:
                     auto     Detect magenta or teal/cyan key color per file.
                     magenta  Force #ff00ff as the key color.
                     teal     Force #00ffff as the key color.
                     none     Disable keyed-transparency preprocessing.
  input_dir   Directory containing source assets.
  scale       xbrz scale factor. Expected values are typically 2, 3, 4, 5, or 6.
  output_dir  Directory where upscaled assets will be written.
EOF
}

quantize_8bit=false
only_pcx=false
key_transparency="none"
temp_files=()

cleanup_temp_files()
{
    if [[ ${#temp_files[@]} -eq 0 ]]; then
        return
    fi

    rm -f -- "${temp_files[@]}" 2>/dev/null || true
    temp_files=()
}

make_temp_file()
{
    local suffix="$1"
    local path

    path="$(mktemp "${TMPDIR:-/tmp}/openyamm-upscale-XXXXXX${suffix}")"
    temp_files+=("$path")
    printf '%s\n' "$path"
}

image_has_key_color()
{
    local source_path="$1"
    local key_color="$2"
    local opaque

    opaque="$(
        convert \
            "$source_path" \
            -alpha set \
            -fuzz 3% \
            -transparent "$key_color" \
            -format '%[opaque]' \
            info: 2>/dev/null || true
    )"

    [[ "$opaque" != "true" && "$opaque" != "True" ]]
}

resolve_key_color()
{
    local source_path="$1"

    case "$key_transparency" in
        none)
            printf 'none\n'
            ;;
        magenta)
            printf '#ff00ff\n'
            ;;
        teal)
            printf '#00ffff\n'
            ;;
        auto)
            local has_magenta=false
            local has_teal=false

            if image_has_key_color "$source_path" "#ff00ff"; then
                has_magenta=true
            fi

            if image_has_key_color "$source_path" "#00ffff"; then
                has_teal=true
            fi

            if [[ "$has_magenta" == true && "$has_teal" == true ]]; then
                echo "Ambiguous key color detected in file: $source_path" >&2
                echo "Both magenta and teal/cyan look like transparency keys. Re-run with --key-transparency." >&2
                return 1
            fi

            if [[ "$has_magenta" == true ]]; then
                printf '#ff00ff\n'
            elif [[ "$has_teal" == true ]]; then
                printf '#00ffff\n'
            else
                printf 'none\n'
            fi
            ;;
        *)
            echo "Unsupported key transparency mode: $key_transparency" >&2
            return 1
            ;;
    esac
}

write_output_image()
{
    local input_path="$1"
    local destination_path="$2"
    local source_extension_lower="$3"
    local quantize="$4"
    local background_key_color="${5:-#000000}"

    if [[ "$source_extension_lower" == "bmp" ]]; then
        if [[ "$quantize" == true ]]; then
            convert \
                "$input_path" \
                -background "$background_key_color" \
                -alpha remove \
                -alpha off \
                -colors 256 \
                -type Palette \
                -compress None \
                "BMP3:$destination_path"
        else
            convert \
                "$input_path" \
                -background "$background_key_color" \
                -alpha remove \
                -alpha off \
                "BMP3:$destination_path"
        fi
    elif [[ "$source_extension_lower" == "pcx" ]]; then
        if [[ "$quantize" == true ]]; then
            convert \
                "$input_path" \
                -background "$background_key_color" \
                -alpha remove \
                -alpha off \
                -colors 256 \
                -type Palette \
                "PCX:$destination_path"
        else
            convert \
                "$input_path" \
                -background "$background_key_color" \
                -alpha remove \
                -alpha off \
                "PCX:$destination_path"
        fi
    else
        echo "Unsupported input extension for output file: $destination_path" >&2
        return 1
    fi
}

run_standard_pipeline()
{
    local source_path="$1"
    local scale="$2"
    local destination_path="$3"
    local source_extension_lower="$4"
    local quantize="$5"
    local temp_output_path

    temp_output_path="$(make_temp_file ".bmp")"
    xbrz "$source_path" "$scale" "$temp_output_path"

    if [[ "$source_extension_lower" == "bmp" && "$quantize" == false ]]; then
        mv "$temp_output_path" "$destination_path"
        return
    fi

    write_output_image "$temp_output_path" "$destination_path" "$source_extension_lower" "$quantize"
}

run_keyed_pipeline()
{
    local source_path="$1"
    local scale="$2"
    local destination_path="$3"
    local source_extension_lower="$4"
    local quantize="$5"
    local key_color="$6"
    local bleed_passes="$7"
    local rgba_source_path
    local alpha_mask_path
    local bleed_rgba_path
    local prepared_rgba_path
    local prepared_bmp_path
    local upscaled_rgb_path
    local upscaled_alpha_mask_path
    local final_rgba_path

    rgba_source_path="$(make_temp_file ".png")"
    alpha_mask_path="$(make_temp_file ".png")"
    bleed_rgba_path="$(make_temp_file ".png")"
    prepared_rgba_path="$(make_temp_file ".png")"
    prepared_bmp_path="$(make_temp_file ".bmp")"
    upscaled_rgb_path="$(make_temp_file ".bmp")"
    upscaled_alpha_mask_path="$(make_temp_file ".png")"
    final_rgba_path="$(make_temp_file ".png")"

    convert \
        "$source_path" \
        -alpha set \
        -fuzz 3% \
        -transparent "$key_color" \
        "$rgba_source_path"

    convert \
        "$rgba_source_path" \
        -alpha extract \
        "$alpha_mask_path"

    cp "$rgba_source_path" "$bleed_rgba_path"

    for (( pass_index = 0; pass_index < bleed_passes; ++pass_index )); do
        convert \
            "$bleed_rgba_path" \
            -morphology Dilate Octagon:1 \
            "$prepared_rgba_path"
        mv "$prepared_rgba_path" "$bleed_rgba_path"
    done

    convert \
        "$bleed_rgba_path" \
        "$alpha_mask_path" \
        -compose CopyOpacity \
        -composite \
        "$prepared_rgba_path"

    convert \
        "$prepared_rgba_path" \
        -background black \
        -alpha remove \
        -alpha off \
        "BMP3:$prepared_bmp_path"

    xbrz "$prepared_bmp_path" "$scale" "$upscaled_rgb_path"

    convert \
        "$alpha_mask_path" \
        -filter point \
        -resize "$((scale * 100))%" \
        "$upscaled_alpha_mask_path"

    convert \
        "$upscaled_rgb_path" \
        "$upscaled_alpha_mask_path" \
        -compose CopyOpacity \
        -composite \
        "$final_rgba_path"

    write_output_image "$final_rgba_path" "$destination_path" "$source_extension_lower" "$quantize" "$key_color"
}

trap cleanup_temp_files EXIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quantize-8bit)
            quantize_8bit=true
            shift
            ;;
        --only-pcx)
            only_pcx=true
            shift
            ;;
        --key-transparency)
            if [[ $# -lt 2 ]]; then
                echo "--key-transparency requires a value: auto, magenta, teal, or none" >&2
                exit 1
            fi

            key_transparency="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -ne 3 ]]; then
    usage >&2
    exit 1
fi

input_dir="$1"
scale="$2"
output_dir="$3"

if ! command -v xbrz >/dev/null 2>&1; then
    echo "xbrz not found in PATH" >&2
    exit 1
fi

if [[ "$only_pcx" == true ]]; then
    find_expression=( -iname '*.pcx' )
else
    find_expression=( \( -iname '*.bmp' -o -iname '*.pcx' \) )
fi

if [[ ! -d "$input_dir" ]]; then
    echo "Input directory does not exist: $input_dir" >&2
    exit 1
fi

if [[ ! "$scale" =~ ^[0-9]+$ ]]; then
    echo "Scale must be a positive integer: $scale" >&2
    exit 1
fi

if (( scale <= 0 )); then
    echo "Scale must be greater than zero: $scale" >&2
    exit 1
fi

mkdir -p "$output_dir"

input_dir_abs="$(cd "$input_dir" && pwd)"
output_dir_abs="$(cd "$output_dir" && pwd)"

needs_convert=false

if [[ "$quantize_8bit" == true ]]; then
    needs_convert=true
elif find "$input_dir_abs" -type f "${find_expression[@]}" -iname '*.pcx' -print -quit | grep -q .; then
    needs_convert=true
fi

if [[ "$needs_convert" == true ]] && ! command -v convert >/dev/null 2>&1; then
    echo "ImageMagick 'convert' not found in PATH" >&2
    exit 1
fi

if [[ "$key_transparency" != "none" && "$key_transparency" != "auto" && "$key_transparency" != "magenta" \
    && "$key_transparency" != "teal" ]]; then
    echo "Unsupported --key-transparency value: $key_transparency" >&2
    exit 1
fi

if [[ "$input_dir_abs" == "$output_dir_abs" ]]; then
    echo "Input and output directories must be different." >&2
    exit 1
fi

if [[ "$output_dir_abs" == "$input_dir_abs"/* ]]; then
    echo "Output directory must not be inside the input directory." >&2
    exit 1
fi

processed_count=0

while IFS= read -r -d '' source_path; do
    cleanup_temp_files
    relative_path="${source_path#"$input_dir_abs"/}"
    destination_path="$output_dir_abs/$relative_path"
    destination_dir="$(dirname "$destination_path")"
    source_extension="${source_path##*.}"
    source_extension_lower="${source_extension,,}"
    detected_key_color="none"
    bleed_passes="$scale"

    mkdir -p "$destination_dir"

    echo "Upscaling: $relative_path"
    if [[ "$source_extension_lower" != "bmp" && "$source_extension_lower" != "pcx" ]]; then
        echo "Unsupported input extension for file: $source_path" >&2
        exit 1
    fi

    if [[ "$key_transparency" != "none" ]]; then
        detected_key_color="$(resolve_key_color "$source_path")"
    fi

    if [[ "$detected_key_color" != "none" ]]; then
        echo "  using key-transparency pipeline ($detected_key_color)"
        run_keyed_pipeline \
            "$source_path" \
            "$scale" \
            "$destination_path" \
            "$source_extension_lower" \
            "$quantize_8bit" \
            "$detected_key_color" \
            "$bleed_passes"
    else
        run_standard_pipeline \
            "$source_path" \
            "$scale" \
            "$destination_path" \
            "$source_extension_lower" \
            "$quantize_8bit"
    fi

    cleanup_temp_files

    processed_count=$((processed_count + 1))
done < <(
    find "$input_dir_abs" -type f \
        "${find_expression[@]}" \
        -print0 | sort -z
)

echo "Done. Upscaled $processed_count file(s) to $output_dir_abs"
