"""Clear free forearms and fingers against skin and armour during the fall."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import armik

source, output, *clips = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=source)
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
rig.animation_data_create()
names = [g.name for g in body.vertex_groups]
weight = np.zeros((len(body.data.vertices), len(names)))
for vertex in body.data.vertices:
    for entry in vertex.groups:
        weight[vertex.index, entry.group] = entry.weight
def mask(side, parts, threshold):
    indices = [i for i,n in enumerate(names) if n.startswith('B_'+side+'_') and any(p in n for p in parts)]
    return weight[:, indices].sum(1) > threshold
hands = {s: mask(s, ['Hand','Finger'], .25) for s in 'LR'}
moving = {s: mask(s, ['Forearm','Hand','Finger'], .5) | hands[s] for s in 'LR'}
arms = {s: mask(s, ['Clavicle','UpperArm','Forearm','Hand','Finger'], .2) for s in 'LR'}
faces = {s: [tuple(p.vertices) for p in body.data.polygons if all(not arms[s][i] and
             not hands['L'][i] and not hands['R'][i] for i in p.vertices)] for s in 'LR'}
directions = [Vector(d).normalized() for d in ((.0123,.0217,1),(.71,-.33,-.62),(-.55,.81,.2),(.12,-.97,.21),(-.83,-.18,-.52))]
def inside(tree, point):
    votes = 0
    for direction in directions:
        origin, distance, count = point.copy(), 0., 0
        while distance < 3:
            loc, _, _, step = tree.ray_cast(origin, direction, 3-distance)
            if loc is None:
                break
            count += 1
            distance += step+1e-5
            origin = loc+direction*1e-5
        votes += count%2
    return votes >= 3

for clip in clips:
    rig.animation_data.action = bpy.data.actions['Carbine_Standing']
    rig.animation_data.action_slot = rig.animation_data.action.slots[0]
    bpy.context.scene.frame_set(0)
    head_rest = {n:rig.pose.bones[n].rotation_quaternion.copy() for n in ('B_Neck','B_Head')}
    action = bpy.data.actions[clip]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    frames = range(int(action.frame_range[0]), int(action.frame_range[1])+1)
    # The broad tassets occupy the human clip's narrow hand path at the start of the fall.
    opening = {}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        amount = min(1., max(0., (40-frame)/15))
        amount = amount*amount*(3-2*amount)
        tuck = min(1.,max(0.,min((frame-10)/15,(100-frame)/15)))
        tuck = .5*tuck*tuck*(3-2*tuck)
        for name,rest in head_rest.items():
            bone = rig.pose.bones[name]
            bone.rotation_quaternion = bone.rotation_quaternion.slerp(rest,tuck)
        across = (armik.W(rig,'B_L_UpperArm').translation-armik.W(rig,'B_R_UpperArm').translation).normalized()
        for side, sign in (('L',1),('R',-1)):
            hand = armik.W(rig, f'B_{side}_Hand')
            spacing = .14 if side == 'L' else .12
            armik.solve(rig, side, hand.translation+across*(sign*spacing*amount), hand_rot=hand.to_3x3().normalized())
        opening[frame] = {f'B_{s}_{part}': rig.pose.bones[f'B_{s}_{part}'].matrix_basis.to_quaternion()
                          for s in 'LR' for part in ('UpperArm','Forearm','Hand')}
        opening[frame].update({n:rig.pose.bones[n].rotation_quaternion.copy() for n in head_rest})
    previous = {}
    for frame, poses in opening.items():
        for n,q in poses.items():
            if n in previous and previous[n].dot(q)<0:
                q=-q
            previous[n]=q.copy()
            rig.pose.bones[n].rotation_quaternion=q
            rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=frame)
    for iteration in range(6):
        offsets = {s: [] for s in 'LR'}
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            points = [body.matrix_world @ v.co for v in mesh.vertices]
            evaluated.to_mesh_clear()
            for side in 'LR':
                trees = [BVHTree.FromPolygons(points, faces[side])]
                for obj in bpy.data.objects:
                    if not obj.name.startswith('Arm_') or obj.get('bone') in (f'B_{side}_Forearm', f'B_{side}_UpperArm'):
                        continue
                    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                    mesh = ev.to_mesh()
                    trees.append(BVHTree.FromPolygons([obj.matrix_world @ v.co for v in mesh.vertices],
                                 [tuple(p.vertices) for p in mesh.polygons if p.material_index == 0]))
                    ev.to_mesh_clear()
                best, offset = 0., Vector()
                for tree in trees:
                    for i in np.where(moving[side])[0]:
                        point = points[i]
                        loc, normal, _, distance = tree.find_nearest(point, .10)
                        if loc is not None and distance > best and (point-loc).dot(normal) < -.7*distance and inside(tree, point):
                            best, offset = distance, normal*(distance+.008)
                offsets[side].append(np.array(offset))
        maximum = max(float(np.linalg.norm(v)) for s in 'LR' for v in offsets[s])
        print('FREE_HANDS', clip, iteration, maximum, flush=True)
        if maximum < .007:
            break
        for side in 'LR':
            array = np.array(offsets[side])
            smooth = np.vstack([np.convolve(np.pad(array[:,k],2,mode='edge'), [1/9,2/9,3/9,2/9,1/9],mode='valid') for k in range(3)]).T
            offsets[side] = (array+smooth)/2
        keys = {}
        for index, frame in enumerate(frames):
            bpy.context.scene.frame_set(frame)
            for side in 'LR':
                hand = armik.W(rig, f'B_{side}_Hand')
                armik.solve(rig, side, hand.translation+Vector(offsets[side][index]), hand_rot=hand.to_3x3().normalized())
            keys[frame] = {f'B_{s}_{part}': rig.pose.bones[f'B_{s}_{part}'].matrix_basis.to_quaternion()
                           for s in 'LR' for part in ('UpperArm','Forearm','Hand')}
        previous = {}
        for frame, poses in keys.items():
            for n, q in poses.items():
                if n in previous and previous[n].dot(q) < 0:
                    q = -q
                previous[n] = q.copy()
                bone = rig.pose.bones[n]
                bone.rotation_mode = 'QUATERNION'
                bone.rotation_quaternion = q
                bone.keyframe_insert('rotation_quaternion', frame=frame)
bpy.ops.wm.save_as_mainfile(filepath=output)
