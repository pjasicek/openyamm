#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
. scripts/env.sh; export VIEWER=${VIEWER:-viewer}
if [ -f textures/liz_ramps.json ]; then $G scripts/viewer_tiers.py >/dev/null; A=review/$VIEWER/liz_a.glb; B=review/$VIEWER/liz_b.glb; C=review/$VIEWER/liz_c.glb; else cp export/mm9_lizardorc.glb review/viewer/liz_a.glb; cp export/mm9_lizardorc.glb review/viewer/liz_b.glb; cp export/mm9_lizardorc.glb review/viewer/liz_c.glb; A=review/viewer/liz_a.glb; B=review/viewer/liz_b.glb; C=review/viewer/liz_c.glb; fi
$G scripts/make_viewer_manifest.py $1 liz_a="Lizard-Orc (row 189)"=$A liz_b="Lizard-Orc Warrior (row 190)"=$B liz_c="Lizard-Orc Mage (row 191)"=$C 2>&1 | tail -1 | cut -c1-100
