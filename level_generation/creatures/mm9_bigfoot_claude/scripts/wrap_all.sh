#!/bin/bash
# graft -> voxel wrap -> finish. Project folder, env TARGET.
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
F='^(CAP|LOOPS|FILLED|FACE|PIECES|HEADPREP)' W=120 scripts/run.sh head_prep.py $R/meshy/bf_head_smart_v1/model_urls_glb.glb $R/work/head_v1.blend 4 | tail -12
F='^(BOUNDARY|floor|FITTED)' scripts/run.sh fit_bf.py $R/meshy/bf_smart_v1/model_urls_glb.glb $R/source/true/bigfoot1_true.glb $R/work/pose_v1.blend
F='^(NPZ)' scripts/run.sh face_npz.py $R/work/head_v1.blend $R/work/face.npz
$G scripts/wrap_bf.py work/face.npz work/blocks_face.npz 0.002 1 2>&1 | grep -E 'LABELS|SOLID|BLOCKS|Error|Traceback'
F='^(PROJECT|MAN|HEADCLOSE)' scripts/run.sh head_close.py $R/work/blocks_face.npz $R/work/face.npz $R/work/face_closed.blend 30000
F='^(SHRUNK|COUNTS|FACE|opt|UNION|MAN|NEW|FINAL)' scripts/run.sh union_bf.py $R/work/pose_v1.blend $R/work/face_closed.blend $R/work/wrap_v1.blend
