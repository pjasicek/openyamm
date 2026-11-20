#!/bin/bash
# Meshy -> fitted, grafted, wrapped closed skin. Project folder.
R=$PWD; G=$R/../claude_shared/gltf_venv/bin/python
F='^(KNEE|LEN|floor|FINAL|Traceback|Error)' W=120 scripts/run.sh fit_trell.py $R/meshy/trell_smart_v1/model_urls_glb.glb $R/source/true/trellborg1_true.glb $R/scripts/fit_config.json $R/work/pose_v1.blend | tail -2
F='^(HOLES|BAND|ASSEMBLED|Traceback|Error)' scripts/run.sh graft_trell.py $R/work/pose_v1.blend $R/work/head_parts.blend $R/work/asm_v1.npz
$G scripts/wrap_voxel.py work/asm_v1.npz work/blocks_v1.npz ${H:-0.004} ${RR:-2} 2>&1 | grep -E 'GRID|SOLID|BLOCKS|Trace|Error'
F='^(NONMAN|FOLD|SLIT|NECK|REMESH|PROJECT|SMOOTH|DECIM|MAN|FINAL|Traceback|Error)' scripts/run.sh wrap_finish.py $R/work/blocks_v1.npz $R/work/asm_v1.npz $R/work/wrap_v1.blend ${TARGET:-70000}
