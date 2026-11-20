"""Fit the repaired serpent, arms and three connected digits; keep tail frames upright."""
import bpy
import heapq
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/geometry_repaired.blend'))
body = bpy.data.objects['Body']
me = body.data
co = np.array([v.co[:] for v in me.vertices])
edges = np.array([e.vertices[:] for e in me.edges])
adj = [[] for _ in co]
for a, b in edges:
    adj[a].append(int(b))
    adj[b].append(int(a))

def unit(v):
    return v / max(np.linalg.norm(v), 1e-9)

def resample(points, count):
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return np.column_stack([np.interp(np.linspace(0, arc[-1], count), arc, points[:, k]) for k in range(3)])

def distances(seed, allowed):
    d = np.full(len(co), 1e9)
    d[seed] = 0
    queue = [(0., int(seed))]
    while queue:
        value, v = heapq.heappop(queue)
        if value > d[v] + 1e-9:
            continue
        for w in adj[v]:
            if w not in allowed:
                continue
            nextValue = value + float(np.linalg.norm(co[w] - co[v]))
            if nextValue < d[w]:
                d[w] = nextValue
                heapq.heappush(queue, (nextValue, w))
    return d

root = np.array([0., .35, .235])
tail = [root]
for y in np.arange(.52, 3.34, .12):
    slab = co[(abs(co[:, 1] - y) < .055) & (co[:, 2] < .8)]
    assert len(slab) > 3, y
    tail.append((slab.min(0) + slab.max(0)) / 2)
tail.append(co[(co[:, 1] > 3.35) & (co[:, 0] < -.5)].mean(0))
tail = resample(np.array(tail), 27)
trunk = [root]
for z in [.4, .65, .85, 1.05, 1.25, 1.45, 1.60]:
    slab = co[(abs(co[:, 0]) < .12) & (abs(co[:, 2] - z) < .04) & (co[:, 1] < .7)]
    if z == 1.60:
        slab = slab[slab[:, 1] > .2]
    center = (slab.min(0) + slab.max(0)) / 2
    trunk.append([0., center[1], z])
trunk = np.array(trunk)
bones = {}

def add(name, head, tip, parent=None, tailFrame=False):
    head, tip = np.array(head), np.array(tip)
    axis = unit(tip - head)
    side = unit(np.cross(axis, [0, 0, 1])) if tailFrame else unit(np.array([1., 0, 0]) - axis * axis[0])
    if np.linalg.norm(side) < .1:
        side = np.array([0., 1, 0])
    bones[name] = dict(head=head.tolist(), tail=tip.tolist(), parent=parent,
                       roll=np.cross(side, axis).tolist())

add('Root', root, root + [0, 0, .1])
tailNames = []
for i in range(len(tail) - 1):
    name = f'Tail_{i:02d}'
    add(name, tail[i], tail[i + 1], tailNames[-1] if tailNames else 'Root', True)
    tailNames.append(name)
spineNames = []
for i in range(len(trunk) - 1):
    name = f'Spine_{i:02d}'
    add(name, trunk[i], trunk[i + 1], spineNames[-1] if spineNames else 'Root')
    spineNames.append(name)
