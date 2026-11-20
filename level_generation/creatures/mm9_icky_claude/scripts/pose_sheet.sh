#!/usr/bin/env bash
# Pose renders of a rigged blend: pose_sheet.sh <token> <blend> <outdir> <prefix> <view> <ortho> <centre> <action@frame>...
set -euo pipefail
T=$1; B=$2; O=$3; PRE=$4; VIEW=$5; ORTHO=$6; C=$7; shift 7
P=level_generation/creatures/mm9_icky_claude
for pf in "$@"; do
  n=${pf//@/_}
  tools/run_creature_blender.sh --token $T $P/scripts/render_views.py $B $O ${PRE}_$n $VIEW 384 $pf $ORTHO $C >/dev/null
done
