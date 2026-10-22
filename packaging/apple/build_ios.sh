#!/usr/bin/env bash
# Build OpenYAMM.app for iPhone and iPad (arm64), or for the iOS Simulator on Apple silicon. See BUILDING-APPLE.md.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: packaging/apple/build_ios.sh [options]

  --simulator         Build for the iOS Simulator (default: devices)
  --build-dir DIR     CMake build directory (default: build/ios or build/ios-simulator)
  --host-build-dir D  macOS build that provides openyamm_shaderc, the sprite atlas cooker and the dependency
                      sources (default: build/macos, configured and built by packaging/apple/build_macos.sh)
  --debug             Debug build instead of Release
  --package-assets    Package assets_dev with the Android texture profile into OpenYAMM.app/assets
  --bundle-id ID      Bundle identifier (default: io.github.openyamm.OpenYAMM); a personal signing team needs its own
  --sign IDENTITY     Code signing identity, for example "Apple Development: Name (TEAMID)"; requires --profile
  --profile FILE      Provisioning profile (.mobileprovision) that includes the target devices
  -h, --help          Show this help

Simulator builds are signed ad hoc. Device builds are left unsigned unless --sign and --profile are given.
CMAKE_BUILD_PARALLEL_LEVEL sets the number of build jobs.
EOF
}

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(CDPATH= cd -- "${script_dir}/../.." && pwd)
sdk=iphoneos
build_dir=
host_build_dir="${repo_root}/build/macos"
build_type=Release
package_assets=false
bundle_id=io.github.openyamm.OpenYAMM
sign_identity=
provisioning_profile=

while [[ $# -gt 0 ]]; do
    case "$1" in
        --simulator) sdk=iphonesimulator; shift ;;
        --build-dir) build_dir=$2; shift 2 ;;
        --host-build-dir) host_build_dir=$2; shift 2 ;;
        --debug) build_type=Debug; shift ;;
        --package-assets) package_assets=true; shift ;;
        --bundle-id) bundle_id=$2; shift 2 ;;
        --sign) sign_identity=$2; shift 2 ;;
        --profile) provisioning_profile=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

if [[ -z "${build_dir}" ]]; then
    build_dir="${repo_root}/build/$([[ "${sdk}" == iphonesimulator ]] && echo ios-simulator || echo ios)"
fi
if [[ -n "${sign_identity}" && -z "${provisioning_profile}" ]]; then
    echo "--sign requires --profile" >&2
    exit 2
fi

jobs=${CMAKE_BUILD_PARALLEL_LEVEL:-$(sysctl -n hw.ncpu)}
host_targets=(openyamm_shaderc)
if [[ "${package_assets}" == true ]]; then
    host_targets+=(openyamm_sprite_atlas_cook)
fi
if [[ ! -f "${host_build_dir}/CMakeCache.txt" ]]; then
    echo "Configure the macOS build first: packaging/apple/build_macos.sh --build-dir ${host_build_dir}" >&2
    exit 1
fi
cmake --build "${host_build_dir}" --target "${host_targets[@]}" --parallel "${jobs}"

# Reuse the host build's dependency checkouts (bgfx patches included) instead of fetching them again.
dependency_args=()
for dependency in bgfx bimg bx ffmpeg fmt freetype imgui lua monocypher openyamm_zstd physfs sdl3 spdlog yaml-cpp; do
    variable="FETCHCONTENT_SOURCE_DIR_$(printf '%s' "${dependency}" | tr '[:lower:]' '[:upper:]')"
    source_dir=$(sed -n "s|^${variable}:PATH=||p" "${host_build_dir}/CMakeCache.txt")
    if [[ -z "${source_dir}" ]]; then
        source_dir="${host_build_dir}/_deps/${dependency}-src"
    fi
    if [[ -d "${source_dir}" ]]; then
        dependency_args+=("-D${variable}=${source_dir}")
    fi
done

cmake -S "${repo_root}" -B "${build_dir}" -G Ninja \
    -DCMAKE_BUILD_TYPE="${build_type}" \
    -DCMAKE_SYSTEM_NAME=iOS \
    -DCMAKE_OSX_SYSROOT="$(xcrun --sdk "${sdk}" --show-sdk-path)" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 \
    -DCMAKE_OSX_DEPLOYMENT_TARGET=26.0 \
    -DOPENYAMM_BUILD_TESTS=OFF \
    -DOPENYAMM_APPLE_BUNDLE_IDENTIFIER="${bundle_id}" \
    -DOPENYAMM_HOST_SHADERC="${host_build_dir}/openyamm_shaderc" \
    "${dependency_args[@]}"
cmake --build "${build_dir}" --target openyamm --parallel "${jobs}"

app="${build_dir}/game/OpenYAMM.app"
if [[ "${package_assets}" == true ]]; then
    rm -rf "${app}/assets"
    python3 "${repo_root}/tools/package_runtime_assets.py" \
        --assets-root "${repo_root}/assets_dev" --output "${app}/assets" \
        --profile android --cooker "${host_build_dir}/game/openyamm_sprite_atlas_cook"
fi

if [[ "${sdk}" == iphonesimulator ]]; then
    codesign --force --sign - "${app}"
elif [[ -n "${sign_identity}" ]]; then
    # The entitlements come from the profile, whose application identifier must cover the bundle identifier.
    entitlements="${build_dir}/entitlements.plist"
    security cms -D -i "${provisioning_profile}" > "${build_dir}/profile.plist"
    /usr/libexec/PlistBuddy -x -c 'Print :Entitlements' "${build_dir}/profile.plist" > "${entitlements}"
    cp "${provisioning_profile}" "${app}/embedded.mobileprovision"
    codesign --force --sign "${sign_identity}" --entitlements "${entitlements}" --timestamp=none "${app}"
fi
printf 'iOS app (%s): %s\n' "${sdk}" "${app}"
