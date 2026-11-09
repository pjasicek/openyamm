from pathlib import Path
import sys,runpy,os,bpy,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
s=p/'scripts/author_motion.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
os.environ['TWIST_BAKE_ONLY']='1';os.environ['FA']='.65';os.environ['FA_RAMP']='.15,.85'
s=p/'scripts/twist_bones.py';sys.argv=[str(s),'--',str(p/'work/motion_fitted.blend'),str(p/'work/motion_final.blend')];runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig'];common.workbench_clay(bpy.context.scene)
for name,fs in {'Attack':[7,12,18,24,27,30,34], 'Walking':[0,9,18,27], 'Running':[0,6,12,18], 'Death':[0,20,40,60,78]}.items():
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in fs:
  bpy.context.scene.frame_set(f);common.render_views(str(p/f'review/motion_final_{name}_{f:02}'),1.4,3.1,views=('front','left'),resolution=(500,700))
