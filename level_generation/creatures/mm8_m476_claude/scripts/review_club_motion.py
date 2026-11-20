from pathlib import Path
import runpy,sys,bpy,json
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('reduce_rigged.py',p/'work/motion_grip_smooth.blend',p/'work/rig_v5.blend')
run('attach_club.py')
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_club.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene,True)
for view in ['front','left','three_quarter']:
 rows=[]
 for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
  a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];row=[]
  for i in range(7):
   f=a.frame_range[1]*i/6;scene.frame_set(int(f),subframe=f-int(f))
   out=p/'review'/('club_motion_'+view);out.mkdir(exist_ok=True)
   path=common.render_views(str(out/f'{name}_{i}'),.8,2.6,views=(view,),resolution=(360,420))[0];row.append([path,f'{name} {f:.1f}'])
  rows.append(row)
 (p/'review'/('club_motion_'+view)/'frames.json').write_text(json.dumps(rows))
