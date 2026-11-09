import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/accepted_master.blend'))
with bpy.data.libraries.load(str(P/'work/round2_sources.blend'))as(s,d):d.actions=['Overhead','Recoil']
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,textured=True)
rows={}
for role in ['Overhead','Recoil']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows[role]=[]
 for i in range(9):
  f=a.frame_range[1]*i/8;sc.frame_set(int(f),subframe=f%1)
  rows[role].append({'f':f,'hand':list(rig.pose.bones['B_R_Hand'].head),'elbow':list(rig.pose.bones['B_R_Forearm'].head)})
  common.render_views(str(P/f'review/round2/source_{role}_{i}'),1,2.6,views=('front','left'),resolution=(240,320))
(P/'review/round2/source_samples.json').write_text(json.dumps(rows,indent=2))
