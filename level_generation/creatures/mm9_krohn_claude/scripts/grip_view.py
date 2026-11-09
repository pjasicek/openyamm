"""Rest-pose check of the fist: the right hand turned by hand_offset and the fingers posed from hand_poses.json, the glaive
static where MM9 keeps it (unparented copy); renders close-ups. Args: blend poses.json outprefix"""
import bpy, sys, json
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
P = json.load(open(a[1]))
rig = bpy.data.objects['Body'].parent
pr = bpy.data.objects['Props']
dg = bpy.context.evaluated_depsgraph_get()
mw = pr.matrix_world.copy()
me = pr.evaluated_get(dg).to_mesh().copy()
st = bpy.data.objects.new('PropsStatic', me); bpy.context.scene.collection.objects.link(st); st.matrix_world = mw
pr.hide_render = True
for n, q in list(P.get('hand_offset', {}).items()) + list(P['grip'].items()):
    pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((q[3], q[0], q[1], q[2]))
bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.4; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = rig.matrix_world @ rig.data.bones['Bip01 R Hand'].head_local
c = c + (rig.matrix_world.to_3x3() @ rig.data.bones['Bip01 R Hand'].matrix_local.to_3x3() @ Vector((0, 0.08, 0)))
for v, d in (('front', Vector((0, -1, 0.1))), ('out', Vector((1, 0, 0))), ('top', Vector((0.1, -0.2, 1))), ('below', Vector((0.2, -0.3, -1))), ('back', Vector((0, 1, 0.1)))):
    d.normalize(); cam.location = c + d * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{v}.png'; bpy.ops.render.render(write_still=True)
print('GRIPVIEW done')
