#!/bin/bash
# finish -> rig -> runtime -> viewer -> face shots + sheet. Usage (project folder): scripts/quick_face.sh <rev tag>
set -e
python3 scripts/tweak_wo.py work/asm_f.npz work/uv.npz work/asm_tw.npz work/uv_tw.npz >/dev/null; scripts/linings_wo.sh; python3 scripts/finish_wo.py >/dev/null; python3 scripts/body_fix_wo.py; python3 scripts/finish_wo.py | tail -1 | cut -c1-60
ASM=work/asm_tw.npz systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 scripts/rig_wo.sh work/uv_tex.npz 2>&1 | tail -1
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 scripts/build_runtime_wo.sh 2>&1 | tail -2
scripts/viewer_update.sh $1-20261102 | tail -1
G=../claude_shared/gltf_venv/bin/python; PYTHONPATH=/usr/lib/python3/dist-packages $G -W ignore scripts/face_specs.py export/mm9_wyrdold.glb $1 Standing:0 > work/face_specs_$1.txt
scripts/vs.sh wo review/face_$1 $(cat work/face_specs_$1.txt)
python3 scripts/face_sheet.py review/face_$1 $1 review/face_$1_sheet.png
