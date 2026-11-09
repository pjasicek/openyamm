from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
run('polish_motion.py',[])
run('foot_level.py',[p/'work/polished.blend',p/'work/levelled.blend','Standing','Walking:const','Attack','Hit','Fidget','Death:until=8','Running:const'])
run('floor_motion.py',[])
for view in ['front','left']:
 run('clip_sheet.py',[p/'work/animated.blend',p/'review/finished_motion'/view,view,'6','Standing','Walking','Attack','Hit','Death','Fidget','Running'])
run('g6_contacts.py',[p/'work/animated.blend','Standing','Walking','Attack','Hit','Death','Fidget','Running'])
