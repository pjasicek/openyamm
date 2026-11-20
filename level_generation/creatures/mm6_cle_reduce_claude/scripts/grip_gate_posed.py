"""Posed grip gate (cleric): body GLB + staff GLB, the staff at the Staff joint (glTF node frame recovered from the
inverse bind matrix), every 2nd frame of the clips. Left-hand vertices (LeftHand* weights > 0.5) within 6 cm of the
staff are measured against its surface (signed by the nearest face normal): penetration = more than 1 mm inside,
contact = within 4 mm. Usage: blender -b -P grip_gate_posed.py -- <body glb> <staff glb> <label>"""
import bpy, sys, json, struct
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
body, mace, label = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
Mg = np.linalg.inv(ibm[names.index('Staff')].T)  # glTF world from Mace joint at bind
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ Mg @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Cleric') and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]:
    bpy.data.objects.remove(o)
names_b = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=mace)
mo = next(o for o in bpy.data.objects if o.name not in names_b and o.type == 'MESH' and 'LOD' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in names_b and o != mo and o.type == 'MESH']:
    bpy.data.objects.remove(o)
mo.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Staff']
C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
hand_groups = {g.index for g in bodyo.vertex_groups if g.name.startswith('LeftHand')}
glove = np.array([sum(g.weight for g in v.groups if g.group in hand_groups) > .5 for v in bodyo.data.vertices])
R = .0125; out = {}
for act in bpy.data.actions:
    if act.name not in ('Attack', 'Cast', 'Standing', 'Walking', 'Hit', 'Fidget', 'Death'):
        continue
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    pen = cont = 0; worst = 1.0; fr = 0
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        W = arm.matrix_world @ pbm.matrix @ C  # mace world (Blender)
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        P = np.array([bodyo.matrix_world @ me.vertices[i].co for i in np.where(glove)[0]]); ev.to_mesh_clear()
        mo.matrix_world = W; bpy.context.view_layer.update()
        sm = mo.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        bvh = BVHTree.FromPolygons([mo.matrix_world @ v.co for v in sm.vertices], [tuple(q.vertices) for q in sm.polygons])
        for p in P:
            loc, nrm, fi, dist = bvh.find_nearest(Vector(p), 0.06)
            if loc is None: continue
            sd = (Vector(p) - loc).dot(nrm)
            pen += sd < -.001; cont += abs(sd) < .004; worst = min(worst, sd)
        fr += 1
    out[act.name] = dict(frames=fr, penetrating_vertex_frames=pen, contact_vertex_frames=cont, deepest_mm=round(worst * 1000, 1))
print('GRIP', label, json.dumps(out))
