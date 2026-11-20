#!/usr/bin/env bash
# The native and the WebAssembly core must write the same bytes (PLAN.md section 3). Builds with both: the slice
# project and the shapes gallery; the 22 calibration projects (tests/calibration_projects.sh), each from a fresh
# copy, comparing every output file, the JSON report and the project folder after the build (skipped when the asset
# root, or for the Xeen projects the Xeen root, has no worlds: the fixture root has none); and compares their export
# of one shipped map of each kind.
# Usage: tests/native_vs_wasm.sh [--native <oymap>] [--wasm <oymap.js>] [--xeen-root <folder>] [--keep] [asset root]
#   defaults: build/oymap, build-wasm/oymap.js, ../output/studio_play/xeen_root, ../assets_dev. --keep leaves the
#   work folder (its path is printed). Exit code 1 when anything differs or a build fails.
set -euo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
native="$studio/build/oymap"
wasmScript="$studio/build-wasm/oymap.js"
xeenRoot="$studio/../output/studio_play/xeen_root"
keep=0
assets="$studio/../assets_dev"

while [ $# -gt 0 ]; do
    case "$1" in
        --native) native="$2"; shift 2 ;;
        --wasm) wasmScript="$2"; shift 2 ;;
        --xeen-root) xeenRoot="$2"; shift 2 ;;
        --keep) keep=1; shift ;;
        -*) echo "unknown option $1" >&2; exit 2 ;;
        *) assets="$1"; shift ;;
    esac
done

wasm=(node "$wasmScript")
work="$(mktemp -d)"
if [ "$keep" = 0 ]; then
    trap 'rm -rf "$work"' EXIT
else
    echo "work folder: $work"
fi

# shellcheck source=calibration_projects.sh
source "$studio/tests/calibration_projects.sh"
failed=0

# The slice, and the test map with one of every room feature and moving part.
for project in "$studio/examples/gatehouse_cellars" "$studio/examples/shapes_gallery"; do
    name="$(basename "$project")"
    "$native" build "$project" --assets "$assets" --out "$work/native_$name" >/dev/null
    "${wasm[@]}" build "$project" --assets "$assets" --out "$work/wasm_$name" >/dev/null
    diff -r "$work/native_$name" "$work/wasm_$name"
    echo "build $name: identical ($(find "$work/native_$name" -type f | wc -l) files)"
done

# The calibration projects.
identical=0
total=0
skipped=0

while read -r name project root; do
    if [ ! -d "$root/worlds" ]; then
        echo "build $name: skipped, no asset root with worlds at $root"
        skipped=$((skipped + 1))
        continue
    fi

    total=$((total + 1))
    build_fresh_copy "$work/22/$name/native" "$project" "$root" "$native"
    build_fresh_copy "$work/22/$name/wasm" "$project" "$root" "${wasm[@]}"
    nativeRc="$(cat "$work/22/$name/native/rc")"
    wasmRc="$(cat "$work/22/$name/wasm/rc")"
    problems=()

    if [ "$nativeRc" != 0 ] || [ "$wasmRc" != 0 ]; then
        problems+=("exit codes native $nativeRc, wasm $wasmRc")
    fi
    if ! diff -r "$work/22/$name/native/out" "$work/22/$name/wasm/out" >/dev/null 2>&1; then
        problems+=("output differs")
    fi
    if ! cmp -s "$work/22/$name/native/stdout.json" "$work/22/$name/wasm/stdout.json"; then
        problems+=("JSON report differs")
    fi
    if ! diff -r "$work/22/$name/native/proj" "$work/22/$name/wasm/proj" >/dev/null 2>&1; then
        problems+=("project folder after the build differs")
    fi

    if [ ${#problems[@]} -eq 0 ]; then
        identical=$((identical + 1))
        echo "build $name: identical ($(find "$work/22/$name/native/out" -type f | wc -l) files)"
    else
        failed=1
        echo "build $name: $(IFS=';'; echo "${problems[*]}") (see $work/22/$name; --keep keeps it)"
    fi
done < <(calibration_projects "$assets" "$xeenRoot")

echo "calibration projects: $identical of $total identical$([ "$skipped" -gt 0 ] && echo ", $skipped skipped")"

for map in worlds/mm6/maps/oute3.odm worlds/mm7/maps/7d06.blv; do
    if [ -f "$assets/$map" ]; then
        "$native" export "$assets/$map" > "$work/native.json"
        "${wasm[@]}" export "$assets/$map" > "$work/wasm.json"
        cmp "$work/native.json" "$work/wasm.json"
        echo "export $map: identical"
    fi
done

exit "$failed"
