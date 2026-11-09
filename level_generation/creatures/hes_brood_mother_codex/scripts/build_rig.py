"""Fitted source-frame upper-body rig; belly, cradle and stalk caps remain on Base."""
import bpy
import bmesh
import heapq
import json
import math
from pathlib import Path

import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

P = Path(__file__).resolve().parents[1]
REFERENCE = P.parent / 'mm6_qfi_claude/work/source_rest.json'
SRC = json.loads(REFERENCE.read_text())
landmarks = json.loads((P / 'work/joints.json').read_text())
J = {name: Vector(point) for name, point in landmarks['joints'].items()}
FIT = json.loads((P / 'work/fingers_fit.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/repaired_geometry.blend'))
queen = bpy.data.objects['BroodMother']
mesh = queen.data
co = np.array([tuple(v.co) for v in mesh.vertices])
edges = np.array([tuple(e.vertices) for e in mesh.edges])
N = len(co)
adj = [[] for _ in range(N)]
for a, b in edges:
    length = float(np.linalg.norm(co[a] - co[b]))
    adj[a].append((int(b), length))
    adj[b].append((int(a), length))


def components(mask):
    unseen = set(np.where(mask)[0])
    out = []
    while unseen:
        v = unseen.pop()
        part, todo = [v], [v]
        while todo:
            for w, _ in adj[todo.pop()]:
                if w in unseen:
                    unseen.remove(w)
                    part.append(w)
                    todo.append(w)
        out.append(np.array(part, dtype=int))
    return out


def finger_names(side, digit):
    if side == 'R' and digit == 0:
        return ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
    return [f'B_{side}_Finger{digit}', f'B_{side}_Finger{digit}1', f'B_{side}_Finger{digit}2']


mapping = {f'B_{name}': name for name in J}
names = [name for name in SRC if name in mapping or 'Finger' in name]
head = {name: J[source].copy() for name, source in mapping.items()}
rotation, swing, finger_ends = {}, {}, {}
for name in names:
    source = SRC[name]
    child = source['child']
    if name == 'B_Pelvis':
        q = Quaternion()
    elif name in mapping and child in mapping:
        q = Vector(source['seg']).rotation_difference(head[child] - head[name])
    else:
        q = swing.get(source['parent'], Quaternion())
    swing[name] = q
    rotation[name] = q.to_matrix() @ Matrix(source['rot'])


def basis(forward, across):
    forward = np.array(forward)
    forward /= np.linalg.norm(forward)
    across = np.array(across) - forward * np.dot(across, forward)
    across /= np.linalg.norm(across)
    return np.column_stack((forward, across, np.cross(forward, across)))


for side in ('L', 'R'):
    hand = f'B_{side}_Hand'
    chains = FIT[side]['chains']
    our_forward = np.array(chains['middle']['points'][0]) - np.array(head[hand])
    our_across = np.array(chains['index']['points'][0]) - np.array(chains['pinky']['points'][0])
    src_forward = np.array(SRC[f'B_{side}_Finger2']['head']) - np.array(SRC[hand]['head'])
    src_across = np.array(SRC[f'B_{side}_Finger1']['head']) - np.array(SRC[f'B_{side}_Finger4']['head'])
    qhand = Matrix((basis(our_forward, our_across) @ basis(src_forward, src_across).T).tolist()).to_quaternion()
    swing[hand] = qhand
    rotation[hand] = qhand.to_matrix() @ Matrix(SRC[hand]['rot'])
    for digit, label in enumerate(('thumb', 'index', 'middle', 'ring', 'pinky')):
        points = [Vector(point) for point in chains[label]['points']]
        for k, name in enumerate(finger_names(side, digit)):
            head[name] = points[k]
            source_segment = Vector(SRC[name]['seg'] or (0, 0, 0))
            if source_segment.length < 1e-8:
                source_segment = Vector(SRC[name]['head']) - Vector(SRC[SRC[name]['parent']]['head'])
            q = (qhand @ source_segment).rotation_difference(points[k + 1] - points[k]) @ qhand
            swing[name] = q
            rotation[name] = q.to_matrix() @ Matrix(SRC[name]['rot'])
            finger_ends[name] = points[k + 1]

