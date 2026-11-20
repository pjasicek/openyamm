import bpy,sys,json,runpy,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2';roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];results=[]
def run(name,args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
for level in range(4):
 src=W/f'selected_body_l{level}.blend';tag=f'round2_l{level}';bpy.ops.wm.open_mainfile(filepath=str(src));fps=bpy.context.scene.render.fps;picks=[f'{r}:{f}'for r in roles for f in np.arange(0,float(bpy.data.actions[r].frame_range[1])+.001,fps/48)]
 run('g4_round2.py',[src,tag,*picks]);run('g5_round2.py',[src,*roles]);run('g6_contacts_round2.py',[src,*roles]);run('g6_cloth_round2.py',[src,*roles])
 files={}
 for old,new in [(f'g4_{tag}.json',f'g4_l{level}.json'),('g5_final.json',f'g5_l{level}.json'),('g6_contacts.json',f'g6_contacts_l{level}.json'),('g6_fauld.json',f'g6_cloth_l{level}.json')]:shutil.copyfile(P/'work'/old,R/new);files[new]=json.loads((R/new).read_text())
 g4=files[f'g4_l{level}.json'];g5=files[f'g5_l{level}.json'];contact=files[f'g6_contacts_l{level}.json'];cloth=files[f'g6_cloth_l{level}.json'];p99=max(v['stretch_p99']for row in g4.values()for v in row.values());edge=max(v['stretch_max']for row in g4.values()for v in row.values());hand=max(v['max_edge_stretch']for row in g5.values()for v in row.values());cm=max([v[0]for row in contact.values()for k,v in row.items()if k!='max_clear_blade_m']or [0]);fm=max(v['depth_m']for v in cloth.values())
 sys.path.insert(0,str(P/'scripts'));from g6_head_clearance import Clearance
 C=Clearance(bpy.data.objects['Body']);rig=bpy.data.objects['Rig'];head={}
 for role in roles:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];depth=0.
  for f in np.arange(0,float(a.frame_range[1])+.001,bpy.context.scene.render.fps/48):
   bpy.context.scene.frame_set(int(f),subframe=float(f%1));depth=max(depth,C.measure()[0])
  head[role]=depth
 (R/f'g6_head_l{level}.json').write_text(json.dumps(head,indent=2));hm=max(head.values())
 result={'lod':level,'samples_g4':len(g4),'sample_hz':48,'arm_p99':p99,'arm_max':edge,'hand_max':hand,'body_contact_max_mm':cm,'cloth_max_mm':fm*1000,'head_max_mm':hm*1000,'pass':hm<=.005 and p99<=2 and edge<=4.5 and hand<=4.5 and cm<=2 and fm<=.002};results.append(result);(R/'body_gate_summary.json').write_text(json.dumps(results,indent=2));print('BODY GATES',json.dumps(result),flush=True)
