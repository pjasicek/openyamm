#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
. scripts/env.sh
python3 scripts/viewer_tiers.py >/dev/null
$G scripts/make_viewer_manifest.py $1 trog_a="Troglodyte (row 96)"=review/viewer/trog_a.glb trog_b="Troglodyte Wren (row 97)"=review/viewer/trog_b.glb trog_c="Troglodyte Gnoll (row 98)"=review/viewer/trog_c.glb 2>&1 | tail -1 | cut -c1-100
