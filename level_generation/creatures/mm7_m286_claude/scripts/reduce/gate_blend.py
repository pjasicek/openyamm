"""Gate copy of the gated master with a runtime-equivalent body and axe, for the Arm and hand gate on the reduced model:
open work/rig_v5.blend (read only, never saved in place), replace Body by <object> from <blend> (a ladder candidate,
or 'Body' of work/source.blend = the v2c export LOD0, 4 influences, for a like-for-like baseline), carry the 'piece',
'garment' and 'finger' point labels from the master Body by nearest rest vertex, and attach the axe LOD0 of <axe glb>
(glTF axe space = the prop frame of axe_frame.py) 100 % on a 'Sword' bone as axe_attach.py does (piece 1000 /
garment 9). Usage: blender -b -P gate_blend.py -- <blend> <object> <axe glb> <out blend>"""
import json, os, struct, sys, bpy
import numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import axe_frame  # noqa: E402
lib, name, axe_glb, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; old = bpy.data.objects['Body']
with bpy.data.libraries.load(os.path.abspath(lib), link=False) as (src, dst):
    dst.objects = [name]
new = dst.objects[0]; sc.collection.objects.link(new)
for m in list(new.modifiers):
    new.modifiers.remove(m)
new.parent = rig; new.matrix_parent_inverse = old.matrix_parent_inverse.copy(); new.matrix_basis = old.matrix_basis.copy()
new.modifiers.new('Armature', 'ARMATURE').object = rig
bones = {b.name for b in rig.data.bones}
for g in list(new.vertex_groups):
    if g.name not in bones:
        new.vertex_groups.remove(g)
om = old.data; t = kdtree.KDTree(len(om.vertices))
for v in om.vertices:
    t.insert(v.co, v.index)
t.balance()
near = [t.find(v.co) for v in new.data.vertices]
for at in ('piece', 'garment', 'finger'):
    if at in om.attributes:
        vals = np.zeros(len(om.vertices), np.int32); om.attributes[at].data.foreach_get('value', vals)
        new.data.attributes.new(at, 'INT', 'POINT').data.foreach_set('value', [int(vals[i]) for _, i, _ in near])
print('GATEBLEND', name, 'verts', len(new.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in new.data.polygons),
      'label map max dist mm', round(max(d for _, _, d in near) * 1000, 3), 'old matrix identity', old.matrix_world.is_identity)
bpy.data.objects.remove(old, do_unlink=True); new.name = 'Body'; new.data.name = 'Body'
# axe LOD0 from the GLB (raw arrays)
b = open(os.path.abspath(axe_glb), 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; d = json.loads(b[20:20 + n]); base = 20 + n + 8
def acc(i):
    a = d['accessors'][i]; bv = d['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]; k = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    return np.frombuffer(b, comp, a['count'] * k, base + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], k)
p = d['meshes'][0]['primitives'][0]; P = acc(p['attributes']['POSITION']); I = acc(p['indices']).reshape(-1, 3)
me = bpy.data.meshes.new('AxeMesh'); me.from_pydata([tuple(map(float, x)) for x in P], [], [tuple(map(int, x)) for x in I]); me.update()
ax = bpy.data.objects.new('AxeMesh', me); sc.collection.objects.link(ax)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
M = rig.data.bones['B_R_Hand'].matrix_local @ axe_frame.hand_local(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.get('Sword') or rig.data.edit_bones.new('Sword')
eb.head = M.translation; eb.tail = M.translation + M.col[1].xyz * 0.15; eb.align_roll(M.col[2].xyz)
eb.parent = rig.data.edit_bones['B_R_Hand']; eb.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
ax.data.transform(M); nv = len(ax.data.vertices)
ax.vertex_groups.new(name='Sword').add(list(range(nv)), 1.0, 'REPLACE')
body = bpy.data.objects['Body']
for at in ('piece', 'garment', 'finger'):
    if at in body.data.attributes:
        ax.data.attributes.new(at, 'INT', 'POINT').data.foreach_set('value', [1000 if at == 'piece' else (9 if at == 'garment' else 0)] * nv)
if 'Sword' not in body.vertex_groups:
    body.vertex_groups.new(name='Sword')
for o in bpy.data.objects:
    o.select_set(o in (body, ax))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('GATEBLEND axe verts', nv, 'tris', len(I), '->', out)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
