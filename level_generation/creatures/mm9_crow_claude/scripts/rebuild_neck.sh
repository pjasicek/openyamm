#!/usr/bin/env bash
# Neck join rebuild (2026-10-30): graft_v6 -> close_holes -> neck_fair -> maps -> export -> runtime -> viewer tiers (no install).
# Run from the repository root: TOKEN=<lease> level_generation/creatures/mm9_crow_claude/scripts/rebuild_neck.sh <t_min> <t_max>
set -euo pipefail
P=level_generation/creatures/mm9_crow_claude; : "${TOKEN:?set TOKEN}"
B="tools/run_creature_blender.sh --token $TOKEN"
$B $P/scripts/close_holes.py $P/work/graft_v6.blend $P/work/graft_v6c.blend $P/work/close_holes.json >/dev/null
$B $P/scripts/neck_fair.py $P/work/graft_v6c.blend $P/work/anim_v6.blend $P/work/graft_v7.blend $P/work/neck_fair_v7.json "$1" "$2" >/dev/null
export HEAD_GROUPS=Xbeak JAW_GROUPS=Xbeak
FACE_FILTER=head=0 $B $P/scripts/dump_uv3d.py $P/work/graft_v7.blend $P/work/uv3d_crow.npz Body >/dev/null
FACE_FILTER=head=1 $B $P/scripts/dump_uv3d.py $P/work/graft_v7.blend $P/work/uv3d_head.npz Body >/dev/null
SEPARATE_ATTR=head $B $P/scripts/bake_ao.py $P/work/graft_v7.blend Body $PWD/$P/textures/crow_ao_2k.png 0.03 2048 >/dev/null
python3 $P/scripts/compose_crow.py >/dev/null
python3 level_generation/creatures/claude_shared/grade_basecolor.py --ao $P/textures/crow_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/crow_basecolor.png >/dev/null
python3 $P/scripts/compose_crow.py | cut -c1-900
$B $P/scripts/build_export.py $P/work/graft_v7.blend $P/work/anim_v7.blend $P/export/mm9_crow_lod0.glb $P/work/clips_v7.json >/dev/null
python3 tools/creature_workspace.py run --project $P --token "$TOKEN" -- $P/scripts/build_runtime.sh 2>&1 | grep -E "LOD tri|variants|WINDING|^hover "
(cd $P && python3 scripts/viewer_tiers.py >/dev/null && python3 scripts/make_viewer_manifest.py r10_crow_20261030 \
  "crow_a=Bird A (crow)=review/viewer/crow_a.glb" "crow_b=Bird B / C (eagle, BIRD.dtx)=review/viewer/crow_b.glb" >/dev/null)
cat $P/work/neck_fair_v7.json | tr -d '\n '; echo
