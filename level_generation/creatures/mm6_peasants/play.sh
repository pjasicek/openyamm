#!/usr/bin/env bash
set -euo pipefail

demo_root="${OPENYAMM_SORPIGAL_PEASANTS_DEMO:-/tmp/openyamm-sorpigal-peasants-playtest}"
demo_mode="${1:-enhanced}"
case "$demo_mode" in
    original|enhanced) ;;
    *) echo 'Usage: play.sh [enhanced|original] [--reset-start]' >&2; exit 2 ;;
esac
if [[ $# -gt 2 || ( $# -eq 2 && "$2" != '--reset-start' ) ]]; then
    echo 'Usage: play.sh [enhanced|original] [--reset-start]' >&2
    exit 2
fi
if [[ ! -f "$demo_root/playtest_snapshot.json" ]]; then
    echo 'Prepare first: python3 level_generation/creatures/mm6_peasants/prepare_playtest.py' >&2
    exit 1
fi
if [[ "${2:-}" == '--reset-start' ]]; then
    cp -- "$demo_root/seed/New_Sorpigal_Start.oysav" "$demo_root/$demo_mode/saves/New_Sorpigal_Start.oysav"
fi
echo "New Sorpigal: $demo_mode visuals. Choose Load Game and the supplied starting save."
cd -- "$demo_root/$demo_mode"
exec ../openyamm --world mm6
