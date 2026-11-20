"""Frames for a filmstrip of viewer frames (48 fps), before vs after, textured: renders work/film/<label>_<clip>_<k>.png
and work/film/rows.json (rows = clip x model); film_sheet.py composes them into <out.png>.
Usage: blender -b -P filmstrip.py -- <out.png> <before.glb> <after.glb> "<Clip:f0-f1:step:view;...>" """
import json, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, before, after, spec = sys.argv[sys.argv.index('--') + 1:][:4]
tmp = os.path.join(HERE, 'work', 'film'); os.makedirs(tmp, exist_ok=True)
VIEWS = {'side': (1, -.15, .1), 'front': (.15, -1, .1), 'q34': (.7, -.7, .2)}
rows = []
for label, glb in (('before', before), ('after', after)):
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb)); fps = sc.render.fps / sc.render.fps_base
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.7; sc.render.resolution_x = sc.render.resolution_y = 260
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for item in spec.split(';'):
        clip, rng, step, view = item.split(':'); f0, f1 = (int(x) for x in rng.split('-'))
        rig.animation_data.action = bpy.data.actions[clip]; files = []
        for k in range(f0, f1 + 1, int(step)):
            fr = k / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr))
            c = Vector((0, 0, .7)); cam.location = c + Vector(VIEWS[view]).normalized() * 4
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            p = os.path.join(tmp, f'{label}_{clip}_{k}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
            files.append((k, p))
        rows.append((f'{clip} {label}', files))
json.dump({'out': out, 'rows': rows}, open(os.path.join(tmp, 'rows.json'), 'w'))
print('FILM frames', sum(len(r[1]) for r in rows))
