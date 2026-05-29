#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
cd "${repo_root}"

python_bin="${PYTHON:-python3}"
build_dir="${OPENYAMM_BUILD_DIR:-build}"
editor_bin="${OPENYAMM_EDITOR_BIN:-${build_dir}/editor/openyamm-editor}"
unit_tests_bin="${OPENYAMM_UNIT_TESTS_BIN:-${build_dir}/tests/openyamm_unit_tests}"
active_maps=("thjorgard" "thjorgardcity")

usage() {
    cat <<'EOF'
usage: run_mm9_active_gate.sh [options]

Runs the focused MM9 active two-map editor gate. This intentionally validates only
the active editor slice, not the future all-map regression scope.

Options:
  --build-dir PATH       Build directory. Default: build
  --editor-bin PATH      openyamm-editor executable. Default: <build-dir>/editor/openyamm-editor
  --unit-tests-bin PATH  openyamm_unit_tests executable. Default: <build-dir>/tests/openyamm_unit_tests
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        --build-dir)
            build_dir="$2"
            editor_bin="${build_dir}/editor/openyamm-editor"
            unit_tests_bin="${build_dir}/tests/openyamm_unit_tests"
            shift 2
            ;;
        --editor-bin)
            editor_bin="$2"
            shift 2
            ;;
        --unit-tests-bin)
            unit_tests_bin="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ ! -x "${editor_bin}" ]]
then
    echo "openyamm-editor executable not found: ${editor_bin}" >&2
    echo "Build it first, for example: cmake --build ${build_dir} --target openyamm-editor openyamm_unit_tests" >&2
    exit 1
fi

if [[ ! -x "${unit_tests_bin}" ]]
then
    echo "openyamm_unit_tests executable not found: ${unit_tests_bin}" >&2
    echo "Build it first, for example: cmake --build ${build_dir} --target openyamm-editor openyamm_unit_tests" >&2
    exit 1
fi

echo "MM9 active gate: event idempotency for assets_dev"
"${python_bin}" tools/mm9_import_discovery/generate_mm9_events.py \
    --only-map thjorgard \
    --only-map thjorgardcity \
    --check-idempotent

echo "MM9 active gate: event idempotency for assets_editor_dev"
"${python_bin}" tools/mm9_import_discovery/generate_mm9_events.py \
    --maps-root assets_editor_dev/worlds/mm9/maps \
    --events-root assets_editor_dev/worlds/mm9/events \
    --only-map thjorgard \
    --only-map thjorgardcity \
    --check-idempotent

echo "MM9 active gate: CTest active-gate checker tests"
ctest --test-dir "${build_dir}" -R mm9_active_gate_tests --output-on-failure

echo "MM9 active gate: focused MM9 DAT editor/import unit tests"
editor_dat_unit_tests=(
    "MM9 DAT parser loads source world models matching generated sidecars"
    "MM9 DAT render mesh preserves source polygon surface and texture ids"
    "MM9 DAT render mesh picking returns DAT source ids"
    "MM9 DAT render mesh material assignment uses map-local aliases"
    "MM9 DAT render mesh bounds and camera frame are finite"
    "MM9 DAT render mesh filters classify roles and surface flags"
    "MM9 DAT mechanism preview transforms target model without mutating source mesh"
    "MM9 DAT surface flag constants match LithTech references"
    "MM9 DAT render mesh filters classify real helper geometry"
    "MM9 DAT render mesh filters split visible water from water volumes"
    "MM9 DAT render mesh filters classify AI rail containers as helper geometry"
    "MM9 DAT level metadata loader reads native editor entrypoint"
    "MM9 DAT level sidecar loaders read generated editor summaries"
    "MM9 DAT world sidecar validation checks source-index and total consistency"
    "MM9 DAT document path inventory separates read-only source from generated state"
    "MM9 DAT level sidecar bundle loader reads all declared native sidecars"
    "MM9 DAT level metadata rejects legacy scene documents"
    "MM9 DAT level file validation reports missing required native assets"
    "MM9 DAT level file validation rejects wrong sidecar kind"
    "MM9 DAT level file validation rejects stale source DAT hash"
    "MM9 DAT level file validation accepts generated active-slice entrypoints"
    "MM9 DAT world sidecars have zero invalid decoded leaf polygon references"
    "MM9 DAT helper world models are classified consistently"
)
editor_dat_filter="$(IFS=,; echo "${editor_dat_unit_tests[*]}")"
"${unit_tests_bin}" --test-case="${editor_dat_filter}" --success=false

echo "MM9 active gate: document dispatch isolation"
"${editor_bin}" --world mm9 --headless-verify-document-dispatch

echo "MM9 active gate: MM6 outdoor editor smoke"
"${editor_bin}" --world mm6 --headless-run-regression-suite editor-world-outdoor-terrain-load

for map_id in "${active_maps[@]}"
do
    echo "MM9 active gate: headless DAT filter validation for ${map_id}.level.yml"
    "${editor_bin}" --world mm9 --headless-verify-mm9-dat-filters "${map_id}.level.yml"

    echo "MM9 active gate: headless DAT validation for ${map_id}.level.yml"
    "${editor_bin}" --world mm9 --headless-verify-mm9-dat-level "${map_id}.level.yml"

    echo "MM9 active gate: headless inspector search for ${map_id}.level.yml"
    "${editor_bin}" --world mm9 --headless-verify-mm9-inspector-search "${map_id}.level.yml"
done

echo "MM9 active gate: active summary counter check"
"${python_bin}" tools/mm9_import_discovery/check_mm9_active_gate.py
