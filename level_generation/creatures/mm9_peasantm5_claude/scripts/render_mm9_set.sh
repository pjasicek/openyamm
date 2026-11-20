#!/bin/bash
# Render MM9 body (5 views) + head (5 views) for each <glb>:<name> into <outdir>/<name>/. Repo root. One Blender at a time.
set -e
OUT=$1; HZ=$2; shift 2
RR=$(dirname $0)/ref_renders.py
for spec in "$@"; do
  g=${spec%%:*}; n=${spec##*:}
  mkdir -p $OUT/$n
  B="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python $RR --"
  $B $g $OUT/$n body 640 1.95 > $OUT/$n/render.log 2>&1
  VIEWS=q34,front,left,back,right CENTER=0,0,$HZ $B $g $OUT/$n head 512 0.42 > $OUT/$n/render_head.log 2>&1
done
