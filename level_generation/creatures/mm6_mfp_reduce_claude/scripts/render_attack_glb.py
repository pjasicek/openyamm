"""Textured review frames of a clip from a runtime body GLB with the knife attached at its Knife joint (the joint's
bind frame from the inverse bind matrix, as the engine attaches it): N frames x cameras (front = party eye height
1.7 m at 2.6 m, side, tq) -> review/attack/_<tag>_<cam>_NN.png for strip.py. Close-up camera 'hand' follows the
right hand. Args: -- <body glb> <knife glb> <clip> <tag> <frames> [cams]"""
import bpy, sys, os, json, struct, math
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
body, knife, clip, tag, N = a[0], a[1], a[2], a[3], int(a[4]); cams = (a[5] if len(a) > 5 else 'front,side,tq').split(',')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(HERE, 'review', 'attack')
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
acc = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][acc['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * acc['count'], bin0 + bv.get('byteOffset', 0) + acc.get('byteOffset', 0)).reshape(-1, 4, 4)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ np.linalg.inv(ibm[names.index('Knife')].T) @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(body))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
nb = set(bpy.data.objects.keys()); bpy.ops.import_scene.gltf(filepath=os.path.abspath(knife))
ko = next(o for o in bpy.data.objects if o.name not in nb and o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in nb and o != ko and o.type == 'MESH']: o.hide_render = True
ko.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Knife']; C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
act = next(x for x in bpy.data.actions if x.name.startswith(clip))
arm.animation_data.action = act
if len(act.slots): arm.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 400, 520
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(x for x in w.node_tree.nodes if x.type == 'BACKGROUND').inputs[0].default_value = (0.45, 0.48, 0.52, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.5
sun.rotation_euler = (0.8, 0.1, 0.5)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
POS = {'front': (Vector((0.15, -2.6, 1.7)), Vector((0, 0, 1.0)), 40), 'side': (Vector((2.6, -0.4, 1.3)), Vector((0, -0.2, 1.0)), 40),
       'tq': (Vector((-1.9, -1.9, 1.5)), Vector((0, 0, 1.0)), 40)}
f0, f1 = act.frame_range
for i in range(N):
    f = f0 + (f1 - f0) * i / (N - 1); sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    s = arm.pose.bones['Knife'].scale
    ko.matrix_world = arm.matrix_world @ pbm.matrix @ C
    ko.hide_render = s.x < 0.01
    for cn in cams:
        if cn == 'hand':
            h = arm.matrix_world @ arm.pose.bones['B_R_Hand'].head; cp, tg, lens = h + Vector((-0.25, -0.45, 0.15)), h, 50
        else:
            cp, tg, lens = POS[cn]
        cam.location = cp; cam.data.lens = lens; cam.rotation_euler = (tg - cp).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f'_{tag}_{cn}_{i:02d}.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', clip, tag, N, cams)
