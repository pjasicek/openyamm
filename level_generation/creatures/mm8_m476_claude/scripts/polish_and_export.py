from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('polish_idle.py')
run('sync_actions.py',p/'work/rig_v5.blend',p/'work/rig_v6.blend')
os.environ['STEP']='0.5';run('sole_probe.py',p/'work/rig_v5.blend','Standing','Walking','Attack','Hit','Fidget','Death')
run('g4_weights.py',p/'work/rig_v5.blend','final','Standing:0','Attack:25','Attack:28','Attack:34','Walking:6','Running:6','Hit:8','Fidget:30','Death:20')
run('export_runtime.py')
