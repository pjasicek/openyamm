"""Bow and bowstring clearance against the body: every 2nd frame of every clip, bow vertices (bow GLB at the posed
Bow joint) and string/arrow vertices (body material LizardBow_A) signed against the body surface without the left
hand and forearm (nearest face normal; inside = deeper than 2 mm). Usage: blender -b -P bow_clearance.py -- <body> <bow> <label>"""
import bpy, bmesh, sys, json, struct, os
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
body, bow, label = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ np.linalg.inv(ibm[names.index('Bow')].T) @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(body))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Lizard') and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]: bpy.data.objects.remove(o)
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=os.path.abspath(bow))
bo = next(o for o in bpy.data.objects if o.name not in before and o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in before and o != bo and o.type == 'MESH']: bpy.data.objects.remove(o)
bo.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Bow']; C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
bowv = [v.co.copy() for v in bo.data.vertices]
skip = {g.index for g in bodyo.vertex_groups if g.name.startswith(('B_L_Hand', 'B_L_Finger', 'B_L_Forearm', 'Bow', 'Arrow', 'String'))}
mat = [p.material_index for p in bodyo.data.polygons]
vskip = np.array([sum(g.weight for g in v.groups if g.group in skip) > .3 for v in bodyo.data.vertices])
string_v = sorted({i for p in bodyo.data.polygons if p.material_index == 1 for i in p.vertices})
keepf = [p.index for p in bodyo.data.polygons if p.material_index == 0 and not vskip[list(p.vertices)].any()]
me_idx = [bodyo.data.polygons[i].vertices[0] for i in keepf]
out = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    ins = 0; worst = (1.0, ''); near = 1.0
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        W = bodyo.matrix_world
        co = [W @ v.co for v in me.vertices]
        tree = BVHTree.FromPolygons(co, [me.polygons[i].vertices[:] for i in keepf])
        pts = [(arm.matrix_world @ pbm.matrix @ C) @ v for v in bowv] + [co[i] for i in string_v]
        ev.to_mesh_clear()
        for k, p in enumerate(pts):
            loc, nrm, fi, d = tree.find_nearest(p, 0.05)
            if loc is None: continue
            s = (p - loc).dot(nrm); near = min(near, d)
            if s < -.002:
                ins += 1
                if s < worst[0]:
                    vg = max(bodyo.data.vertices[me_idx[fi]].groups, key=lambda g: g.weight).group
                    worst = (s, f"{f} {'bow' if k < len(bowv) else 'string'} into {bodyo.vertex_groups[vg].name}")
    out[act.name] = dict(inside_vertex_frames=ins, deepest_mm=round(min(0, worst[0]) * 1000, 1) if ins else 0, at=worst[1], nearest_mm=round(near * 1000, 1))
print('CLEAR', label, json.dumps(out))
