"""Check changed body delivery, early elbow continuity and exported arm/wing clearance."""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree

P = Path(__file__).resolve().parents[1]
W = P / 'work/attack_v6'
report = {}
for label, path in [('before', W/'before.blend'), ('after', P/'export/mm6_gar.blend'),
                    ('export', P/'export/mm6_gar_lod0.glb')]:
    if label == 'export':
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
    else:
        bpy.ops.wm.open_mainfile(filepath=str(path))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    obj = bpy.data.objects['Gargoyle']
    scene = bpy.context.scene
    action = next(a for a in bpy.data.actions if a.name == 'Attack' or a.name.endswith('|Attack'))
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    fps = scene.render.fps / scene.render.fps_base
    rows = []
    for frame in range(361):
        t = frame / 240
        f = t * fps
        scene.frame_set(math.floor(f), subframe=f % 1)
        row = {'time': t}
        for name in ['B_Pelvis', 'B_Neck', 'B_R_Forearm', 'B_R_Hand']:
            # Convert imported glTF Y-up coordinates back to Blender's authored frame.
            xyz = rig.matrix_world @ rig.pose.bones[name].head
            row[name] = list(xyz)
        d = np.array(row['B_Neck']) - row['B_Pelvis']
        row['lean_degrees'] = math.degrees(math.atan2(-d[1], d[2]))
        rows.append(row)
    elbow = np.array([r['B_R_Forearm'] for r in rows])
    report[label] = {'samples': rows, 'early_peak_elbow_speed_m_s': float(np.linalg.norm(np.diff(elbow[:73],axis=0),axis=1).max()*240),
                     'frame_6_to_8_elbow_travel_m': float(np.linalg.norm(elbow[40]-elbow[30]))}
    if label == 'export':
        rest = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
        obj.data.calc_loop_triangles()
        faces = [tuple(t.vertices) for t in obj.data.loop_triangles]
        def weight(terms):
            return np.array([sum(g.weight for g in v.groups if any(s in obj.vertex_groups[g.group].name for s in terms))
                             for v in obj.data.vertices])
        wing = weight(['W_'])
        wf = [f for f in faces if min(wing[list(f)]) > .45]
        af, masks = {}, {}
        for side in 'LR':
            shoulder = np.array(rig.matrix_world @ rig.data.bones[f'B_{side}_UpperArm'].head_local)
            aw = weight([f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand', f'B_{side}_Finger'])
            away = np.linalg.norm(rest-shoulder,axis=1) > .12
            af[side] = [f for f in faces if min(aw[list(f)]) > .55 and all(away[list(f)])]
            masks[side] = np.where((weight([f'B_{side}_Forearm', f'B_{side}_Hand', f'B_{side}_Finger']) > .8) & (wing < .01))[0]
            assert len(af[side]) > 100 and len(masks[side]) > 100
        pairs, clearance = 0, float('inf')
        for frame in range(181):
            f = frame / 120 * fps
            scene.frame_set(math.floor(f), subframe=f % 1)
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = ev.to_mesh()
            co = [obj.matrix_world @ v.co for v in mesh.vertices]
            ev.to_mesh_clear()
            tree = BVHTree.FromPolygons(co, wf, all_triangles=True)
            for side in 'LR':
                pairs = max(pairs, len(tree.overlap(BVHTree.FromPolygons(co, af[side], all_triangles=True))))
                clearance = min(clearance, min(tree.find_nearest(co[int(i)])[3] for i in masks[side]))
        report['clearance'] = {'samples': 181, 'maximum_intersecting_triangle_pairs': pairs,
                               'minimum_forearm_hand_clearance_m': clearance}
        assert pairs == 0 and clearance > .02
for label in ['after', 'export']:
    assert report[label]['early_peak_elbow_speed_m_s'] < 2
    assert report[label]['frame_6_to_8_elbow_travel_m'] < .06
for frame in [0, 360]:
    for name in ['B_Pelvis', 'B_Neck', 'B_R_Forearm', 'B_R_Hand']:
        assert np.allclose(report['before']['samples'][frame][name], report['after']['samples'][frame][name], atol=1e-5)
before = report['before']['samples']
after = report['after']['samples']
assert after[103]['lean_degrees'] < before[103]['lean_degrees'] - 8
assert after[180]['lean_degrees'] > before[180]['lean_degrees'] + 8
reach = min(after, key=lambda r: r['B_R_Hand'][1])
report['impact'] = {'event_seconds': .75, 'maximum_wrist_forward_reach_seconds': reach['time']}
assert abs(reach['time'] - .75) <= .025
(W/'motion_check.json').write_text(json.dumps(report, indent=2)+'\n')
print('MOMENTUM_CHECK', {k: {n:v for n,v in r.items() if n != 'samples'} for k,r in report.items()})
