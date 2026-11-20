"""Per loop triangle of the creature's build blend (../mm9_peasantdm4_claude/work/rigid_v3n.blend, the build default):
rest centroid (object local), face attributes head/hand/lined -> work/blend_parts.npz."""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
co = np.array([v.co[:] for v in me.vertices]); mw = np.array(o.matrix_world)
co = co @ mw[:3, :3].T + mw[:3, 3]
tris = np.array([t.vertices[:] for t in me.loop_triangles]); poly = np.array([t.polygon_index for t in me.loop_triangles])
att = {k: np.array([d.value for d in me.attributes[k].data]) for k in ('head', 'hand', 'lined')}
out = dict(cen=co[tris].mean(1), co=co, tri=tris, poly=poly, **{k: v[poly] for k, v in att.items()})
for k in ('head', 'hand', 'lined'):
    u, c = np.unique(out[k], return_counts=True); print('ATTR', k, dict(zip(u.tolist(), c.tolist())))
np.savez(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'blend_parts.npz'), **out)
print('BLEND_PARTS', len(tris))
