#!/bin/bash
# Meshy body + head -> fitted, unioned, smoothed, rigged, hands grafted, weighted, reduced, symmetric -> quick clips and gates. Project folder.
R=$PWD
if [[ -z "$FROM_RIG" ]]; then
SC=2.014 WIDEN=1.15 LEG=0.13,0,0 F='^(WIDENED|floor|FITTED)' scripts/run.sh fit_cw.py $R/meshy/cw_smart_v1/model_urls_glb.glb $R/source/true/colloidal2_true.glb $R/work/pose_v1.blend
F='^(COMP|LOOPS|CAP|FILLED|HEADPREP)' W=120 scripts/run.sh head_prep.py $R/meshy/cw_head_smart_v1/model_urls_glb.glb $R/work/head_v1.blend 4 | grep -v '^COMP'
DROP_EYES=1 F='^(HOLES|FIXED)' scripts/run.sh head_fix.py $R/work/head_v1.blend $R/work/head_v1f.blend
OY=-0.03 F='^(PLACED)' scripts/run.sh face_place.py $R/work/head_v1f.blend $R/work/face_closed.blend
F='^(SHRUNK|UNION|MAN|NEW|FINAL)' scripts/run.sh union_cw.py $R/work/pose_v1.blend $R/work/face_closed.blend $R/work/wrap_v1.blend
F='^(SMOOTH)' scripts/run.sh sculpt_fix.py $R/work/wrap_v1.blend $R/work/wrap_v1s.blend
fi
F='^(RIG|RIGGED)' scripts/run.sh rig_cw.py $R/work/wrap_v1s.blend $R/source/true/colloidal2_true.glb $R/work/pose_v1.blend.joints.npz $R/work/rig_v1.blend
./scripts/step_b.sh
./scripts/quick.sh
./scripts/q2.sh
