"""Posed grip gate: body GLB + bow GLB, the bow at the Bow joint (glTF node frame recovered from the inverse bind
matrix), every 2nd frame of every clip. Left-hand vertices (hand/finger weights > 0.5) are measured against the
grip axis (bow local y in Blender data) over the grip span: penetration = closer than the handle radius - 1 mm, contact = within
4 mm of the handle surface. Usage: blender -b -P grip_gate_posed.py -- <body glb> <bow glb> <label>"""
import bpy, sys, json, struct
import numpy as np
from mathutils import Matrix
body, bow, label = sys.argv[sys.argv.index('--') + 1:][:3]
b = open(body, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
sk = j['skins'][0]; names = [j['nodes'][i]['name'] for i in sk['joints']]
a = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][a['bufferView']]
ibm = np.frombuffer(b, np.float32, 16 * a['count'], bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 4, 4)
Mg = np.linalg.inv(ibm[names.index('Bow')].T)  # glTF world from Bow joint at bind
A = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
bind_b = Matrix((A @ Mg @ np.linalg.inv(A)).tolist())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bodyo = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Archer') and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o != bodyo]:
    bpy.data.objects.remove(o)
names_b = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=bow)
mo = next(o for o in bpy.data.objects if o.name not in names_b and o.type == 'MESH' and 'LOD' not in o.name)
for o in [o for o in bpy.data.objects if o.name not in names_b and o != mo and o.type == 'MESH']:
    bpy.data.objects.remove(o)
mo.parent = None
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pbm = arm.pose.bones['Bow']
C = (arm.matrix_world @ pbm.matrix).inverted() @ bind_b
hand_groups = {g.index for g in bodyo.vertex_groups if g.name.startswith('B_L_Hand') or g.name.startswith('B_L_Finger')}
glove = np.array([sum(g.weight for g in v.groups if g.group in hand_groups) > .5 for v in bodyo.data.vertices])
R = .011; out = {}
for act in bpy.data.actions:
    if act.name not in ('Attack', 'Cast', 'Standing', 'Walking', 'Hit', 'Fidget'):
        continue
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    pen = cont = 0; worst = 1.0; fr = 0
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        W = arm.matrix_world @ pbm.matrix @ C  # bow world (Blender)
        ev = bodyo.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        P = np.array([bodyo.matrix_world @ me.vertices[i].co for i in np.where(glove)[0]]); ev.to_mesh_clear()
        L = (np.array(W.inverted()) @ np.c_[P, np.ones(len(P))].T).T[:, :3]
        # the grip axis is the bow's local y in Blender mesh data
        t = -L[:, 1]; rad = np.hypot(L[:, 0], L[:, 2]); s = (t > -.07) & (t < .07)
        pen += int(((rad < R - .001) & s).sum()); cont += int(((rad < R + .004) & s).sum()); fr += 1
        if s.any(): worst = min(worst, float(rad[s].min()))
    out[act.name] = dict(frames=fr, penetrating_vertex_frames=pen, contact_vertex_frames=cont, nearest_axis_mm=round(worst * 1000, 1))
print('GRIP', label, json.dumps(out))
# GRIP_RENDER=<out prefix>: textured close-ups of the gripping hand (Standing 0, Attack mid), two views each
import os
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
    for clip, frac in (('Standing', 0.0), ('Attack', 0.55)):
        act = bpy.data.actions[clip]; arm.animation_data.action = act
        if len(act.slots): arm.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(act.frame_range[0] + frac * (act.frame_range[1] - act.frame_range[0])))
        mo.matrix_world = arm.matrix_world @ pbm.matrix @ C
        h = arm.matrix_world @ arm.pose.bones['B_L_Hand'].head
        for k, d in (('a', Vector((.18, -.18, .08))), ('b', Vector((-.18, -.12, -.05)))):
            cam.location = h + d; cam.rotation_euler = (h - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{os.environ['GRIP_RENDER']}_{clip}_{k}.png"; bpy.ops.render.render(write_still=True)
