"""Rig the male peasant: proxy weight transfer for skin/tunic/legs, rigid head hair, belt on the pelvis, knife bone
in the curled right fist, palm sockets. Tunic panels below the belt blend hips and thighs (front/back flaps do not
split between the legs). Output work/rigged_v1.blend: Peasant (face attribute 'part') + Peasant_Rig."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import posing as P

PARTS = ['Body', 'Tunic', 'Legs', 'Hair', 'Belt', 'Buckle', 'Knife']
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'fit_v1.blend'))
rig = bpy.data.objects['Peasant_Rig']; proxy = bpy.data.objects['Proxy']
O = {n: bpy.data.objects[n] for n in PARTS if n in bpy.data.objects}

pgroups = {g.index: g.name for g in proxy.vertex_groups}
bm = bmesh.new(); bm.from_mesh(proxy.data); deform = bm.verts.layers.deform.active
helper = {i for i, n in pgroups.items() if n in ('HelperGeometry', 'JointCubes')}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if any(k in helper and w > 0 for k, w in v[deform].items())], context='VERTS')
bm.to_mesh(proxy.data); bm.free()
for g in list(proxy.vertex_groups):
    if not g.name.startswith('mixamorig:'):
        proxy.vertex_groups.remove(g)


def bone_head(name):
    return rig.matrix_world @ rig.data.bones['mixamorig:' + name].head_local


# knife in the curled right fist (same construction as pfem; palm side measured from finger flexion)
P.reset(rig)
hand_rest = rig.matrix_world @ rig.data.bones['mixamorig:RightHand'].matrix_local
tip0 = P.bone_world(rig, 'RightHandMiddle3', tail=True)
P.curl_hand(rig, 'Right', 80, thumb=35)
loop = [P.bone_world(rig, 'RightHandMiddle1'), P.bone_world(rig, 'RightHandMiddle2'),
        P.bone_world(rig, 'RightHandMiddle3'), P.bone_world(rig, 'RightHandMiddle3', tail=True)]
grip_posed = sum(loop, Vector()) / 4
hand_pose = rig.matrix_world @ rig.pose.bones['mixamorig:RightHand'].matrix
P.reset(rig)
grip = hand_rest @ (hand_pose.inverted() @ grip_posed)
hand = bone_head('RightHand')
across = (bone_head('RightHandIndex1') - bone_head('RightHandPinky1')).normalized()
finger_dir = (bone_head('RightHandMiddle1') - hand).normalized()
P.rotate_local(rig, 'mixamorig:RightHandMiddle1', 'X', 20)
palm_normal = P.bone_world(rig, 'RightHandMiddle3', tail=True) - tip0
P.reset(rig)
palm_normal = (palm_normal - finger_dir * palm_normal.dot(finger_dir)).normalized()
blade_dir = across
side_v = palm_normal.cross(blade_dir).normalized()
verts, faces = [], []


def add_box(c, hl, hw, ht):
    base = len(verts)
    for a in (-1, 1):
        for b in (-1, 1):
            for cc in (-1, 1):
                verts.append(c + blade_dir * a * hl + side_v * b * hw + palm_normal * cc * ht)
    faces.extend(tuple(base + i for i in q) for q in
                 [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])


add_box(grip, 0.05, 0.010, 0.008)
add_box(grip + blade_dir * 0.055, 0.006, 0.018, 0.009)
root = grip + blade_dir * 0.061; base = len(verts); w, t = 0.011, 0.0025
verts += [root + side_v * w, root + palm_normal * t, root - side_v * w, root - palm_normal * t, root + blade_dir * 0.11]
faces += [(base, base + 1, base + 4), (base + 1, base + 2, base + 4), (base + 2, base + 3, base + 4),
          (base + 3, base, base + 4), (base, base + 3, base + 2, base + 1)]
km = bpy.data.meshes.new('Knife'); km.from_pydata([tuple(v) for v in verts], [], faces); km.update()
O['Knife'] = bpy.data.objects.new('Knife', km); bpy.context.scene.collection.objects.link(O['Knife'])

bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
inv = rig.matrix_world.inverted()
kb = rig.data.edit_bones.new('Knife'); kb.head = inv @ grip; kb.tail = inv @ (grip + blade_dir * 0.1)
kb.align_roll(inv.to_3x3() @ palm_normal); kb.parent = rig.data.edit_bones['mixamorig:RightHand']
bpy.ops.object.mode_set(mode='OBJECT')
for side in ('Left', 'Right'):
    sock = bpy.data.objects.new(f'Socket_Palm_{side}', None); bpy.context.scene.collection.objects.link(sock)
    sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = f'mixamorig:{side}Hand'
    sock.matrix_world = Matrix.Translation((bone_head(f'{side}Hand') + bone_head(f'{side}HandMiddle1')) / 2)


def set_weights(obj, fn):
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    groups = {}
    for v in obj.data.vertices:
        ws = {k: w for k, w in fn(obj.matrix_world @ v.co).items() if w > 0}
        tot = sum(ws.values())
        for name, w in ws.items():
            groups.setdefault(name, obj.vertex_groups.new(name=name)).add([v.index], w / tot, 'REPLACE')


head_z = bone_head('Head').z
set_weights(O['Hair'], lambda co: {'mixamorig:Head': 1.0, 'mixamorig:Neck': max(0.0, min(0.5, (head_z + 0.02 - co.z) / 0.05))})
set_weights(O['Knife'], lambda co: {'Knife': 1.0})
for name in ('Belt', 'Buckle'):
    set_weights(O[name], lambda co: {'mixamorig:Hips': 0.6, 'mixamorig:Spine': 0.4})
for name in ('Body', 'Tunic', 'Legs'):
    obj = O[name]
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    bpy.context.view_layer.objects.active = obj
    for o in bpy.data.objects:
        o.select_set(o == obj)
    mod = obj.modifiers.new('weights', 'DATA_TRANSFER')
    mod.object = proxy; mod.use_vert_data = True; mod.data_types_verts = {'VGROUP_WEIGHTS'}
    mod.vert_mapping = 'POLYINTERP_NEAREST'; mod.layers_vgroup_select_src = 'ALL'; mod.layers_vgroup_select_dst = 'NAME'
    bpy.ops.object.datalayout_transfer(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=2, expand=0.0)
    bpy.ops.object.mode_set(mode='OBJECT')
# Tunic skirt panels: towards the centre line the hips carry the cloth, at the sides each thigh does.
tunic = O['Tunic']
gid = {g.name: g for g in tunic.vertex_groups}
hips = gid.get('mixamorig:Hips') or tunic.vertex_groups.new(name='mixamorig:Hips')
for v in tunic.data.vertices:
    co = tunic.matrix_world @ v.co
    if co.z > 0.94:
        continue
    k = min(1.0, (0.94 - co.z) / 0.06) * max(0.0, 1.0 - abs(co.x) / 0.13) * 0.6
    ws = {tunic.vertex_groups[g.group].name: g.weight for g in v.groups}
    leg = sum(w for n, w in ws.items() if 'UpLeg' in n or n.endswith('Leg'))
    if leg <= 0:
        continue
    for n in list(ws):
        if 'UpLeg' in n or n.endswith('Leg'):
            gid[n].add([v.index], ws[n] * (1 - k), 'REPLACE')
    hips.add([v.index], ws.get('mixamorig:Hips', 0.0) + leg * k, 'REPLACE')
legs = O['Legs']
for g in list(legs.vertex_groups):
    if not any(s in g.name for s in ('UpLeg', 'Leg', 'Foot', 'ToeBase', 'Hips')):
        legs.vertex_groups.remove(g)
bpy.data.objects.remove(proxy, do_unlink=True)

objects = [O[n] for n in PARTS]
for i, obj in enumerate(objects):
    obj.data.materials.clear()
    attr = obj.data.attributes.new('part', 'INT', 'FACE')
    attr.data.foreach_set('value', [i] * len(obj.data.polygons))
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    mw = obj.matrix_world.copy(); obj.parent = rig; obj.matrix_world = mw
for o in bpy.data.objects:
    o.select_set(o in objects)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
mesh.name = 'Peasant'; mesh.data.name = 'Peasant'
mesh.modifiers.new('Armature', 'ARMATURE').object = rig
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
for p in mesh.data.polygons:
    p.use_smooth = True
bpy.context.scene['pfem_parts'] = json.dumps(PARTS)
bpy.context.scene['pfem_knife'] = json.dumps({'grip': list(grip), 'blade_dir': list(blade_dir), 'palm_normal': list(palm_normal)})
print('RIGGED tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'bones', len(rig.data.bones),
      'unweighted', sum(1 for v in mesh.data.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rigged_v1.blend'))
