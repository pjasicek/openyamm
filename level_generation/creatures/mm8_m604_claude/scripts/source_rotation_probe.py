from pathlib import Path
import bpy,numpy as np,json,math
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(p.parents[2]/'anim_library/humanoid_set/1Hand.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=next(a for a in bpy.data.actions if a.name.endswith('SwordAttackR6'));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
names=['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_Forearm','B_Spine2'];qs={n:[] for n in names}
for f in np.arange(a.frame_range[0],a.frame_range[1]+1e-5,30/48):
 sc.frame_set(int(f),subframe=float(f-int(f)))
 for n in names:qs[n].append(rig.pose.bones[n].matrix.to_quaternion())
r={}
for n,Q in qs.items():
 ds=np.array([min(math.degrees(x.rotation_difference(y).angle),360-math.degrees(x.rotation_difference(y).angle)) for x,y in zip(Q[:-1],Q[1:])]);r[n]={'step_deg_48Hz':float(ds.max()),'step_change_deg':float(np.abs(np.diff(ds)).max())}
(p/'work/source_attack_steps.json').write_text(json.dumps(r,indent=2));print('SOURCE_STEPS',r)
