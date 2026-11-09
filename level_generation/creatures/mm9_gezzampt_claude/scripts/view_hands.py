"""Close clay views of the hands at rest. Args: <blend> <prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.3, 0.3, 0.33); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.46; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for s in 'LR':
    b = rig.data.bones[f'Bip01 {s} Hand']; c = rig.matrix_world @ b.head_local; c = Vector((c.x, c.y, c.z - 0.08))
    sx = 1 if s == 'L' else -1
    for v, d in {'out': (sx, -0.3, 0.1), 'front': (0, -1, 0.1), 'in': (-sx, -0.3, 0.1)}.items():
        d = Vector(d).normalized(); cam.location = c + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[1]}_{s}_{v}.png'; bpy.ops.render.render(write_still=True)
