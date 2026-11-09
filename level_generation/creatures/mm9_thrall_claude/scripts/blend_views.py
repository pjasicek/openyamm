"""Clay views of 'Body' in a blend beside the MM9 model's stand-in, for fit checks. Args: <blend> <mm9 glb> <prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
for m in list(body.modifiers): body.modifiers.remove(m)
body.parent = None
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 1000
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 2.2; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0.0, -0.05, 0.09))
for v, d in {'q34': (-1.0, -1.25, 0.55), 'front': (0, -1, 0.08), 'left': (1, 0, 0.08), 'back': (0, 1, 0.08), 'right': (-1, 0, 0.08)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{v}.png'; bpy.ops.render.render(write_still=True)