add('Neck', trunk[-1], [0, .39, 1.77], spineNames[-1])
add('Head', [0, .39, 1.77], [0, -.22, 1.77], 'Neck')
add('Jaw', [0, .115, 1.715], [0, -.215, 1.60], 'Head')
arms = {}
fingers = {}
for side, sign in [('L', 1), ('R', -1)]:
    points = np.array([[sign * .30, .38, 1.46], [sign * .62, .43, 1.22],
                       [sign * .87, .34, 1.005], [sign * .965, .255, .86]])
    names = [side + '_' + n for n in ['Arm', 'Forearm', 'Hand']]
    for i, name in enumerate(names):
        add(name, points[i], points[i + 1], names[i - 1] if i else spineNames[-1])
    arms[side] = dict(points=points.tolist(), names=names)
    allowed = set(np.where((co[:, 0] * sign > .6) & (co[:, 2] < .97) & (co[:, 1] < .7))[0])
    remaining = {v for v in allowed if co[v, 2] < .75}
    parts = []
    while remaining:
        queue = [remaining.pop()]
        ids = []
        while queue:
            v = queue.pop()
            ids.append(v)
            for w in adj[v]:
                if w in remaining:
                    remaining.remove(w)
                    queue.append(w)
        if len(ids) > 10:
            parts.append(ids)
    assert len(parts) == 3, (side, list(map(len, parts)))
    tips = [ids[int(np.argmin(co[ids, 2]))] for ids in parts]
    scores = np.array([distances(seed, allowed) for seed in tips])
    owner = scores.argmin(0)
    fingers[side] = []
    for digit, seed in enumerate(tips):
        ids = np.array([v for v in allowed if owner[v] == digit and co[v, 2] < .865])
        d = scores[digit, ids]
        length = np.percentile(d, 94)
        samples = []
        for station in np.linspace(length, 0, 10):
            local = ids[abs(d - station) < max(.014, length / 14)]
            samples.append(co[local].mean(0) if len(local) else co[ids[np.argmin(abs(d-station))]])
        samples[-1] = co[seed]
        points = resample(np.array(samples), 4)
        names = [f'{side}_Digit{digit}_{i}' for i in range(3)]
        for i, name in enumerate(names):
            add(name, points[i], points[i + 1], names[i - 1] if i else side + '_Hand')
        fingers[side].append(dict(points=points.tolist(), names=names, vertices=ids.tolist()))

armature = bpy.data.armatures.new('SerpentmanSkeleton')
rig = bpy.data.objects.new('Rig', armature)
bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for name, b in bones.items():
    bone = armature.edit_bones.new(name)
    bone.head, bone.tail = b['head'], b['tail']
    bone.align_roll(Vector(b['roll']))
    if b['parent']:
        bone.parent = armature.edit_bones[b['parent']]
    bone.use_deform = name != 'Root'
bpy.ops.object.mode_set(mode='OBJECT')
names = list(bones)
index = {n: i for i, n in enumerate(names)}
weights = np.zeros((len(co), len(names)))

def chain(ids, nodes, points, target):
    ids = np.asarray(ids, dtype=int)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    closest = np.full(len(ids), 1e9)
    station = np.zeros(len(ids))
    for i, (a, b) in enumerate(zip(points[:-1], points[1:])):
        direction = b - a
        t = np.clip((co[ids] - a) @ direction / (direction @ direction), 0, 1)
        distance = np.linalg.norm(co[ids] - a - t[:, None] * direction, axis=1)
        use = distance < closest
        closest[use] = distance[use]
        station[use] = arc[i] + t[use] * (arc[i + 1] - arc[i])
    centers = (arc[:-1] + arc[1:]) / 2
    for k, n in enumerate(nodes):
        target[ids, index[n]] = np.interp(station, centers, np.eye(len(nodes))[k])

central = np.vstack([tail[::-1], trunk[1:], [0, .39, 1.77], [0, -.22, 1.77]])
chain(np.arange(len(co)), tailNames[::-1] + spineNames + ['Neck', 'Head'], central, weights)
# Blend around the inside of the tail/trunk bend, where nearest-segment stations are discontinuous.
base = np.where((co[:, 2] < .85) & (co[:, 1] < .95) & (abs(co[:, 0]) < .40))[0]
for _ in range(28):
    blended = weights.copy()
    for i in base:
        if adj[i]:
            blended[i] = .35 * weights[i] + .65 * weights[adj[i]].mean(0)
    weights = blended

for side, sign in [('L', 1), ('R', -1)]:
    ids = np.where((co[:, 0] * sign > .24) & (co[:, 2] > 1.06) & (co[:, 1] < .7) |
                   ((co[:, 0] * sign > .60) & (co[:, 2] > .45) & (co[:, 1] < .7)))[0]
    new = np.zeros_like(weights)
    chain(ids, arms[side]['names'], np.array(arms[side]['points']), new)
    blend = np.clip((co[ids, 0] * sign - .24) / .17, 0, 1)
    blend = blend * blend * (3 - 2 * blend)
    weights[ids] = weights[ids] * (1 - blend[:, None]) + new[ids] * blend[:, None]
    for finger in fingers[side]:
        ids = np.array(finger['vertices'])
        new = np.zeros_like(weights)
        chain(ids, finger['names'], np.array(finger['points']), new)
        blend = np.clip((.87 - co[ids, 2]) / .06, 0, 1)
        weights[ids] = weights[ids] * (1 - blend[:, None]) + new[ids] * blend[:, None]

