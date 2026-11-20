"""Rest-pose triangles (UV, 3D position, part by dominant bone) of the cockatrice -> work/uv3d.npz.
part: 0 body, 1 wing, 2 leg, 3 tail, 4 neck/head; -1 for faces of the separate head texture set (attribute `head`,
their UVs are the head layout, not the body atlas)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Ckt_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
mesh = bpy.data.objects['Cockatrice']; me = mesh.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
names = {g.index: g.name for g in mesh.vertex_groups}


def part_of(name):
    if name.startswith(('UpperArm', 'ForeArm', 'Finger')):
        return 1
    if name.startswith(('Thigh', 'Shin', 'Tarsus', 'Foot')):
        return 2
    if name.startswith('Tail'):
        return 3
    if name.startswith(('Neck', 'Head')):
        return 4
    return 0


vpart = np.array([part_of(names[max(v.groups, key=lambda g: g.weight).group]) if v.groups else 0 for v in me.vertices])
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
head = me.attributes['head'].data if 'head' in me.attributes else None
P = np.array([-1 if head is not None and head[t.polygon_index].value else
              np.bincount(vpart[list(t.vertices)], minlength=5).argmax() for t in me.loop_triangles], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=X, part=P)
print('DUMPED', len(U), np.bincount(P))
