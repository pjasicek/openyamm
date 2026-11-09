"""Shaded orthographic renders (side from +X, top, front from -Y, back) of a blend's Body at a known mapping;
grid_overlay.py then draws a labelled 5 cm grid. Usage: grid_render.py -- <blend> <outdir> [clip frame]"""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0]); out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
rig = bpy.data.objects.get('Rig')
if rig and len(args) > 3:
    rig.animation_data.action = bpy.data.actions[args[2]]; bpy.context.scene.frame_set(int(args[3]))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.7, .72, .7); sc.display.shading.show_cavity = True
sc.render.film_transparent = True; PX = 1400; C = Vector((0, 0, .3)); S = 1.1
sc.render.resolution_x = sc.render.resolution_y = int(PX * S); sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('GridCam', bpy.data.cameras.new('GridCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = S
views = {'side': (3, 0, 0), 'top': (0, -1e-4, 3), 'front': (0, -3, 0), 'back': (0, 3, 0)}
for name, d in views.items():
    cam.location = C + Vector(d); cam.rotation_euler = (C - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(out / f'render_{name}.png'); bpy.ops.render.render(write_still=True)
(out / 'render_mapping.json').write_text(json.dumps({'center': list(C), 'ortho_scale': S, 'pixels_per_metre': PX}))
