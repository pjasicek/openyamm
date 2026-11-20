"""Head silhouette / textured head render of a GLB in its bind pose (finishing round 2026-11-04: hair vs MM9's outline).
Camera ortho on the Head bone (world): front = camera on -Y looking +Y rotated by yaw_deg (pick the yaw that shows
the face), side = 90 deg further (true profile).
Args: <glb> <out prefix> <ortho m> <yaw_deg_extra> ; writes <prefix>_front.png/_side.png (RGBA textured, Workbench) and
<prefix>_head.json (head bone world position)."""
import bpy, sys, math, json
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, orth, yaw = a[0], a[1], float(a[2]), float(a[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Icosphere')): o.hide_render = True
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head'))
H = rig.matrix_world @ hb.head
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'TEXTURE'
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = orth
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, extra in (('front', 0.0), ('side', -90.0)):
    ang = math.radians(yaw + extra)
    d = Vector((math.sin(ang), -math.cos(ang), 0))            # yaw 0: camera on -Y looking +Y (faces -Y)
    cam.location = H + d * 3.0
    cam.rotation_euler = (math.radians(90), 0, math.atan2(d.x, -d.y))
    sc.render.filepath = f'{pre}_{v}.png'; bpy.ops.render.render(write_still=True)
json.dump({'head': list(H)}, open(pre + '_head.json', 'w'))
print('HEADSIL', pre, [round(x, 3) for x in H])
