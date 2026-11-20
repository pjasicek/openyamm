from pathlib import Path
import bpy,sys,runpy,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_gated.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
out=p/'review/final_clay';out.mkdir(exist_ok=True)
for name,frames in [('Death',[0,10,20,30,40,57]),('Walking',[0,4,8,12,16,20]),('Running',[0,4,8,12,16,20]),('Attack',[0,10,20,30,38,46]),('Hit',[0,3,6,9,12,15])]:
 a=bpy.data.actions[name];r.animation_data.action=a
 if a.slots:r.animation_data.action_slot=a.slots[0]
 for f in frames:
  sc.frame_set(f);common.render_views(str(out/f'{name}_{f:02}'),.85,2.7,views=('left',),resolution=(480,400),target=(0,.35))
runpy.run_path(str(p/'scripts/inspect_contacts.py'),run_name='__main__')
