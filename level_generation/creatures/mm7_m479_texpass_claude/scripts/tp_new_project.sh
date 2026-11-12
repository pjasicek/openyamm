#!/usr/bin/env bash
# New texture-pass project from the kit (run from the repository root):
#   tp_new_project.sh <world> <stem>    -> level_generation/creatures/<stem>_texpass_claude, lease <world>:<id>
# Copies the kit scripts and the review viewer, backs up the installed GLB and its actors.yml entries, claims.
set -euo pipefail
W=$1; S=$2; ID=${S#${W}_}
KIT=level_generation/creatures/mm6_demon_texpass_claude
P=level_generation/creatures/${S}_texpass_claude
mkdir -p $P/scripts $P/work/before_texpass $P/review/viewer/feedback $P/textures $P/requests $P/export $P/references_hd
cp $KIT/scripts/glb.py $KIT/scripts/texlib.py $KIT/scripts/tp_* $P/scripts/
cp $KIT/review/viewer/index.html $KIT/review/viewer/review.js $P/review/viewer/
echo '{"findings": []}' > $P/review/viewer/feedback/user_feedback.json
cp assets_source/worlds/$W/models/$S.glb $P/work/before_texpass/
python3 $P/scripts/tp_backup_actors.py $W $S $P/work/before_texpass/actors_entries.yml
python3 tools/creature_workspace.py claim --project $P --identity $W:$ID --owner texpass-texpass-1 | tee $P/work/LEASE.txt
python3 $P/scripts/tp_glbinfo.py $P/work/before_texpass/$S.glb | cut -c1-260 | grep -v "_LOD[23]'"
