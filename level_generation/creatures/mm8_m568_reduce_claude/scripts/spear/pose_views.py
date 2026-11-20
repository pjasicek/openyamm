"""Key-pose renders of a spear blend (work/spear_<tag>.blend): body and polearm, Eevee, front / three-quarter / side.
Usage: blender -b -P pose_views.py -- <tag> -> review/spear/<tag>_<clip>_<ms>_<view>.png and review/spear/sheet_<tag>.png"""
import bpy, os, sys
from mathutils import Vector
from pathlib import Path
P = Path(__file__).resolve().parents[2]; tag = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=str(P / f'work/spear_{tag}.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; out = P / 'review/spear'; out.mkdir(parents=True, exist_ok=True)
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 360; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .36, .39, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sun.rotation_euler = (0.8, 0, -0.6); sc.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('ORTHO', '3.6')) if 'os' in dir() else 3.6
import os
POSES = [tuple((c, float(t)) for c, t in [x.split(':')]) [0] for x in os.environ['POSES'].split(',')] if os.environ.get('POSES') else [('Standing', 0), ('Walk', .25), ('Attack', .3), ('Attack', .62), ('Attack', 1.0), ('Cast', 1.0), ('Hit', .25), ('Fidget', .31), ('Death', .3)]
VIEWS = [('front', (0, -6, 1.2)), ('quarter', (4.2, -4.2, 2)), ('side', (6, 0, 1.2))]
for clip, t in POSES:
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(round(t * 48) + 1)
    for v, d in VIEWS:
        target = Vector([float(x) for x in os.environ.get('TARGET', '0,-.2,1.35').split(',')]); cam.location = target + Vector(d); cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(out / f'{tag}_{clip}_{int(t * 1000):04d}_{v}.png'); bpy.ops.render.render(write_still=True)
print('POSEVIEWS', tag)
