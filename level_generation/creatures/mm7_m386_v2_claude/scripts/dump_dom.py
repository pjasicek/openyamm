"""Rest-pose dominant bone per vertex of work/<blend> -> work/dom.npz (co, tri, part = dominant bone index, names)."""
import bpy, os, sys
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'work/rig_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, src))
m = bpy.data.objects['Robot']; me = m.data; me.calc_loop_triangles()
names = [g.name for g in m.vertex_groups]
co = np.array([tuple(v.co) for v in me.vertices]); tri = np.array([tuple(t.vertices) for t in me.loop_triangles])
dom = np.array([max(v.groups, key=lambda g: g.weight).group if v.groups else -1 for v in me.vertices])
np.savez(os.path.join(P, 'work/dom.npz'), co=co, tri=tri, part=dom, names=np.array(names))
print('DOM', len(co), names)
