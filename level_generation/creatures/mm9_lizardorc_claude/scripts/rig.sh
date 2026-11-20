#!/bin/bash
# fingers -> heat -> weights -> quick glb -> clips. Project folder.
. scripts/env.sh
$G - <<'P'
import numpy as np
D=np.load('work/joined.npz'); nb=int(D['nb']); co=D['co'][:nb]; tri=D['tri']; tri=tri[(tri<nb).all(1)]
np.savez('work/body_rig.npz',co=co,tri=tri)
part=D['part']; ids=np.where(part==0)[0]; r=-np.ones(len(part),int); r[ids]=np.arange(len(ids)); t=tri[(part[tri]==0).all(1)]
np.savez('work/main.npz',co=D['co'][ids],tri=r[t],ids=ids)
P
$G scripts/fingers.py work/body_rig.npz 2>&1 | grep -E '^Finger|^Thumb|Error'
$G scripts/prep_bones.py work/main.npz 2>/dev/null
TAIL=4 scripts/run.sh heat.py $P/work/main.npz $P/work/heat2.npz 2>&1 | grep -E 'HEAT|rror|failed'
