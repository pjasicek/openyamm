"""Rig corrections on work/uv_master.blend (UVs and retexture kept):
- Meshy piece 11 is the tongue, not the central eye (the eye is painted on the head piece): bone EyeBall -> Tongue;
- EyeSocket (non-deforming, parent Head) moves to the painted iris (work/iris.json, from the retexture);
- the eyeball of Stalk3 (the top stalk on the creature's left) is split off its stalk (faces within BALL_R of the
  ball centre, mesh.split keeps the UVs) and bound to a new bone StalkEye under Stalk3_2, so the death can pop it."""
import bpy, bmesh, os, json
import numpy as np
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BALL_R = 0.037
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
mesh = bpy.data.objects['Beholder']; rig = bpy.data.objects['Beholder_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
raw = np.load(os.path.join(P, 'work/raw_st1.npz')); piece = raw['part']
co = np.array([tuple(v.co) for v in mesh.data.vertices]); shift = co[:, 2].min() - raw['co'][:, 2].min()
assert len(co) == len(piece)
iris = json.load(open(os.path.join(P, 'work/iris.json')))
idx = np.nonzero(piece == 12)[0]; p = co[idx]
plan = json.load(open(os.path.join(P, 'work/rig_plan.json')))
st = [b for b in plan['bones'] if b[0].startswith('Stalk3_')]
base = np.array(st[0][2]) + [0, 0, shift]; tip = np.array(st[-1][3]) + [0, 0, shift]
ax = (tip - base) / np.linalg.norm(tip - base)
centre = p[((p - base) @ ax) > 0.15].mean(0)
ball = set(idx[np.linalg.norm(p - centre, axis=1) < BALL_R].tolist())
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
eb['EyeBall'].name = 'Tongue'
s = eb['EyeSocket']; s.parent = eb['Head']
c = Vector(iris['iris_centre']); s.head = c + Vector((0, -0.008, 0)); s.tail = c + Vector((0, -0.03, 0))
e = eb.new('StalkEye'); e.head = Vector(centre.tolist()); e.tail = Vector(centre.tolist()) + Vector(ax.tolist()) * 0.03
e.parent = eb['Stalk3_2']
bpy.ops.object.mode_set(mode='OBJECT')
if 'EyeBall' in mesh.vertex_groups: mesh.vertex_groups['EyeBall'].name = 'Tongue'   # bone rename usually renames it
for o in bpy.data.objects: o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh.data)
for f in bm.faces: f.select = all(v.index in ball for v in f.verts)
bmesh.update_edit_mesh(mesh.data)
nsel = sum(f.select for f in bm.faces)
bpy.ops.mesh.split()
bm = bmesh.from_edit_mesh(mesh.data)
sel = [v.index for v in bm.verts if v.select]
bpy.ops.object.mode_set(mode='OBJECT')
g = mesh.vertex_groups.new(name='StalkEye')
for vi in sel:
    v = mesh.data.vertices[vi]
    for gg in list(v.groups): mesh.vertex_groups[gg.group].remove([vi])
    g.add([vi], 1.0, 'REPLACE')
rig.animation_data.action = bpy.data.actions.get('Fly')
bpy.ops.wm.save_mainfile()
print('FIXED faces', nsel, 'ball verts', len(sel), 'verts now', len(mesh.data.vertices), 'iris', [round(x, 3) for x in c])
