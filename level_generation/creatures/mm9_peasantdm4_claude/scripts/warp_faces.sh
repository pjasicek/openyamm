#!/bin/bash
# Codex repaints warped onto the renders' landmarks (project folder): anchors measured with scripts/iris_centres.py and the
# mouth-line rows (repaint minus input), see README "Face pass".
V=../claude_shared/gltf_venv/bin/python
ANCHORS="482,502,-5,-10;721,499,-4,-6;600,782,0,-15;530,782,0,-15;670,782,0,-15" $V scripts/warp_face.py references_face/in_face_a.png references_face/out_face_a.png references_face/out_face_a_warped.png
ANCHORS="486,511,-7,-16;712,508,8,-12;600,788,0,-20;530,788,0,-20;670,788,0,-20" $V scripts/warp_face.py references_face/in_face_b.png references_face/out_face_b.png references_face/out_face_b_warped.png
