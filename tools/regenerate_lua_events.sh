#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

cd "${repo_root}"

cmake --build build --target openyamm_event_asset_export -j25

exporter="./build/tools/openyamm_event_asset_export"

# Global.lua is shared engine content. Generate it exactly once from the canonical
# MM8/default global source, then regenerate each world's map-local scripts only.
"${exporter}" --world mm8 --lua-export-config tools/lua_event_export.mm8.ini --map __none__
"${exporter}" --world mm6 --lua-export-config tools/lua_event_export.mm6.ini --skip-global
"${exporter}" --world mm7 --lua-export-config tools/lua_event_export.mm7.ini --skip-global
"${exporter}" --world mm8 --lua-export-config tools/lua_event_export.mm8.ini --skip-global
