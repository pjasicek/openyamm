"""Seat the staff (work/staff.blend, make_staff.py) in the fist on the solved grip (work/grip_pose.json, grip_from_fist.py):
the staff's grip point (grip_z up its axis) on the grip centre, its axis on the grip axis (head out of the thumb side).
Adds bone 'Staff' (child of B_<side>_Hand, at the grip, +Y along the staff toward the head) and 'Socket_Staff_Head'
(non-deforming, at the gem: bolts and the cast charge leave from it). The staff stays its own object 'Staff', 100 %
on bone Staff (rigid; split into an attachment GLB at export). Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg, common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json'))); side = G['side']
with bpy.data.libraries.load(os.path.join(common.WORK, 'staff.blend'), link=False) as (s_, d_):
    d_.objects = ['Staff']
staff = d_.objects[0]; scene.collection.objects.link(staff)
grip_z, head_z = staff['grip_z'], staff['head_z']
H = rig.data.bones[f'B_{side}_Hand'].matrix_local
ax_l = Vector(G['handle_axis_hand_local']).normalized(); c_l = Vector(G['handle_centre_hand_local'])
R = Vector((0, 0, 1)).rotation_difference(ax_l).to_matrix().to_4x4(); R.translation = c_l
M = H @ R @ Matrix.Translation((0, 0, -grip_z))
staff.data.transform(M); staff.matrix_world = Matrix()
axis_w = (H.to_3x3() @ ax_l).normalized(); grip_w = H @ c_l; head_w = M @ Vector((0, 0, head_z))
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
b = eb.new('Staff'); b.head = grip_w; b.tail = grip_w + axis_w * 0.15; b.parent = eb[f'B_{side}_Hand']
b.align_roll(Vector((0, -1, 0)) - axis_w * Vector((0, -1, 0)).dot(axis_w))
k = eb.new('Socket_Staff_Head'); k.head = head_w; k.tail = head_w + axis_w * 0.05; k.parent = b; k.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
staff.parent = rig
staff.vertex_groups.new(name='Staff').add(list(range(len(staff.data.vertices))), 1.0, 'REPLACE')
m = staff.modifiers.new('Armature', 'ARMATURE'); m.object = rig
foot = M @ Vector((0, 0, 0))
print('SEAT staff', side, 'axis world', [round(x, 3) for x in axis_w], 'tilt from vertical deg', round(math.degrees(axis_w.angle(Vector((0, 0, 1)))), 1),
      'butt z', round(foot.z, 3), 'gem', [round(x, 3) for x in head_w])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
