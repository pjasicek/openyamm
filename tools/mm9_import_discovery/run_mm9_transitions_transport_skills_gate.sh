#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
openyamm_binary="${1:-${repository_root}/build/game/openyamm}"
unit_tests_binary="${2:-${repository_root}/build/tests/openyamm_unit_tests}"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

cd "${repository_root}"

python3 tools/mm9_import_discovery/generate_mm9_transitions.py
python3 tools/mm9_import_discovery/generate_mm9_transport_routes.py
python3 tools/mm9_import_discovery/generate_mm9_skill_trainers.py
python3 tools/mm9_import_discovery/generate_mm9_teacher_schedules.py

python3 tools/mm9_import_discovery/test_generate_mm9_transitions.py
python3 tools/mm9_import_discovery/test_generate_mm9_transport_routes.py
python3 tools/mm9_import_discovery/test_generate_mm9_skill_trainers.py
python3 tools/mm9_import_discovery/test_generate_mm9_teacher_schedules.py

"${unit_tests_binary}" \
    --test-case='MM9 positioned transition*,MM9 transport*,MM9 RUDE transport*,MM9 skill trainer*,MM9 teacher schedule*,MM9 RUDE trainer topics*' \
    --no-skip

run_diagnostic()
{
    local output_name="$1"
    shift
    "${openyamm_binary}" --world mm9 "$@" > "${temporary_directory}/${output_name}.txt"
    cat "${temporary_directory}/${output_name}.txt"
}

require_output()
{
    local output_name="$1"
    local expected_text="$2"
    grep -Fq "${expected_text}" "${temporary_directory}/${output_name}.txt"
}

run_diagnostic gate_open --headless-open-event guberlandcity.odm 30847 3
require_output gate_open 'mechanism 900847 state=open moving=no distance=1'
require_output gate_open 'mechanism 900848 state=open moving=no distance=1'
require_output gate_open 'affected mechanisms=900847,900848'

run_diagnostic gate_passage --headless-verify-outdoor-mechanism-passage guberlandcity.odm 900847
require_output gate_passage 'name="Gate8L"'
require_output gate_passage 'closed_blocked=yes open_passed=yes'

run_diagnostic transition \
    --headless-verify-mm9-positioned-transition guberlandcity.odm 185
require_output transition 'source_object=185 canceled=yes debounce=yes confirmed=yes'
require_output transition 'destination="guberland.odm" arrival=(-5248,-10140,1761)'

run_diagnostic automatic_transition \
    --headless-verify-mm9-positioned-transition bootcamp.odm 217
require_output automatic_transition 'source_object=217 automatic=yes debounce=yes travel_days=6'
require_output automatic_transition 'destination="isleofashes.odm"'

run_diagnostic outdoor_to_dungeon \
    --headless-verify-mm9-positioned-transition guberland.odm 40
require_output outdoor_to_dungeon 'source_object=40 canceled=yes debounce=yes confirmed=yes'
require_output outdoor_to_dungeon 'destination="templeofhonk.odm"'

run_diagnostic dungeon_to_outdoor \
    --headless-verify-mm9-positioned-transition tasaracademy.odm 319
require_output dungeon_to_outdoor 'source_object=319 canceled=yes debounce=yes confirmed=yes'
require_output dungeon_to_outdoor 'destination="lindisfarne.odm"'

echo "MM9 transitions, transport, and skills focused gate passed."
