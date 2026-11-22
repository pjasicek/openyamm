"""Dump vertex part labels (max face part per vertex) of work/<blend> Skull -> work/<out>_vpart.npy"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
me = bpy.data.objects['Skull'].data
fp = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', fp)
vp = -np.ones(len(me.vertices), np.int32)
for p, k in zip(me.polygons, fp):
    for v in p.vertices:
        vp[v] = max(vp[v], k)
np.save(os.path.join(HERE, 'work', a[1] + '_vpart.npy'), vp)
print('VPART', np.bincount(vp + 1).tolist())
