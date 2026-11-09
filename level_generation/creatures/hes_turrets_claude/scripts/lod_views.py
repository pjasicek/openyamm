"""Workbench views of every LOD in the actor's LOD0 and authored-LOD exports (rest pose), side by side per view.
Args: -- <actor name> <out prefix>"""
import math, os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, prefix = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'export', f'{name}_lod0.glb'))
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'export', f'{name}_authored_lods.glb'))
meshes = sorted([o for o in bpy.context.scene.objects if o.type == 'MESH'], key=lambda o: o.name)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x = scene.render.resolution_y = 600
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.4
for o in meshes:
    for x in meshes:
        x.hide_render = x is not o
    for view, (az, el) in {'q': (40, 10), 'side': (90, 0)}.items():
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        centre = Vector((0, -0.3, 1.1))
        cam.location = centre + d * 8; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f'{prefix}_{o.name}_{view}.png'
        bpy.ops.render.render(write_still=True)
print('LODVIEWS', [o.name for o in meshes])
