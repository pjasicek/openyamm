#!/bin/bash
# project folder: work/uv_tex2.npz -> work/uv_lined.npz
../claude_shared/gltf_venv/bin/python -W ignore scripts/line_rims_pf7.py work/uv_tex2.npz work/uv_lined.npz textures/pf_head_a_fix.png textures/pf_body_tone.png textures/pf_body_mask.png 0.06 0.003 0.17 2>&1 | grep -E "LINE_RIMS|Error|Trace"
