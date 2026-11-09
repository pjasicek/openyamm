"""Probe: wing-labelled MeshyPosed vertices near the head (the long wrist spikes). Args: fit blend"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']; bones = [b.name for b in arm.data.bones]
mp = bpy.data.objects['MeshyPosed']; body = bpy.data.objects['Body']
lm = np.array([d.value for d in body.data.attributes['label_meshy'].data])
P = np.array([tuple(v.co) for v in mp.data.vertices])
wing = np.array([bones[l].startswith('Y') for l in lm])
for lo, hi in ((0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 6.0), (6.0, 9.0)):
    sel = wing & (np.abs(P[:, 0]) >= lo) & (np.abs(P[:, 0]) < hi)
    if sel.any():
        print('X', lo, hi, int(sel.sum()), 'z', P[sel, 2].min().round(2), P[sel, 2].max().round(2), 'y', P[sel, 1].min().round(2), P[sel, 1].max().round(2))
print('head x', P[np.array([bones[l] in ('Xheadpiv','Xhead') for l in lm])][:, :].min(0).round(2), P[np.array([bones[l] in ('Xheadpiv','Xhead') for l in lm])].max(0).round(2))
