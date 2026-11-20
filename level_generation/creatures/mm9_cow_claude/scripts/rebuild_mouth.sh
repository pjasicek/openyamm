#!/bin/bash
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures; B=$P/mm9_cow_claude/scripts/bl.sh
export GREP="^MOUTH|^DESPIKE|Error|line [0-9]" RINGS=4
CAP=1.47,0.6,-1.0,-0.78 $B cow despike.py $P/mm9_cow_claude/work/sym_v6.blend $P/mm9_cow_claude/work/desp_v6.blend $P/mm9_cow_claude/work/desp_v6.json
SKIP_ABOVE=0.84 $B goat despike.py $P/mm9_goat_claude/work/sym_v6.blend $P/mm9_goat_claude/work/desp_v6.blend $P/mm9_goat_claude/work/desp_v6.json
MUZZLE=-1.08,-1.19,1.215,1.3,1.13 MOUTH_A=-1.245,1.212 MOUTH_B=-1.12,1.2 CAV_L=0.11 CAV_H=0.035 CAV_F=0.012 LIP_R=0.05 JAW_FADE=0.08 $B cow mouth.py $P/mm9_cow_claude/work/desp_v6.blend $P/mm9_cow_claude/work/mouth_v6.blend $P/mm9_cow_claude/work/mouth_v6.json 2>&1 | cut -c1-200
MOUTH_A=-0.645,0.67 MOUTH_B=-0.565,0.688 CAV_L=0.05 CAV_H=0.016 CAV_F=0.007 LIP_R=0.02 JAW_FADE=0.05 $B goat mouth.py $P/mm9_goat_claude/work/desp_v6.blend $P/mm9_goat_claude/work/mouth_v6.blend $P/mm9_goat_claude/work/mouth_v6.json 2>&1 | cut -c1-200
