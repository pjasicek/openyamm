"""Textured workbench views of a static GLB. Args: <glb> <out prefix> <ortho> <cx,cy,cz> view[,view...] (dx:dy:dz)"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH':
        for p in o.data.polygons: p.use_smooth = True
        if 'LOD' in o.name: o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[3].split(',')])
for k, vs in enumerate(a[4].split(',')):
    v = Vector([float(x) for x in vs.split(':')]).normalized()
    cam.location = c + v * 5; cam.rotation_euler = (-v).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{k}.png'; bpy.ops.render.render(write_still=True)
print('TEXLOOK', a[1])
