from pathlib import Path
import bpy,sys,runpy,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
out=p/'review/selected_clay';out.mkdir(exist_ok=True)
for name,frames in [('Running',[0,4,8,12,16,20]),('Standing',[0]),('Death',[20,57]) ]:
 a=bpy.data.actions[name];r.animation_data.action=a
 if a.slots:r.animation_data.action_slot=a.slots[0]
 for f in frames:
  sc.frame_set(f);common.render_views(str(out/f'{name}_{f:02}'),.85,2.7,views=('left','front'),resolution=(480,400),target=(0,.35))
