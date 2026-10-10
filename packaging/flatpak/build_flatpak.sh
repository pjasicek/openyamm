#!/usr/bin/env bash
set -euo pipefail

# Parse the complete workflow before running commands. The checkout can change during a long build.
{
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"

app_id="io.github.openyamm.OpenYAMM"
branch="stable"
manifest="$script_dir/io.github.openyamm.OpenYAMM.yml"
output_dir="$repo_root/build/flatpak"
build_dir=""
repo_dir=""
state_dir=""
source_dir=""
generated_manifest=""
bundle_path=""
install_app=1
create_bundle=1
force_clean=1
install_deps_from=""
assume_yes=1
add_flathub=0
clean_only=0
bundle_only=0
build_jobs=""

usage()
{
    cat <<EOF
Usage: $0 [options]

Builds OpenYAMM with flatpak-builder, installs it for the current user, and
creates a .flatpak bundle from the local build repo.

Options:
  --output-dir=PATH       Output root. Default: build/flatpak
  --build-dir=PATH        flatpak-builder build directory.
  --repo-dir=PATH         Local Flatpak repository directory.
  --state-dir=PATH        flatpak-builder state/cache directory.
  --source-dir=PATH       Minimal source staging directory.
  --bundle=PATH           Output bundle path.
  --bundle-only           Bundle an existing exported repo without rebuilding or installing.
  --branch=NAME           Flatpak branch. Default: stable
  --no-install            Build and bundle without installing the app.
  --no-bundle             Build and install without creating a .flatpak bundle.
  --no-force-clean        Reuse the flatpak-builder build directory.
  --install-deps          Ask flatpak-builder to install missing runtimes from Flathub.
  --add-flathub           Add the user Flathub remote if it is missing.
  --jobs=N                Parallel build jobs. Default: online CPU count minus 2.
  --clean-only            Remove Flatpak build output/state and exit.
  --no-assumeyes          Allow flatpak-builder to prompt.
  -h, --help              Show this help.
EOF
}

for argument in "$@"; do
    case "$argument" in
        --output-dir=*)
            output_dir="${argument#*=}"
            ;;
        --build-dir=*)
            build_dir="${argument#*=}"
            ;;
        --repo-dir=*)
            repo_dir="${argument#*=}"
            ;;
        --state-dir=*)
            state_dir="${argument#*=}"
            ;;
        --source-dir=*)
            source_dir="${argument#*=}"
            ;;
        --bundle=*)
            bundle_path="${argument#*=}"
            ;;
        --bundle-only)
            bundle_only=1
            ;;
        --branch=*)
            branch="${argument#*=}"
            ;;
        --no-install)
            install_app=0
            ;;
        --no-bundle)
            create_bundle=0
            ;;
        --no-force-clean)
            force_clean=0
            ;;
        --install-deps)
            install_deps_from="flathub"
            ;;
        --add-flathub)
            add_flathub=1
            ;;
        --jobs=*)
            build_jobs="${argument#*=}"
            ;;
        --clean-only)
            clean_only=1
            ;;
        --no-assumeyes)
            assume_yes=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n\n' "$argument" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ "$bundle_only" -eq 1 ] && { [ "$create_bundle" -eq 0 ] || [ "$clean_only" -eq 1 ]; }; then
    printf '%s\n' '--bundle-only cannot be combined with --no-bundle or --clean-only' >&2
    exit 2
fi

detect_default_build_jobs()
{
    local cpu_count=""

    if command -v nproc >/dev/null 2>&1; then
        cpu_count="$(nproc)"
    elif getconf _NPROCESSORS_ONLN >/dev/null 2>&1; then
        cpu_count="$(getconf _NPROCESSORS_ONLN)"
    fi

    case "$cpu_count" in
        ''|*[!0-9]*)
            cpu_count=2
            ;;
    esac

    if [ "$cpu_count" -gt 2 ]; then
        printf '%s\n' "$((cpu_count - 2))"
    else
        printf '1\n'
    fi
}

if [ -z "$build_dir" ]; then
    build_dir="$output_dir/build"
fi

if [ -z "$repo_dir" ]; then
    repo_dir="$output_dir/repo"
fi

