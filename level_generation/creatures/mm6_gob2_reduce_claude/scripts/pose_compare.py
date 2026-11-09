"""Source vs candidates at one clip frame, clay (workbench, cavity) close to a point: review/pose/<clip>_<frame>_*.png.
Usage: blender -b -P pose_compare.py -- <clip> <frame> <x,y,z rest point> <size> Cand_70 [Cand_55 ...]"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; clip, frame, point, size, cands = a[0], int(a[1]), Vector([float(x) for x in a[2].split(',')]), float(a[3]), a[4:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(frame)
src = bpy.data.objects['Body']
# follow the rest point to its posed position through the nearest source vertex
dg = bpy.context.evaluated_depsgraph_get(); ev = src.evaluated_get(dg); me = ev.to_mesh()
i = min(range(len(src.data.vertices)), key=lambda k: (src.data.vertices[k].co - point).length)
target = src.matrix_world @ me.vertices[i].co; ev.to_mesh_clear()
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 500
out = os.path.join(HERE, 'review', 'pose'); os.makedirs(out, exist_ok=True)
for name in ['Body'] + cands:
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o.name != name
    for view, d in {'back': (0, 1, .2), 'side': (1, 0, .1), 'q34b': (.7, .7, .3)}.items():
        dv = Vector(d).normalized(); cam.location = target + dv * 3
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{clip}_{frame}_{name}_{view}.png'); bpy.ops.render.render(write_still=True)
