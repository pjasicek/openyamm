#!/bin/bash
R=$PWD
F='^(PROJECT|DESPIKE|MAN|HEADCLOSE)' scripts/run.sh head_close.py $R/work/blocks_face.npz $R/work/face.npz $R/work/face_closed.blend 30000
F='^(SHRUNK|COUNTS|FACE|opt|UNION|MAN|NEW|FINAL)' scripts/run.sh union_bf.py $R/work/pose_v1.blend $R/work/face_closed.blend $R/work/wrap_v1.blend
