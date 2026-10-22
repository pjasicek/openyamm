#!/usr/bin/env bash
# Build OpenYAMM.app for macOS on Apple silicon. See BUILDING-APPLE.md.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: packaging/apple/build_macos.sh [options]

  --build-dir DIR    CMake build directory (default: build/macos)
  --debug            Debug build instead of Release
  --tests            Also build openyamm_unit_tests
  --package-assets   Package assets_dev into OpenYAMM.app/Contents/Resources/assets (desktop texture profile),
                     making the app self-contained
  -h, --help         Show this help

CMAKE_BUILD_PARALLEL_LEVEL sets the number of build jobs.
EOF
}

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(CDPATH= cd -- "${script_dir}/../.." && pwd)
build_dir="${repo_root}/build/macos"
build_type=Release
build_tests=OFF
package_assets=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build-dir) build_dir=$2; shift 2 ;;
        --debug) build_type=Debug; shift ;;
        --tests) build_tests=ON; shift ;;
        --package-assets) package_assets=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

jobs=${CMAKE_BUILD_PARALLEL_LEVEL:-$(sysctl -n hw.ncpu)}
targets=(openyamm openyamm_shaderc)
if [[ "${build_tests}" == ON ]]; then
    targets+=(openyamm_unit_tests)
fi
if [[ "${package_assets}" == true ]]; then
    targets+=(openyamm_sprite_atlas_cook)
fi

# The asset cooks need the private assets_source checkout; without it, use the cooked files in assets_dev.
cook_on_build=OFF
if [[ -d "${repo_root}/assets_source/worlds" ]]; then
    cook_on_build=ON
fi

cmake -S "${repo_root}" -B "${build_dir}" -G Ninja \
    -DCMAKE_BUILD_TYPE="${build_type}" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 \
    -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0 \
    -DOPENYAMM_BUILD_TESTS="${build_tests}" \
    -DOPENYAMM_COOK_ON_BUILD="${cook_on_build}"
cmake --build "${build_dir}" --target "${targets[@]}" --parallel "${jobs}"

app="${build_dir}/game/OpenYAMM.app"
if [[ "${package_assets}" == true ]]; then
    rm -rf "${app}/Contents/Resources/assets"
    python3 "${repo_root}/tools/package_runtime_assets.py" \
        --assets-root "${repo_root}/assets_dev" --output "${app}/Contents/Resources/assets" \
        --profile desktop --cooker "${build_dir}/game/openyamm_sprite_atlas_cook"
fi

# Seal the bundle with an ad-hoc signature (the linker signs only the executable). Distribution outside this Mac
# needs a Developer ID signature and notarization instead.
codesign --force --sign - "${app}"
printf 'macOS app: %s\n' "${app}"
