from pathlib import Path
import bpy,math,json
p=Path(__file__).resolve().parents[1];root=p.parents[2];report={}
for clip in ['ArmedCastLAttack1']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(root/'anim_library/humanoid_set/Armed.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==clip);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;f0,f1=a.frame_range;rows={n:[] for n in ['B_L_UpperArm','B_L_Forearm','B_R_Hand']};f=f0
 while f<=f1:
  sc.frame_set(int(f),subframe=f-int(f))
  for n in rows:rows[n].append((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())
  f+=sc.render.fps/48
 report[clip]={}
 for n,qs in rows.items():
  steps=[min(math.degrees(a.rotation_difference(b).angle),360-math.degrees(a.rotation_difference(b).angle)) for a,b in zip(qs,qs[1:])];report[clip][n]={'step_deg':max(steps),'step_change_deg':max(abs(a-b) for a,b in zip(steps,steps[1:]))}
(p/'work/source_motion_audit.json').write_text(json.dumps(report,indent=2));print('SOURCE_MOTION',report)
