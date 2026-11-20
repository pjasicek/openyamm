"""Grey or part-coloured shots of Body in a blend, optional rest pose or ACTION@frame. Backface culling on, as in game.
Args: blend outdir prefix spec...   spec = name:cx,cy,cz:ortho:dx,dy,dz"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
BL, outdir, prefix = argv[:3]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BL)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body':
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68)
sh.show_backface_culling = True; sh.show_cavity = True
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.15, 0.2, 0.3); sh.background_type = 'WORLD'
sc.render.resolution_x = 900; sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for s in argv[3:]:
    n, c, o, d = s.split(':')
    c = Vector([float(x) for x in c.split(',')]); d = Vector([float(x) for x in d.split(',')]).normalized()
    cd.ortho_scale = float(o); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{n}.png'); bpy.ops.render.render(write_still=True)
