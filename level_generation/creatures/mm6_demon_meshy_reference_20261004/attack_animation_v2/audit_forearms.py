import bpy
import importlib
import sys
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v2')
sys.path.insert(0, str(stage))
sys.modules.pop('motion', None)
import motion
scene, rig, mesh = motion.objects()
rig.hide_set(False)
rig.animation_data.action = None
for track in rig.animation_data.nla_tracks:
    track.mute = True
source = np.load(stage / 'source_geometry.npz')
names = list(source['group_names'])
v = source['vertices']
report = []
motion.TWIST_HISTORY.clear()
for frame in range(37):
    motion.pose_at(frame)
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    posed = np.array([tuple(vertex.co) for vertex in temporary.vertices])
    evaluated.to_mesh_clear()
    row = {'frame': frame, 'sides': {}}
    for side in ('Right', 'Left'):
        lower = rig.pose.bones['mixamorig:' + side + 'ForeArm']
        hand = rig.pose.bones['mixamorig:' + side + 'Hand']
        elbow = np.array(lower.head)
        wrist = np.array(hand.head)
        original_elbow = np.array(lower.bone.head_local)
        original_wrist = np.array(hand.bone.head_local)
        delta = original_wrist - original_elbow
        axis = delta / np.linalg.norm(delta)
        t = (v - original_elbow) @ delta / np.dot(delta, delta)
        radius = np.linalg.norm(v - original_elbow - np.outer((v-original_elbow)@axis, axis), axis=1)
        posed_axis = (wrist-elbow)/np.linalg.norm(wrist-elbow)
        posed_radius = np.linalg.norm(posed-elbow-np.outer((posed-elbow)@posed_axis,posed_axis),axis=1)
        core = (source['weights'][:,names.index(lower.name)]>.8)&(t>.2)&(t<.8)&(radius>.015)
        ratio = posed_radius[core]/radius[core]
        wrist_delta = hand.matrix.to_quaternion() @ lower.matrix.to_quaternion().inverted()
        digit_bases = [rig.data.bones['mixamorig:' + side + 'Hand' + digit + '1'].head_local
                       for digit in ('Index','Middle','Pinky','Ring')]
        rest_long = sum(digit_bases, Vector()) / 4 - hand.bone.head_local
        world_long = hand.matrix.to_quaternion() @ hand.bone.matrix_local.to_quaternion().inverted() @ rest_long
        row['sides'][side] = {
            'pronation_degrees': float(np.rad2deg(motion.TWIST_HISTORY[side])),
            'core_radius_ratio_min': float(ratio.min()),
            'core_radius_ratio_median': float(np.median(ratio)),
            'wrist_bend_degrees': float(np.rad2deg(world_long.angle(hand.head-lower.head))),
            'elbow': elbow.tolist(), 'wrist': wrist.tolist(),
        }
    report.append(row)
(stage / 'forearm_pose_audit.json').write_text(json.dumps(report, indent=2)+'\n')
for row in report:
    if row['frame'] in (0,6,12,18,19,20,21,22,23,24,26,28,30):
        print(row['frame'],{side:{k:round(value,3) for k,value in data.items() if isinstance(value,float)} for side,data in row['sides'].items()})
