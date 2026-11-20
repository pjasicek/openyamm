"""Render the source body and one ladder candidate (work/ladder.blend) at a clip frame, camera on a world point, both
untextured (workbench, cavity). Usage: blender -b -P spot_render.py -- <cand> <clip> <frame> <x> <y> <z> <size> <out>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cand, clip, frame, x, y, z, size, out = sys.argv[sys.argv.index('--') + 1:][:8]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(frame))
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.show_cavity = True; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = sc.render.resolution_y = 500
cam = bpy.data.objects.new('SpotCam', bpy.data.cameras.new('SpotCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(size)
c = Vector((float(x), float(y), float(z)))
for name in ['Body', cand]:
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o.name != name
    for i, d in enumerate([(0, -1, .3), (1, 0, .3), (0, 1, .3), (-1, 0, .3), (0, 0, 1)]):
        dv = Vector(d).normalized(); cam.location = c + dv * 3
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{name}_{i}.png'; bpy.ops.render.render(write_still=True)
