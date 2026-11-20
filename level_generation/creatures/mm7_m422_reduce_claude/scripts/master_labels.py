"""Per-triangle labels of the production master (read only: ../mm7_m422_claude/work/rig_v6.blend, rest pose):
centroid, piece and garment (majority of the corner vertices), head-set flag -> work/master_tris.npz. The rest
geometry is the export's, so make_groups.py matches source faces to these by centroid."""
import os, bpy, collections, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m422_claude', 'work', 'rig_v6.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
hf = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hf)
co = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
T = np.array([t.vertices[:] for t in me.loop_triangles]); poly = np.array([t.polygon_index for t in me.loop_triangles])
maj = lambda a: np.array([collections.Counter(r).most_common(1)[0][0] for r in a[T]])
np.savez(os.path.join(HERE, 'work', 'master_tris.npz'), cent=co[T].mean(1), piece=maj(pv), garment=maj(gv), head=hf[poly],
         vco=co, vpiece=pv, vgarment=gv)
print('MASTER tris', len(T), 'polys', len(me.polygons), 'verts', len(co))
