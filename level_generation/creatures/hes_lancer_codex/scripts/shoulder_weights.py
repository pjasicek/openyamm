"""Smooth the abrupt source skin weights at the boss's broad shoulder/torso junctions."""
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils.kdtree import KDTree

source, output = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=source)
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
positions = np.array([v.co[:] for v in body.data.vertices])
skin = np.array([x.value == 0 for x in body.data.attributes['piece'].data])
names = [g.name for g in body.vertex_groups]
weights = np.zeros((len(positions),len(names)))
for v in body.data.vertices:
    for e in v.groups:
        weights[v.index,e.group] = e.weight
distance = np.minimum.reduce([np.linalg.norm(positions-np.array(rig.data.bones[f'B_{s}_UpperArm'].head_local),axis=1) for s in 'LR'])
selected = np.where(skin & (distance<.25))[0]
tree = KDTree(int(skin.sum()))
for index in np.where(skin)[0]:
    tree.insert(positions[index],int(index))
tree.balance()
neighbors = {}
for index in selected:
    nearby = tree.find_range(positions[index],.10)
    ids = np.array([i for _,i,_ in nearby])
    coefficients = np.exp(-np.array([d for _,_,d in nearby])**2/(2*.035**2))
    neighbors[index] = ids,coefficients/coefficients.sum()
for _ in range(5):
    updated = weights.copy()
    for index,(ids,coefficients) in neighbors.items():
        amount = .65*min(1.,max(0.,(.25-distance[index])/.08))
        updated[index] = (1-amount)*weights[index]+amount*(coefficients@weights[ids])
    weights = updated
for index in selected:
    strongest = np.argsort(weights[index])[-4:]
    values = weights[index,strongest]
    values /= values.sum()
    for group in body.vertex_groups:
        group.remove([int(index)])
    for group,value in zip(strongest,values):
        if value>1e-6:
            body.vertex_groups[int(group)].add([int(index)],float(value),'REPLACE')
assert np.isfinite(weights).all()
assert np.allclose(weights[selected].sum(1),1,atol=1e-5)
print('SHOULDER_WEIGHTS',len(selected),'skin vertices, positions and skeleton unchanged',flush=True)
bpy.ops.wm.save_as_mainfile(filepath=output)
