#!/usr/bin/env bash
# Builds Map Studio in its own tree. Usage: ./build.sh [native|wasm] [extra cmake --build arguments]
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kind="${1:-native}"
[ $# -gt 0 ] && shift

if [ "$kind" = wasm ]; then
    if ! command -v emcmake >/dev/null; then
        # shellcheck disable=SC1091
        source "$here/emsdk/emsdk_env.sh" >/dev/null 2>&1 || { echo "emsdk not found: see wasm/README.md" >&2; exit 1; }
    fi
    emcmake cmake -S "$here" -B "$here/build-wasm" -G Ninja -DCMAKE_BUILD_TYPE=Release
    cmake --build "$here/build-wasm" "$@"
else
    cmake -S "$here" -B "$here/build" -G Ninja -DCMAKE_BUILD_TYPE=Release
    cmake --build "$here/build" -j 12 "$@"
fi
