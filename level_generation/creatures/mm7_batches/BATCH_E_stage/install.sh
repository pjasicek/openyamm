#!/usr/bin/env bash
# Install the staged Batch E models (run only when the user asks): verify the staged hashes, check winding, install
# each GLB with tools/install_model.py (assets_source copy + runtime copy in assets_dev), then place actors.yml.
# Refuses to overwrite an existing assets_dev/worlds/mm7/models/actors.yml (merge by hand then).
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
if [ -e "$DEST" ]; then echo "$DEST exists: merge $STAGE/assets_dev/worlds/mm7/models/actors.yml by hand" >&2; exit 1; fi
for glb in "$STAGE"/assets_source/worlds/mm7/models/*.glb; do
    python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py "$glb"
    python3 tools/install_model.py "$glb" --world mm7
done
cp "$STAGE/assets_dev/worlds/mm7/models/actors.yml" "$DEST"
echo "installed 5 models and $DEST"
