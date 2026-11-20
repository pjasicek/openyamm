#!/bin/bash
# scripts/headview.sh <uv npz> <head png> <out prefix> [body png] (repo root): studio-lit head views front, left, q34, below, back + montage
P=level_generation/creatures/mm9_peasantf4_claude
B=${4:-$PWD/$P/textures/pf_body_raw.png}
VIEW_LIGHT=STUDIO $P/scripts/bl.sh scripts/view_uvtex.py $PWD/$P/$1 $B $PWD/$P/$2 $PWD/$P/$3 0,0,0.65 0.34 640 "front=0,-1,0.05:left=1,0,0.02:q34=-1,-1.25,0.3:below=-0.75,-1,-0.5:back=0,1,0.1" > /dev/null 2>&1
cd $P && python3 scripts/montage.py $3_sheet.png 5 front=$3_front.png left=$3_left.png q34=$3_q34.png below=$3_below.png back=$3_back.png
