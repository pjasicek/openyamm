"""Unlit renders of the head (rest pose) with the tier A head set, the inputs for the Codex tier heads and the cameras of the
projection bake. Args: <glb> <out dir> <cx cy cz> <ortho> [size 1254]. Faces -Y; views: front, q34 (camera at -x, 40 deg), side (-x, 90 deg).
Coordinates: GLB is y up with the floor at 0; the render keeps Blender's z up with the import's axes."""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, c, ortho = a[0], a[1], Vector([float(x) for x in a[2:5]]), float(a[5])
size = int(a[6]) if len(a) > 6 else 1254
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True; sh.show_shadows = False; sh.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = size; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for n, deg in (('front', 0), ('q34', 40), ('side', 90)):
    r = math.radians(deg); D = Vector((-math.sin(r), -math.cos(r), 0))
    cam.location = c + D * 5; cam.rotation_euler = (-D).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}/{n}.png'; bpy.ops.render.render(write_still=True)
print('HEADVIEWS done')
