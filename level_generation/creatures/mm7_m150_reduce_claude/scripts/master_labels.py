"""Per-face labels of the accepted master (../mm7_m150_claude/work/rig_v6.blend, read only): face centroid at rest,
piece and garment (point attributes, majority of the face's vertices) -> work/master_faces.npz. The exported body is
the same mesh (export_runtime.py joins the props, which are split off later), so source faces match master faces by
centroid (match_labels.py). Args: none"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'mm7_m150_claude', 'work', 'rig_v6.blend'))
rig = bpy.data.objects['Rig']; b = bpy.data.objects['Body']; me = b.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
me.calc_loop_triangles()
tri = np.array([t.vertices[:] for t in me.loop_triangles]); tp = np.array([t.polygon_index for t in me.loop_triangles])
cen = co[tri].mean(1)
maj = lambda a: np.array([np.bincount(r).argmax() for r in a[tri]])
np.savez(os.path.join(HERE, 'work', 'master_faces.npz'), centroid=cen, piece=maj(pv), garment=maj(gv), head=hd[tp])
print('MASTERFACES', len(tri))
