"""Rigid belt (review 3: "the belt sways a bit" in the walk): the belt (piece 8) and its medallion (14) copied skin
weights with 22 % thigh weight (left 14 %, right 8 %), so every stride twisted them. Every belt/medallion vertex gets
the same weights: B_Pelvis 0.7, B_Spine 0.3. In place on <blend> (the textured master keeps its own weights; the
rebuild applies the same rule in weights_fix.py). Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
b = bpy.data.objects['Body']; me = b.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
ids = [int(i) for i in np.where(np.isin(pv, (8, 14)))[0]]
for g in b.vertex_groups:
    g.remove(ids)
b.vertex_groups['B_Pelvis'].add(ids, 0.7, 'REPLACE'); b.vertex_groups['B_Spine'].add(ids, 0.3, 'REPLACE')
bpy.ops.wm.save_mainfile()
print('BELTRIGID vertices', len(ids))
