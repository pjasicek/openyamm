#!/bin/bash
# Clay sheet of the head parts of a geometry npz (project folder): scripts/clay_head.sh <npz> <name>
set -e
P=$(pwd); N=$1; NAME=$2
python3 - "$N" <<'PY'
import sys, numpy as np
B=np.load(sys.argv[1]); co,tri,comp=B['co'],B['tri'],B['comp']; names=list(B['names'])
keep=np.isin(comp,[names.index(n) for n in ('head','dress','arms','hair','ears','braid') if n in names])
tk=keep[tri].all(1); idx=-np.ones(len(co),int); idx[keep]=np.arange(keep.sum())
np.savez('work/view_head.npz', co=co[keep], tri=idx[tri[tk]], comp=comp[keep])
PY
cd ../../..
level_generation/creatures/mm9_peasantf6_claude/scripts/bl.sh scripts/view_npz.py $P/work/view_head.npz $P/review/clay/$NAME 0,0.01,0.64 0.55 512 front:q34:left:q34b:back:below col > /dev/null
cd $P/review/clay && python3 -c "
from PIL import Image
v=['front','q34','left','q34b','back','below']
S=Image.new('RGB',(512*3,1024))
for i,n in enumerate(v): S.paste(Image.open('${NAME}_'+n+'.png').convert('RGB'),(512*(i%3),512*(i//3)))
S.save('${NAME}_sheet.png')"
