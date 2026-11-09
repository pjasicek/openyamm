"""Club geometry in its own space (work/club_in.npz: verts, faces, wedge uv, normals) and the grip: club faces within
REA_GRIP_R (default 0.025 m) of the body's left hand and finger skin at rest (club placed on the Club bone as the
engine attaches it), from work/review_r100.glb. -> work/club_in.npz, work/club_grip.npy"""
import os, bpy, bmesh, numpy as np
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', 'review_r100.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
club = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('ClubReview'))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Troll')
dg = bpy.context.evaluated_depsgraph_get()
bb = bmesh.new(); bb.from_object(body, dg); bb.transform(body.matrix_world)
names = {g.index: g.name for g in body.vertex_groups}
hand = [i for i, v in enumerate(body.data.vertices) if v.groups and names[max(v.groups, key=lambda g: g.weight).group].startswith(('B_L_Finger', 'B_L_Hand'))]
bb.verts.ensure_lookup_table(); t = KDTree(len(hand))
for k, i in enumerate(hand):
    t.insert(bb.verts[i].co, k)
t.balance()
me = club.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data; W = club.matrix_world
R = float(os.environ.get('REA_GRIP_R', '0.025'))
near = np.array([t.find(W @ v.co)[2] < R for v in me.vertices])
tris = me.loop_triangles
f = np.array([tt.vertices[:] for tt in tris], np.int32)
np.savez(os.path.join(HERE, 'work', 'club_in.npz'), verts=np.array([v.co[:] for v in me.vertices]), faces=f,
         wuv=np.array([[uv[l].uv[0] + 2.0 * tt.material_index, uv[l].uv[1]] for tt in tris for l in tt.loops]),
         protect=near[f].any(1).astype(float))
np.save(os.path.join(HERE, 'work', 'club_grip.npy'), near[f].any(1))
co = np.array([v.co[:] for v in me.vertices])
print('CLUB verts', len(co), 'tris', len(f), 'size', (co.max(0) - co.min(0)).round(3), 'grip faces', int(near[f].any(1).sum()),
      'grip span', co[near].min(0).round(3) if near.any() else None, co[near].max(0).round(3) if near.any() else None, 'mats', [m.name for m in me.materials])