if [ -z "$state_dir" ]; then
    state_dir="$output_dir/state"
fi

if [ -z "$source_dir" ]; then
    source_dir="$output_dir/source"
fi

if [ -z "$generated_manifest" ]; then
    generated_manifest="$output_dir/io.github.openyamm.OpenYAMM.yml"
fi

if [ -z "$bundle_path" ]; then
    bundle_path="$output_dir/OpenYAMM.flatpak"
fi

if [ -z "$build_jobs" ] || [ "$build_jobs" = "auto" ]; then
    build_jobs="$(detect_default_build_jobs)"
fi

case "$build_jobs" in
    ''|*[!0-9]*)
        printf 'Invalid --jobs value: %s\n' "$build_jobs" >&2
        exit 2
        ;;
esac

if [ "$build_jobs" -lt 1 ]; then
    printf 'Invalid --jobs value: %s\n' "$build_jobs" >&2
    exit 2
fi

if [ "$clean_only" -eq 1 ]; then
    printf 'Removing Flatpak build output: %s\n' "$output_dir"
    rm -rf "$output_dir"

    if [ -d "$repo_root/.flatpak-builder" ]; then
        printf 'Removing legacy Flatpak state: %s\n' "$repo_root/.flatpak-builder"
        rm -rf "$repo_root/.flatpak-builder"
    fi

    exit 0
fi

require_command()
{
    if ! command -v "$1" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$1" >&2
        exit 1
    fi
}

require_file()
{
    if [ ! -f "$repo_root/$1" ]; then
        printf 'Required release input is missing: %s\n' "$1" >&2
        exit 1
    fi
}

require_dir()
{
    if [ ! -d "$repo_root/$1" ]; then
        printf 'Required release input is missing: %s\n' "$1" >&2
        exit 1
    fi
}

create_flatpak_bundle()
{
    require_command flatpak
    if [ ! -d "$repo_dir/objects" ]; then
        printf 'No exported Flatpak repository at: %s\n' "$repo_dir" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$bundle_path")"
    printf 'Creating Flatpak bundle %s\n' "$bundle_path"
    flatpak build-bundle "$repo_dir" "$bundle_path" "$app_id" "$branch"
    printf 'Bundle: %s\n' "$bundle_path"
}

if [ "$bundle_only" -eq 1 ]; then
    create_flatpak_bundle
    exit 0
fi

require_command flatpak-builder
require_command flatpak
require_command cmake

configure_local_ostree_repo()
{
    if ! command -v ostree >/dev/null 2>&1; then
        return
    fi

    ostree --repo="$repo_dir" init --mode=archive-z2
    ostree --repo="$repo_dir" config set core.min-free-space-percent 0
}

version_at_least()
{
    [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n 1)" = "$2" ]
}

require_file settings_release.ini
require_dir assets_dev/engine
require_dir assets_dev/worlds/mm6
require_dir assets_dev/worlds/mm7
require_dir assets_dev/worlds/mm8
require_dir assets_dev/worlds/mmmerge

copy_source_entry()
{
    local source_path="$repo_root/$1"
    local destination_path="$source_dir/$1"

    if [ ! -e "$source_path" ]; then
        printf 'Required source input is missing: %s\n' "$1" >&2
        exit 1
    fi

    mkdir -p "$(dirname "$destination_path")"
    cp -a "$source_path" "$destination_path"
}

stage_flatpak_assets()
{
    local host_build_dir="${OPENYAMM_HOST_BUILD_DIR:-$repo_root/build}"
    if [ ! -f "$host_build_dir/CMakeCache.txt" ]; then
        cmake -S "$repo_root" -B "$host_build_dir" -DCMAKE_BUILD_TYPE=Release \
            -DOPENYAMM_BUILD_TESTS=OFF -DOPENYAMM_BUILD_EDITOR=OFF -DOPENYAMM_BUILD_TOOLS=OFF \
            -DOPENYAMM_BUILD_DESKTOP_EXECUTABLE=OFF \
            -DSDL_ALSA=OFF -DSDL_JACK=OFF -DSDL_KMSDRM=OFF -DSDL_PIPEWIRE=OFF \
            -DSDL_PULSEAUDIO=OFF -DSDL_SNDIO=OFF -DSDL_UNIX_CONSOLE_BUILD=ON \
            -DSDL_WAYLAND=OFF -DSDL_X11=OFF
    fi
    cmake --build "$host_build_dir" --target openyamm_sprite_atlas_cook --parallel "$build_jobs"
    python3 "$repo_root/tools/package_runtime_assets.py" \
        --assets-root "$repo_root/assets_dev" --output "$source_dir/assets" \
        --profile desktop --cooker "$host_build_dir/game/openyamm_sprite_atlas_cook"
}

