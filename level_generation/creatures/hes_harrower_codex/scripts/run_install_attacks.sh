#!/usr/bin/env bash
# Install the picked library attacks (2026-10-24) and rebuild every runtime export: install_attacks.py puts the
# finished clips of work/cand_final.blend into the base master (default work/before_attacks_20261024/final.blend, the
# master before the attacks; BASE overrides it, e.g. the warglaive base) as work/final.blend, then
# run_rebuild_exports.sh. The first run keeps the previous master, exports and binding in
# work/before_attacks_20261024/. Env as run_lib.sh.
set -euo pipefail
source "$(dirname "$0")/run_lib.sh"
B=work/before_attacks_20261024
if [[ ! -e $B/final.blend ]]; then
    mkdir -p "$B/export" "$B/integration" "$B/review"
    cp work/final.blend "$B/final.blend"; cp export/*.glb export/attachments.json "$B/export/"
    cp integration/actors.yml "$B/integration/"; cp review/validation.json review/lod_audit.json "$B/review/"
fi
blend install install_attacks.py "$W/${BASE:-$B/final.blend}" "$W/work/cand_final.blend" "$W/work/final.blend"
grep INSTALLED "$LOG/install.log" | cut -c1-300
"$W/scripts/run_rebuild_exports.sh"
