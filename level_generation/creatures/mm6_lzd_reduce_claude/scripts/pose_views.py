"""Whole-body renders with the bow attached at the posed Bow joint (Standing frame REA_FRAME, default 0): front,
the character's left side, three-quarter left, and a left-hand close-up from the front.
Usage: blender -b -P pose_views.py -- <body glb> <bow glb> <out prefix>"""
import bpy, sys, json, struct, os, math
import numpy as np
from mathutils import Matrix, Vector
body, bow, out = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ np.linalg.inv(ibm[names.index('Bow')].T) @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(body))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): bpy.data.objects.remove(o)
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=os.path.abspath(bow))
bo = next(o for o in bpy.data.objects if o.name not in before and o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in before and o != bo and o.type == 'MESH']: bpy.data.objects.remove(o)
bo.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Bow']; C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
act = bpy.data.actions[os.environ.get('REA_CLIP', 'Standing')]; arm.animation_data.action = act
if len(act.slots): arm.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; sc.frame_set(int(os.environ.get('REA_FRAME', '0')))
bo.matrix_world = arm.matrix_world @ pbm.matrix @ C
P = lambda nm: arm.matrix_world @ arm.pose.bones[nm].head
fwd = (P('B_L_Toe0') - P('B_L_Foot') + P('B_R_Toe0') - P('B_R_Foot')); fwd.z = 0; fwd.normalize()
left = (P('B_L_UpperArm') - P('B_R_UpperArm')); left.z = 0; left.normalize()
ctr = (P('B_Head') + P('B_L_Foot')) / 2; hand = P('B_L_Hand')
sc.render.resolution_x, sc.render.resolution_y = 500, 700
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(nd for nd in w.node_tree.nodes if nd.type == 'BACKGROUND').inputs[0].default_value = (0.4, 0.42, 0.45, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (-fwd + left * .4 + Vector((0, 0, -1.2))).to_track_quat('-Z', 'Y').to_euler()
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
shots = {'front': (ctr + fwd * 3.2, ctr, 50), 'left': (ctr + left * 3.2, ctr, 50),
         'q34left': (ctr + (fwd + left).normalized() * 3.2, ctr, 50),
         'hand_front': (hand + fwd * .9 + left * .25, hand, 50), 'hand_below': (hand + fwd * .5 + left * .5 + Vector((0, 0, -.35))), }
shots['hand_below'] = (shots['hand_below'], hand, 50)
for k, (p, t, lens) in shots.items():
    cam.location = p; cam.data.lens = lens; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{k}.png'; bpy.ops.render.render(write_still=True)
# palm direction: the hand's local axis that points from the back of the hand to the palm is unknown, so report the
# direction from the hand bone to the mean of the finger tips and the bow grip centre relative to the body
tips = [P(nm) for nm in ('B_L_Finger12', 'B_L_Finger22', 'B_L_Finger32', 'B_L_Finger42')]
tipc = sum(tips, Vector()) / 4
grip = bo.matrix_world.translation
side = lambda v: round(v.dot(left), 3)
print('POSE hand', [round(x, 3) for x in hand], 'fingertips->body (left comp, + = away from body)', side(tipc - hand),
      'grip->hand left comp', side(grip - hand), 'fwd comp of fingertips', round((tipc - hand).dot(fwd), 3))
