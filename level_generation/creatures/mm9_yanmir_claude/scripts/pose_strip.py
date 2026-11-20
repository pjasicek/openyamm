"""Clay frames of a clips GLB in one Blender run: CLIPS env 'Clip@frame,Clip@frame,...', view dir. Args: <glb> <out png> [view dx:dy:dz] [ortho]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]
view = Vector([float(x) for x in (a[2] if len(a) > 2 else '-1:-1.2:0.3').split(':')]).normalized()
ortho = float(a[3]) if len(a) > 3 else 3.4
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.type == 'MESH':
        for p in o.data.polygons: p.use_smooth = True
        if 'LOD' in o.name: o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR', 'SINGLE'); sh.single_color = (.72, .72, .72)
R = int(os.environ.get('RES', 500)); sc.render.resolution_x = sc.render.resolution_y = R
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in os.environ['C'].split(',')]) if os.environ.get('C') else Vector((0, 0, float(os.environ.get('CZ', 1.45))))
cam.location = c + view * 10; cam.rotation_euler = (-view).to_track_quat('-Z', 'Y').to_euler()
arm.animation_data_create()
tiles = []
for spec in os.environ['CLIPS'].split(','):
    nm, fr = spec.split('@')
    act = next(x for x in bpy.data.actions if x.name == nm or x.name.startswith(nm + '_') or x.name.split('|')[-1] == nm)
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(int(fr)); bpy.context.view_layer.update()
    p = f'{out}.{len(tiles):02d}.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True); tiles.append(p)
print('STRIP', out, len(tiles))
