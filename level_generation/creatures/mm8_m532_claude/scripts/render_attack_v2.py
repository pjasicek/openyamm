"""Workbench renders of an Attack master (textured, bow and quiver included) at given frames and views -> PNGs and
one contact sheet. Usage: blender -b -P render_attack_v2.py -- <master.blend> <out_dir> <label> <frames,comma> [views]
views: front, quarter (front-left, bow side), side (left), rside (right), back, top-close variants 'hands' (close
on both hands from the quarter view)."""
import bpy, sys, math
from pathlib import Path
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, out, label, frames = args[0], Path(args[1]), args[2], [int(x) for x in args[3].split(',')]
views = args[4].split(',') if len(args) > 4 else ['front', 'quarter', 'side']
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
import os; rig.animation_data.action = bpy.data.actions[os.environ.get('CENTAUR_ACTION', 'Attack')]; rig.animation_data.action_slot = rig.animation_data.action.slots[0]
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.show_cavity = True; sc.render.resolution_x = 520; sc.render.resolution_y = 560
sc.render.film_transparent = False; sc.world = sc.world or bpy.data.worlds.new('W')
sc.display.shading.background_type = 'VIEWPORT'; sc.display.shading.background_color = (.42, .44, .47)
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
spots = {'front': ((0, -6.6, 1.8), (0, -0.4, 1.5)), 'quarter': ((3.9, -5.0, 2.1), (0, -0.4, 1.5)),
         'side': ((6.6, -0.4, 1.7), (0, -0.4, 1.5)), 'rside': ((-6.6, -0.4, 1.7), (0, -0.4, 1.5)),
         'back': ((-2.2, 6.0, 2.3), (0, -0.4, 1.6)), 'hands': ((2.4, -3.6, 2.35), (0, -0.85, 2.0)),
         'hands_top': ((0.6, -1.6, 4.2), (0, -0.85, 2.0)), 'rclose': ((-2.6, -0.9, 2.5), (0, -0.5, 2.25)),
         'bclose': ((-1.2, 2.2, 2.7), (0, -0.5, 2.25)), 'fclose': ((-0.6, -3.0, 2.45), (0, -0.6, 2.25)),
         'dhand1': ((-0.9, -1.5, 2.55), (-0.08, -0.62, 2.3)), 'dhand2': ((-1.1, 0.1, 2.6), (-0.08, -0.6, 2.3)),
         'dhand3': ((0.2, -1.6, 2.4), (-0.08, -0.62, 2.3)), 'bhand': ((1.1, -2.2, 2.4), (0.1, -1.3, 2.15)),
         'lhand0': ((1.7, -2.3, 1.8), (0.5, -0.85, 1.45)), 'nock': ((0.9, -2.5, 2.3), (0.05, -0.85, 1.9)),
         'nockr': ((-1.4, -2.3, 2.2), (0.05, -0.85, 1.9)),
         'user': ((4.6, 3.3, 3.0), (0.0, -0.5, 1.5)), 'lside': ((2.6, -1.0, 1.9), (0.4, -0.75, 1.6)), 'lback': ((2.1, 1.4, 2.3), (0.3, -0.6, 1.8)),
         'death': ((4.4, -3.4, 2.6), (1.5, -0.6, 0.7)), 'deathtop': ((1.7, -1.4, 5.0), (1.6, -0.7, 0.3)),
         'lfront': ((1.4, -3.0, 1.9), (0.4, -0.75, 1.6)), 'top': ((0.3, -0.9, 6.4), (0.05, -0.9, 1.9))}
out.mkdir(parents=True, exist_ok=True); shots = []
for f in frames:
    sc.frame_set(f)
    for v in views:
        loc, target = spots[v]; cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        p = out / f'{label}_{v}_{f:02d}.png'; sc.render.filepath = str(p); bpy.ops.render.render(write_still=True); shots.append((f, v, p))
print('RENDERED', len(shots))
