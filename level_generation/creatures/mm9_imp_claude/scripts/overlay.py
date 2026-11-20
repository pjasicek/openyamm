"""Grey Body + MM9 mesh (cyan wire) + joints, front/side/top. Args: <blend> <out png> [ortho] [cx cy cz]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out = a[1]; ortho = float(a[2]) if len(a) > 2 else 1.6
c = Vector(tuple(float(x) for x in a[3:6])) if len(a) > 5 else Vector((0, 0.05, -0.03))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_xray = False
sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.55, 0.6)
body = bpy.data.objects.get('Body')
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body:
        o.color = (0.1, 0.9, 0.9, 1); o.display_type = 'WIRE'
        o.show_wire = True; m = o.modifiers.new('w', 'WIREFRAME'); m.thickness = 0.003; 
        o.hide_render = False
    if o.type == 'MESH' and o == body:
        o.color = (0.75, 0.7, 0.55, 1)
arm = bpy.data.objects['MM9_Rig']
import bmesh
me = bpy.data.meshes.new('J'); bm = bmesh.new()
for b in arm.data.bones:
    r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.008, matrix=__import__('mathutils').Matrix.Translation(arm.matrix_world @ b.head_local))
bm.to_mesh(me); bm.free(); J = bpy.data.objects.new('J', me); sc.collection.objects.link(J); J.color = (1, 0.1, 0.1, 1)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
views = {'front': (0, -1, 0), 'side': (1, 0, 0), 'q34': (-0.7, -0.9, 0.3), 'back': (0, 1, 0)}
for n, d in views.items():
    d = Vector(d).normalized()
    cam.location = c + d * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{n}.png'
    bpy.ops.render.render(write_still=True)