prepare_source_tree()
{
    printf 'Preparing minimal Flatpak source tree: %s\n' "$source_dir"
    rm -rf "$source_dir"
    mkdir -p "$source_dir"

    copy_source_entry CMakeLists.txt
    copy_source_entry LICENSE
    copy_source_entry COPYRIGHT
    copy_source_entry settings_release.ini
    copy_source_entry cmake
    copy_source_entry engine
    copy_source_entry game
    copy_source_entry packaging/flatpak
    copy_source_entry packaging/icons
    copy_source_entry packaging/licenses
    copy_source_entry tools/openyamm_shaderc_stubs.cpp
    copy_source_entry tools/cook_sprite_atlases_main.cpp
    copy_source_entry tools/SpriteAtlasEncode.cpp
    copy_source_entry tools/SpriteAtlasEncode.h
    copy_source_entry tools/TextureBlockEncode.cpp
    copy_source_entry tools/TextureBlockEncode.h
    copy_source_entry tools/cook_model_textures_main.cpp
    copy_source_entry tools/cook_sprite_atlases.py
    copy_source_entry tools/package_runtime_assets.py
    stage_flatpak_assets

    mkdir -p "$(dirname "$generated_manifest")"
    cmake \
        -DOPENYAMM_FLATPAK_MANIFEST_TEMPLATE="$manifest" \
        -DOPENYAMM_FLATPAK_MANIFEST_OUTPUT="$generated_manifest" \
        -DOPENYAMM_FLATPAK_SOURCE_DIR="$source_dir" \
        -P "$script_dir/CreateOpenYammFlatpakManifest.cmake"
}

flatpak_version="$(flatpak --version | awk '{ print $2 }')"
if [ "$install_deps_from" = "flathub" ] && ! version_at_least "$flatpak_version" "1.12.0"; then
    cat >&2 <<EOF
Flatpak $flatpak_version is too old to install current Flathub runtimes.

This script needs org.freedesktop.Platform and org.freedesktop.Sdk 24.08.
Upgrade flatpak, or install those runtimes with a newer Flatpak client and rerun
this script without --install-deps.
EOF
    exit 1
fi

if [ "$add_flathub" -eq 1 ] && [ "$install_deps_from" = "flathub" ]; then
    if ! flatpak remotes --user --columns=name | grep -Fxq flathub; then
        printf 'Adding user Flatpak remote: flathub\n'
        flatpak --user remote-add --if-not-exists --from flathub https://flathub.org/repo/flathub.flatpakrepo
    fi
fi

mkdir -p "$output_dir" "$repo_dir"
configure_local_ostree_repo
prepare_source_tree

builder_args=(
    "--repo=$repo_dir"
    "--default-branch=$branch"
    "--state-dir=$state_dir"
    "--delete-build-dirs"
    "--jobs=$build_jobs"
    "--user"
)

if [ "$force_clean" -eq 1 ]; then
    builder_args+=("--force-clean")
fi

if [ "$install_app" -eq 1 ]; then
    builder_args+=("--install")
fi

if [ -n "$install_deps_from" ]; then
    builder_args+=("--install-deps-from=$install_deps_from")
fi

if [ "$assume_yes" -eq 1 ]; then
    builder_args+=("-y")
fi

printf 'Building Flatpak app %s (%s, jobs=%s)\n' "$app_id" "$branch" "$build_jobs"
flatpak-builder "${builder_args[@]}" "$build_dir" "$generated_manifest"

if [ "$create_bundle" -eq 1 ]; then
    create_flatpak_bundle
fi

if [ "$install_app" -eq 1 ]; then
    printf 'Installed app: flatpak run %s\n' "$app_id"
fi

exit 0
}
