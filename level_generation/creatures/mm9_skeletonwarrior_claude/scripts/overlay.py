"""Side and front overlay of Body (blue) and the MM9 mesh (orange) plus joint dots. Args: <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'OBJECT'
sc.display.shading.show_xray = True; sc.display.shading.xray_alpha = 0.5
sc.render.resolution_x = 900; sc.render.resolution_y = 1000
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (1, 1, 1); sc.display.shading.background_type = 'WORLD'
b = bpy.data.objects['Body']; m = bpy.data.objects['MM9_Mesh']
b.color = (.1, .3, 1, 1); m.color = (1, .5, .05, 1)
rig = bpy.data.objects['MM9_Rig']
for n in ('Bip01 R UpperArm','Bip01 R Forearm','Bip01 R Hand','Bip01 R Thigh','Bip01 R Calf','Bip01 R Foot','Bip01 R Toe0','Bip01 Head','Bip01 Spine','Bip01 Pelvis'):
    s = bpy.data.objects.new('j', None); sc.collection.objects.link(s)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.018, location=rig.matrix_world @ rig.data.bones[n].head_local); o = bpy.context.active_object; o.color = (1, 0, 0, 1)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.3; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, -0.04))
for n, d in dict(front=(0, -1, 0), side=(1, 0, 0)).items():
    cam.location = c + Vector(d) * 8
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'
    bpy.ops.render.render(write_still=True)
