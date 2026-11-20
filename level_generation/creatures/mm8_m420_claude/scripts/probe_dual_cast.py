import bpy,math,json,sys
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set/Unarmed.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=next(a for a in bpy.data.actions if a.name.endswith('UnarmedCastDualAttack2'));r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
T=Matrix.Rotation(math.pi,4,'Z')@r.matrix_world;f0,f1=a.frame_range;out=[]
for k in range(121):
 f=f0+(f1-f0)*k/120;sc.frame_set(int(f),subframe=f%1);out.append({'t':k/120,'joints':{n:list((T@r.pose.bones[n].matrix).translation) for n in ['B_Pelvis','B_Head','B_R_Clavicle','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand']}})
(P/'review/dual_cast/source_probe.json').write_text(json.dumps(out,indent=2))
print('SOURCE',a.name,list(a.frame_range),(f1-f0)/30,flush=True)
for row in out[::10]:print(row,flush=True)
