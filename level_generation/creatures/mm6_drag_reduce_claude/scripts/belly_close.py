import os, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
objs = {'r100': bpy.data.objects['Body'], 'r55': bpy.data.objects['Cand_55'], 'r35': bpy.data.objects['Cand_35']}
sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.get('W') or bpy.data.worlds.new('W'); sc.world = w
cam = sc.camera; cam.data.lens = 50; sc.render.resolution_x, sc.render.resolution_y = 600, 700; sc.render.film_transparent = False
for name, (loc, tgt) in {'belly': ((0, -1.1, 0.45), (0, -0.1, 0.42)), 'side': ((1.0, -0.4, 0.5), (0, -0.1, 0.45))}.items():
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    for tag, o in objs.items():
        for x in objs.values(): x.hide_render = x is not o
        sc.render.filepath = os.path.join(HERE, 'review', 'close', f'{name}_{tag}.png'); bpy.ops.render.render(write_still=True)
