"""Rest-pose triangles of the mantis: UV, 3D position, connected piece, dominant bone and the face attribute `piece`
(the Smart Topology piece number of prep.py) -> work/uv3d.npz."""
import bpy, bmesh, os, json, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Mantis_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
ob = bpy.data.objects['Mantis']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); k = 0
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = k; st.append(w)
    k += 1
names = [g.name for g in ob.vertex_groups]
dom = [names[max(v.groups, key=lambda g: g.weight).group] for v in me.vertices]
bones = sorted(set(dom)); bidx = {b: i for i, b in enumerate(bones)}
me.calc_loop_triangles(); uv = me.uv_layers.active.data
tris = [t for t in me.loop_triangles ]
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
part = np.array([label[t.vertices[0]] for t in tris], dtype=np.int32)
bone = np.array([bidx[dom[t.vertices[0]]] for t in tris], dtype=np.int32)
mpart = np.array([me.attributes['piece'].data[t.polygon_index].value for t in tris], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=part, bone=bone, bones=np.array(bones), mpart=mpart)
print('DUMPED', len(U), 'pieces', k)
