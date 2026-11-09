#!/bin/bash
# r8 fixes after the paint (user review 2026-11-02), project folder: uv_v3.blend -> uv_v6.blend, then the head paint despeck.
# face_rigid (face on the Head) -> chin_fold (chin pockets, midline fins) -> wrist_fill (glove flare + rim cap) ->
# subdiv_fingers (one smooth cut) -> uv_slivers (origin-collapsed PartUV corners). Then: IN=uv_v6.blend scripts/rebuild.sh
S=$PWD
F='^FACERIGID|Traceback|Error' scripts/run.sh face_rigid.py $S/work/uv_v3.blend $S/work/fix_face.blend
F='^CHINFOLD |Traceback|Error' scripts/run.sh chin_fold.py $S/work/fix_face.blend $S/work/fix_chin.blend
F='^WRISTFILL|Traceback|Error' W=600 scripts/run.sh wrist_fill.py $S/work/fix_chin.blend $S/work/fix_wrist.blend 0.85
F='^SUBDIV|Traceback|Error' scripts/run.sh subdiv_fingers.py $S/work/fix_wrist.blend $S/work/fix_fing.blend
F='^UVSLIVERS|Traceback|Error' W=600 scripts/run.sh uv_slivers.py $S/work/fix_fing.blend $S/work/uv_v6.blend
../claude_shared/gltf_venv/bin/python -W ignore scripts/chin_paint.py work/mm9_kira_r7_rollback.glb 0.95 0.92 2>/dev/null
