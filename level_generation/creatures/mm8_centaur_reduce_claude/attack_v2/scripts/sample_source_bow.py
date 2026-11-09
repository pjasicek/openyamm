"""Measure the stored humanoid bow shot (humanoid set 2Hand Bow, Attack1) in its own body frame: torso yaw against
the pelvis, bow-arm direction, draw-hand position against the shoulders, wrist bend, and the release frame (draw hand
speed peak). Output: attack_v2/work/source_bow.json. Usage: blender -b -P sample_source_bow.py -- [clip]"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[3]
clip = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '2HandBowAttack1'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'anim_library/humanoid_set/2Hand Bow.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[clip]; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(x) for x in act.frame_range); sc = bpy.context.scene
W = lambda n, tail=False: rig.matrix_world @ (rig.pose.bones[n].tail if tail else rig.pose.bones[n].head)
rows = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    pel = rig.matrix_world.to_3x3() @ rig.pose.bones['B_Pelvis'].matrix.to_3x3()
    sl, sr = W('B_L_UpperArm'), W('B_R_UpperArm'); mid = (sl + sr) / 2
    shoulder_axis = (sl - sr); shoulder_axis.z = 0
    hip_axis = W('B_L_Thigh') - W('B_R_Thigh'); hip_axis.z = 0
    yaw = math.degrees(hip_axis.angle(shoulder_axis)) * (1 if hip_axis.cross(shoulder_axis).z > 0 else -1)
    lh, rh = W('B_L_Hand'), W('B_R_Hand'); arm = (W('B_L_Forearm') - sl).length + (lh - W('B_L_Forearm')).length
    bow_dir = (lh - sl).normalized()
    def wrist(side):
        fa = (W(f'B_{side}_Hand') - W(f'B_{side}_Forearm')).normalized(); h = (W(f'B_{side}_Hand', True) - W(f'B_{side}_Hand')).normalized()
        return round(math.degrees(fa.angle(h)), 1)
    rows.append({'f': f, 'yaw_deg': round(yaw, 1), 'bow_elev_deg': round(math.degrees(math.asin(bow_dir.z)), 1),
                 'bow_reach': round((lh - sl).length / arm, 3), 'draw_from_mid': [round(x / arm, 3) for x in (rh - mid)],
                 'bow_from_mid': [round(x / arm, 3) for x in (lh - mid)], 'hands_dist': round((lh - rh).length / arm, 3),
                 'wrist_L': wrist('L'), 'wrist_R': wrist('R'), 'rh': list(rh)})
speed = [0] + [(Vector(rows[i]['rh']) - Vector(rows[i - 1]['rh'])).length for i in range(1, len(rows))]
release = max(range(len(rows)), key=lambda i: speed[i] if rows[i]['hands_dist'] > 0 else 0)
for r in rows: r.pop('rh')
out = {'clip': clip, 'frames': [f0, f1], 'fps': sc.render.fps, 'release_frame_by_draw_speed': rows[release]['f'], 'rows': rows}
(P / 'work').mkdir(exist_ok=True); (P / 'work/source_bow.json').write_text(json.dumps(out, indent=1))
print('SRC', clip, f0, f1, 'fps', sc.render.fps, 'release', rows[release]['f'])
for r in rows[::2]: print('ROW', r)
