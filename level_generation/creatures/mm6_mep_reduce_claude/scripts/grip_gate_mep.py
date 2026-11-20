"""Posed grip gate for the Mep's staff: body GLB + staff GLB placed at the Staff joint (glTF joint frame recovered
from the inverse bind matrix, as at runtime), every 2nd frame of every clip. Hand vertices of both hands (hand/finger
weights > 0.5) against the staff surface: penetration depth = inside the staff along its nearest-face normal;
contact = within 4 mm of the surface. Usage: blender -b -P grip_gate_mep.py -- <body glb> <staff glb> <label>"""
import bpy, sys, json, struct
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
body, staff, label = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
Mg = np.linalg.inv(ibm[names.index('Staff')].T)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ Mg @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Mep')
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]:
    bpy.data.objects.remove(o)
names_b = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=staff)
so = next(o for o in bpy.data.objects if o.name not in names_b and o.type == 'MESH' and 'LOD' not in o.name)
M0 = so.matrix_world.copy()
sv = [M0 @ v.co for v in so.data.vertices]; sp = [list(p.vertices) for p in so.data.polygons]
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbs = arm.pose.bones['Staff']
C = (arm.matrix_world @ pbs.matrix).inverted() @ bind_b
hand_groups = {g.index for g in bodyo.vertex_groups if g.name[:8] in ('B_R_Hand', 'B_L_Hand', 'B_R_Fing', 'B_L_Fing')}
hand = np.where([sum(g.weight for g in v.groups if g.group in hand_groups) > .5 for v in bodyo.data.vertices])[0]
from mathutils import Vector
DIR = Vector((.811, .357, .463)).normalized()
def inside(tree, v):
    count, origin = 0, v.copy()
    for _ in range(64):
        hit = tree.ray_cast(origin, DIR, 3)[0]
        if hit is None: return count % 2 == 1
        count += 1; origin = hit + DIR * 1e-5
    return False
out = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    gaps, deepest, pen, fr = [], 0.0, 0, 0
    end = act.frame_range[1] if act.name != 'Death' else min(act.frame_range[1], act.frame_range[0] + 2)  # staff released
    if act.name == 'Dead': continue
    for f in range(int(act.frame_range[0]), int(end) + 1, 2):
        bpy.context.scene.frame_set(f)
        W = arm.matrix_world @ pbs.matrix @ C
        tree = BVHTree.FromPolygons([W @ p for p in sv], sp)
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); best = 1.0
        for i in hand:
            p = bodyo.matrix_world @ me.vertices[i].co
            loc, nrm, _, dist = tree.find_nearest(p, .05)
            if loc is None: continue
            best = min(best, dist)
            if dist < .015 and inside(tree, p):
                pen += 1; deepest = max(deepest, dist)
        ev.to_mesh_clear(); fr += 1; gaps.append(best)
    out[act.name] = dict(frames=fr, max_gap_mm=round(max(gaps) * 1000, 2), pen_vertex_frames=pen, deepest_mm=round(deepest * 1000, 2))
print('GRIP', label, json.dumps(out))
# GRIP_RENDER=<out prefix>: textured close-ups of the gripping hand (Standing 0, Attack mid, Cast mid), two views each
import os
if os.environ.get('GRIP_RENDER'):
    sc = bpy.context.scene; sc.render.resolution_x = sc.render.resolution_y = 500
    sc.render.engine = 'BLENDER_EEVEE'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.55, 0.6, 0.66, 1)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
    sun.rotation_euler = (0.7, 0.2, 0.5)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    for clip, frac in (('Standing', 0.0), ('Attack', 0.55), ('Cast', 0.5)):
        act = bpy.data.actions[clip]; arm.animation_data.action = act
        if len(act.slots): arm.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(act.frame_range[0] + frac * (act.frame_range[1] - act.frame_range[0])))
        so.matrix_world = arm.matrix_world @ pbs.matrix @ C @ M0
        h = arm.matrix_world @ arm.pose.bones['B_R_Hand'].head
        for k, d in (('a', Vector((-.18, -.18, .08))), ('b', Vector((.05, .2, .05)))):
            cam.location = h + d; cam.rotation_euler = (h - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{os.environ['GRIP_RENDER']}_{clip}_{k}.png"; bpy.ops.render.render(write_still=True)
