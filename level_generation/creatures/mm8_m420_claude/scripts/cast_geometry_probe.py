import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];rows={}
for label,file,clip,time in [('ours',P/'review/cast_revision/baseline/work/master_settled.blend','Standing',0),('sorcerer_stand',P.parent/'mm6_sor1_codex/work/production_master.blend','Cast',0),('sorcerer_release',P.parent/'mm6_sor1_codex/work/production_master.blend','Cast',.7375)]:
 bpy.ops.wm.open_mainfile(filepath=str(file));rig=bpy.data.objects['Rig'];a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=time*bpy.context.scene.render.fps;bpy.context.scene.frame_set(int(f),subframe=f%1)
 rows[label]={n:list((rig.matrix_world@rig.pose.bones[n].matrix).translation) for n in ['B_R_Clavicle','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_Pelvis','B_Head']}
print('GEOMETRY',json.dumps(rows),flush=True)
(P/'review/cast_revision/arm_geometry.json').write_text(json.dumps(rows,indent=2))
