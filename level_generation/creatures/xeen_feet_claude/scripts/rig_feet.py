"""The pair: the textured right foot (work/foot_uv.blend, 3,234 triangles, our uv_atlas layout) and its mirrored copy
as the left foot (same UVs, faces reversed), placed as in the native frames (the right foot higher and further back,
toes turned out; the left foot lower and nearer, toes toward the party), joined into one mesh 'Feet' on rig
'Feet_Rig'. Forward -Y, the creature's left is +X.
Bones: Root; per side s (R, L): Foot_s (rigid body, pivot at the foot's centre), Toes_s (child; the toes ramp in over
the ball of the foot), WingIn_s / WingOut_s (child; medial and lateral wing, rigid, hinge at the wing root).
Writes work/rig.blend and work/rig_layout.json. Args: -- [source blend in work/] (default foot_uv.blend)"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0] if a else 'foot_uv.blend'))
src = bpy.data.objects['Foot']
H = json.load(open(os.path.join(HERE, 'work', 'foot_hinges.json')))
co = np.array([v.co[:] for v in src.data.vertices])
gi = {g.name: g.index for g in src.vertex_groups}
body = np.array([any(g.group == gi['Foot'] or g.group == gi['Toes'] for g in v.groups) for v in src.data.vertices])
bc = co[body]
PIVOT = Vector(((bc[:, 0].min() + bc[:, 0].max()) / 2, (bc[:, 1].min() + bc[:, 1].max()) / 2, 0.06))
ball_y = sum(H['ball']) / 2
toe_sel = bc[(bc[:, 1] < ball_y + 0.01) & (bc[:, 1] > ball_y - 0.01)]
BALL = Vector((float(toe_sel[:, 0].mean()), ball_y, float(np.percentile(toe_sel[:, 2], 40))))
TOE_TIP = Vector((float(bc[np.argmin(bc[:, 1])][0]), float(bc[:, 1].min()), BALL.z))
# layout: (world position of PIVOT, yaw degrees); the creature's right foot is at -X
LAYOUT = {'R': ((-0.185, 0.065, 0.135), -22.0), 'L': ((0.185, -0.055, 0.06), 8.0)}
MIRROR = {'R': Matrix.Identity(4), 'L': Matrix.Scale(-1, 4, Vector((1, 0, 0)))}


def place(side):
    p, yaw = LAYOUT[side]
    piv = MIRROR[side] @ PIVOT
    return Matrix.Translation(Vector(p)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Translation(-piv) \
        @ MIRROR[side]


arm = bpy.data.armatures.new('Feet_Rig'); rig = bpy.data.objects.new('Feet_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
root = eb.new('Root'); root.head = (0, 0, 0); root.tail = (0, 0, 0.12)
info = {}
for s in ('R', 'L'):
    M = place(s)
    f = eb.new(f'Foot_{s}'); f.head = M @ PIVOT; f.tail = M @ (PIVOT + Vector((0, 0, 0.08))); f.parent = root
    f.align_roll(M.to_3x3() @ Vector((0, -1, 0)))
    t = eb.new(f'Toes_{s}'); t.head = M @ BALL; t.tail = M @ TOE_TIP; t.parent = f
    t.align_roll(Vector((0, 0, 1)))
    for w in ('WingIn', 'WingOut'):
        b = eb.new(f'{w}_{s}'); b.head = M @ Vector(H['hinges'][w]); b.tail = M @ Vector(H['hinges'][w + '_tip'])
        b.parent = f; b.align_roll(Vector((0, 0, 1)))
    info[s] = {'pivot': list(M @ PIVOT), 'ball': list(M @ BALL), 'matrix': [list(r) for r in M]}
bpy.ops.object.mode_set(mode='OBJECT')
objs = []
for s in ('R', 'L'):
    o = src.copy(); o.data = src.data.copy(); o.name = f'foot_{s}'
    bpy.context.scene.collection.objects.link(o)
    o.data.transform(place(s))
    if s == 'L':
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()
    for g in o.vertex_groups:
        g.name = f'{g.name}_{s}'
    objs.append(o)
bpy.data.objects.remove(src, do_unlink=True)
for o in bpy.data.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
feet = bpy.context.view_layer.objects.active
feet.name = feet.data.name = 'Feet'
feet.data.update()
feet.parent = rig
mod = feet.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
unw = [v.index for v in feet.data.vertices if not v.groups]
co = np.array([v.co[:] for v in feet.data.vertices])
print('MESH Feet tris', len(feet.data.polygons), 'groups', sorted(g.name for g in feet.vertex_groups), 'unweighted', len(unw))
print('BOX', co.min(0).round(3), co.max(0).round(3))
json.dump({'layout': LAYOUT, 'pivot': list(PIVOT), 'ball': list(BALL), 'sides': info},
          open(os.path.join(HERE, 'work', 'rig_layout.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig.blend'))
print('SAVED rig.blend bones', [b.name for b in arm.bones])
