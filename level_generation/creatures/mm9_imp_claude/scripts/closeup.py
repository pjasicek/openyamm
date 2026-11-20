"""Closeups of a GLB/blend mesh: args <file> <out prefix> then name=cx,cy,cz,ortho,dx,dy,dz ... (solid + wire overlay)"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
f = a[0]
if f.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=f)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=f)
sc = bpy.context.scene
want = 'Body' if 'Body' in bpy.data.objects else None
for o in list(bpy.data.objects):
    if o.type == 'MESH' and want and o.name != want:
        o.hide_render = True
    if o.type == 'MESH' and (not want or o.name == want):
        m = o.modifiers.get('Armature')
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_flat() if False else None
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.7, 0.55)
sh.show_cavity = True
sc.display.render_aa = 'FXAA'
sc.render.resolution_x = sc.render.resolution_y = 640
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.4, 0.45, 0.5)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for spec in a[2:]:
    n, v = spec.split('=')
    cx, cy, cz, o, dx, dy, dz = [float(x) for x in v.split(',')]
    cd.ortho_scale = o
    d = Vector((dx, dy, dz)).normalized()
    c = Vector((cx, cy, cz))
    cam.location = c + d * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'
    bpy.ops.render.render(write_still=True)
