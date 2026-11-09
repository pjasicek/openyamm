#!/bin/bash
# viewer GLBs + manifest. Usage: scripts/viewer_update.sh <rev>
. scripts/env.sh
PYTHONPATH=scripts:../claude_shared $PYG -W ignore scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback|viewer "
python3 scripts/make_viewer_manifest.py $1 "nos_a=Bloodsucker (green)=work/viewer_nos_a.glb" "nos_b=Annelid (red)=work/viewer_nos_b.glb" "nos_c=Vampir (black)=work/viewer_nos_c.glb" | cut -c1-120
