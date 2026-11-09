"""X-ray of the fitted joints: the body semi-transparent, fitted joints (green) and the original MM9 joints (red).
Args: <fit blend> <mm9 glb> <out png prefix>  (renders front and left views)"""
import bpy, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
fitted = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=argv[1])
src = next(o for o in bpy.data.objects if o not in existing and o.type == 'ARMATURE')
orig = {b.name: src.matrix_world @ b.head_local for b in src.data.bones}
for o in list(bpy.data.objects):
    if o not in existing:
        bpy.data.objects.remove(o)
def mat(name, rgba):
    m = bpy.data.materials.new(name); m.diffuse_color = rgba; return m
mg, mr = mat('g', (0.1, 1, 0.1, 1)), mat('r', (1, 0.1, 0.1, 1))
for pts, m, r in ((orig, mr, 0.012), (fitted, mg, 0.015)):
    for n, p in pts.items():
        if n in ('Scene Root',):
            continue
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p, segments=8, ring_count=6)
        o = bpy.context.active_object; o.data.materials.append(m); o.show_in_front = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'MATERIAL'; sh.show_xray = True; sh.xray_alpha = 0.35
body.data.materials.clear(); body.data.materials.append(mat('b', (0.7, 0.7, 0.7, 1)))
sc.render.resolution_x = 1000; sc.render.resolution_y = 1000
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.4
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in (('front', Vector((0, -1, 0))), ('left', Vector((1, 0, 0)))):
    c = Vector((0, 0, 0.02))
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{argv[2]}_{v}.png'
    bpy.ops.render.render(write_still=True)
print('XRAY done')
