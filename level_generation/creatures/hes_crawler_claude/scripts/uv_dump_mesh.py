"""Rest mesh for the xatlas unwrap: positions, triangles (polygons are triangles) and a head flag per triangle
(dominant bone Head, Mandible_* or Sac) -> work/uv_in.npz."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
ob = bpy.data.objects['Crawler']; me = ob.data
assert all(len(p.vertices) == 3 for p in me.polygons)
names = [g.name for g in ob.vertex_groups]
dom = [names[max(v.groups, key=lambda g: g.weight).group] for v in me.vertices]
pos = np.array([tuple(v.co) for v in me.vertices], np.float32)
idx = np.array([tuple(p.vertices) for p in me.polygons], np.uint32)
head = np.array([sum(dom[i] in ('Head', 'Mandible_L', 'Mandible_R', 'Sac') for i in t) >= 2 for t in idx])
np.savez(os.path.join(HERE, 'work', 'uv_in.npz'), pos=pos, idx=idx, head=head)
print('UVDUMP', len(pos), len(idx), int(head.sum()))
