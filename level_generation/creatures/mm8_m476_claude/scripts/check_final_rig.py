from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('check_contacts.py')
a=['Standing','Walking','Running','Attack','Hit','Fidget','Death'];blend=p/'work/rig_v5.blend'
os.environ['STEP']='0.5';run('sole_probe.py',blend,*a)
run('jerk_probe.py',blend,*a)
