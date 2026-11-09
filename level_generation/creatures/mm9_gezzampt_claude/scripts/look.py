"""Clay close-ups of a glb or blend. Args: <file> <out prefix> <ortho> <cx,cy,cz> view[,view...]  views: front left back right q34 below top, or dx:dy:dz. Env RES, BF=1 shows backfaces red."""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
f, out, ortho, c, vs = a[0], a[1], float(a[2]), Vector([float(x) for x in a[3].split(',')]), a[4].split(',')
if f.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=f)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=f)
sc = bpy.context.scene
if os.environ.get('POSE'):
    arm = next(o for o in sc.objects if o.type == 'ARMATURE')
    nm, fr = os.environ['POSE'].split('@')
    act = next(a for a in bpy.data.actions if a.name == nm or a.name.startswith(nm + '_') or a.name.endswith('|' + nm))
    arm.animation_data_create(); arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(int(fr)); bpy.context.view_layer.update()
if sc.objects:
    for o in sc.objects:
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = not os.environ.get('FLATS')
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = False; sh.show_shadows = False
sh.show_backface_culling = bool(os.environ.get('BF'))
R = int(os.environ.get('RES', 800)); sc.render.resolution_x = sc.render.resolution_y = R
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.8, 0.1, 0.1) if os.environ.get('BF') else (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0), 'q34': (-1, -1.2, 0.3), 'below': (0, -1, -1.2), 'top': (0, 0.0001, 1)}
for n in vs:
    d = Vector(D[n] if n in D else [float(x) for x in n.split(':')]).normalized()
    cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{n.replace(":", "_")}.png'; bpy.ops.render.render(write_still=True)
print('LOOK', out)
