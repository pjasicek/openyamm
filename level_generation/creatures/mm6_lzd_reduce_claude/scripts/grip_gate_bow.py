"""Posed bow grip gate: body GLB + bow GLB, the bow at the Bow joint (glTF node frame recovered from the inverse bind
matrix), every 2nd frame of every clip. Left-hand vertices (hand/finger weights > 0.5) within 1 cm of the bow surface
are signed by the nearest bow face normal: inside = deeper than 1 mm, contact = within 3 mm.
Usage: blender -b -P grip_gate_bow.py -- <body glb> <bow glb> <label>"""
import bpy, sys, json, struct, os
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
body, bow, label = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
Mg = np.linalg.inv(ibm[names.index('Bow')].T)
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ Mg @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(body))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Lizard') and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]:
    bpy.data.objects.remove(o)
names_b = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=os.path.abspath(bow))
bo = next(o for o in bpy.data.objects if o.name not in names_b and o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in names_b and o != bo and o.type == 'MESH']:
    bpy.data.objects.remove(o)
bo.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Bow']
C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
hg = {g.index for g in bodyo.vertex_groups if g.name.startswith('B_L_Hand') or g.name.startswith('B_L_Finger')}
hand = np.where([sum(g.weight for g in v.groups if g.group in hg) > .5 for v in bodyo.data.vertices])[0]
tree = BVHTree.FromPolygons([v.co for v in bo.data.vertices], [p.vertices for p in bo.data.polygons])
out = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    inside = cont = fr = 0; deepest = 0.0
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        Winv = (arm.matrix_world @ pbm.matrix @ C).inverted()
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        for i in hand:
            p = Winv @ (bodyo.matrix_world @ me.vertices[i].co)
            loc, nrm, _, dist = tree.find_nearest(p, 0.01)
            if loc is None: continue
            s = (p - loc).dot(nrm)
            inside += s < -.001; cont += abs(s) < .003; deepest = min(deepest, s)
        ev.to_mesh_clear(); fr += 1
    out[act.name] = dict(frames=fr, inside_vertex_frames=int(inside), contact_vertex_frames=int(cont), deepest_mm=round(deepest * 1000, 1))
print('GRIP', label, len(hand), 'hand verts', json.dumps(out))
# GRIP_RENDER=<out prefix>: textured close-ups of the bow hand (Standing 0, Attack at the release), two views each
if os.environ.get('GRIP_RENDER'):
    from mathutils import Vector
    sc = bpy.context.scene; sc.render.resolution_x = sc.render.resolution_y = 500
    try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError: sc.render.engine = 'BLENDER_EEVEE'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.55, 0.6, 0.66, 1)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
    sun.rotation_euler = (0.7, 0.2, 0.5)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    for clip, frac in (('Standing', 0.0), ('Attack', 0.45)):
        act = bpy.data.actions[clip]; arm.animation_data.action = act
        if len(act.slots): arm.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(act.frame_range[0] + frac * (act.frame_range[1] - act.frame_range[0])))
        bo.matrix_world = arm.matrix_world @ pbm.matrix @ C
        h = arm.matrix_world @ arm.pose.bones['B_L_Hand'].head
        for k, d in (('a', Vector((.22, -.22, .08))), ('b', Vector((-.2, -.15, -.05))), ('w', Vector((.9, -1.4, .3)))):
            cam.location = h + d; cam.rotation_euler = (h - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{os.environ['GRIP_RENDER']}_{clip}_{k}.png"; bpy.ops.render.render(write_still=True)
