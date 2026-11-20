"""Step 2b: secondary bones + weights on the fitted rig; join parts into one skinned mesh.

Input work/fit_v1.blend (step-1 parts, fitted Peasant_Rig, fitted Proxy). Output work/rigged_v2.blend with
Peasant (mesh, face attribute 'part'), Peasant_Rig, Socket_Palm_* empties and hidden SimLegs/SimSkirt helpers.
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import posing as P

PARTS = ['Body', 'EyeLeft', 'EyeRight', 'LegLeft', 'LegRight', 'Belt', 'Buckle', 'Skirt', 'Hair', 'Braid',
         'Headband', 'Knife']
N_CHAINS = 12
CHAIN_Z = [0.985, 0.72, 0.46, 0.21]

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'fit_v1.blend'))
rig = bpy.data.objects['Peasant_Rig']; proxy = bpy.data.objects['Proxy']
O = {n: bpy.data.objects[n] for n in PARTS if n in bpy.data.objects}

# ---------------------------------------------------------------- clean proxy (weight source / collider)
pgroups = {g.index: g.name for g in proxy.vertex_groups}
bm = bmesh.new(); bm.from_mesh(proxy.data); deform = bm.verts.layers.deform.active
helper = {i for i, n in pgroups.items() if n in ('HelperGeometry', 'JointCubes')}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if any(k in helper and w > 0 for k, w in v[deform].items())], context='VERTS')
bm.to_mesh(proxy.data); bm.free()
for g in list(proxy.vertex_groups):
    if not g.name.startswith('mixamorig:'):
        proxy.vertex_groups.remove(g)
proxy.data.update()


def tree_of(objs):
    verts, polys = [], []
    for o in objs:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


skirt = O['Skirt']
skirt_tree = tree_of([skirt])
sk = np.array([tuple(skirt.matrix_world @ v.co) for v in skirt.data.vertices])
waist = sk[np.abs(sk[:, 2] - 1.0) < 0.02]
axis_xy = Vector((float((waist[:, 0].max() + waist[:, 0].min()) / 2), float((waist[:, 1].max() + waist[:, 1].min()) / 2), 0))


def skirt_point(phi, z, inset=0.012):
    d = Vector((math.sin(phi), -math.cos(phi), 0))
    c = Vector((axis_xy.x, axis_xy.y, z))
    hit = skirt_tree.ray_cast(c + d * 0.8, -d, 0.8)
    r = (0.8 - hit[3]) if hit[0] is not None else 0.15
    return c + d * max(r - inset, 0.02)


# ---------------------------------------------------------------- knife mesh in the curled right fist
def bone_head(name):
    return rig.matrix_world @ rig.data.bones['mixamorig:' + name].head_local


P.reset(rig); P.curl_hand(rig, 'Right', 80, thumb=35)
loop = [P.bone_world(rig, 'RightHandMiddle1'), P.bone_world(rig, 'RightHandMiddle2'),
        P.bone_world(rig, 'RightHandMiddle3'), P.bone_world(rig, 'RightHandMiddle3', tail=True)]
grip_posed = sum(loop, Vector()) / 4
# Express the grip in the hand's rest frame (the knife mesh is authored in rest pose).
hand_pose = rig.matrix_world @ rig.pose.bones['mixamorig:RightHand'].matrix
hand_rest = rig.matrix_world @ rig.data.bones['mixamorig:RightHand'].matrix_local
P.reset(rig)
hand = bone_head('RightHand')
index1, pinky1, middle1 = bone_head('RightHandIndex1'), bone_head('RightHandPinky1'), bone_head('RightHandMiddle1')
across = (index1 - pinky1).normalized()
finger_dir = (middle1 - hand).normalized()
palm_normal = -across.cross(finger_dir).normalized()   # verified on the previous rig: +X flexion curls toward this side
grip = hand_rest @ (hand_pose.inverted() @ grip_posed)
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

# ---------------------------------------------------------------- new bones
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; inv = rig.matrix_world.inverted()
chain_rest = {}
for c in range(N_CHAINS):
    phi = 2 * math.pi * c / N_CHAINS
    pts = [skirt_point(phi, z) for z in CHAIN_Z]
    parent = eb['mixamorig:Hips']
    for k in range(3):
        b = eb.new(f'Skirt_{c}_{k + 1}')
        b.head = inv @ pts[k]; b.tail = inv @ pts[k + 1]
        b.parent = parent; b.use_connect = False
        b.align_roll(inv.to_3x3() @ Vector((math.sin(phi), -math.cos(phi), 0)))
        parent = b
    chain_rest[c] = pts
braid = O['Braid']
path = [Vector(p) for p in braid['path']]
idx = [1, 6, 12, len(path) - 1]
parent = eb['mixamorig:Head']
for k in range(3):
    b = eb.new(f'Braid_{k + 1}')
    b.head = inv @ path[idx[k]]; b.tail = inv @ path[idx[k + 1]]
    b.parent = parent; b.use_connect = k > 0
    b.align_roll(Vector((0, 1, 0)))
    parent = b
kb = eb.new('Knife'); kb.head = inv @ grip; kb.tail = inv @ (grip + blade_dir * 0.1)
kb.align_roll(inv.to_3x3() @ palm_normal); kb.parent = eb['mixamorig:RightHand']
bpy.ops.object.mode_set(mode='OBJECT')
for side in ('Left', 'Right'):
    h = bone_head(f'{side}Hand'); m1 = bone_head(f'{side}HandMiddle1')
    sock = bpy.data.objects.new(f'Socket_Palm_{side}', None); bpy.context.scene.collection.objects.link(sock)
    sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = f'mixamorig:{side}Hand'
    sock.matrix_world = Matrix.Translation((h + m1) / 2); sock.empty_display_size = 0.02


# ---------------------------------------------------------------- weights
def set_weights(obj, fn):
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    groups = {}
    for v in obj.data.vertices:
        weights = {k: w for k, w in fn(obj.matrix_world @ v.co, v.index).items() if w > 0}
        total = sum(weights.values())
        for name, w in weights.items():
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([v.index], w / total, 'REPLACE')


def tent(u, count):
    out = {}
    for b in range(count):
        w = max(0.0, 1.0 - abs(u - (b + 0.5)))
        if (u < 0.5 and b == 0) or (u > count - 0.5 and b == count - 1):
            w = 1.0
        if w > 0:
            out[b] = w
    return out


def chain_u(z, levels):
    for k in range(len(levels) - 1):
        if z >= levels[k + 1]:
            return k + (levels[k] - z) / (levels[k] - levels[k + 1])
    return len(levels) - 1.0


def skirt_weights(co, _i):
    phi = math.atan2(co.x - axis_xy.x, -(co.y - axis_xy.y)) % (2 * math.pi)
    s = phi / (2 * math.pi) * N_CHAINS
    c0 = int(math.floor(s)) % N_CHAINS; c1 = (c0 + 1) % N_CHAINS; t = s - math.floor(s); t = t * t * (3 - 2 * t)
    hips = min(max((co.z - 0.93) / 0.07, 0.0), 1.0)
    out = {'mixamorig:Hips': hips}
    for b, w in tent(chain_u(co.z, CHAIN_Z), 3).items():
        for c, wc in ((c0, 1 - t), (c1, t)):
            out[f'Skirt_{c}_{b + 1}'] = out.get(f'Skirt_{c}_{b + 1}', 0.0) + w * wc * (1 - hips)
    return out


set_weights(skirt, skirt_weights)
braid_z = [path[i].z for i in idx]


def braid_weights(co, _i):
    headw = min(max((co.z - (braid_z[0] - 0.015)) / 0.025, 0.0), 1.0)
    out = {'mixamorig:Head': headw}
    for b, w in tent(chain_u(co.z, braid_z), 3).items():
        out[f'Braid_{b + 1}'] = out.get(f'Braid_{b + 1}', 0.0) + w * (1 - headw)
    return out


set_weights(braid, braid_weights)
for name in ('Headband', 'EyeLeft', 'EyeRight'):
    set_weights(O[name], lambda co, i: {'mixamorig:Head': 1.0})
neck_z = bone_head('Head').z
set_weights(O['Hair'], lambda co, i: {'mixamorig:Head': 1.0, 'mixamorig:Neck': max(0.0, min(0.5, (neck_z + 0.03 - co.z) / 0.06))})
set_weights(O['Knife'], lambda co, i: {'Knife': 1.0})
for name in ('Belt', 'Buckle'):
    set_weights(O[name], lambda co, i: {'mixamorig:Hips': 0.55, 'mixamorig:Spine': 0.45})
for name in ('Body', 'LegLeft', 'LegRight'):
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
    # Light smoothing removes islands where puffed sleeves/bust sit far from the proxy skin.
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=2, expand=0.0)
    bpy.ops.object.mode_set(mode='OBJECT')
# Legs below the skirt never belong to the pelvis/spine.
for name in ('LegLeft', 'LegRight'):
    side = 'Left' if name == 'LegLeft' else 'Right'
    obj = O[name]
    keep = {f'mixamorig:{side}{b}' for b in ('UpLeg', 'Leg', 'Foot', 'ToeBase')}
    for g in list(obj.vertex_groups):
        if g.name not in keep:
            obj.vertex_groups.remove(g)

# ---------------------------------------------------------------- sim helpers (hidden, not exported)
legs = proxy.copy(); legs.data = proxy.data.copy(); legs.name = 'SimLegs'
bpy.context.scene.collection.objects.link(legs)
bm = bmesh.new(); bm.from_mesh(legs.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.85 or abs(v.co.x) > 0.22], context='VERTS')
bm.to_mesh(legs.data); bm.free()
dec = legs.modifiers.new('dec', 'DECIMATE'); dec.ratio = 0.15
bpy.context.view_layer.objects.active = legs
for o in bpy.data.objects:
    o.select_set(o == legs)
while legs.modifiers[0].name != 'dec':
    bpy.ops.object.modifier_move_up(modifier='dec')
bpy.ops.object.modifier_apply(modifier='dec')
legs.hide_render = True
sim = skirt.copy(); sim.data = skirt.data.copy(); sim.name = 'SimSkirt'
bpy.context.scene.collection.objects.link(sim); sim.hide_render = True
bpy.context.scene['pfem_chain_rest'] = json.dumps({str(c): [tuple(p) for p in pts] for c, pts in chain_rest.items()})
bpy.data.objects.remove(proxy, do_unlink=True)

# ---------------------------------------------------------------- join
objects = [O[n] for n in PARTS]
for i, obj in enumerate(objects):
    obj.data.materials.clear()
    if 'part' in obj.data.attributes:
        obj.data.attributes.remove(obj.data.attributes['part'])
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
unweighted = sum(1 for v in mesh.data.vertices if not v.groups)
bpy.context.scene['pfem_parts'] = json.dumps(PARTS)
bpy.context.scene['pfem_knife'] = json.dumps({'grip': list(grip), 'blade_dir': list(blade_dir), 'palm_normal': list(palm_normal)})
print('RIGGED', 'tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'bones', len(rig.data.bones),
      'unweighted', unweighted)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rigged_v2.blend'))
