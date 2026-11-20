#!/bin/bash
# All four designs' paint chains with their settings (project folder). Usage: scripts/paint_all.sh [d1 d2 d3 d4]
G=work/pdf_pos.glb
for d in ${@:-d1 d2 d3 d4}; do case $d in
  d1) WRIST_BAND=158,160,168 scripts/paint_chain.sh pdf1_tp meshy/body_retexture_d1 meshy/head_retexture_d1 $G;;
  d2) NECKR=0.092 NECKFILL=0.862 HEM=1 WRIST_BAND=165,160,150 scripts/paint_chain.sh pdf2_tp meshy/combined_retexture_d2_body meshy/head_retexture_d4 $G;;
  d3) BRAIDS=196,112,52 CLEAN_ARGS="--lip-tone 0.55" WRIST_BAND=110,70,45 scripts/paint_chain.sh pdf3_tp meshy/body_retexture_d3 meshy/head_retexture_d3 $G;;
  d4) NECKFILL=0.872 HAND_REF=face WRIST_BAND=205,190,160 scripts/paint_chain.sh pdf4_tp meshy/body_retexture_d4 meshy/head_retexture_d4 $G;;
esac; done
