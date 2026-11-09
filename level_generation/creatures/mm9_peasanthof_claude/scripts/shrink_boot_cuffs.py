"""HOF2: the boots' turned-down cuffs (flared to |x| 0.27 m) poked through the floor-length dress (robe_gate: 5.8-8 cm in
every clip). Under the dress they are hidden, so every vertex mostly weighted to a Calf/Foot bone between Z0 and Z1 (MM9
frame) further than RMAX from that leg's calf axis (Calf joint -> Foot joint) is pulled radially to RMAX. Positions only.
Args: <in blend> <out blend> [z0 -0.80] [z1 -0.45] [rmax 0.065]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
Z0 = float(a[2]) if len(a) > 2 else -0.80; Z1 = float(a[3]) if len(a) > 3 else -0.45; RMAX = float(a[4]) if len(a) > 4 else 0.065
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world; mwi = mw.inverted()
names = {g.index: g.name for g in ob.vertex_groups}
n = 0
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Calf'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Foot'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    for v in ob.data.vertices:
        w = sum(g.weight for g in v.groups if (f'{tok} Calf' in names[g.group] or f'{tok} Foot' in names[g.group]))
        if w < 0.5: continue
        p = np.array(mw @ v.co)
        if not (Z0 < p[2] < Z1): continue
        s = (p - a0) @ ax; foot = a0 + s * ax; d = p - foot; r = np.linalg.norm(d)
        if r > RMAX:
            v.co = mwi @ Vector((foot + d / r * RMAX).tolist()); n += 1
ob.data.update()
print('SHRINK_BOOT_CUFFS moved', n)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
