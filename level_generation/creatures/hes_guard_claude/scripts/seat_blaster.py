"""Seat the blaster (work/blaster.blend, make_blaster.py) in the right fist on the solved grip tunnel
(work/grip_pose.json, grip_from_fist.py). Prop space -> hand: +Z (up the grip, toward the barrel) on the tunnel axis
(its thumb-side end, the tunnel's own sign), +Y (the barrel) along the hand bone's axis (wrist -> knuckles) made
perpendicular to the grip, the grip centre on the tunnel centre: a hanging fist points the barrel down along the
forearm (native standing), a fist held level and thumb-up aims it forward (native attack).
Adds bone 'Blaster' (child of B_R_Hand, at the grip, +Y along the barrel) and 'Socket_Muzzle' (non-deforming, at the
muzzle: the shot leaves there). The prop stays its own object 'Blaster', 100 % on bone Blaster (rigid; split into an
attachment GLB at export). Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json'))); side = G['side']
with bpy.data.libraries.load(os.path.join(common.WORK, 'blaster.blend'), link=False) as (s_, d_):
    d_.objects = ['Blaster']
gun = d_.objects[0]; scene.collection.objects.link(gun)
H = rig.data.bones[f'B_{side}_Hand'].matrix_local
g = Vector(G['handle_axis_hand_local']).normalized(); c = Vector(G['handle_centre_hand_local'])
f = Vector((0, 1, 0))                                       # the hand bone's axis (wrist -> knuckles), hand-local
b = (f - g * f.dot(g)).normalized(); x = b.cross(g)
R = Matrix((x, b, g)).transposed().to_4x4(); R.translation = c
M = H @ R
gun.data.transform(M); gun.matrix_world = Matrix()
grip_w = M @ Vector((0, 0, 0)); barrel_w = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
muzzle_w = M @ Vector(gun['muzzle'])
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
bb = eb.new('Blaster'); bb.head = grip_w; bb.tail = grip_w + barrel_w * 0.12; bb.parent = eb[f'B_{side}_Hand']
bb.align_roll(M.to_3x3() @ Vector((0, 0, 1)))
k = eb.new('Socket_Muzzle'); k.head = muzzle_w; k.tail = muzzle_w + barrel_w * 0.04; k.parent = bb; k.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
gun.parent = rig
gun.vertex_groups.new(name='Blaster').add(list(range(len(gun.data.vertices))), 1.0, 'REPLACE')
m = gun.modifiers.new('Armature', 'ARMATURE'); m.object = rig
fa = rig.data.bones[f'B_{side}_Forearm']
fdir = (rig.data.bones[f'B_{side}_Hand'].head_local - fa.head_local).normalized()
print('SEAT blaster', side, 'barrel world', [round(v, 3) for v in barrel_w], 'angle to forearm deg',
      round(math.degrees(barrel_w.angle(fdir)), 1), 'muzzle', [round(v, 3) for v in muzzle_w])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
