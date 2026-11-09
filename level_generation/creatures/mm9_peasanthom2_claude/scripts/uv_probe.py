"""Blender: flat (unlit) render of a GLB in its rest pose, Workbench FLAT + TEXTURE, camera like ear_views.py 'rear'
(the character's right ear, 0.13 m) or given yaw; used with a UV-coded head texture to map shot pixels to texels.
Args: <glb> <out png> <yaw deg> <ortho m> [target z offset]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
hb = rig.matrix_world @ rig.pose.bones['Bip01 Head'].head
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = 600
sc.display.render_aa = 'OFF'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[3])
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
t = hb + Vector((0, 0, float(a[4]) if len(a) > 4 else 0.1))
yaw = math.radians(float(a[2]))
d = Vector((math.sin(yaw), -math.cos(yaw), 0))
cam.location = t + d * 3; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = a[1]; bpy.ops.render.render(write_still=True)
print('PROBE', hb[:])
