import bpy, json, math, runpy, sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
OLD = P.parent
REPO = OLD.parents[3]
bpy.ops.wm.open_mainfile(filepath=str(P / 'master_weights.blend'))
rig = bpy.data.objects['Lizardman_Rig']
body = bpy.data.objects['Lizardman_Body']
scene = bpy.context.scene
assert len(rig.data.bones) == 40
assert all(abs(v - 1) < 1e-6 for v in rig.scale)
for track in rig.animation_data.nla_tracks:
    track.mute = True
names = [g.name for g in body.vertex_groups]
rest = np.array([v.co[:] for v in body.data.vertices])
edges = np.array([e.vertices[:] for e in body.data.edges])
lengths = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
regions = {}
for region, groups in {
    'hands': [n for n in names if any(k in n for k in ('Hand', 'Thumb', 'Digit'))],
    'arms': [n for n in names if 'Arm' in n],
    'left_foot': ['LeftFoot', 'LeftToeBase'],
    'right_foot': ['RightFoot', 'RightToeBase'],
}.items():
    regions[region] = np.array([sum(g.weight for g in v.groups if names[g.group] in groups) > .5
                                for v in body.data.vertices])
report = {'fps': scene.render.fps, 'bones': [b.name for b in rig.data.bones], 'clips': {}}
for name in ['Standing', 'Walk', 'Hit', 'Fidget', 'Death', 'Corpse']:
    action = bpy.data.actions[name]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    start, end = action.frame_range
    frames = np.arange(start, end + .001, .5)
    soles, ratios, rotations = [], [], []
    for frame in frames:
        scene.frame_set(int(frame), subframe=float(frame % 1))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = ev.to_mesh()
        xyz = np.array([(ev.matrix_world @ v.co)[:] for v in mesh.vertices])
        ev.to_mesh_clear()
        assert len(xyz) == len(rest)
        soles.append([float(xyz[regions[k], 2].min()) for k in ['left_foot', 'right_foot']])
        ratios.append(np.linalg.norm(xyz[edges[:, 0]] - xyz[edges[:, 1]], axis=1) / np.maximum(lengths, 1e-9))
        rotations.append({b.name: b.matrix.to_quaternion().copy() for b in rig.pose.bones})
    ratios = np.array(ratios)
    result = {'duration': float((end-start)/scene.render.fps), 'samples': len(frames),
              'sole_min_m': np.min(soles,axis=0).tolist(), 'grounded_sole_max_m': float(np.min(soles,axis=1).max()),
              'edge_max': float(ratios.max()), 'edge_p99': float(np.percentile(ratios,99))}
    for region in ['hands','arms']:
        mask = regions[region][edges].all(axis=1) & (lengths > .0001)
        result[region] = {'edge_max': float(ratios[:,mask].max()), 'edge_p99': float(np.percentile(ratios[:,mask],99))}
    worst = np.unravel_index(np.argmax(ratios), ratios.shape)
    edge = edges[worst[1]]
    result['worst_edge'] = {'frame':float(frames[worst[0]]), 'length_m':float(lengths[worst[1]]),
        'vertices':[{'id':int(i),'rest':rest[i].tolist(),
          'weights':{names[g.group]:g.weight for g in body.data.vertices[i].groups}} for i in edge]}
    result['max_rotation_step_degrees'] = {}
    for bone in ['Head','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftHand','RightHand']:
        steps = [math.degrees(a[bone].rotation_difference(b[bone]).angle) for a,b in zip(rotations,rotations[1:])]
        result['max_rotation_step_degrees'][bone] = max(min(x,360-x) for x in steps)
    report['clips'][name] = result
    print('PROBE',name,json.dumps(result),flush=True)
(P/'review/rig_probe_corrected.json').write_text(json.dumps(report,indent=2)+'\n')
