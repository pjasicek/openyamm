"""Diagnosis render: our body (clay) with MM9's mesh as wireframe and its joints as dots. Args: <blend> <mm9 glb> <out prefix> [object name]"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
name = a[3] if len(a) > 3 else 'Body'
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != name: bpy.data.objects.remove(o)
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=a[1])
new = [o for o in bpy.data.objects if o not in ex]
rig = next(o for o in new if o.type == 'ARMATURE')
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in new:
    if o.type == 'MESH' and not o.name.startswith('Box06'): bpy.data.objects.remove(o)
    elif o.type == 'MESH': o.color = (1, 0.2, 0.2, 1)
for b in rig.data.bones:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=rig.matrix_world @ b.head_local)
    s = bpy.context.active_object; s.color = (0.1, 0.3, 1, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_xray = True; sh.xray_alpha = 0.55
sc.render.resolution_x = 900; sc.render.resolution_y = 1000
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4]) if len(a) > 4 else 2.8
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector([float(x) for x in a[5].split(',')]) if len(a) > 5 else Vector((0, 0, 0))
for v, d in {'front': (0, -1, 0), 'side': (1, 0, 0)}.items():
    d = Vector(d); cam.location = C + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{v}.png'; bpy.ops.render.render(write_still=True)
