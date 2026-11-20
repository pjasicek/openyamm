#!/bin/bash
# Paint chain of one design (project folder): body compose + gentle grade -> head/hands compose -> paint_clean ->
# seam_tone -> wrist_fix -> face_warm [-> braid_paint (BRAIDS=r,g,b) -> kerchief_hem (HEM=1)] (each restarts from the
# freshly composed maps: RESET=1).
# Usage: scripts/paint_chain.sh <prefix pdfN_tp> <body job dir> <head job dir> <export glb for positions>
# BODY_UPLOAD overrides the body upload (default texturing/pdf_body_upload_tp.glb); CLEAN_ARGS extra paint_clean options.
set -e
pre=$1; bj=$2; hj=$3; glb=$4
PY=../claude_shared/gltf_venv/bin/python
CAP="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
$CAP $PY scripts/compose_texpass.py $pre $bj ${BODY_UPLOAD:-texturing/pdf_body_upload_tp.glb} textures/pdf_tp_ao.png 2>&1 | grep COMPOSE
python3 ../claude_shared/grade_basecolor.py --ao textures/pdf_tp_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 \
  --contrast 1.06 --saturation 1.15 textures/${pre}_basecolor.png | tail -1
$CAP python3 scripts/compose_headhand.py $pre $hj textures/${pre}_basecolor_graded.png textures/${pre}_material_classes.png \
  textures/${pre}_metal_rough_1k.png --ref-head 2>&1 | grep HEADHAND
RESET=1 $CAP $PY scripts/paint_clean.py $glb $pre ${CLEAN_ARGS:-} 2>&1 | grep PAINTCLEAN
if [ -n "${NECKFILL:-}" ]; then $CAP $PY scripts/neck_fill.py $glb $pre --y0 $NECKFILL --r ${NECKR:-0.075} 2>&1 | grep NECKFILL; fi
RESET=1 $CAP $PY scripts/seam_tone.py $glb $pre --cut ${SEAM_CUT:-0.927} 2>&1 | grep SEAMTONE
RESET=1 $CAP $PY scripts/wrist_fix.py $glb $pre --band ${WRIST_BAND:-150,150,155} --hand-ref ${HAND_REF:-forearm} 2>&1 | grep WRISTFIX
RESET=1 $CAP $PY scripts/face_warm.py $glb $pre 2>&1 | grep FACEWARM
if [ -n "${BRAIDS:-}" ]; then python3 scripts/braid_paint.py $pre $BRAIDS | grep BRAIDPAINT; fi
if [ -n "${HEM:-}" ]; then $CAP $PY scripts/kerchief_hem.py $glb $pre 2>&1 | grep KERCHIEFHEM; fi
echo PAINTCHAIN $pre done
