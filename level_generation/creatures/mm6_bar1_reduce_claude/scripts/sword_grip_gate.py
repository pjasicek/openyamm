"""Posed sword grip gate: body GLB + sword GLB, the sword at the Sword joint (glTF node frame from the inverse bind
matrix), every 2nd frame of the held clips. Right-glove vertices (hand/finger weights > 0.5) against the posed sword
mesh (BVH): penetration = behind the nearest sword face by more than 1 mm, contact = within 4 mm of the surface.
Compare installed and reduced: counts scale with the glove's vertex count.
Usage: blender -b -P sword_grip_gate.py -- <body glb> <sword glb> <label>"""
import bpy, sys, json, struct
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
body, sword, label = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
Mg = np.linalg.inv(ibm[names.index('Sword')].T)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ Mg @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Barbarian')
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]:
    bpy.data.objects.remove(o)
names_b = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=sword)
so = next(o for o in bpy.data.objects if o.name not in names_b and o.type == 'MESH' and 'LOD' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in names_b and o != so and o.type == 'MESH']:
    bpy.data.objects.remove(o)
so.parent = None; so.matrix_world = Matrix.Identity(4)
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbs = arm.pose.bones['Sword']
C = (arm.matrix_world @ pbs.matrix).inverted() @ bind_b
hand_groups = {g.index for g in bodyo.vertex_groups if g.name.startswith('B_R_Hand') or g.name.startswith('B_R_Finger')}
glove = np.array([sum(g.weight for g in v.groups if g.group in hand_groups) > .5 for v in bodyo.data.vertices])
sv = [v.co.copy() for v in so.data.vertices]; sf = [tuple(p.vertices) for p in so.data.polygons]
out = {}
for act in bpy.data.actions:
    if act.name not in ('Attack', 'Standing', 'Walking', 'Running', 'Hit', 'Fidget'):
        continue
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    pen = cont = 0; deepest = 0.0; fr = 0
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        W = arm.matrix_world @ pbs.matrix @ C
        tree = BVHTree.FromPolygons([W @ v for v in sv], sf)
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        P = [bodyo.matrix_world @ me.vertices[i].co for i in np.where(glove)[0]]; ev.to_mesh_clear()
        for p in P:
            loc, nrm, _, dist = tree.find_nearest(p, .05)
            if loc is None: continue
            inside = (p - loc).dot(nrm) < 0
            if inside and dist > .001: pen += 1; deepest = max(deepest, dist)
            if dist < .004: cont += 1
        fr += 1
    out[act.name] = dict(frames=fr, penetrating_vertex_frames=pen, contact_vertex_frames=cont, deepest_mm=round(deepest * 1000, 1))
print('GRIP', label, int(glove.sum()), 'glove verts', json.dumps(out))
# GRIP_RENDER=<out prefix>: textured close-ups of the gripping hand with the sword (Standing 0, Attack 12 and 22)
import os, math
if os.environ.get('GRIP_RENDER'):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 500
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
    sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .3
    hand = arm.pose.bones['B_R_Hand']
    for clip, k in [('Standing', 0), ('Attack', 12), ('Attack', 22)]:
        arm.animation_data.action = bpy.data.actions[clip]; sc.frame_set(k)
        so.matrix_world = arm.matrix_world @ pbs.matrix @ C
        c = arm.matrix_world @ hand.tail
        for vn, d in {'a': Vector((0, -1, .2)), 'b': Vector((1, -.4, .3))}.items():
            cam.location = c + d.normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{os.environ['GRIP_RENDER']}_{clip}{k}_{vn}.png"; bpy.ops.render.render(write_still=True)
