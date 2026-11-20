#!/usr/bin/env bash
# Undefined behaviour is where the native core (libstdc++) and the WebAssembly core (libc++) can answer differently
# (S5-0 spike 6): builds the studio with sanitizers into a build folder of its own and builds the 22 calibration
# projects (tests/calibration_projects.sh) with it, each from a fresh copy. Any report fails the run.
#   native: GCC AddressSanitizer and UndefinedBehaviorSanitizer with _GLIBCXX_ASSERTIONS (libstdc++'s checks, e.g.
#           std::clamp's bounds); also runs the unit tests. A few minutes.
#   wasm:   Emscripten's AddressSanitizer (libc++'s container annotations too) with libc++'s extensive hardening,
#           under Node. Slow: one to thirty minutes a project; use -j.
# Usage: tests/sanitize.sh native|wasm [--build-dir <folder>] [-j <parallel builds>] [--xeen-root <folder>]
#        [--keep] [asset root]
#   defaults: build-asan or build-wasm-asan, -j 1, ../output/studio_play/xeen_root, ../assets_dev. --keep leaves
#   the work folder (its path is printed).
set -euo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kind="${1:-}"
[ "$kind" = native ] || [ "$kind" = wasm ] || { echo "usage: tests/sanitize.sh native|wasm [options]" >&2; exit 2; }
shift
buildDir=""
jobs=1
xeenRoot="$studio/../output/studio_play/xeen_root"
keep=0
assets="$studio/../assets_dev"

while [ $# -gt 0 ]; do
    case "$1" in
        --build-dir) buildDir="$2"; shift 2 ;;
        -j) jobs="$2"; shift 2 ;;
        --xeen-root) xeenRoot="$2"; shift 2 ;;
        --keep) keep=1; shift ;;
        -*) echo "unknown option $1" >&2; exit 2 ;;
        *) assets="$1"; shift ;;
    esac
done

if [ "$kind" = native ]; then
    buildDir="${buildDir:-$studio/build-asan}"
    flags="-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer"
    cmake -S "$studio" -B "$buildDir" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        "-DCMAKE_C_FLAGS=$flags" "-DCMAKE_CXX_FLAGS=$flags -D_GLIBCXX_ASSERTIONS" \
        "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined" >/dev/null
    cmake --build "$buildDir" -j "$(nproc)"
    oymap=("$buildDir/oymap")
    export ASAN_OPTIONS="detect_leaks=0:abort_on_error=0:halt_on_error=1"
    export UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1"
    (cd "$studio" && "$buildDir/oymap_tests" --minimal)
else
    buildDir="${buildDir:-$studio/build-wasm-asan}"
    if ! command -v emcmake >/dev/null; then
        # shellcheck disable=SC1091
        source "$studio/emsdk/emsdk_env.sh" >/dev/null 2>&1 || { echo "emsdk not found: see wasm/README.md" >&2; exit 1; }
    fi
    flags="-fsanitize=address -g2"
    emcmake cmake -S "$studio" -B "$buildDir" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        "-DCMAKE_C_FLAGS=$flags" \
        "-DCMAKE_CXX_FLAGS=$flags -D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_EXTENSIVE" \
        "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address -sINITIAL_MEMORY=512MB" >/dev/null
    cmake --build "$buildDir" -j "$(nproc)"
    oymap=(node "$buildDir/oymap.js")
fi

work="$(mktemp -d)"
if [ "$keep" = 0 ]; then
    trap 'rm -rf "$work"' EXIT
else
    echo "work folder: $work"
fi

# shellcheck source=calibration_projects.sh
source "$studio/tests/calibration_projects.sh"
export -f build_fresh_copy

# One project: a fresh copy built by the sanitized core; prints its verdict.
check_one()
{
    local work="$1" name="$2" project="$3" root="$4" verdict started=$SECONDS
    # shellcheck disable=SC2086
    build_fresh_copy "$work/$name" "$project" "$root" $sanitizedOymap

    if [ "$(cat "$work/$name/rc")" != 0 ] \
        || grep -qE "$reportPattern" "$work/$name/stderr.txt"; then
        verdict="REPORT (exit $(cat "$work/$name/rc")): $work/$name/stderr.txt"
        grep -m 3 -E "$reportPattern" "$work/$name/stderr.txt" | sed 's/^/    /' || true
    else
        verdict="clean"
    fi

    echo "$name: $verdict ($((SECONDS - started)) s)"
}
export -f check_one
export sanitizedOymap="${oymap[*]}"
export reportPattern="ERROR: AddressSanitizer|runtime error:|[Aa]ssertion .* failed|Aborted\\("

list="$work/projects.txt"
calibration_projects "$assets" "$xeenRoot" > "$list"

while read -r name project root; do
    if [ ! -d "$root/worlds" ]; then
        echo "$name: skipped, no asset root with worlds at $root" >&2
    else
        printf '%s\0%s\0%s\0%s\0' "$work" "$name" "$project" "$root"
    fi
done < "$list" | xargs -0 -n 4 -P "$jobs" bash -c 'check_one "$@"' _ | tee "$work/verdicts.txt"

clean="$(grep -c ': clean (' "$work/verdicts.txt" || true)"
reported="$(grep -c ': REPORT' "$work/verdicts.txt" || true)"
echo "$kind sanitizers: $clean clean, $reported with a report"
[ "$reported" = 0 ]
