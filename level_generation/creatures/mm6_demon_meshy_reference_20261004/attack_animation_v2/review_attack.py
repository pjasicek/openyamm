import bpy
import importlib
import itertools
import json
import numpy as np
import sys
from pathlib import Path
from mathutils.bvhtree import BVHTree

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v2')
if str(stage) not in sys.path:
    sys.path.insert(0, str(stage))
import motion
importlib.reload(motion)
scene, rig, obj = motion.objects()
action = bpy.data.actions['Demon_Native_Attack_v2']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene.render.resolution_x = 1300
scene.render.resolution_y = 1100
data = np.load(stage / 'source_geometry.npz')
rest, faces, original_weights = data['vertices'], data['faces'], data['weights']
names = list(data['group_names'])
edges = np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
rest_lengths = np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
rest_area = np.linalg.norm(np.cross(rest[faces[:,1]]-rest[faces[:,0]],rest[faces[:,2]]-rest[faces[:,0]]),axis=1)
masks = json.loads((stage / 'tip_vertex_masks.json').read_text())
body_columns = [i for i,n in enumerate(names) if n in ('mixamorig:Hips','mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2')]
body = original_weights[:,body_columns].sum(1)>.70
body_faces = faces[np.all(body[faces],axis=1)]
hands = {}
for side in ('Right','Left'):
    columns=[i for i,n in enumerate(names) if n.startswith('mixamorig:'+side+'Hand')]
    selected=original_weights[:,columns].sum(1)>.75
    hands[side] = faces[np.all(selected[faces],axis=1)]
foot_ids = {side: np.flatnonzero(original_weights[:,names.index('mixamorig:'+side+'Foot')]>.999) for side in ('Right','Left')}
tip_edges = {name: np.all(np.isin(edges, ids),axis=1) for name,ids in masks.items()}
rows=[]
foot_first={}
previous_matrices=None
for time in np.arange(0,36.01,.25):
    scene.frame_set(int(time),subframe=float(time%1))
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    v=np.array([tuple(vertex.co) for vertex in mesh.vertices])
    evaluated.to_mesh_clear()
    ratio=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1)/rest_lengths
    area=np.linalg.norm(np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]]),axis=1)/rest_area
    row={'frame':float(time),'time_ms':float(time/48*1000), 'arms':{},'feet':{},'hard_tips':{},'digit_gaps':{},'hand_body_intersections':{}}
    for side in ('Right','Left'):
        upper,lower,hand=[rig.pose.bones['mixamorig:'+side+suffix] for suffix in ('Arm','ForeArm','Hand')]
        lengths=((lower.head-upper.head).length,(hand.head-lower.head).length)
        expected=((lower.bone.head_local-upper.bone.head_local).length,(hand.bone.head_local-lower.bone.head_local).length)
        errors=[abs(a/b-1) for a,b in zip(lengths,expected)]
        row['arms'][side]={'length_relative_error':max(errors),'elbow':list(lower.head),'wrist':list(hand.head),
                           'wrist_local_rotation_degrees':float(hand.rotation_quaternion.angle*180/np.pi)}
        points=v[foot_ids[side]]
        if time==0:foot_first[side]=points.copy()
        row['feet'][side]={'rigid_sole_height':float(points[:,2].min()),'maximum_drift':float(np.linalg.norm(points-foot_first[side],axis=1).max())}
        hand_bvh=BVHTree.FromPolygons(v.tolist(),hands[side].tolist(),all_triangles=True)
        body_bvh=BVHTree.FromPolygons(v.tolist(),body_faces.tolist(),all_triangles=True)
        row['hand_body_intersections'][side]=len(hand_bvh.overlap(body_bvh))
        for first,second in itertools.combinations(('Thumb','Index','Middle','Pinky','Ring'),2):
            a,b=v[masks[side+'_'+first]],v[masks[side+'_'+second]]
            row['digit_gaps'][side+'_'+first+'_'+second]=float(np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2).min())
    for name,es in tip_edges.items():
        row['hard_tips'][name]=float(np.abs(ratio[es]-1).max())
    row['minimum_triangle_area_ratio']=float(area.min())
    row['triangle_area_ratios_below_01']=int((area<.1).sum())
    row['maximum_bone_scale_error']=max(max(abs(x-1) for x in b.scale) for b in rig.pose.bones)
    current={b.name:b.matrix.to_quaternion() for b in rig.pose.bones}
    row['maximum_quarter_sample_rotation_degrees']=0 if previous_matrices is None else max(
        2*np.arccos(min(1,abs(previous_matrices[name].dot(quat))))*180/np.pi for name,quat in current.items())
    previous_matrices=current
    rows.append(row)
summary={
    'samples':len(rows),'duration_seconds':.75,'output_samples':37,'bone_count':len(rig.data.bones),
    'maximum_arm_length_relative_error':max(a['length_relative_error'] for r in rows for a in r['arms'].values()),
    'maximum_rigid_tip_edge_relative_error':max(x for r in rows for x in r['hard_tips'].values()),
    'minimum_rigid_sole_height':min(a['rigid_sole_height'] for r in rows for a in r['feet'].values()),
    'maximum_foot_drift':max(a['maximum_drift'] for r in rows for a in r['feet'].values()),
    'minimum_distal_digit_surface_gap':min(x for r in rows for x in r['digit_gaps'].values()),
    'maximum_hand_torso_triangle_intersections':max(x for r in rows for x in r['hand_body_intersections'].values()),
    'minimum_triangle_area_ratio':min(r['minimum_triangle_area_ratio'] for r in rows),
    'maximum_quarter_sample_rotation_degrees':max(r['maximum_quarter_sample_rotation_degrees'] for r in rows),
    'numerical_review_only':True,
}
(stage/'deformation_review.json').write_text(json.dumps({'summary':summary,'samples':rows},indent=2)+'\n')
print(json.dumps(summary,indent=2))
frames=stage/'review_frames'
frames.mkdir(exist_ok=True)
for frame in range(37):
    scene.frame_set(frame)
    motion.render('review_frames/front_'+f'{frame:02d}')
    motion.render('review_frames/side_'+f'{frame:02d}',(6,0,0))
    if frame%6==0:
        motion.render('review_frames/rear_'+f'{frame:02d}',(0,6,0))
        motion.render('review_frames/threequarter_'+f'{frame:02d}',(4,-6,.25))
        motion.render('review_frames/opposite_'+f'{frame:02d}',(-6,0,0))
# Locomotion remains the same bone motion; repaired jaw/tips also need representative visual checks.
for clip,end in [('Walking',50),('Running',32)]:
    act=bpy.data.actions['Demon_Package_'+clip]
    rig.animation_data.action=act
    rig.animation_data.action_slot=act.slots[0]
    for frame in np.linspace(0,end,7):
        scene.frame_set(int(frame),subframe=float(frame%1))
        motion.render('review_frames/'+clip.lower()+'_'+f'{frame:05.2f}',(3,-6,.25))
rig.animation_data.action=action
rig.animation_data.action_slot=action.slots[0]
scene.frame_set(24)
motion.render('preview')
print('Rendered all 37 poses front/profile; seven rear, opposite-profile and three-quarter poses; locomotion checks.')
