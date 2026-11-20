#!/usr/bin/env bash
# Install the staged Batch C models (run only when the user asks): verify the staged hashes, check winding, install
# each GLB with tools/install_model.py (assets_source copy + runtime copy in assets_dev), then add the bindings to
# assets_dev/worlds/mm7/models/actors.yml. If that file already exists (Batch E or another batch installed first),
# the Batch C entries are appended; it refuses when any of their descriptors is already bound there.
set -euo pipefail
STAGE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$STAGE/../../../.." && pwd)"; cd "$ROOT"
python3 - "$STAGE" <<'PY'
import hashlib, json, sys
from pathlib import Path
s = Path(sys.argv[1]); m = json.loads((s / 'manifest.json').read_text())
bad = [f for f, h in m['files'].items() if hashlib.sha256((s / f).read_bytes()).hexdigest() != h]
sys.exit('staged files changed since build_stage.py: ' + ', '.join(bad) if bad else 0)
PY
DEST=assets_dev/worlds/mm7/models/actors.yml
python3 - "$STAGE/assets_dev/worlds/mm7/models/actors.yml" "$DEST" <<'PY'
import sys, yaml
from pathlib import Path
new = yaml.safe_load(Path(sys.argv[1]).read_text())['actors']; dest = Path(sys.argv[2])
if dest.exists():
    old = yaml.safe_load(dest.read_text()) or {}
    assert set(old) <= {'actors'}, f'{dest}: unexpected top-level keys {set(old)}; merge by hand'
    dup = {a['descriptor'] for a in old.get('actors', [])} & {a['descriptor'] for a in new}
    sys.exit(f'{dest} already binds {sorted(dup)}; merge by hand' if dup else 0)
PY
for glb in "$STAGE"/assets_source/worlds/mm7/models/*.glb; do
    python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$glb"
    python3 tools/install_model.py "$glb" --world mm7
done
if [ -e "$DEST" ]; then
    { echo; echo "# Batch C (level_generation/creatures/mm7_batches/BATCH_C_stage)"; sed -n '/^actors:/,$p' "$STAGE/assets_dev/worlds/mm7/models/actors.yml" | tail -n +2; } >> "$DEST"
    echo "appended the Batch C bindings to $DEST"
else
    cp "$STAGE/assets_dev/worlds/mm7/models/actors.yml" "$DEST"
fi
python3 -c "import yaml,sys; d=yaml.safe_load(open('$DEST')); print('actors.yml bindings:', len(d['actors']))"
echo "installed $(ls "$STAGE"/assets_source/worlds/mm7/models/*.glb | wc -l) GLBs"
