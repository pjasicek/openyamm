#!/bin/bash
# clay of poses: looks.sh <glb> <name> <ortho> <cx,cy,cz> <views> Clip@frame ...   (repo root)
P=level_generation/creatures/mm9_bigfoot_claude; R=$PWD/$P; T=$(cat $P/work/token); g=$1; n=$2; o=$3; c=$4; v=$5; shift 5
for p in "$@"; do POSE=$p RES=${RES:-520} tools/run_creature_blender.sh --token $T $P/scripts/look.py $R/$g $R/work/ins/${n}_${p/@/_} $o $c $v </dev/null >/dev/null 2>&1; done
