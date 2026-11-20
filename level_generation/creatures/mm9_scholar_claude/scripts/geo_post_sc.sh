#!/bin/bash
# After the paint (project folder): tweak (ears, legs, forearm stubs) -> linings. work/uv.npz -> work/uv_tw.npz -> work/uv_cap.npz -> work/uv_ln.npz
# Linings: faces seen from behind at rest (work/backfaces.npy) and in posed frames (work/posed_backfaces.npy) plus the robe's hem band, doubled
# 2 mm behind themselves with rim strips (linings_wy.py, the Wyrde's). Budget: LOD0 <= 15k.
set -e
python3 scripts/tweak_sc.py work/asm.npz work/uv.npz work/asm_tw.npz work/uv_tw.npz | tail -3
cp work/uv_tw.npz work/uv_cap.npz      # (jaw_fill_sc.py found no open edge: the jaw gap was paint, head_fix_sc.py 1b) no inner sleeve caps (cuff_caps_sc.py kept for the record: see tweak_sc.py step 3)
if [ -f work/posed_backfaces.npy ]; then
  RINGS=0 PART_RINGS="head=1,hands=0,legs=0,hair=0,cap=0" SKIP_PARTS="jewel,hands,legs" LOOPS="robe:-0.6:0.04" \
    python3 scripts/linings_wy.py work/asm_tw.npz work/uv_cap.npz work/uv_ln.npz 2>&1 | tail -1
else cp work/uv_cap.npz work/uv_ln.npz; fi
