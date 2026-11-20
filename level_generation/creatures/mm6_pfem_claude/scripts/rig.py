"""Stage D: extend the MPFB Mixamo rig (skirt chains, braid, knife), weight every part, join into one mesh.

Input work/assembly_v2.blend, output work/rigged_v1.blend with objects Peasant (mesh) + Peasant_Rig.
Face attribute 'part' keeps the garment identity for UV packing and texture work.
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import posing as P

PARTS = ['Body', 'Eyes', 'ShoeLeft', 'ShoeRight', 'Belt', 'Buckle', 'Skirt', 'SleeveLeft', 'SleeveRight',
         'HairCap', 'Braid', 'Headband', 'Knife']
N_CHAINS = 12
CHAIN_Z = [0.975, 0.73, 0.47, 0.19]

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'assembly_v2.blend'))
for o in list(bpy.data.objects):
    if o.name.startswith('Meshy'):
        bpy.data.objects.remove(o, do_unlink=True)
rig = bpy.data.objects['Human.rig']
rig.name = 'Peasant_Rig'; rig.data.name = 'Peasant_Rig'
skirt = bpy.data.objects['Skirt']
braid = bpy.data.objects['Braid']
radii = np.array(skirt['radii']); zs = list(skirt['zs']); ycs = list(skirt['yc'])
seg = radii.shape[1]


def skirt_point(phi, z, inset=0.9):
    k = int(np.argmin([abs(z - zz) for zz in zs]))
    s = phi / (2 * math.pi) * seg
    s0 = int(math.floor(s)) % seg; s1 = (s0 + 1) % seg; t = s - math.floor(s)
    r = radii[k][s0] * (1 - t) + radii[k][s1] * t
    return Vector((math.sin(phi) * r * inset, ycs[k] - math.cos(phi) * r * inset, z))


# ---------------------------------------------------------------- knife mesh (forward grip in the right palm)
bones = rig.data.bones
def bone_head(name):
    return rig.matrix_world @ bones['mixamorig:' + name].head_local
hand = bone_head('RightHand')
index1, pinky1, middle1 = bone_head('RightHandIndex1'), bone_head('RightHandPinky1'), bone_head('RightHandMiddle1')
across = (index1 - pinky1).normalized()           # toward the thumb/index side
finger_dir = (middle1 - hand).normalized()
palm_normal = across.cross(finger_dir).normalized()
# Verified by curl renders: MPFB finger flexion (+local X) moves the tips toward -(across x finger_dir).
palm_normal = -palm_normal
# Grip axis: centre of the loop the middle finger forms at the authored 80-degree grip curl.
P.reset(rig); P.curl_hand(rig, 'Right', 80, thumb=35)
loop = [P.bone_world(rig, 'RightHandMiddle1'), P.bone_world(rig, 'RightHandMiddle2'),
        P.bone_world(rig, 'RightHandMiddle3'), P.bone_world(rig, 'RightHandMiddle3', tail=True)]
grip = sum(loop, Vector()) / 4
P.reset(rig)
blade_dir = across
side = palm_normal.cross(blade_dir).normalized()
knife_parts = []
def box(centre, half_len, half_w, half_t, taper=1.0):
    corners = []
    for a in (-1, 1):
        for b in (-1, 1):
            for c in (-1, 1):
                scale = taper if a > 0 else 1.0
                corners.append(centre + blade_dir * a * half_len + side * b * half_w * scale + palm_normal * c * half_t * scale)
    return corners
verts, faces = [], []
def add_box(corners, tip=None):
    base = len(verts)
    verts.extend(corners)
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    faces.extend(tuple(base + i for i in q) for q in quads)
handle_c = grip
add_box(box(handle_c, 0.05, 0.010, 0.008))                                     # wooden grip
add_box(box(handle_c + blade_dir * 0.055, 0.006, 0.018, 0.009))              # crossguard
blade_root = handle_c + blade_dir * 0.061
base = len(verts)
w, t = 0.011, 0.0025
verts.extend([blade_root + side * w, blade_root + palm_normal * t, blade_root - side * w, blade_root - palm_normal * t,
              blade_root + blade_dir * 0.11])
faces.extend([(base, base + 1, base + 4), (base + 1, base + 2, base + 4), (base + 2, base + 3, base + 4),
              (base + 3, base, base + 4), (base, base + 3, base + 2, base + 1)])
knife_me = bpy.data.meshes.new('Knife'); knife_me.from_pydata([tuple(v) for v in verts], [], faces); knife_me.update()
knife = bpy.data.objects.new('Knife', knife_me); bpy.context.scene.collection.objects.link(knife)

# ---------------------------------------------------------------- new bones
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
inv = rig.matrix_world.inverted()
for c in range(N_CHAINS):
    phi = 2 * math.pi * c / N_CHAINS
    points = [skirt_point(phi, z) for z in CHAIN_Z]
    parent = eb['mixamorig:Hips']
    for k in range(3):
        b = eb.new(f'Skirt_{c}_{k + 1}')
        b.head = inv @ points[k]; b.tail = inv @ points[k + 1]
        b.parent = parent; b.use_connect = False  # joints are keyed to simulated positions (cloth bunching)
        b.align_roll(inv.to_3x3() @ Vector((math.sin(phi), -math.cos(phi), 0)))
        parent = b
path = [Vector(p) for p in braid['path']]
idx = [0, 5, 10, len(path) - 1]
parent = eb['mixamorig:Head']
for k in range(3):
    b = eb.new(f'Braid_{k + 1}')
    b.head = inv @ path[idx[k]]; b.tail = inv @ path[idx[k + 1]]
    b.parent = parent; b.use_connect = k > 0
    b.align_roll(Vector((0, 1, 0)))
    parent = b
kb = eb.new('Knife')
kb.head = inv @ grip; kb.tail = inv @ (grip + blade_dir * 0.1)
kb.align_roll(inv.to_3x3() @ palm_normal)
kb.parent = eb['mixamorig:RightHand']
bpy.ops.object.mode_set(mode='OBJECT')

# Socket empties (not joints): palms, for optional future FX.
for side_name in ('Left', 'Right'):
    h = bone_head(f'{side_name}Hand'); m1 = bone_head(f'{side_name}HandMiddle1')
    sock = bpy.data.objects.new(f'Socket_Palm_{side_name}', None)
    bpy.context.scene.collection.objects.link(sock)
    sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = f'mixamorig:{side_name}Hand'
    sock.matrix_world = Matrix.Translation((h + m1) / 2)
    sock.empty_display_size = 0.02

# ---------------------------------------------------------------- weights
def set_weights(obj, fn):
    """fn(world_co, index) -> {bone: weight}"""
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    groups = {}
    for v in obj.data.vertices:
        weights = fn(obj.matrix_world @ v.co, v.index)
        total = sum(weights.values())
        for name, w in weights.items():
            if w <= 0:
                continue
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([v.index], w / total, 'REPLACE')


def tent(u, count):
    out = {}
    for b in range(count):
        w = max(0.0, 1.0 - abs(u - (b + 0.5)))
        if u < 0.5 and b == 0: w = 1.0
        if u > count - 0.5 and b == count - 1: w = 1.0
        if w > 0: out[b] = w
    return out


def chain_u(z, levels):
    for k in range(len(levels) - 1):
        if z >= levels[k + 1]:
            return k + (levels[k] - z) / (levels[k] - levels[k + 1])
    return len(levels) - 1.0


def skirt_weights(co, _i):
    yc = np.interp(-co.z, [-z for z in zs], ycs)
    phi = math.atan2(co.x, -(co.y - yc)) % (2 * math.pi)
    s = phi / (2 * math.pi) * N_CHAINS
    c0 = int(math.floor(s)) % N_CHAINS; c1 = (c0 + 1) % N_CHAINS; t = s - math.floor(s)
    t = t * t * (3 - 2 * t)
    u = chain_u(co.z, CHAIN_Z)
    hips = min(max((co.z - 0.90) / 0.075, 0.0), 1.0)
    out = {'mixamorig:Hips': hips} if hips > 0 else {}
    for b, w in tent(u, 3).items():
        for c, wc in ((c0, 1 - t), (c1, t)):
            name = f'Skirt_{c}_{b + 1}'
            out[name] = out.get(name, 0.0) + w * wc * (1 - hips)
    return out


set_weights(skirt, skirt_weights)
braid_z = [path[i].z for i in idx]
def braid_weights(co, _i):
    u = chain_u(co.z, braid_z)
    head = min(max((co.z - (braid_z[0] - 0.02)) / 0.03, 0.0), 1.0)
    out = {'mixamorig:Head': head} if head > 0 else {}
    for b, w in tent(u, 3).items():
        out[f'Braid_{b + 1}'] = out.get(f'Braid_{b + 1}', 0.0) + w * (1 - head)
    return out


set_weights(braid, braid_weights)
for name in ('HairCap', 'Headband'):
    set_weights(bpy.data.objects[name], lambda co, i: {'mixamorig:Head': 1.0})
set_weights(knife, lambda co, i: {'Knife': 1.0})

body_ref = bpy.data.objects['BodyRef']
for name in ('ShoeLeft', 'ShoeRight', 'Belt', 'Buckle', 'SleeveLeft', 'SleeveRight'):
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('weights', 'DATA_TRANSFER')
    mod.object = body_ref
    mod.use_vert_data = True
    mod.data_types_verts = {'VGROUP_WEIGHTS'}
    mod.vert_mapping = 'POLYINTERP_NEAREST'
    mod.layers_vgroup_select_src = 'ALL'
    mod.layers_vgroup_select_dst = 'NAME'
    bpy.ops.object.datalayout_transfer(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for g in list(obj.vertex_groups):
        if not g.name.startswith('mixamorig:'):
            obj.vertex_groups.remove(g)
# Belt/buckle ride the pelvis/lower spine rigidly enough to stay round.
for name in ('Belt', 'Buckle'):
    set_weights(bpy.data.objects[name], lambda co, i: {'mixamorig:Hips': 0.55, 'mixamorig:Spine': 0.45})

# ---------------------------------------------------------------- cloth-sim helpers (not exported)
collider = body_ref
collider.name = 'SimLegs'
bm = bmesh.new(); bm.from_mesh(collider.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.85 or abs(v.co.x) > 0.22], context='VERTS')
bm.to_mesh(collider.data); bm.free()
dec = collider.modifiers.new('dec', 'DECIMATE'); dec.ratio = 0.15
bpy.context.view_layer.objects.active = collider
bpy.ops.object.modifier_apply(modifier='dec')
for g in list(collider.vertex_groups):
    if not g.name.startswith('mixamorig:'):
        collider.vertex_groups.remove(g)
for m in list(collider.modifiers):
    if m.type != 'ARMATURE':
        collider.modifiers.remove(m)
if not any(m.type == 'ARMATURE' for m in collider.modifiers):
    collider.modifiers.new('Armature', 'ARMATURE').object = rig
collider.parent = rig
collider.hide_render = True
sim = skirt.copy(); sim.data = skirt.data.copy(); sim.name = 'SimSkirt'
bpy.context.scene.collection.objects.link(sim)
sim.hide_render = True

# ---------------------------------------------------------------- join
objects = [bpy.data.objects[n] for n in PARTS]
for i, obj in enumerate(objects):
    obj.data.materials.clear()
    attr = obj.data.attributes.new('part', 'INT', 'FACE')
    attr.data.foreach_set('value', [i] * len(obj.data.polygons))
    for g in list(obj.vertex_groups):
        if not (g.name.startswith('mixamorig:') or g.name.startswith(('Skirt_', 'Braid_', 'Knife'))):
            obj.vertex_groups.remove(g)
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
mesh.name = 'Peasant'; mesh.data.name = 'Peasant'
arm = mesh.modifiers.new('Armature', 'ARMATURE'); arm.object = rig
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
for p in mesh.data.polygons:
    p.use_smooth = True
# Remove deforming bones nobody uses? Keep the full Mixamo set for retargeting.
bpy.context.scene['pfem_parts'] = json.dumps(PARTS)
bpy.context.scene['pfem_knife'] = json.dumps({'grip': list(grip), 'blade_dir': list(blade_dir), 'palm_normal': list(palm_normal)})
tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print('RIGGED tris', tris, 'bones', len(rig.data.bones), 'groups', len(mesh.vertex_groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rigged_v1.blend'))
