import bpy,json,sys,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene);out=P/'review/clay';out.mkdir(exist_ok=True);rows={};post={};points={}
for role in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows[role]=[];post[role]=[];points[role]=[]
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f);pel=rig.pose.bones['B_Pelvis'].head;neck=rig.pose.bones['B_Neck'].head;d=neck-pel;post[role].append({'frame':f,'pelvis_z':pel.z,'trunk_lean_deg':float(np.degrees(np.arctan2(np.hypot(d.x,d.y),d.z)))})
  if role in ['Death','Hit']:points[role].append({'f':f,'shoulder':list(rig.pose.bones['B_R_UpperArm'].head),'hand':list(rig.pose.bones['B_R_Hand'].head)})
 for i,f in enumerate(np.linspace(*a.frame_range,5)):
  scene.frame_set(int(f),subframe=float(f-int(f)))
  for v in ['front','left','three_quarter']:
   path=common.render_views(str(out/f'{role}_{i}'),.9,3.3,views=(v,),resolution=(270,390))[0];rows[role].append({'view':v,'seconds':float(f/30),'path':str(Path(path).relative_to(P))})
(P/'review/clay/frames.json').write_text(json.dumps(rows,indent=2));(P/'work/posture_pilot.json').write_text(json.dumps(post,indent=2));(P/'work/points_pilot.json').write_text(json.dumps(points,indent=2))
args=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
for n,extra in [('g5_hand_stretch.py',args),('g4_weights.py',['pilot']+[f'{r}:{f}'for r in args for f in range(0,int(bpy.data.actions[r].frame_range[1])+1,3)]),('g6_contacts.py',args)]:
 sys.argv=[n,'--',str(P/'work/animated_master.blend'),*extra];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
