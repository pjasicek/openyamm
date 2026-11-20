"""Close-up of a hand at rest with its bones drawn as thin rods: palm view, back view and side view.
Args: side out_prefix [blend pose: 'rest' or 'Action:frame']"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import author_clips as A, posing as P

args = sys.argv[sys.argv.index('--') + 1:]
side, prefix = args[0], args[1]
pose = args[2] if len(args) > 2 else 'rest'
rig = A.rig
P.reset(rig)
if pose != 'rest':
    act, fr = pose.split(':'); rig.animation_data.action = bpy.data.actions[act]; bpy.context.scene.frame_set(int(fr))
bpy.context.view_layer.update()
hand = rig.pose.bones['mixamorig:' + side + 'Hand']
mid = rig.pose.bones['mixamorig:' + side + 'HandMiddle1']
f = (mid.head - hand.head).normalized()
p = A.HAND_REST[side][1] if pose == 'rest' else (hand.matrix.to_3x3() @ hand.bone.matrix_local.to_3x3().inverted()) @ A.HAND_REST[side][1]
p = (p - f * p.dot(f)).normalized()
centre = hand.head + f * float(os.environ.get('HV_FWD', 0.07))
# bone rods
bm = bmesh.new()
for b in rig.pose.bones:
    if not b.name.startswith('mixamorig:' + side + 'Hand'):
        continue
    h, t = b.head, b.tail
    d = (t - h); L = d.length
    if L < 1e-5:
        continue
    m = Matrix.Translation((h + t) / 2) @ d.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.004, radius2=0.0015, depth=L, matrix=m)
me = bpy.data.meshes.new('rods'); bm.to_mesh(me); rods = bpy.data.objects.new('rods', me)
bpy.context.scene.collection.objects.link(rods)
mat = bpy.data.materials.new('rodmat'); mat.diffuse_color = (1, 0.1, 0.1, 1); me.materials.append(mat)
body = bpy.data.objects['Peasant']
body.show_in_front = False; rods.show_in_front = True
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'MATERIAL'
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name not in ('Peasant', 'rods')
scene.render.resolution_x = scene.render.resolution_y = 520
s = f.cross(p).normalized()
for name, d in (('palm', p), ('back', -p), ('side', s)):
    loc = centre + d * 1.5
    cam_data = bpy.data.cameras.new('c'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = float(os.environ.get('HV_SCALE', 0.30))
    cam = bpy.data.objects.new('c', cam_data); bpy.context.scene.collection.objects.link(cam)
    cam.matrix_world = Matrix.Translation(loc) @ (-d).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    scene.camera = cam
    # x-ray so the rods show through the mesh
    scene.display.shading.show_xray = os.environ.get('HV_XRAY', '1') == '1'; scene.display.shading.xray_alpha = 0.55
    scene.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('HAND', prefix)
