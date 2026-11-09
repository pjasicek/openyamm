#!/usr/bin/env bash
# In-game captures of the current export without changing the game: install it, snapshot a hard-linked assets fixture
# (ingame_prepare.py), reinstall the rollback source, then run the tours against the fixture. Usage: capture.sh <label>
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm8_m596_v2_claude; L=$1
mkdir -p $P/work/restore; cp $P/work/mm8_m596_source_pre_v2.glb $P/work/restore/mm8_m596.glb
restore() { python3 tools/install_model.py $P/work/restore/mm8_m596.glb --world mm8 >/dev/null; }
trap restore EXIT
python3 tools/install_model.py $P/export/mm8_m596.glb --world mm8 >/dev/null
python3 $P/scripts/ingame_prepare.py "$L" >/dev/null
restore; trap - EXIT
cmp -s $P/work/mm8_m596_source_pre_v2.glb assets_source/worlds/mm8/models/mm8_m596.glb && echo "installed model restored"
bash $P/scripts/ingame_run.sh "$L"
