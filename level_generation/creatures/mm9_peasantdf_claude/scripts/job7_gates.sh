#!/bin/bash
# Job 7 rebuild tail + gates (repo root): paint d2 d3, rebuild d2 d3, then for d1..d4 gates_pdf.sh, see-through gate,
# sleeve poke (d1: shared arms), one Blender at a time. Outputs review/gates/job7/.
P=level_generation/creatures/mm9_peasantdf_claude
cd $P
for d in d2 d3; do systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 ../claude_shared/gltf_venv/bin/python scripts/ear_paint.py $d work/job7/ears_$d.npz 2>&1 | grep -v Warn | cut -c1-80; done
cd - >/dev/null
$P/scripts/rebuild_designs.sh d2 d3 2>&1 | grep -E "LOD tri|WINDING|Error|Trace"
cd $P
for d in d1 d2 d3 d4; do scripts/gates_pdf.sh $d; mkdir -p review/gates/job7/$d; cp review/gates/$d/*.txt review/gates/$d/*.json review/gates/job7/$d/ 2>/dev/null; done
cd - >/dev/null
for k in 1 2 3 4; do
  $P/scripts/bl.sh "SEETHROUGH|Error|Trace" $P/scripts/see_through_gate.py $PWD/$P/export/mm9_peasantdf$k.glb $PWD/$P/review/gates/job7/see_through_d$k/st.json | tail -3
done
cd $P; systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3 scripts/sleeve_poke_gate.py export/mm9_peasantdf1.glb review/gates/job7/sleeve_poke_d1.json 2>&1 | tail -3
echo JOB7GATES_DONE
