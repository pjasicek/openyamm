"""Diagnosis: a clip pose with the collapse gate's bad faces (collapse_where.py DUMP json) painted red. Single-primitive GLBs.
Args: <glb> <clip> <frame> <dump json> <out prefix> [ortho] [bone] [views]"""
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH')
bad = set(json.load(open(a[3]))['faces'])
me = body.data
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0.1, 0.1, 1)
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.75, 0.73, 0.7, 1)
me.materials.clear(); me.materials.append(grey); me.materials.append(red)
for p in me.polygons: p.material_index = 1 if p.index in bad else 0
act = bpy.data.actions[a[1]]
rig.animation_data_create(); rig.animation_data.action = act
try: rig.animation_data.action_slot = act.slots[0]
except Exception: pass
bpy.context.scene.frame_set(int(a[2])); bpy.context.view_layer.update()
fb = a[6] if len(a) > 6 else 'Bip01 Head'
c = (rig.matrix_world @ rig.pose.bones[fb].matrix).to_translation()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = True
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.2, 0.22)
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[5]) if len(a) > 5 else 1.0
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
V = {'q34': (-1, -1.2, 0.35), 'front': (0, -1, 0.05), 'side': (-1, 0, 0.05), 'back': (0.3, 1, 0.2), 'low': (-0.6, -1, -0.5), 'top': (0, -0.3, 1), 'lside': (1, 0, 0.05)}
for v in (a[7].split(',') if len(a) > 7 else ['q34', 'front', 'side', 'back']):
    d = Vector(V[v]).normalized(); cam.location = c + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[4]}_{v}.png'; bpy.ops.render.render(write_still=True)
