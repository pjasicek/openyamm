#!/usr/bin/env bash
# Android asset cooks, on demand (before a release or push): every cook into assets_cooked/android, each incremental
# (only sources or settings changed since its receipt are cooked again), then each cook's --verify. Desktop cooks into
# assets_dev run with the normal build and tools/install_model.py; nothing cooks for Android automatically.
#
#   tools/cook_android.sh            cook what changed, then verify
#   tools/cook_android.sh --repack   also rebuild the Android runtime packages (android/repack_runtime_assets.sh)
#
# See ASSET_COOKING_PLAN.md. OPENYAMM_HOST_BUILD_DIR selects the desktop build that provides the cooker (default build).
set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build_dir="${OPENYAMM_HOST_BUILD_DIR:-${repo_root}/build}"
repack=false
for argument in "$@"; do
    case "${argument}" in
        --repack) repack=true ;;
        *) echo "usage: tools/cook_android.sh [--repack]" >&2; exit 2 ;;
    esac
done

cd "${repo_root}"
cmake --build "${build_dir}" --target openyamm_model_texture_cook --parallel "${CMAKE_BUILD_PARALLEL_LEVEL:-25}"
cooker="${build_dir}/game/openyamm_model_texture_cook"

python3 tools/cook_models.py --profile android --cooker "${cooker}"
python3 tools/cook_surface_textures.py --profile android --cooker "${cooker}"
# Xeen's x2 sources are the PNGs xtex.py installs beside its x4 cook in assets_dev (lane P, 2026-11-22).
python3 tools/cook_surface_textures.py --profile android --world xeen --sources assets_dev --cooker "${cooker}"
python3 tools/terrain_materials.py cook --profile android
python3 tools/cook_effect_textures.py --profile android --cooker "${cooker}"
python3 tools/cook_ui_textures.py --profile android --cooker "${cooker}"
python3 tools/cook_sky_textures.py --profile android --cooker "${cooker}"

python3 tools/cook_models.py --verify
python3 tools/cook_surface_textures.py --profile android --verify
python3 tools/cook_surface_textures.py --profile android --world xeen --sources assets_dev --verify
python3 tools/cook_effect_textures.py --profile android --verify
python3 tools/cook_ui_textures.py --profile android --verify
python3 tools/cook_sky_textures.py --profile android --verify

if "${repack}"; then
    android/repack_runtime_assets.sh
fi
echo "Android cooks are current."
