"""Inspect the affected poses and repeat the contact gates on the verified UV master."""
import bpy,runpy,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
rows=[]
for name,frames in [('Attack',[0,18,42,75,160,180,198,210]),('Walking',[0,12,24,36,48,60,72,84]),('Running',[0,11,22,33,44,55,66,77])]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for view in ('front','left'):
  row=[]
  for f in frames:
   sc.frame_set(f)
   path=common.render_views(str(P/f'review/foot_revision/{name}_{f}'),.63,1.65,(view,),resolution=(320,380))[0]
   row.append([path,f'{name} {view} {f}'])
  rows.append(row)
(P/'review/foot_revision/frames.json').write_text(json.dumps(rows))
os.environ['M632_CHECK_BLEND']='work/textured_uv.blend';os.environ['M632_CHECK_CLIPS']='Walking,Running,Attack'
for name in ('contacts.py','grip_contacts.py'):
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
