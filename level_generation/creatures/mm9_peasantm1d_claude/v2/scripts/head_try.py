"""Lit close-ups of the head with another head base colour. Args: <glb> <out png> <head png> [views]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
for m in bpy.data.materials:
    if 'Head' in m.name and m.use_nodes:
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        t = b.inputs['Base Color'].links[0].from_node
        while t.type != 'TEX_IMAGE':
            t = t.inputs[0].links[0].from_node
        t.image = bpy.data.images.load(a[2]); t.image.colorspace_settings.name = 'sRGB'
bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
sc.world = bpy.data.worlds.new('w'); sc.world.color = (.4, .42, .45); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.42; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0.02, 1.66))
for n, deg in (('f', 0), ('q', 40), ('s', 90), ('qm', -40)):
    r = math.radians(deg); D = Vector((-math.sin(r), -math.cos(r), 0))
    cam.location = c + D * 5; cam.rotation_euler = (-D).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
