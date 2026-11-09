import bpy,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
sys.argv=['retarget.py','--',str(P/'work/master.blend'),str(P/'work/round4/source_set.blend'),str(R/'anim_library/humanoid_set/Relax.glb')+':RelaxIdle:SourceIdle',str(R/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedGetHitF1:SourceHit']
runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
sys.argv=['retarget_mixamo.py','--',str(P/'work/round4/source_set.blend'),str(P/'work/round4/sources.blend'),str(R/'anim_library/mixamo/Shooting Arrow.fbx')+':SourceShot']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;common.workbench_clay(sc,True)
for ob in bpy.data.objects:
 if ob.type=='MESH':ob.hide_render=ob!=b
report={}
for role,fs in [('SourceIdle',[0,30]),('SourceHit',[0,5,10,15]),('SourceShot',[0,20,40,60,80,100,120,150])]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];report[role]={}
 for f in fs:
  sc.frame_set(f);report[role][f]={n:list(r.pose.bones[n].head)for n in ['B_Pelvis','B_Head','B_L_UpperArm','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_Hand']}
  common.render_views(str(P/f'review/round4/source_{role}_{f}'),.9,2.2,views=('front','left'),resolution=(350,420))
(P/'review/round4/source_positions.json').write_text(json.dumps(report,indent=2))
