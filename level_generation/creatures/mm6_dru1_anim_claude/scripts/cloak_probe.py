"""Cloak extent per height (piece 100 of work/rig_v4f.blend): the angular span around the body axis (0 = straight
back, +90 = her left) and the radius range, per 10 cm band. Args: -- <blend>"""
import bpy, sys, os, math
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']; me = ob.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
rig = bpy.data.objects['Rig']
ax = np.array(rig.data.bones['B_Spine1'].head_local)[:2]
c = co[pv == 100]
a = np.degrees(np.arctan2(c[:, 0] - ax[0], c[:, 1] - ax[1]))
r = np.hypot(c[:, 0] - ax[0], c[:, 1] - ax[1])
print('AXIS', ax.round(3), 'cloak z', c[:, 2].min().round(3), c[:, 2].max().round(3))
for z0 in np.arange(0.0, 1.5, 0.1):
    m = (c[:, 2] >= z0) & (c[:, 2] < z0 + 0.1)
    if m.any():
        print(f'BAND {z0:.1f} n {m.sum():4d} angle {a[m].min():7.1f} {a[m].max():7.1f} radius {r[m].min():.3f} {r[m].max():.3f}')
