#!/bin/bash
# Linings (project folder): faces seen from behind at rest (work/backfaces.npy, visible_backfaces.py on work/asm_tw.npz) and in posed frames
# (work/posed_backfaces.npy, posed_backfaces.py on the export), plus the open lower hem / front-edge bands of the robe (below -0.30) and the
# gown, are doubled 2 mm behind themselves with rim strips (linings_wy.py, the Wyrde's). work/uv_tw.npz -> work/uv_ln.npz. Budget: LOD0 <= 15k.
LINE_CUFF=0 RINGS=0 PART_RINGS="head=1,hands=0,legs=0,braids=0" SKIP_PARTS="jewel,hands,legs" LOOPS="robe:-0.3:0.04,skirt:-0.7:0.03" BOXES="robe:-0.12,0.12:-0.15,0.2:0.40,0.52" \
  python3 scripts/linings_wy.py work/asm_tw.npz work/uv_tw.npz work/uv_ln.npz 2>&1 | tail -1