# Mesh connectivity keeps upper fangs with the skull while the lower jaw opens.
headIds=set(np.where((co[:,2]>1.52)&(co[:,1]<.7)&(abs(co[:,0])<.35))[0])
upperSeed=min(headIds,key=lambda i:np.linalg.norm(co[i]-[0,-.19,1.81]))
lowerSeed=min(headIds,key=lambda i:np.linalg.norm(co[i]-[0,-.16,1.60]))
upperDistance=distances(upperSeed,headIds)
lowerDistance=distances(lowerSeed,headIds)
connected=(upperDistance<1e8)&(lowerDistance<1e8)
jawWeight=np.clip((upperDistance-lowerDistance)/.10+.5,0,1)*np.clip((.18-co[:,1])/.15,0,1)
jawWeight[~connected]=0
jawWeight*=np.clip((co[:,2]-1.53)/.07,0,1)
# Detached teeth inherit their attachment surface, not their low tips.
left=set(i for i in headIds if not connected[i])
while left:
 todo=[left.pop()];ids=[]
 while todo:
  v=todo.pop();ids.append(v)
  for w in adj[v]:
   if w in left:left.remove(w);todo.append(w)
 main=np.where(connected)[0]
 pair=np.linalg.norm(co[ids,None]-co[main],axis=2)
 toothVertex,mainVertex=np.unravel_index(pair.argmin(),pair.shape)
 jawWeight[ids]=jawWeight[main[mainVertex]]
# Skull and tooth roots follow the head; blend only the actual rear-neck transition.
skull=np.zeros(len(co))
ids=np.array(sorted(headIds))
skull[ids]=np.clip((co[ids,2]-1.60)/.18+(.30-co[ids,1])/.25,0,1)
skull[ids[~connected[ids]]]=1
skull=skull*skull*(3-2*skull)
weights*=1-skull[:,None]
weights[:,index['Head']]+=skull
jaw=jawWeight>.98
weights*=1-jawWeight[:,None]
weights[:,index['Jaw']]+=jawWeight
for _ in range(3):
    smoothed = weights.copy()
    for i, neighbors in enumerate(adj):
        if neighbors and not jaw[i]:
            smoothed[i] = .75 * weights[i] + .25 * weights[neighbors].mean(0)
    weights = smoothed
keep = np.argpartition(weights, -4, axis=1)[:, -4:]
mask = np.zeros_like(weights, dtype=bool)
np.put_along_axis(mask, keep, True, axis=1)
weights[~mask] = 0
assert np.all(weights.sum(1) > .5)
weights /= weights.sum(1)[:, None]
assert np.allclose(weights.sum(1), 1) and len(bones) < 128
for n in names:
    group = body.vertex_groups.new(name=n)
    for i in np.where(weights[:, index[n]] > 1e-7)[0]:
        group.add([int(i)], float(weights[i, index[n]]), 'REPLACE')
for e in me.edges:e.use_edge_sharp=False
body.parent = rig
modifier = body.modifiers.new('SerpentSkin', 'ARMATURE')
modifier.object = rig
rig.show_in_front = True
for bone in rig.pose.bones:
    bone.rotation_mode = 'QUATERNION'
for name, point, parent in [('Socket_Mouth', [0, -.24, 1.69], 'Head')]:
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = parent
    obj.matrix_world.translation = Vector(point)
data = dict(bones=bones, tail=tail.tolist(), tail_names=tailNames, trunk=trunk.tolist(),
            spine_names=spineNames, arms=arms, fingers=fingers)
(P / 'work/rig.json').write_text(json.dumps(data, indent=2) + '\n')
np.savez(P / 'work/weights.npz', co=co, edges=edges, weights=weights, names=np.array(names))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_v1.blend'))
print('RIG', len(names), 'bones;', len(co), 'weighted vertices; three fingers per hand')
