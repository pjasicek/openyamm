"""Rig the male peasant: proxy weight transfer for skin/tunic/legs, rigid head hair, belt on the pelvis, knife bone
in the curled right fist, palm sockets. Tunic panels below the belt blend hips and thighs (front/back flaps do not
split between the legs). Output work/rigged_v1.blend: Peasant (face attribute 'part') + Peasant_Rig."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import posing as P

PARTS = ['Body', 'Armor', 'Leather', 'Spikes', 'Teeth', 'Hoops', 'Sword']
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
flex = palm_normal.copy()
palm_normal = across.cross(finger_dir).normalized()          # orthogonal hand frame; sign from finger flexion
if palm_normal.dot(flex) < 0:
    palm_normal = -palm_normal
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


add_box(grip, 0.055, 0.012, 0.010)                                   # leather grip
add_box(grip + blade_dir * 0.064, 0.008, 0.042, 0.012)              # gold crossguard
add_box(grip - blade_dir * 0.063, 0.010, 0.016, 0.014)              # pommel
# curved scimitar blade: widening toward the tip, edge on the palm side, back with a notch
L, N = 0.62, 10
root = grip + blade_dir * 0.072
wdir = (finger_dir - blade_dir * finger_dir.dot(blade_dir)).normalized()   # blade plane = blade axis + forearm
tdir = blade_dir.cross(wdir).normalized()
ring = []
for k in range(N + 1):
    t = k / N
    curve = -wdir * (0.09 * t * t)                                 # blade curves toward the spine
    centre = root + blade_dir * (L * t) + curve
    w = 0.032 + 0.034 * t - 0.064 * max(0.0, t - 0.85) / 0.15     # widens, then clips to the point
    w = max(w, 0.003)
    back = 0.0 if not (0.55 < t < 0.70) else -0.008                # small notch in the back
    ring.append((centre + wdir * (w * 0.55), centre - wdir * (w * 0.45 + back), centre + tdir * 0.0035))
base = len(verts)
for edge, spine, flat in ring:
    verts += [edge, flat, spine, 2 * (edge + spine) / 2 - flat]
for k in range(N):
    a0 = base + 4 * k; a1 = a0 + 4
    for j in range(4):
        faces.append((a0 + j, a0 + (j + 1) % 4, a1 + (j + 1) % 4, a1 + j))
faces.append(tuple(base + j for j in range(4))[::-1])
faces.append(tuple(base + 4 * N + j for j in range(4)))
km = bpy.data.meshes.new('Sword'); km.from_pydata([tuple(v) for v in verts], [], faces); km.update()
O['Sword'] = bpy.data.objects.new('Sword', km); bpy.context.scene.collection.objects.link(O['Sword'])

bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
inv = rig.matrix_world.inverted()
kb = rig.data.edit_bones.new('Sword'); kb.head = inv @ grip; kb.tail = inv @ (grip + blade_dir * 0.1)
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


for name in ('Teeth', 'Hoops'):
    set_weights(O[name], lambda co: {'mixamorig:Head': 1.0})
set_weights(O['Sword'], lambda co: {'Sword': 1.0})


def transfer(obj, src, mapping='POLYINTERP_NEAREST'):
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    bpy.context.view_layer.objects.active = obj
    for o in bpy.data.objects:
        o.select_set(o == obj)
    mod = obj.modifiers.new('weights', 'DATA_TRANSFER')
    mod.object = src; mod.use_vert_data = True; mod.data_types_verts = {'VGROUP_WEIGHTS'}
    mod.vert_mapping = mapping; mod.layers_vgroup_select_src = 'ALL'; mod.layers_vgroup_select_dst = 'NAME'
    bpy.ops.object.datalayout_transfer(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)


transfer(O['Body'], proxy)
bpy.context.view_layer.objects.active = O['Body']
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=2, expand=0.0)
bpy.ops.object.mode_set(mode='OBJECT')
for name in ('Armor', 'Leather', 'Spikes'):
    transfer(O[name], O['Body'])
# skirt strips below the belt: centre carried by the hips, sides by each thigh (no splitting between legs)
lea = O['Leather']
gid = {g.name: g for g in lea.vertex_groups}
hips = gid.get('mixamorig:Hips') or lea.vertex_groups.new(name='mixamorig:Hips')
for v in lea.data.vertices:
    co = lea.matrix_world @ v.co
    if not (0.55 < co.z < 0.86):
        continue
    k = min(1.0, (0.86 - co.z) / 0.08) * max(0.0, 1.0 - abs(co.x) / 0.16) * 0.6
    ws = {lea.vertex_groups[g.group].name: g.weight for g in v.groups}
    leg = sum(w for n, w in ws.items() if 'UpLeg' in n or n.endswith('Leg'))
    if leg <= 0:
        continue
    for n in list(ws):
        if 'UpLeg' in n or n.endswith('Leg'):
            gid[n].add([v.index], ws[n] * (1 - k), 'REPLACE')
    hips.add([v.index], ws.get('mixamorig:Hips', 0.0) + leg * k, 'REPLACE')
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
bpy.context.scene['pfem_sword'] = json.dumps({'grip': list(grip), 'blade_dir': list(blade_dir), 'palm_normal': list(palm_normal)})
print('RIGGED tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'bones', len(rig.data.bones),
      'unweighted', sum(1 for v in mesh.data.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rigged_v1.blend'))
