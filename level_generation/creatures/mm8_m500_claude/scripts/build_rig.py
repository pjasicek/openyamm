"""Fit the repaired serpent, arms and five connected digits; keep tail frames upright."""
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

root = np.array([.02, .10, .23])
tail = resample(np.array([root,[.055,.35,.22],[.09,.55,.29],[.10,.8,.31],[.08,1.,.25],
                         [.05,1.2,.20],[0,1.4,.18],[-.04,1.6,.19],[-.08,1.8,.23],
                         [-.11,2.0,.33],[-.12,2.12,.50],[-.10,2.13,.66]]),27)
trunk = np.array([root,[0,-.08,.40],[0,-.12,.60],[0,-.10,.80],[0,-.05,1.0],
                  [0,-.025,1.20],[0,.02,1.40],[0,.015,1.52]])
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
add('Neck', trunk[-1], [0, 0, 1.70], spineNames[-1])
add('Head', [0, 0, 1.70], [0, -.19, 1.75], 'Neck')
add('Jaw', [0, -.045, 1.69], [0, -.19, 1.675], 'Head')
arms = {}
fingers = {}
for side, sign in [('L', 1), ('R', -1)]:
    points = np.array([[sign*.23,0,1.35],[sign*.36,-.045,1.12],
                       [sign*.54,-.27,.97],[sign*.66,-.40,.87]])
    names = [side + '_' + n for n in ['Arm', 'Forearm', 'Hand']]
    for i, name in enumerate(names):
        add(name, points[i], points[i + 1], names[i - 1] if i else spineNames[-1])
    arms[side] = dict(points=points.tolist(), names=names)
    allowed=set(np.where((co[:,0]*sign>.48)&(co[:,2]<1.04)&(co[:,1]<.12))[0])
    guesses=([( .65,.975),(.832,.87),(.81,.785),(.72,.735),(.55,.75)] if sign>0 else
             [(.63,.99),(.805,.89),(.79,.82),(.69,.76),(.535,.78)])
    tips=[min(allowed,key=lambda i:(co[i,0]*sign-x)**2+(co[i,2]-z)**2) for x,z in guesses]
    assert len(set(tips))==5
    scores=np.array([distances(seed,allowed) for seed in tips]);owner=scores.argmin(0)
    fingers[side]=[]
    for digit,seed in enumerate(tips):
        ids=np.array([v for v in allowed if owner[v]==digit])
        tip=co[seed].copy();base=points[-1]+.25*(tip-points[-1])
        fingerPoints=np.array([base,base+.4*(tip-base),base+.75*(tip-base),tip])
        fingerNames=[f'{side}_Digit{digit}_{i}' for i in range(3)]
        for i,name in enumerate(fingerNames):
            add(name,fingerPoints[i],fingerPoints[i+1],fingerNames[i-1] if i else side+'_Hand')
        fingers[side].append(dict(points=fingerPoints.tolist(),names=fingerNames,vertices=ids.tolist()))
finNames=[]
for i in range(2,len(spineNames)):
    point=trunk[i].copy();point[1]+=.10
    name=f'Dorsal_{i}';add(name,point,point+[0,.35,0],spineNames[i]);finNames.append(name)
add('Caudal',tail[-1],tail[-1]+[0,0,.45],tailNames[-1])

armature = bpy.data.armatures.new('WaterElementalSkeleton')
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

central = np.vstack([tail[::-1], trunk[1:], [0, 0, 1.70], [0, -.19, 1.75]])
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
    ids = np.where((((co[:,0]*sign>.18)&(co[:,2]>1.23)) |
                    ((co[:,0]*sign>.28)&(co[:,2]>.65))) & (co[:,1]<.18))[0]
    new = np.zeros_like(weights)
    chain(ids, arms[side]['names'], np.array(arms[side]['points']), new)
    blend = np.clip((co[ids, 0] * sign - .19) / .14, 0, 1)
    blend = blend * blend * (3 - 2 * blend)
    weights[ids] = weights[ids] * (1 - blend[:, None]) + new[ids] * blend[:, None]
    for finger in fingers[side]:
        ids = np.array(finger['vertices'])
        new = np.zeros_like(weights)
        chain(ids, finger['names'], np.array(finger['points']), new)
        palm=np.array(arms[side]['points'][-1]);blend=np.clip((np.linalg.norm(co[ids]-palm,axis=1)-.025)/.075,0,1)
        weights[ids] = weights[ids] * (1 - blend[:, None]) + new[ids] * blend[:, None]

# The medial sail follows its spinal height, not the spatially closer tail beneath it.
allowed=set(np.where((abs(co[:,0])<.20)&(co[:,1]>.13)&(co[:,1]<1.12)&(co[:,2]>.60))[0])
seed=min(allowed,key=lambda i:np.linalg.norm(co[i]-[.02,.45,1.30]))
finIds=[];todo=[seed];allowed.remove(seed)
while todo:
    v=todo.pop();finIds.append(v)
    for w in adj[v]:
        if w in allowed:allowed.remove(w);todo.append(w)
assert 200<len(finIds)<600,len(finIds)
heights=np.array([bones[n]['head'][2] for n in finNames])
for i in finIds:
    weights[i]=0
    for k,n in enumerate(finNames):weights[i,index[n]]=np.interp(co[i,2],heights,np.eye(len(finNames))[k])
caudal=np.where((co[:,1]>1.25)&(co[:,2]>.65))[0]
blend=np.clip((co[caudal,2]-.65)/.15,0,1)
weights[caudal]*=1-blend[:,None];weights[caudal,index['Caudal']]+=blend
headIds=np.where((co[:,2]>1.57)&(co[:,1]<.55))[0]
headBlend=np.clip((co[headIds,2]-1.57)/.12,0,1)
weights[headIds]*=1-headBlend[:,None];weights[headIds,index['Head']]+=headBlend
# The narrow lower lip opens; the skull, cheek plates, eyes and upper teeth remain on Head.
jawWeight=np.clip((1.69-co[:,2])/.035,0,1)*np.clip((-.035-co[:,1])/.055,0,1)
jawWeight*=((co[:,2]>1.63)&(abs(co[:,0])<.075))
weights*=1-jawWeight[:,None];weights[:,index['Jaw']]+=jawWeight
jaw=jawWeight>.98
for _ in range(5):
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
for name, point, parent in [('Socket_Mouth', [0, -.22, 1.70], 'Head'),('Socket_PalmL',[.67,-.44,.87],'L_Hand'),('Socket_PalmR',[-.67,-.44,.87],'R_Hand')]:
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = parent
    obj.matrix_world.translation = Vector(point)
data = dict(bones=bones, tail=tail.tolist(), tail_names=tailNames, trunk=trunk.tolist(),
            spine_names=spineNames, arms=arms, fingers=fingers, fin_names=finNames)
(P / 'work/rig.json').write_text(json.dumps(data, indent=2) + '\n')
np.savez(P / 'work/weights.npz', co=co, edges=edges, weights=weights, names=np.array(names))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_v1.blend'))
print('RIG', len(names), 'bones;', len(co), 'weighted vertices; five webbed digits per hand')
