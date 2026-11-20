#!/bin/bash
# tiers + runtime build for the listed designs, one after the other (repo root). Usage: scripts/rebuild_designs.sh d1 d2 ...
P=level_generation/creatures/mm9_peasantdf_claude
for d in "$@"; do
  (cd $P && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 ../claude_shared/gltf_venv/bin/python scripts/tiers_pdf.py $d work/pdf_pos.glb 2>&1 | grep -v Warn | cut -c1-200)
  TOKEN=$(cut -d' ' -f3 $P/LEASE_TOKEN.txt) $P/scripts/build_runtime_pdf.sh $d ${INSTALL:-} 2>&1 | grep -E "LOD tri|WINDING|STEP|variants|Error|Traceback|install|Installed|sha"
done
echo REBUILD_DONE
