from pathlib import Path
import runpy,sys,json,bpy
P=Path(__file__).resolve().parents[1];W=P/'work'
def run(n,args):
 s=P/'scripts'/n;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
run('twist_bones.py',[W/'all_motion_clear.blend',W/'all_twist.blend'])
run('foot_level.py',[W/'all_twist.blend',W/'levelled.blend','Standing','Walking:const','Running:const','Attack','Hit','Fidget','Death:until=10'])
run('floor_motion.py',[])
picks=[]
for n in roles:
 a=bpy.data.actions[n];picks += [f'{n}:{i}' for i in range(0,int(a.frame_range[1])+1,3)]
run('g4_weights.py',[W/'animated.blend','all',*picks])
run('g5_hand_stretch.py',[W/'animated.blend',*roles])
for v in ['front','left']:run('clip_sheet.py',[W/'animated.blend',P/f'review/all_motion/{v}',v,6,*roles])
