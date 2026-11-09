#!/usr/bin/env bash
# Head-set paint chain after the compose (project folder; face fix 2026-11-01). Each step keeps its own first-run backup
# (*_preneck, *_prebrow, *_preface) and reads from it: this script deletes the prebrow/preface backups first so a re-run
# chains from the preneck originals.
# 1 fix_neck.py (collar paint on the neck -> skin, collar shadow), 2 fix_brow.py, 3 project_face.py (Codex eye-area
# repaint by front projection onto the relaxed head of work/eyes_v6.blend's export), 4 fix_seam.py (body set: the neck/shirt shell
# below the head cut continued as the neck skin, region mask zeroed there; reads *_prechest / *_preseam backups).
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
G=${1:-work/pm1_body_tex_v6.glb}
rm -f textures/pm1_tp_head_basecolor_prebrow.png textures/pm1_tp_head_basecolor_preface.png textures/pm1_tp_head_normal_1k_preface.png
rm -f textures/pm1b_tp_head_basecolor_prebrow.png textures/pm1b_tp_head_basecolor_preface.png textures/pm1b_tp_head_normal_1k_preface.png
"$V" scripts/fix_neck.py "$G" pm1_tp pm1b_tp 2>/dev/null
"$V" scripts/fix_brow.py "$G" pm1_tp pm1b_tp 2>/dev/null
"$V" scripts/project_face.py "$G" pm1_tp references_face/out_face_a_final.png 2>/dev/null
"$V" scripts/project_face.py "$G" pm1b_tp references_face/out_face_b.png 2>/dev/null
"$V" scripts/fix_seam.py "$G" 2>/dev/null
