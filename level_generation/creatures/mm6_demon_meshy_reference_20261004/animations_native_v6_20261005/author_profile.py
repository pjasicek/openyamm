"""Revise the native tail curve and foot anatomy, retaining the reviewed body motion."""
import importlib.util
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

STAGE = Path(__file__).resolve().parent
BASELINE = STAGE.parent/'animations_native_v5_20261005'
spec = importlib.util.spec_from_file_location('motion', STAGE/'motion.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
TAIL = [f'Bone_{i:03d}' for i in range(20,14,-1)]
LEGS = ['mixamorig:'+side+part for side in ('Right','Left') for part in ('UpLeg','Leg','Foot')]


def solve_leg(rig, side, target, orientation, old_knee):
    upper, lower, foot = [rig.pose.bones['mixamorig:'+side+part] for part in ('UpLeg','Leg','Foot')]
    a, b = lower.bone.head_local-upper.bone.head_local, foot.bone.head_local-lower.bone.head_local
    hip = upper.head.copy()
    old_upper,old_lower = upper.matrix.to_quaternion(),lower.matrix.to_quaternion()
    old_a,old_b = lower.head-upper.head,foot.head-lower.head
    delta = target-hip
    distance = delta.length
    assert abs(a.length-b.length)<distance<a.length+b.length, (side,distance)
    axis = delta.normalized()
    pole = old_knee-hip
    pole = (pole-axis*pole.dot(axis)).normalized()
    along = (a.length_squared-b.length_squared+distance*distance)/(2*distance)
    knee = hip+axis*along+pole*math.sqrt(max(0,a.length_squared-along*along))
    motion.assign(upper,old_a.rotation_difference(knee-hip)@old_upper,hip)
    motion.assign(lower,old_b.rotation_difference(target-knee)@old_lower,knee)
    motion.assign(foot,orientation,target)


def tighten_tail(rig):
    bones = [rig.pose.bones[name] for name in TAIL]
    root = bones[0].head.copy()
    target = bones[-1].tail.copy()
    target.y = root.y+(target.y-root.y)*.72
    lengths = [bone.length for bone in bones]
    assert (target-root).length<sum(lengths)
    horizontal = Vector((target.x-root.x,target.y-root.y,0)).normalized()
    points = [root.copy()]
    # Arch out from the hip, return toward the thigh, then let the distal tip hang.
    for length,degrees in zip(lengths,[18,-47,-110,-75,-105,-75]):
        angle = math.radians(degrees)
        points.append(points[-1]+length*(horizontal*math.cos(angle)+Vector((0,0,math.sin(angle)))))
    alignment = (points[-1]-root).rotation_difference(target-root)
    points = [root+alignment@(point-root) for point in points]
    for iteration in range(60):
        points[-1] = target.copy()
        for i in range(5,-1,-1):
            points[i] = points[i+1]+(points[i]-points[i+1]).normalized()*lengths[i]
        points[0] = root.copy()
        for i in range(6):
            points[i+1] = points[i]+(points[i+1]-points[i]).normalized()*lengths[i]
        if (points[-1]-target).length<1e-7:
            break
    for i,bone in enumerate(bones):
        motion.rotate(bone,(bone.tail-bone.head).rotation_difference(points[i+1]-points[i]))
    assert (bones[-1].tail-target).length<1e-5


def apply():
    scene,rig,mesh = motion.objects()
    # Always start from the preserved revision, including repeat runs through MCP.
    with bpy.data.libraries.load(str(BASELINE/'mm6_demon_native_animations.blend')) as (available,loaded):
        loaded.scenes = ['MM6_Demon_Native_Animations']
    previous = loaded.scenes[0]
    old_rig = next(o for o in previous.objects if o.type=='ARMATURE')
    for track in rig.animation_data.nla_tracks:
        strip = next(t.strips[0] for t in old_rig.animation_data.nla_tracks if t.name==track.name)
        track.strips[0].action = strip.action.copy()
        track.strips[0].action_slot = track.strips[0].action.slots[0]
    bpy.data.scenes.remove(previous)
    source = np.load(BASELINE/'source_geometry.npz')
    rest = source['vertices']
    changed = rest.copy()
    names = list(source['group_names'])
    for side in ('Right','Left'):
        foot = rig.data.bones['mixamorig:'+side+'Foot']
        weight = source['weights'][:,names.index(foot.name)]
        height = np.clip((.34-rest[:,2])/.12,0,1)
        blend = height*height*(3-2*height)*weight
        forward = rest[:,1]<foot.head_local.y
        changed[:,1] += blend*(rest[:,1]-foot.head_local.y)*np.where(forward,.30,-.50)
        changed[:,0] += blend*(rest[:,0]-foot.head_local.x)*.12
        rear = np.clip((rest[:,1]-foot.head_local.y-.015)/.07,0,1)
        rear = rear*rear*(3-2*rear)
        changed[:,2] -= blend*np.maximum(rest[:,2]-.006,0)*(.12+.65*rear)
    mesh.data.vertices.foreach_set('co',changed.astype(np.float32).ravel())
    mesh.data.update()
    changed = np.array([v.co for v in mesh.data.vertices])
    geometry = {key:source[key] for key in source.files}
    geometry['vertices'] = changed
    np.savez_compressed(STAGE/'source_geometry.npz',**geometry)
    clips = {**motion.ENDS,'Attack':36,'Walking':50,'Running':32}
    frames, samples, actions = {}, {}, {}
    for clip in clips:
        action = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name==clip)
        bag = action.layers[0].strips[0].channelbag(action.slots[0])
        frames[clip] = sorted({float(k.co.x) for c in bag.fcurves for k in c.keyframe_points})
        if clip=='Running':
            frames[clip] = list(np.arange(0,clips[clip]+.01,.25))
        actions[clip] = action
        samples[clip] = []
        for frame in frames[clip]:
            motion.activate(clip,frame)
            samples[clip].append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
    report = dict(changed_vertices=np.where(np.any(changed!=rest,axis=1))[0].tolist(),
                  unchanged_topology_weights_bind=True, tail_depth_factor=.72,
                  tail_front_tip_preserved=True, forefoot_length_factor=1.30,
                  foot_width_factor=1.12, rear_spur_length_factor=.50,
                  minimum_authored_sole_clearance=.006,
                  maximum_extra_root_drop=0., revised_clips={})
    foot_masks = {side:source['weights'][:,names.index('mixamorig:'+side+'Foot')]>.999 for side in ('Right','Left')}
    for clip in clips:
        corrected = []
        for frame,basis in zip(frames[clip],samples[clip]):
            for track in rig.animation_data.nla_tracks:
                track.mute = True
            rig.animation_data.action = None
            for bone in rig.pose.bones:
                bone.matrix_basis = basis[bone.name]
            bpy.context.view_layer.update()
            targets = {}
            for side,mask in foot_masks.items():
                foot = rig.pose.bones['mixamorig:'+side+'Foot']
                transform = np.array(foot.matrix@foot.bone.matrix_local.inverted())
                new_min = (changed[mask]@transform[:3,:3].T+transform[:3,3])[:,2].min()
                target = foot.head.copy()
                # Keep the original airborne ankle path; only lift a foot that crosses the support plane.
                target.z += float(max(0,.006-new_min))
                targets[side] = (target,foot.matrix.to_quaternion(),rig.pose.bones['mixamorig:'+side+'Leg'].head.copy())
            for side,(target,orientation,knee) in targets.items():
                if abs(target.z-rig.pose.bones['mixamorig:'+side+'Foot'].head.z)>1e-7:
                    solve_leg(rig,side,target,orientation,knee)
            if clip not in ('Walking','Running'):
                tighten_tail(rig)
            for bone in rig.pose.bones:
                bone.rotation_mode = 'QUATERNION'
                if bone.name!='mixamorig:Hips':
                    bone.location = (0,0,0)
                bone.scale = (1,1,1)
            bpy.context.view_layer.update()
            corrected.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
        allowed = set(LEGS+(TAIL if clip not in ('Walking','Running') else []))
        bag = actions[clip].layers[0].strips[0].channelbag(actions[clip].slots[0])
        for curve in bag.fcurves:
            name = json.loads(curve.data_path.split('[')[1].split(']')[0])
            prop = curve.data_path.rsplit('.',1)[1]
            if not (name in allowed and prop=='rotation_quaternion'):
                continue
            rotations = []
            for sample in corrected:
                q = sample[name].to_quaternion()
                if rotations and q.dot(rotations[-1])<0:
                    q.negate()
                rotations.append(q)
            curve.keyframe_points.clear()
            curve.keyframe_points.add(len(corrected))
            for index,point in enumerate(curve.keyframe_points):
                point.co = (frames[clip][index],rotations[index][curve.array_index])
                point.interpolation = 'LINEAR'
            curve.update()
        np.savez_compressed(STAGE/(clip+'_baked.npz'),
                            basis=np.array([[np.array(s[b.name]) for b in rig.pose.bones] for s in corrected]),
                            bone_names=np.array([b.name for b in rig.pose.bones]))
        report['revised_clips'][clip] = dict(samples=len(corrected),tail_changed=clip not in ('Walking','Running'))
        print('Revised profile',clip,len(corrected),'samples',flush=True)
    motion.activate('Standing',0)
    camera = scene.camera
    center,direction = Vector((0,0,.91)),Vector((-6,0,0))
    camera.location = center+direction
    camera.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale = 2.55
    scene.render.resolution_x,scene.render.resolution_y = 760,800
    (STAGE/'profile_changes.json').write_text(json.dumps(report,indent=2)+'\n')
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(STAGE/'authored_checkpoint.blend'),compress=True)
    print('Saved profile revision; changed foot vertices',len(report['changed_vertices']),flush=True)
    return report
