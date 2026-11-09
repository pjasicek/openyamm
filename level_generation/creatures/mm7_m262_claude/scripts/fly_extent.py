"""Front silhouette of the exported master over the Walking (flight) clip: per sampled frame the height and width of
all vertices (body, wings, tail), the front-projected area (x-z occupancy on a 1 cm grid) and the lowest point.
Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
a = bpy.data.actions['Walking']; rig.animation_data_create(); rig.animation_data.action = a
if getattr(a, 'slots', None) is not None and len(a.slots):
    rig.animation_data.action_slot = a.slots[0]
deps = bpy.context.evaluated_depsgraph_get()
for f in range(0, 31, 5):
    sc.frame_set(f); deps.update()
    ev = body.evaluated_get(deps); m = ev.to_mesh()
    co = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    occ = set(zip((co[:, 0] / 0.01).astype(int), (co[:, 2] / 0.01).astype(int)))
    print('FLY frame', f, 'height', round(float(np.ptp(co[:, 2])), 3), 'width', round(float(np.ptp(co[:, 0])), 3),
          'area m2', round(len(occ) * 1e-4, 3), 'low', round(float(co[:, 2].min()), 3), 'top', round(float(co[:, 2].max()), 3))