data = bpy.data.armatures.new('BroodMotherRig')
rig = bpy.data.objects.new('Rig', data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
root = data.edit_bones.new('Root')
root.head, root.tail, root.use_deform = (0, 0, 0), (0, 0, .3), False
base = data.edit_bones.new('Base')
base.head, base.tail, base.parent = (0, 0, 0), (0, 0, .5), root
for name in names:
    bone = data.edit_bones.new(name)
    child = SRC[name]['child']
    endpoint = finger_ends.get(name, head.get(child, head[name] + Vector((0, 0, .15))))
    length = max((endpoint - head[name]).length, .03)
    bone.head = head[name]
    bone.tail = head[name] + rotation[name].col[1] * length
    bone.align_roll(rotation[name].col[2])
for name in names:
    parent = SRC[name]['parent']
    data.edit_bones[name].parent = data.edit_bones[parent] if parent in names else base
mouth = data.edit_bones.new('Socket_Mouth')
mouth.head, mouth.tail = (-1.0764, .2847, 3.6669), (-1.0764, .1347, 3.6669)
mouth.parent, mouth.use_deform = data.edit_bones['B_Head'], False
for socket in json.loads((P / 'socket_layout.json').read_text())['sockets']:
    bone = data.edit_bones.new('Socket_Sac_' + socket['name'])
    cap = bpy.data.objects['Socket_' + socket['name']]
    points = np.array([tuple(v.co) for v in cap.data.vertices])
    top = points[np.abs(points[:,2] - points[:,2].max()) < 1e-6]
    bone.head = Vector((top.min(0) + top.max(0)) / 2)
    bone.tail = bone.head + Vector((0, 0, .1))
    bone.parent, bone.use_deform = base, False
bpy.ops.object.mode_set(mode='OBJECT')
frame_error = max(math.degrees(data.bones[name].matrix_local.to_quaternion().rotation_difference(
    rotation[name].to_quaternion()).angle) for name in names)
assert frame_error < .1, frame_error
bpy.context.scene['rig_offsets'] = json.dumps({name: {'q': list(swing[name]), 'R_src': SRC[name]['rot']}
                                              for name in names})

deform = ['Base'] + names
column = {name: k for k, name in enumerate(deform)}
weights = np.zeros((N, len(deform)))
body_names = [name for name in names if 'Finger' not in name]
segments = []
for name in body_names:
    child = SRC[name]['child']
    a = np.array(head[name])
    b = np.array(head.get(child, head[name] + Vector((0, 0, .15))))
    d = b - a
    t = np.clip((co - a) @ d / max(float(d @ d), 1e-12), 0, 1)
    segments.append(a + t[:, None] * d)
closest = np.stack(segments, axis=1)
distance = np.linalg.norm(closest - co[:, None, :], axis=2)
arm_columns = [k for k, name in enumerate(body_names) if any(word in name for word in ('UpperArm', 'Forearm', 'Hand'))]
arm_distance = distance[:, arm_columns].min(1)
spec = landmarks['raw_to_blender']
raw = co @ np.array(Matrix.Rotation(math.radians(-45), 3, 'Z')).T / spec['scale']
raw[:, 2] += spec['floor_raw_z']
hand_ids = np.array(sorted(set(i for side in FIT.values() for i in side['hand_vertices'])))
hand_mask = np.zeros(N, bool)
hand_mask[hand_ids] = True
belly = (raw[:, 1] < .145) & (raw[:, 2] < .112) & (np.abs(raw[:, 0]) < .24) & (arm_distance > .22)
static = ((co[:, 2] < 2.55) & (arm_distance > .38)) | (raw[:, 1] > .335)
static |= ((np.abs(raw[:, 0]) > .32) & (co[:, 2] < 3.4)) | belly
static[hand_ids] = False
head_possible = (raw[:, 2] > .235) | ((np.abs(raw[:, 0]) > .18) & (raw[:, 2] > .155))
head_parts = components(head_possible)
head_part = min(head_parts, key=lambda ids: np.linalg.norm(co[ids] - np.array(J['Head']), axis=1).min())
head_mask = np.zeros(N, bool)
head_mask[head_part] = True
# The returned right horn drops through the height cut; its measured outer arc is one rigid head part.
horn_candidates = (co[:,0] < -1.8) & (co[:,1] < 1.15) & (co[:,2] > 3.2)
horn_part = min(components(horn_candidates), key=lambda ids: np.linalg.norm(co[ids] - [-2.48,.79,3.44], axis=1).min())
horn_tip = np.zeros(N, bool)
horn_tip[horn_part] = True
head_mask |= horn_tip
static[head_mask] = False

bm = bmesh.new()
bm.from_mesh(mesh)
tree = BVHTree.FromBMesh(bm)
bm.free()
seed = np.full(N, -1)
seed[static] = column['Base']
seed[head_mask] = column['B_Head']
for i in np.where(seed < 0)[0]:
    for k in np.argsort(distance[i])[:4]:
        if distance[i, k] > .32:
            break
        start = Vector(co[i]) - mesh.vertices[i].normal * .001
        delta = Vector(closest[i, k]) - start
        if delta.length < 1e-5 or tree.ray_cast(start, delta.normalized(), max(0, delta.length - .001))[0] is None:
            seed[i] = column[body_names[k]]
            break
geo = np.full(N, np.inf)
labels = np.full(N, -1)
queue = []
for i in np.where(seed >= 0)[0]:
    geo[i], labels[i] = 0, seed[i]
    queue.append((0., int(i)))
heapq.heapify(queue)
while queue:
    d, v = heapq.heappop(queue)
    if d > geo[v]:
        continue
    for w, length in adj[v]:
        nd = d + length
        if nd < geo[w]:
            geo[w], labels[w] = nd, labels[v]
            heapq.heappush(queue, (nd, w))
# Disconnected armour/crest pieces inherit one owner from their neighbouring body, never arbitrary fallback bones.
pieces = components(np.ones(N, bool))
main = max(pieces, key=len)
kd = KDTree(len(main))
for k, i in enumerate(main):
    kd.insert(co[i], int(i))
kd.balance()
for ids in pieces:
    if len(ids) == len(main):
        continue
    owners = [labels[kd.find(co[i])[1]] for i in ids]
    owner = max(set(owners), key=owners.count)
    if raw[ids, 2].mean() > .255:
        owner = column['B_Head']
    labels[ids] = owner
assert np.all(labels >= 0)
weights[np.arange(N), labels] = 1
for _ in range(4):
    updated = weights.copy()
    for i, neighbours in enumerate(adj):
        if neighbours:
            updated[i] = .5 * weights[i] + .5 * weights[[j for j, _ in neighbours]].mean(0)
    weights = updated
weights[static] = 0
weights[static, column['Base']] = 1
weights[head_mask] = 0
weights[head_mask, column['B_Head']] = 1
for side in ('L', 'R'):
    hand_name = f'B_{side}_Hand'
    ids = FIT[side]['hand_vertices']
    weights[ids] = 0
    weights[ids, column[hand_name]] = 1
    for digit, label in enumerate(('thumb', 'index', 'middle', 'ring', 'pinky')):
        chain = FIT[side]['chains'][label]
        points = np.array(chain['points'])
        for i in chain['vertices']:
            best = None
            for k in range(3):
                d = points[k + 1] - points[k]
                t = float(np.clip((co[i] - points[k]) @ d / (d @ d), 0, 1))
                value = np.linalg.norm(co[i] - points[k] - t * d)
                if best is None or value < best[0]:
                    best = value, k, t
            _, k, t = best
            weights[i] = 0
            names_digit = finger_names(side, digit)
            if k == 0 and t < .3:
                share = .5 + t / .6
                weights[i, column[hand_name]] = 1 - share
                weights[i, column[names_digit[0]]] = share
            elif t > .7 and k < 2:
                share = (t - .7) / .6
                weights[i, column[names_digit[k]]] = 1 - share
                weights[i, column[names_digit[k + 1]]] = share
            else:
                weights[i, column[names_digit[k]]] = 1
# Remove medial shoulder bleed onto the chest; the generated breast plates share the chest frame.
for side, sign in (('L', 1), ('R', -1)):
    lateral = raw[:, 0] * sign
    for name in (f'B_{side}_UpperArm', f'B_{side}_Forearm'):
        fade = np.clip((lateral - .06) / .07, 0, 1)
        removed = weights[:, column[name]] * (1 - fade)
        weights[:, column[name]] -= removed
        weights[:, column['B_Spine2']] += removed
top = np.argsort(weights, axis=1)[:, -4:]
limited = np.zeros_like(weights)
limited[np.arange(N)[:, None], top] = weights[np.arange(N)[:, None], top]
weights = limited / limited.sum(1, keepdims=True)
assert np.isfinite(weights).all()


def bind(ob, matrix):
    ob.parent = rig
    modifier = ob.modifiers.new('Armature', 'ARMATURE')
    modifier.object = rig
    groups = [ob.vertex_groups.new(name=name) for name in deform]
    for k, group in enumerate(groups):
        for i in np.where(matrix[:, k] > 1e-6)[0]:
            group.add([int(i)], float(matrix[i, k]), 'REPLACE')


bind(queen, weights)
for ob in list(bpy.context.scene.objects):
    if ob.type != 'MESH' or ob == queen:
        continue
    w = np.zeros((len(ob.data.vertices), len(deform)))
    w[:, 0] = 1
    if ob.name == 'LeftLittleFinger':
        points = np.array(FIT['L']['chains']['pinky']['points'])
        coords = np.array([tuple(v.co) for v in ob.data.vertices])
        chain_names = finger_names('L', 4)
        for i, point in enumerate(coords):
            choices = []
            for k in range(3):
                d = points[k + 1] - points[k]
                t = float(np.clip((point - points[k]) @ d / (d @ d), 0, 1))
                choices.append((np.linalg.norm(point - points[k] - t * d), k, t))
            _, k, t = min(choices)
            w[i] = 0
            if k == 0 and t < .4:
                w[i, column['B_L_Hand']] = 1 - t / .4
                w[i, column[chain_names[k]]] = t / .4
            else:
                w[i, column[chain_names[k]]] = 1
    bind(ob, w)
report = {'bones': len(data.bones), 'frame_error_degrees': frame_error, 'main_vertices': N,
          'static_anchor_vertices': int(static.sum()), 'rigid_head_vertices': int(head_mask.sum()),
          'max_influences': int((weights > 1e-6).sum(1).max()), 'weight_sum_error': float(abs(weights.sum(1) - 1).max()),
          'source_frames': str(REFERENCE.relative_to(P.parents[2])),
          'note': 'Initial rig; clip/contact gates not yet passed.'}
(P / 'work/rig.json').write_text(json.dumps(report, indent=2) + '\n')
np.savez(P / 'work/rig_weights.npz', vertices=co, weights=weights, names=np.array(deform), static=static, head=head_mask)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_v1.blend'))
print(json.dumps(report))
